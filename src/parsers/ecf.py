"""
Parser principal da ECF (Leiaute 12 — ADE Cofis 02/2026).

Sprint 8: processa os registros necessários para cruzamentos 43-47.
  - 0000/0010: identificação e parâmetros de tributação
  - K155/K355: saldos contábeis (base para CR-43)
  - M300/M310/M312: Parte A do e-Lalur (base para CR-44)
  - M350/M360/M362: Parte A do e-Lacs — espelho CSLL (base para CR-44)
  - M500: saldos Parte B (base para CR-45)
  - X480: benefícios fiscais (base para CR-46)
  - Y570: IRRF/CSRF retidos (base para CR-47)

A ECF é anual; um arquivo por CNPJ por ano-calendário.
Ao final, atualiza disponibilidade_ecf → "importada" (CLAUDE.md §18.6).
Se 0010.TIP_ESC_PRE = "L", atualiza disponibilidade_ecd → "estruturalmente_ausente"
(art. 45 parágrafo único da Lei 8.981/1995 + IN RFB 2.003/2021; CLAUDE.md §18.2).
"""

import hashlib
import logging
from pathlib import Path

from src.crossref.common.disponibilidade_sped import atualizar_disponibilidade
from src.db.repo import Repositorio
from src.models.registros import RegEcf0000, RegEcf0010, ResultadoImportacao
from src.parsers.blocos.bloco_k_ecf import parsear_k155, parsear_k355
from src.parsers.blocos.bloco_m_ecf import (
    parsear_m300,
    parsear_m312,
    parsear_m350,
    parsear_m362,
    parsear_m500,
)
from src.parsers.blocos.bloco_9 import parsear_9900, parsear_9999
from src.parsers.blocos.bloco_9_ecf import parsear_9100
from src.parsers.blocos.bloco_x_ecf import parsear_x460, parsear_x480
from src.parsers.blocos.bloco_y_ecf import parsear_y570
from src.parsers.common.bloco9 import validar_bloco9
from src.parsers.common.encoding import detectar_encoding, truncar_em_9999

logger = logging.getLogger(__name__)

