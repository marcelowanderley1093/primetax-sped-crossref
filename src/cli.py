"""
CLI primetax-sped — entry point.

Comandos:
  import  <arquivo_ou_diretorio>              Importa SPED(s) para o banco SQLite.
  diagnose <cnpj> <ano>                       Executa cruzamentos e gera Excel.
  parecer  <cnpj> <ano> --tese <codigo>       Gera parecer Word por tese.
  reconciliacao-template <cnpj> <ano>         Gera template Excel para reconciliação manual.
  reconciliacao-import <cnpj> <ano> <xlsx>    Importa template preenchido (§16.6).

Exemplos:
  primetax-sped import data/input/12345678000100/202501/efd_contrib.txt
  primetax-sped import data/input/12345678000100/2025/
  primetax-sped import data/input/12345678000100/2025/ecf.txt --encoding latin1
  primetax-sped diagnose 12345678000100 2025
  primetax-sped parecer 12345678000100 2025 --tese tema-69
  primetax-sped reconciliacao-template 12345678000100 2025
  primetax-sped reconciliacao-import 12345678000100 2025 data/output/12345678000100/2025/reconciliacao_template.xlsx
"""

import argparse
import logging
import sys
from pathlib import Path

from src.crossref.engine import Motor
from src.db.repo import Repositorio
from src.parsers import ecd, ecf, efd_contribuicoes, efd_icms_ipi
from src.reports import (
    excel_diagnostico,
    excel_reconciliacao,
    excel_reconciliacao_import,
    word_parecer,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("primetax-sped")

_SUFIXOS_SPED = {".txt", ".sped", ".efd", ".ecf", ".ecd"}


# ------------------------------------------------------------------
# Detecção de tipo de SPED pelo registro 0000
# ------------------------------------------------------------------

def detectar_tipo_sped(caminho: Path) -> str:
    """
    Detecta o tipo de SPED lendo as primeiras 100 linhas.

    Retorna: 'efd_contribuicoes' | 'efd_icms_ipi' | 'ecd' | 'ecf' | 'desconhecido'

    Estratégia (CLAUDE.md §7.2):
      - campos[2] == 'LECF' → ECF
      - campos[2] == 'LECD' → ECD
      - Presença de registro '0110' (exclusivo da EFD-Contribuições) → efd_contribuicoes
      - Demais: efd_icms_ipi (por eliminação — após ECF/ECD identificados)
    """
    try:
        with caminho.open(encoding="latin-1", errors="replace") as f:
            for i, linha in enumerate(f):
                if i >= 100:
                    break
                campos = linha.strip().split("|")
                if len(campos) < 3:
                    continue
                reg = campos[1].strip().upper()
                if reg == "0000" and len(campos) >= 3:
                    marcador = campos[2].strip().upper()
                    if marcador == "LECF":
                        return "ecf"
                    if marcador == "LECD":
                        return "ecd"
                    # Tiebreaker pelo layout do 0000: posição do CNPJ (CLAUDE.md §7.2).
                    # EFD ICMS/IPI: CNPJ em campos[7] (14 dígitos numéricos).
                    # EFD-Contribuições: CNPJ em campos[9].
                    cnpj7 = campos[7].strip() if len(campos) > 7 else ""
                    cnpj9 = campos[9].strip() if len(campos) > 9 else ""
                    if cnpj7.isdigit() and len(cnpj7) == 14:
                        return "efd_icms_ipi"
                    if cnpj9.isdigit() and len(cnpj9) == 14:
                        return "efd_contribuicoes"
                if reg == "0110":
                    return "efd_contribuicoes"
                # Blocos B, E, G, H são exclusivos do EFD ICMS/IPI.
                if len(reg) >= 2 and reg[0] in {"B", "E", "G", "H"} and reg[1:].isdigit():
                    return "efd_icms_ipi"
    except Exception:
        pass
    return "desconhecido"


# ------------------------------------------------------------------
# Coleta de arquivos
# ------------------------------------------------------------------

def _encontrar_arquivos_sped(caminho: Path) -> list[Path]:
    if caminho.is_file():
        return [caminho]
    arquivos = []
    for p in sorted(caminho.rglob("*")):
        if p.is_file() and p.suffix.lower() in _SUFIXOS_SPED:
            arquivos.append(p)
    return arquivos


# ------------------------------------------------------------------
# Subcomando: import
# ------------------------------------------------------------------

def cmd_import(args: argparse.Namespace) -> int:
    caminho = Path(args.caminho)
    if not caminho.exists():
        logger.error("Caminho não encontrado: %s", caminho)
        return 1

    arquivos = _encontrar_arquivos_sped(caminho)
    if not arquivos:
        logger.error("Nenhum arquivo SPED encontrado em: %s", caminho)
        return 1

    erros_totais = 0
    for arq in arquivos:
        tipo = detectar_tipo_sped(arq)
        if tipo == "desconhecido":
            logger.warning("Tipo não identificado, ignorando: %s", arq.name)
            continue

        logger.info("Importando %s como %s", arq.name, tipo)

        _PARSERS = {
            "efd_contribuicoes": efd_contribuicoes.importar,
            "efd_icms_ipi": efd_icms_ipi.importar,
            "ecd": ecd.importar,
            "ecf": ecf.importar,
        }
        parser_fn = _PARSERS[tipo]

        try:
            resultado = parser_fn(
                arq,
                encoding_override=args.encoding,
                prompt_operador=not args.nao_interativo,
            )
        except ValueError as exc:
            logger.error("Importação rejeitada (%s): %s", arq.name, exc)
            erros_totais += 1
            continue

        if resultado.sucesso:
            print(
                f"  OK  [{tipo}] {arq.name}"
                f" — CNPJ {resultado.cnpj}"
                f" {resultado.dt_ini}->{resultado.dt_fin}"
                f" (encoding={resultado.encoding_origem}/{resultado.encoding_confianca})"
            )
        else:
            print(f"  PARCIAL  [{tipo}] {arq.name} — {resultado.mensagem}")
            if resultado.divergencias_bloco9:
                for div in resultado.divergencias_bloco9[:5]:
                    print(f"    !  {div}")
            erros_totais += 1

    return 0 if erros_totais == 0 else 1


# ------------------------------------------------------------------
# Subcomando: diagnose
# ------------------------------------------------------------------

def cmd_diagnose(args: argparse.Namespace) -> int:
    cnpj = args.cnpj.replace(".", "").replace("/", "").replace("-", "")
    ano_calendario = int(args.ano)

    repo = Repositorio(cnpj, ano_calendario)
    if not repo.caminho.exists():
        logger.error(
            "Banco não encontrado: %s — execute 'import' primeiro.", repo.caminho
        )
        return 1

    motor = Motor(repo)
    logger.info("Iniciando diagnóstico CNPJ=%s AC=%d", cnpj, ano_calendario)
    sumario = motor.diagnosticar_ano(ano_calendario)

    meses = sumario.get("meses", [])
    if not meses:
        logger.error(
            "Nenhum período com dados importados para CNPJ=%s AC=%d."
            " Execute 'import' para pelo menos um SPED.",
            cnpj, ano_calendario,
        )
        return 1

    destino = Path("data/output") / cnpj / str(ano_calendario) / "diagnostico.xlsx"
    excel_diagnostico.gerar(repo, ano_calendario, destino)

    total_ops = sum(m["oportunidades_camada2"] + m.get("oportunidades_camada3", 0) for m in meses)
    total_divs = sum(m["divergencias_camada1"] for m in meses)
    total_imp_cons = sum(m["impacto_conservador"] for m in meses)
    total_imp_max = sum(m["impacto_maximo"] for m in meses)

    print(f"\nDiagnóstico CNPJ {cnpj} — AC {ano_calendario}")
    print(f"  Períodos analisados  : {len(meses)}")
    print(f"  Oportunidades (CR)   : {total_ops}")
    print(f"  Divergências (CI)    : {total_divs}")
    print(f"  Impacto conservador  : R$ {total_imp_cons:,.2f}")
    print(f"  Impacto máximo       : R$ {total_imp_max:,.2f}")
    print(f"  Relatório Excel      : {destino}")

    return 0


# ------------------------------------------------------------------
# Subcomando: parecer
# ------------------------------------------------------------------

def cmd_parecer(args: argparse.Namespace) -> int:
    cnpj = args.cnpj.replace(".", "").replace("/", "").replace("-", "")
    ano_calendario = int(args.ano)
    tese = args.tese

    repo = Repositorio(cnpj, ano_calendario)
    if not repo.caminho.exists():
        logger.error(
            "Banco não encontrado: %s — execute 'import' e 'diagnose' primeiro.",
            repo.caminho,
        )
        return 1

    destino = (
        Path("data/output") / cnpj / str(ano_calendario)
        / f"parecer_{tese.replace('-', '_')}.docx"
    )
    try:
        word_parecer.gerar(repo, ano_calendario, tese=tese, destino=destino)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    print(f"  Parecer gerado: {destino}")
    return 0


# ------------------------------------------------------------------
# Subcomando: reconciliacao-template
# ------------------------------------------------------------------

def cmd_reconciliacao_template(args: argparse.Namespace) -> int:
    cnpj = args.cnpj.replace(".", "").replace("/", "").replace("-", "")
    ano_calendario = int(args.ano)

    repo = Repositorio(cnpj, ano_calendario)
    if not repo.caminho.exists():
        logger.error(
            "Banco não encontrado: %s — importe a ECD antes de gerar o template.",
            repo.caminho,
        )
        return 1

    destino = (
        Path("data/output") / cnpj / str(ano_calendario)
        / "reconciliacao_template.xlsx"
    )
    try:
        excel_reconciliacao.gerar(repo, ano_calendario, destino)
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    print(f"  Template gerado: {destino}")
    print("  Preencha as colunas em amarelo (COD_CTA antigo, NOME antigo, Observações).")
    return 0


# ------------------------------------------------------------------
# Subcomando: reconciliacao-import
# ------------------------------------------------------------------

def cmd_reconciliacao_import(args: argparse.Namespace) -> int:
    cnpj = args.cnpj.replace(".", "").replace("/", "").replace("-", "")
    ano_calendario = int(args.ano)
    caminho_xlsx = Path(args.arquivo)

    repo = Repositorio(cnpj, ano_calendario)
    if not repo.caminho.exists():
        logger.error(
            "Banco não encontrado: %s — importe a ECD antes de importar o template.",
            repo.caminho,
        )
        return 1

    try:
        resultado = excel_reconciliacao_import.importar_template(
            repo, ano_calendario, caminho_xlsx,
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    print(
        f"  Importado: {resultado.linhas_importadas} mapeamento(s) "
        f"({resultado.linhas_ignoradas} linha(s) em branco ignorada(s))"
    )

    # Re-consulta classificação para dar feedback imediato ao operador
    from src.crossref.common.reconciliacao_plano_contas import classificar_reconciliacao
    conn = repo.conexao()
    try:
        estado = classificar_reconciliacao(repo, conn, cnpj, ano_calendario)
    finally:
        conn.close()
    print(f"  Reconciliação agora classificada como: {estado}")
    return 0


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="primetax-sped",
        description=(
            "Primetax SPED Cross-Reference System — "
            "47 cruzamentos fiscais (EFD-Contribuições, EFD ICMS/IPI, ECD, ECF)"
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    # --- import ---
    p_import = sub.add_parser(
        "import",
        help="Importar SPED(s) para o banco SQLite (todos os tipos suportados)",
    )
    p_import.add_argument(
        "caminho",
        help="Arquivo único ou diretório contendo arquivos SPED",
    )
    p_import.add_argument(
        "--encoding",
        choices=["auto", "utf8", "latin1"],
        default="auto",
        help="Forçar encoding (padrão: auto-detecção UTF-8/Latin1)",
    )
    p_import.add_argument(
        "--nao-interativo",
        action="store_true",
        default=False,
        help="Não perguntar ao operador em encoding suspeito (modo batch)",
    )

    # --- diagnose ---
    p_diagnose = sub.add_parser(
        "diagnose",
        help="Executar cruzamentos e gerar relatório Excel de diagnóstico",
    )
    p_diagnose.add_argument("cnpj", help="CNPJ do declarante (14 dígitos, com ou sem máscara)")
    p_diagnose.add_argument("ano", help="Ano-calendário (ex: 2025)")

    # --- parecer ---
    p_parecer = sub.add_parser(
        "parecer",
        help="Gerar parecer Word formal por tese (requer diagnose executado)",
    )
    p_parecer.add_argument("cnpj", help="CNPJ do declarante")
    p_parecer.add_argument("ano", help="Ano-calendário (ex: 2025)")
    p_parecer.add_argument(
        "--tese",
        required=True,
        choices=sorted(word_parecer._TESES.keys()),
        help="Código da tese (tema-69, insumos, retencoes, imobilizado)",
    )

    # --- reconciliacao-template ---
    p_recon = sub.add_parser(
        "reconciliacao-template",
        help="Gerar Excel de reconciliação manual de plano de contas (§16.6)",
    )
    p_recon.add_argument("cnpj", help="CNPJ do declarante")
    p_recon.add_argument("ano", help="Ano-calendário (ex: 2025)")

    # --- reconciliacao-import ---
    p_recon_imp = sub.add_parser(
        "reconciliacao-import",
        help="Importar template de reconciliação preenchido pelo auditor (§16.6)",
    )
    p_recon_imp.add_argument("cnpj", help="CNPJ do declarante")
    p_recon_imp.add_argument("ano", help="Ano-calendário (ex: 2025)")
    p_recon_imp.add_argument(
        "arquivo",
        help="Caminho do arquivo .xlsx preenchido (gerado por reconciliacao-template)",
    )

    args = parser.parse_args()

    if args.comando == "import":
        sys.exit(cmd_import(args))
    elif args.comando == "diagnose":
        sys.exit(cmd_diagnose(args))
    elif args.comando == "parecer":
        sys.exit(cmd_parecer(args))
    elif args.comando == "reconciliacao-template":
        sys.exit(cmd_reconciliacao_template(args))
    elif args.comando == "reconciliacao-import":
        sys.exit(cmd_reconciliacao_import(args))


if __name__ == "__main__":
    main()
