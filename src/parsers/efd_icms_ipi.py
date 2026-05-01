"""
Parser principal da EFD ICMS/IPI (Leiaute 3.2.2).

Sprint 6: processa os registros necessários para cruzamentos 35-37.
  - C100/C170: documentos fiscais (CFOP para CR-37)
  - G110/G125: CIAP (crédito de ICMS sobre imobilizado para CR-35)
  - H005/H010: inventário (VL_ITEM_IR para CR-36)

O banco SQLite é o mesmo banco longitudinal do cliente/ano-calendário
já criado pelo importador da EFD-Contribuições (CLAUDE.md §15.1).
Ao final, atualiza disponibilidade_efd_icms → "importada" (CLAUDE.md §18).
"""

import hashlib
import logging
from pathlib import Path

from src.crossref.common.disponibilidade_sped import atualizar_disponibilidade
from src.db.repo import Repositorio
from src.models.registros import ResultadoImportacao
from src.parsers.blocos.bloco_9 import parsear_9900, parsear_9999
from src.parsers.blocos.bloco_c_icms import parsear_c100_icms, parsear_c170_icms
from src.parsers.blocos.bloco_g_icms import parsear_g110, parsear_g125
from src.parsers.blocos.bloco_h_icms import parsear_h005, parsear_h010
from src.parsers.common.bloco9 import validar_bloco9
from src.parsers.common.encoding import detectar_encoding, truncar_em_9999

logger = logging.getLogger(__name__)

_TIPOS_RELEVANTES = frozenset({
    "0000", "C001", "C100", "C170", "C990",
    "G001", "G100", "G110", "G125", "G990",
    "H001", "H005", "H010", "H990",
    "9001", "9900", "9999",
})


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _data(s: str) -> str:
    """DDMMAAAA → YYYY-MM-DD."""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def _ano_mes(dt_ini: str) -> int:
    """'YYYY-MM-DD' → YYYYMM int."""
    return int(dt_ini[:4] + dt_ini[5:7])


