"""
Parser principal da ECD (Leiaute 9 — ADE Cofis 01/2026).

Sprint 7: processa os registros necessários para cruzamentos 38-42.
  - I010/I050: plano de contas (base para CR-40, CR-42)
  - I150/I155: saldos mensais (base para CR-38)
  - I200: lançamentos extemporâneos (base para CR-41)
  - J005/J150: DRE (base para CR-39)

A ECD é anual; um arquivo por CNPJ por ano-calendário.
O banco SQLite é o mesmo banco longitudinal usado pela EFD-Contribuições e EFD ICMS/IPI (CLAUDE.md §15.1).
Ao final, atualiza disponibilidade_ecd → "importada" e reconciliacao_plano_contas (CLAUDE.md §18).
"""

import hashlib
import logging
from pathlib import Path

from src.crossref.common.disponibilidade_sped import atualizar_disponibilidade
from src.crossref.common.reconciliacao_plano_contas import classificar_reconciliacao
from src.db.repo import Repositorio
from src.models.registros import RegEcd0000, ResultadoImportacao
from src.parsers.blocos.bloco_c_ecd import parsear_c050, parsear_c155
from src.parsers.blocos.bloco_i_ecd import (
    parsear_i010,
    parsear_i050,
    parsear_i150,
    parsear_i155,
    parsear_i200,
    parsear_i250,
)
from src.parsers.blocos.bloco_9 import parsear_9900, parsear_9999
from src.parsers.blocos.bloco_j_ecd import (
    parsear_j005,
    parsear_j100,
    parsear_j150,
)
from src.parsers.common.bloco9 import validar_bloco9
from src.parsers.common.encoding import detectar_encoding, truncar_em_9999

logger = logging.getLogger(__name__)