_TIPOS_RELEVANTES = frozenset({
    "0000", "0010",
    "K001", "K155", "K355", "K990",
    "M001", "M300", "M310", "M312", "M350", "M360", "M362", "M500", "M990",
    "X001", "X460", "X480", "X990",
    "Y001", "Y570", "Y990",
    "9001", "9100", "9900", "9999",
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
    Importa um arquivo ECF para o banco SQLite longitudinal.

    Persiste: ecf_0000, ecf_0010, ecf_k155, ecf_k355,
              ecf_m300, ecf_m312, ecf_m350, ecf_m362, ecf_m500,
              ecf_x480, ecf_y570.
    Atualiza: disponibilidade_ecf → 'importada'.
    Se TIP_ESC_PRE='L': disponibilidade_ecd → 'estruturalmente_ausente'.
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
    m300_linha_atual: int | None = None
    m350_linha_atual: int | None = None
    erros_parse: list[str] = []

    reg0000 = None
    reg0010 = None
    regs_k155: list = []
    regs_k355: list = []
    regs_m300: list = []
    regs_m312: list = []
    regs_m350: list = []
    regs_m362: list = []
    regs_m500: list = []
    regs_x460: list = []
    regs_x480: list = []
    regs_y570: list = []
    regs_9100: list = []
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
                # ECF 0000: [2]=LECF [3]=COD_VER [4]=CNPJ [5]=NOME
                # [6]=IND_SIT_INI_PER [7]=SIT_ESPECIAL [10]=DT_INI [11]=DT_FIN
                # [12]=RETIFICADORA [14]=TIP_ECF
                dt_ini = _data(_g(campos, 10))
                dt_fin = _data(_g(campos, 11))
                cnpj = _g(campos, 4)
                ano_cal = _ano_calendario(dt_ini)
                ctx = {
                    "cnpj_declarante": cnpj,
                    "dt_ini_periodo": dt_ini,
                    "dt_fin_periodo": dt_fin,
                    "ano_mes": int(dt_ini[:4] + dt_ini[5:7]),
                    "ano_calendario": ano_cal,
                    "cod_ver": _g(campos, 3),
                }
                reg0000 = RegEcf0000(
                    linha_arquivo=num_linha,
                    arquivo_origem=arquivo_str,
                    reg="0000",
                    cod_ver=_g(campos, 3),
                    cnpj=cnpj,
                    nome=_g(campos, 5),
                    ind_sit_ini_per=_g(campos, 6),
                    sit_especial=_g(campos, 7),
                    dt_ini=dt_ini,
                    dt_fin=dt_fin,
                    retificadora=_g(campos, 12),
                    tip_ecf=_g(campos, 14),
                )

            elif reg_tipo == "0010" and ctx:
                # ECF 0010: [4]=FORMA_TRIB [5]=FORMA_APUR [6]=COD_QUALIF_PJ
                # [9]=TIP_ESC_PRE
                reg0010 = RegEcf0010(
                    linha_arquivo=num_linha,
                    arquivo_origem=arquivo_str,
                    reg="0010",
                    forma_trib=_g(campos, 4),
                    forma_apur=_g(campos, 5),
                    cod_qualif_pj=_g(campos, 6),
                    tip_esc_pre=_g(campos, 9),
                )

            elif reg_tipo == "K155" and ctx:
                r = parsear_k155(campos, num_linha, arquivo_str)
                regs_k155.append(r)

            elif reg_tipo == "K355" and ctx:
                r = parsear_k355(campos, num_linha, arquivo_str)
                regs_k355.append(r)

            elif reg_tipo == "M300" and ctx:
                r = parsear_m300(campos, num_linha, arquivo_str)
                m300_linha_atual = num_linha
                regs_m300.append(r)

            elif reg_tipo == "M310" and ctx:
                # M310 é pai de M312; atualiza o contexto mas não persiste
                pass

            elif reg_tipo == "M312" and ctx:
                if m300_linha_atual is None:
                    logger.warning("M312 órfão na linha %d — sem M300 pai", num_linha)
                    m300_linha_atual = 0
                r = parsear_m312(campos, num_linha, arquivo_str, m300_linha_atual)
                regs_m312.append(r)

            elif reg_tipo == "M350" and ctx:
                r = parsear_m350(campos, num_linha, arquivo_str)
                m350_linha_atual = num_linha
                regs_m350.append(r)

            elif reg_tipo == "M360" and ctx:
                pass

            elif reg_tipo == "M362" and ctx:
                if m350_linha_atual is None:
                    logger.warning("M362 órfão na linha %d — sem M350 pai", num_linha)
                    m350_linha_atual = 0
                r = parsear_m362(campos, num_linha, arquivo_str, m350_linha_atual)
                regs_m362.append(r)

            elif reg_tipo == "M500" and ctx:
                r = parsear_m500(campos, num_linha, arquivo_str)
                regs_m500.append(r)

            elif reg_tipo == "X460" and ctx:
                regs_x460.append(parsear_x460(campos, num_linha, arquivo_str))

            elif reg_tipo == "X480" and ctx:
                r = parsear_x480(campos, num_linha, arquivo_str)
                regs_x480.append(r)

            elif reg_tipo == "Y570" and ctx:
                r = parsear_y570(campos, num_linha, arquivo_str)
                regs_y570.append(r)

            elif reg_tipo == "9100" and ctx:
                regs_9100.append(parsear_9100(campos, num_linha, arquivo_str))

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
            divergencias_bloco9=["Registro 0000 ausente — ECF rejeitada"],
            sucesso=False,
            mensagem="Registro 0000 não encontrado.",
        )

    cnpj = ctx["cnpj_declarante"]
    ano_cal = ctx["ano_calendario"]
    arquivo_hash = _sha256(caminho)

    # --- Validação Bloco 9 (cruzamento 01) ---
    # 9999.QTD_LIN do PVA conta apenas linhas SPED válidas (com pipe
    # inicial). Mantida semântica do PVA por simetria com os demais
    # parsers.
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
            repo.registrar_importacao(
                conn,
                sped_tipo="ecf",
                dt_ini=ctx["dt_ini_periodo"],
                dt_fin=ctx["dt_fin_periodo"],
                ano_mes=ctx["ano_mes"],
                arquivo_hash=arquivo_hash,
                arquivo_origem=arquivo_str,
                cod_ver=ctx["cod_ver"],
                encoding_origem=res_enc.encoding,
                encoding_confianca=res_enc.confianca,
                status=status,
            )
            repo.inserir_ecf_0000(conn, reg0000, ctx)
            if reg0010:
                repo.inserir_ecf_0010(conn, reg0010, ctx)
            for r in regs_k155:
                repo.inserir_ecf_k155(conn, r, ctx)
            for r in regs_k355:
                repo.inserir_ecf_k355(conn, r, ctx)
            for r in regs_m300:
                repo.inserir_ecf_m300(conn, r, ctx)
            for r in regs_m312:
                repo.inserir_ecf_m312(conn, r, ctx)
            for r in regs_m350:
                repo.inserir_ecf_m350(conn, r, ctx)
            for r in regs_m362:
                repo.inserir_ecf_m362(conn, r, ctx)
            for r in regs_m500:
                repo.inserir_ecf_m500(conn, r, ctx)
            for r in regs_x460:
                repo.inserir_ecf_x460(conn, r, ctx)
            for r in regs_x480:
                repo.inserir_ecf_x480(conn, r, ctx)
            for r in regs_y570:
                repo.inserir_ecf_y570(conn, r, ctx)
            for r in regs_9100:
                repo.inserir_ecf_9100(conn, r, ctx)

            atualizar_disponibilidade(repo, conn, "ecf", "importada")

            # CLAUDE.md §18.2: TIP_ESC_PRE='L' → PJ usa Livro Caixa → sem ECD
            if reg0010 and reg0010.tip_esc_pre == "L":
                atualizar_disponibilidade(repo, conn, "ecd", "estruturalmente_ausente")
                logger.info(
                    "ECF %s: TIP_ESC_PRE='L' → disponibilidade_ecd marcada como "
                    "estruturalmente_ausente (art. 45 Lei 8.981/1995)",
                    caminho.name,
                )
    finally:
        conn.close()

    logger.info(
        "ECF %s AC %d: K155=%d K355=%d M300=%d M312=%d M350=%d M362=%d "
        "M500=%d X460=%d X480=%d Y570=%d 9100=%d (encoding=%s)",
        caminho.name, ano_cal,
        len(regs_k155), len(regs_k355),
        len(regs_m300), len(regs_m312),
        len(regs_m350), len(regs_m362),
        len(regs_m500), len(regs_x460), len(regs_x480), len(regs_y570),
        len(regs_9100),
        res_enc.encoding,
    )

    return ResultadoImportacao(
        arquivo=arquivo_str,
        cnpj=cnpj,
        ano_calendario=ano_cal,
        ano_mes=ctx["ano_mes"],
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