def _ano_calendario(dt_ini: str) -> int:
    return int(dt_ini[:4])


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def importar(
    caminho: Path,
    *,
    encoding_override: str = "auto",
    prompt_operador: bool = True,
    base_dir_db: Path | None = None,
) -> ResultadoImportacao:
    """
    Importa um arquivo EFD ICMS/IPI para o banco SQLite longitudinal.

    Persiste: efd_icms_0000, efd_icms_c100, efd_icms_c170,
              efd_icms_g110, efd_icms_g125, efd_icms_h005, efd_icms_h010.
    Atualiza: disponibilidade_efd_icms → 'importada'.
    """
    arquivo_str = str(caminho.resolve())

    res_enc = detectar_encoding(
        caminho, override=encoding_override, prompt_operador=prompt_operador
    )
    codec = "utf-8" if res_enc.encoding == "utf8" else "latin-1"
    texto = caminho.read_text(encoding=codec, errors="strict")
    texto = truncar_em_9999(texto)
    linhas_raw = texto.splitlines()
    total_linhas = len(linhas_raw)

    ctx: dict = {}
    c100_atual: int | None = None
    h005_atual: int | None = None
    erros_parse: list[str] = []

    reg0000 = None
    regs_c100: list = []
    regs_c170: list = []
    regs_g110: list = []
    regs_g125: list = []
    regs_h005: list = []
    regs_h010: list = []
    regs_9900: list = []
    reg9999 = None

    contagens_reais: dict[str, int] = {}

    for num_linha, linha_raw in enumerate(linhas_raw, start=1):
        linha = linha_raw.strip()
        if not linha:
            continue

        campos = linha.split("|")
        if len(campos) < 2:
            continue

        reg_tipo = campos[1].strip().upper()
        contagens_reais[reg_tipo] = contagens_reais.get(reg_tipo, 0) + 1

        if reg_tipo not in _TIPOS_RELEVANTES:
            continue

        try:
            if reg_tipo == "0000":
                # EFD ICMS/IPI 0000:
                # [2]=COD_VER [3]=COD_FIN [4]=DT_INI [5]=DT_FIN [6]=NOME [7]=CNPJ
                dt_ini = _data(_g(campos, 4))
                dt_fin = _data(_g(campos, 5))
                cnpj = _g(campos, 7)
                cod_ver = _g(campos, 2)
                ctx = {
                    "cnpj_declarante": cnpj,
                    "dt_ini_periodo": dt_ini,
                    "dt_fin_periodo": dt_fin,
                    "ano_mes": _ano_mes(dt_ini),
                    "ano_calendario": _ano_calendario(dt_ini),
                    "cod_ver": cod_ver,
                }
                from src.models.registros import RegIcms0000
                reg0000 = RegIcms0000(
                    linha_arquivo=num_linha,
                    arquivo_origem=arquivo_str,
                    reg="0000",
                    cod_ver=cod_ver,
                    cod_fin=_g(campos, 3),
                    dt_ini=dt_ini,
                    dt_fin=dt_fin,
                    nome=_g(campos, 6),
                    cnpj=cnpj,
                    cpf=_g(campos, 8),
                    uf=_g(campos, 9),
                    ie=_g(campos, 10),
                    cod_mun=_g(campos, 11),
                    im=_g(campos, 12),
                    suframa=_g(campos, 13),
                    ind_perfil=_g(campos, 14),
                    ind_ativ=_g(campos, 15),
                )

            elif reg_tipo == "C100" and ctx:
                r = parsear_c100_icms(campos, num_linha, arquivo_str)
                c100_atual = num_linha
                regs_c100.append(r)

            elif reg_tipo == "C170" and ctx:
                if c100_atual is None:
                    logger.warning("C170 orphan at line %d — no C100 parent", num_linha)
                    continue
                r = parsear_c170_icms(campos, num_linha, arquivo_str, c100_atual)
                regs_c170.append(r)

            elif reg_tipo == "G110" and ctx:
                r = parsear_g110(campos, num_linha, arquivo_str)
                regs_g110.append(r)

            elif reg_tipo == "G125" and ctx:
                r = parsear_g125(campos, num_linha, arquivo_str)
                regs_g125.append(r)

            elif reg_tipo == "H005" and ctx:
                r = parsear_h005(campos, num_linha, arquivo_str)
                h005_atual = num_linha
                regs_h005.append(r)

            elif reg_tipo == "H010" and ctx:
                if h005_atual is None:
                    logger.warning("H010 orphan at line %d — no H005 parent", num_linha)
                    h005_atual = 0
                r = parsear_h010(campos, num_linha, arquivo_str, h005_atual)
                regs_h010.append(r)

            elif reg_tipo == "9900" and ctx:
                regs_9900.append(parsear_9900(campos, num_linha, arquivo_str))

            elif reg_tipo == "9999":
                reg9999 = parsear_9999(campos, num_linha, arquivo_str)

        except Exception as exc:
            msg = f"Erro ao parsear linha {num_linha} ({reg_tipo}): {exc}"
            logger.error(msg)
            erros_parse.append(msg)

    if reg0000 is None:
        return ResultadoImportacao(
            arquivo=arquivo_str,
            cnpj="",
            ano_calendario=0,
            ano_mes=0,
            dt_ini="",
            dt_fin="",
            cod_ver="",
            encoding_origem=res_enc.encoding,
            encoding_confianca=res_enc.confianca,
            total_linhas_lidas=total_linhas,
            contagens_reais=contagens_reais,
            contagens_declaradas={},
            divergencias_bloco9=["Registro 0000 ausente — EFD ICMS/IPI rejeitado"],
            sucesso=False,
            mensagem="Registro 0000 não encontrado.",
        )

    cnpj = ctx["cnpj_declarante"]
    ano_cal = ctx["ano_calendario"]
    ano_mes = ctx["ano_mes"]
    arquivo_hash = _sha256(caminho)

    # --- Validação Bloco 9 (cruzamento 01) ---
    # 9999.QTD_LIN do PVA conta apenas linhas SPED válidas (com pipe
    # inicial). Mantida semântica do PVA por simetria com os demais
    # parsers — embora EFD ICMS/IPI não tenha registros multilinhas
    # como o J801 da ECD.
    total_linhas_sped = sum(1 for l in linhas_raw if l.startswith("|"))
    contagens_declaradas, divergencias_bloco9 = validar_bloco9(
        contagens_reais, regs_9900, reg9999, total_linhas_sped,
    )
    tem_erro = bool(erros_parse)
    tem_div_bloco9 = bool(divergencias_bloco9)
    sucesso = not tem_erro and not tem_div_bloco9
    status = "ok" if sucesso else "parcial"

    repo = Repositorio(cnpj, ano_cal, base_dir=base_dir_db)
    repo.criar_banco()

    conn = repo.conexao()
    try:
        with conn:
            # Bug-002 (Opção 2) — DELETE prévio em todas as tabelas
            # EFD ICMS/IPI filhas para o (cnpj × ano_mes), garantindo
            # dedup em reimport idêntico ou retificadora.
            deletadas = repo.deletar_dados_anteriores(
                conn, sped_tipo="efd_icms",
                cnpj=cnpj, ano_mes=ano_mes,
            )
            if deletadas > 0:
                logger.info(
                    "Reimport detectado para efd_icms %s/%s: "
                    "%d rows antigas removidas (Bug-002 fix)",
                    cnpj, ano_mes, deletadas,
                )
            repo.registrar_importacao(
                conn,
                sped_tipo="efd_icms",
                dt_ini=ctx["dt_ini_periodo"],
                dt_fin=ctx["dt_fin_periodo"],
                ano_mes=ano_mes,
                arquivo_hash=arquivo_hash,
                arquivo_origem=arquivo_str,
                cod_ver=ctx["cod_ver"],
                encoding_origem=res_enc.encoding,
                encoding_confianca=res_enc.confianca,
                status=status,
            )
            repo.inserir_icms_0000(conn, reg0000, ctx)
            for r in regs_c100:
                repo.inserir_icms_c100(conn, r, ctx)
            for r in regs_c170:
                repo.inserir_icms_c170(conn, r, ctx)
            for r in regs_g110:
                repo.inserir_icms_g110(conn, r, ctx)
            for r in regs_g125:
                repo.inserir_icms_g125(conn, r, ctx)
            for r in regs_h005:
                repo.inserir_icms_h005(conn, r, ctx)
            for r in regs_h010:
                repo.inserir_icms_h010(conn, r, ctx)
            atualizar_disponibilidade(repo, conn, "efd_icms", "importada")
    finally:
        conn.close()

    logger.info(
        "EFD ICMS/IPI %s: C170=%d G125=%d H010=%d (encoding=%s)",
        caminho.name, len(regs_c170), len(regs_g125), len(regs_h010),
        res_enc.encoding,
    )

    return ResultadoImportacao(
        arquivo=arquivo_str,
        cnpj=cnpj,
        ano_calendario=ano_cal,
        ano_mes=ano_mes,
        dt_ini=ctx["dt_ini_periodo"],
        dt_fin=ctx["dt_fin_periodo"],
        cod_ver=ctx["cod_ver"],
        encoding_origem=res_enc.encoding,
        encoding_confianca=res_enc.confianca,
        total_linhas_lidas=total_linhas,
        contagens_reais=contagens_reais,
        contagens_declaradas=contagens_declaradas,
        divergencias_bloco9=divergencias_bloco9,
        sucesso=sucesso,
        mensagem=erros_parse[0] if erros_parse else "",
    )