_TIPOS_RELEVANTES = frozenset({
    "0000", "0001",
    "C001", "C050", "C155", "C990",
    "I001", "I010", "I050", "I051", "I150", "I155", "I200", "I250", "I990",
    "J001", "J005", "J100", "J150", "J990",
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
    Importa um arquivo ECD para o banco SQLite longitudinal.

    Persiste: ecd_0000, ecd_i010, ecd_i050, ecd_i150, ecd_i155,
              ecd_i200, ecd_i250, ecd_j005, ecd_j100, ecd_j150.
    Atualiza: disponibilidade_ecd → 'importada'.
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
    i150_atual: int | None = None
    i200_atual: int | None = None  # pai do I250 corrente
    j005_atual: int | None = None
    erros_parse: list[str] = []

    reg0000 = None
    reg_i010 = None
    regs_c050: list = []
    regs_c155: list = []
    regs_i050: list = []
    regs_i150: list = []
    regs_i155: list = []
    regs_i200: list = []
    regs_i250: list = []
    regs_j005: list = []
    regs_j100: list = []
    regs_j150: list = []
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
                # ECD 0000: [2]=LECD [3]=DT_INI [4]=DT_FIN [5]=NOME [6]=CNPJ
                # [7]=UF [9]=COD_MUN [14]=IND_FIN_ESC [16]=IND_GRANDE_PORTE
                # [17]=TIP_ECD [19]=IDENT_MF [22]=IND_MUDANC_PC [23]=COD_PLAN_REF
                dt_ini = _data(_g(campos, 3))
                dt_fin = _data(_g(campos, 4))
                cnpj = _g(campos, 6)
                ctx = {
                    "cnpj_declarante": cnpj,
                    "dt_ini_periodo": dt_ini,
                    "dt_fin_periodo": dt_fin,
                    "ano_mes": _ano_mes(dt_ini),
                    "ano_calendario": _ano_calendario(dt_ini),
                    "cod_ver": "",  # preenchido após I010
                }
                reg0000 = RegEcd0000(
                    linha_arquivo=num_linha,
                    arquivo_origem=arquivo_str,
                    reg="0000",
                    dt_ini=dt_ini,
                    dt_fin=dt_fin,
                    nome=_g(campos, 5),
                    cnpj=cnpj,
                    uf=_g(campos, 7),
                    cod_mun=_g(campos, 9),
                    ind_fin_esc=_g(campos, 14),
                    ind_grande_porte=_g(campos, 16),
                    tip_ecd=_g(campos, 17),
                    ident_mf=_g(campos, 19),
                    ind_mudanc_pc=_g(campos, 22) or "0",
                    cod_plan_ref=_g(campos, 23),
                    cod_ver="",  # preenchido após I010
                )

            elif reg_tipo == "I010" and ctx:
                r = parsear_i010(campos, num_linha, arquivo_str)
                reg_i010 = r
                ctx["cod_ver"] = r.cod_ver_lc
                if reg0000 is not None:
                    reg0000 = RegEcd0000(
                        linha_arquivo=reg0000.linha_arquivo,
                        arquivo_origem=reg0000.arquivo_origem,
                        reg=reg0000.reg,
                        dt_ini=reg0000.dt_ini,
                        dt_fin=reg0000.dt_fin,
                        nome=reg0000.nome,
                        cnpj=reg0000.cnpj,
                        uf=reg0000.uf,
                        cod_mun=reg0000.cod_mun,
                        ind_fin_esc=reg0000.ind_fin_esc,
                        ind_grande_porte=reg0000.ind_grande_porte,
                        tip_ecd=reg0000.tip_ecd,
                        ident_mf=reg0000.ident_mf,
                        ind_mudanc_pc=reg0000.ind_mudanc_pc,
                        cod_plan_ref=reg0000.cod_plan_ref,
                        cod_ver=r.cod_ver_lc,
                    )

            elif reg_tipo == "C050" and ctx:
                regs_c050.append(parsear_c050(campos, num_linha, arquivo_str))

            elif reg_tipo == "C155" and ctx:
                regs_c155.append(parsear_c155(campos, num_linha, arquivo_str))

            elif reg_tipo == "I050" and ctx:
                r = parsear_i050(campos, num_linha, arquivo_str)
                regs_i050.append(r)

            elif reg_tipo == "I150" and ctx:
                r = parsear_i150(campos, num_linha, arquivo_str)
                # I155 inherits the period dates from I150
                i150_dt_ini = r.dt_ini
                i150_dt_fin = r.dt_fin
                # Update ctx for I155 to carry correct period month
                ctx["_i150_dt_ini"] = i150_dt_ini
                ctx["_i150_dt_fin"] = i150_dt_fin
                ctx["_i150_ano_mes"] = _ano_mes(i150_dt_ini)
                i150_atual = num_linha
                regs_i150.append(r)

            elif reg_tipo == "I155" and ctx:
                if i150_atual is None:
                    logger.warning("I155 orphan at line %d — no I150 parent", num_linha)
                    i150_atual = 0
                r = parsear_i155(campos, num_linha, arquivo_str, i150_atual)
                regs_i155.append((r, ctx.get("_i150_ano_mes", ctx["ano_mes"])))

            elif reg_tipo == "I200" and ctx:
                r = parsear_i200(campos, num_linha, arquivo_str)
                i200_atual = num_linha
                regs_i200.append(r)

            elif reg_tipo == "I250" and ctx:
                if i200_atual is None:
                    logger.warning("I250 orphan at line %d — no I200 parent", num_linha)
                    i200_atual = 0
                r = parsear_i250(campos, num_linha, arquivo_str, i200_atual)
                regs_i250.append(r)

            elif reg_tipo == "J005" and ctx:
                r = parsear_j005(campos, num_linha, arquivo_str)
                j005_atual = num_linha
                regs_j005.append(r)

            elif reg_tipo == "J100" and ctx:
                if j005_atual is None:
                    logger.warning("J100 orphan at line %d — no J005 parent", num_linha)
                    j005_atual = 0
                r = parsear_j100(campos, num_linha, arquivo_str, j005_atual)
                regs_j100.append(r)

            elif reg_tipo == "J150" and ctx:
                if j005_atual is None:
                    logger.warning("J150 orphan at line %d — no J005 parent", num_linha)
                    j005_atual = 0
                r = parsear_j150(campos, num_linha, arquivo_str, j005_atual)
                regs_j150.append(r)

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
            divergencias_bloco9=["Registro 0000 ausente — ECD rejeitada"],
            sucesso=False,
            mensagem="Registro 0000 não encontrado.",
        )

    cnpj = ctx["cnpj_declarante"]
    ano_cal = ctx["ano_calendario"]
    ano_mes_base = ctx["ano_mes"]
    arquivo_hash = _sha256(caminho)

    # --- Validação Bloco 9 (cruzamento 01) ---
    # 9999.QTD_LIN do PVA conta apenas linhas SPED válidas (com pipe
    # inicial). Em ECD com J801 (Termo de Encerramento) o conteúdo RTF
    # é embutido em Base64 multilinhas — continuações sem pipe NÃO são
    # contadas pelo PVA.
    total_linhas_sped = sum(1 for l in linhas_raw if l.startswith("|"))
    contagens_declaradas, divergencias_bloco9 = validar_bloco9(
        contagens_reais, regs_9900, reg9999, total_linhas_sped,
    )
    tem_erro = bool(erros_parse)
    tem_div_bloco9 = bool(divergencias_bloco9)
    sucesso = not tem_erro and not tem_div_bloco9
    status = "ok" if sucesso else "parcial"

    # Classificação da reconciliação de plano de contas (§16.2) é feita após
    # os inserts, dentro da transação, via classificar_reconciliacao — que lê
    # IND_MUDANC_PC e cobertura real do Bloco C direto do banco.

    repo = Repositorio(cnpj, ano_cal, base_dir=base_dir_db)
    repo.criar_banco()

    conn = repo.conexao()
    try:
        with conn:
            repo.registrar_importacao(
                conn,
                sped_tipo="ecd",
                dt_ini=ctx["dt_ini_periodo"],
                dt_fin=ctx["dt_fin_periodo"],
                ano_mes=ano_mes_base,
                arquivo_hash=arquivo_hash,
                arquivo_origem=arquivo_str,
                cod_ver=ctx["cod_ver"],
                encoding_origem=res_enc.encoding,
                encoding_confianca=res_enc.confianca,
                status=status,
            )
            repo.inserir_ecd_0000(conn, reg0000, ctx)
            if reg_i010:
                repo.inserir_ecd_i010(conn, reg_i010, ctx)
            for r in regs_c050:
                repo.inserir_ecd_c050(conn, r, ctx)
            for r in regs_c155:
                repo.inserir_ecd_c155(conn, r, ctx)
            for r in regs_i050:
                repo.inserir_ecd_i050(conn, r, ctx)
            for r in regs_i150:
                repo.inserir_ecd_i150(conn, r, ctx)
            for r, ano_mes_i155 in regs_i155:
                ctx_i155 = dict(ctx)
                ctx_i155["ano_mes"] = ano_mes_i155
                repo.inserir_ecd_i155(conn, r, ctx_i155)
            for r in regs_i200:
                repo.inserir_ecd_i200(conn, r, ctx)
            for r in regs_i250:
                repo.inserir_ecd_i250(conn, r, ctx)
            for r in regs_j005:
                repo.inserir_ecd_j005(conn, r, ctx)
            for r in regs_j100:
                repo.inserir_ecd_j100(conn, r, ctx)
            for r in regs_j150:
                repo.inserir_ecd_j150(conn, r, ctx)
            atualizar_disponibilidade(repo, conn, "ecd", "importada")
            reconciliacao = classificar_reconciliacao(repo, conn, cnpj, ano_cal)
            repo.atualizar_sped_contexto(
                conn, reconciliacao_plano_contas=reconciliacao
            )
    finally:
        conn.close()

    logger.info(
        "ECD %s: I050=%d I155=%d I200=%d I250=%d J100=%d J150=%d reconciliacao=%s (encoding=%s)",
        caminho.name, len(regs_i050), len(regs_i155), len(regs_i200),
        len(regs_i250), len(regs_j100), len(regs_j150),
        reconciliacao, res_enc.encoding,
    )

    return ResultadoImportacao(
        arquivo=arquivo_str,
        cnpj=cnpj,
        ano_calendario=ano_cal,
        ano_mes=ano_mes_base,
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
