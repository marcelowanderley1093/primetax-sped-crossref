"""
Parser principal da EFD-Contribuições.

Coordena o processamento linha a linha, despacha para parsers de bloco,
persiste no banco SQLite e valida a integridade do Bloco 9 (cruzamento 01).
Princípio de rastreabilidade: toda linha tem arquivo_origem + linha_arquivo.
"""

import hashlib
import logging
from pathlib import Path

from src.db.repo import Repositorio
from src.models.registros import ResultadoImportacao
from src.parsers.blocos.bloco_0 import parsear_0000, parsear_0110, parsear_0111, parsear_0200
from src.parsers.blocos.bloco_1 import parsear_1100, parsear_1500
from src.parsers.blocos.bloco_9 import parsear_9900, parsear_9999
from src.parsers.blocos.bloco_c import parsear_c100, parsear_c170, parsear_c181, parsear_c185
from src.parsers.blocos.bloco_d import parsear_d201, parsear_d205
from src.parsers.blocos.bloco_f import (
    parsear_f100, parsear_f120, parsear_f130, parsear_f150,
    parsear_f600, parsear_f700, parsear_f800,
)
from src.parsers.blocos.bloco_m import (
    parsear_m100, parsear_m105, parsear_m200, parsear_m210, parsear_m215,
    parsear_m500, parsear_m505, parsear_m600, parsear_m610, parsear_m615,
)
from src.parsers.common.encoding import detectar_encoding

logger = logging.getLogger(__name__)

_TIPOS_CONHECIDOS = frozenset({
    "0000", "0001", "0100", "0110", "0111", "0140", "0145", "0150", "0190",
    "0200", "0205", "0206", "0208", "0400", "0450", "0500", "0600", "0900",
    "A001", "A010", "A100", "A110", "A111", "A120", "A170", "A990",
    "C001", "C010", "C100", "C110", "C111", "C120", "C170", "C175",
    "C180", "C181", "C185", "C188", "C190", "C191", "C195", "C198",
    "C199", "C380", "C381", "C385", "C395", "C396", "C400", "C405",
    "C481", "C485", "C490", "C491", "C495", "C500", "C501", "C505",
    "C509", "C600", "C601", "C605", "C609", "C700", "C800", "C810",
    "C820", "C830", "C860", "C870", "C880", "C890", "C990",
    "D001", "D010", "D100", "D101", "D105", "D111", "D200", "D201",
    "D205", "D209", "D300", "D309", "D350", "D359", "D500", "D501",
    "D505", "D509", "D600", "D601", "D605", "D609", "D990",
    "F001", "F010", "F100", "F111", "F120", "F129", "F130", "F139",
    "F150", "F200", "F205", "F210", "F211", "F500", "F509", "F510",
    "F519", "F525", "F550", "F559", "F600", "F700", "F800", "F990",
    "I001", "I010", "I100", "I199", "I990",
    "M001", "M010", "M100", "M105", "M110", "M115", "M200", "M205",
    "M210", "M211", "M215", "M220", "M225", "M230", "M300", "M350",
    "M400", "M410", "M500", "M505", "M510", "M515", "M600", "M605",
    "M610", "M611", "M615", "M620", "M625", "M630", "M700", "M800",
    "M810", "M990",
    "P001", "P010", "P100", "P110", "P199", "P200", "P210", "P990",
    "1001", "1010", "1011", "1020", "1050", "1100", "1101", "1110",
    "1200", "1210", "1220", "1300", "1500", "1501", "1510", "1700",
    "1800", "1809", "1900", "1990",
    "9001", "9900", "9990", "9999",
})


def _sha256(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _ano_mes(dt_ini: str) -> int:
    """'YYYY-MM-DD' → YYYYMM int."""
    return int(dt_ini[:4] + dt_ini[5:7])


def _ano_calendario(dt_ini: str) -> int:
    return int(dt_ini[:4])


def importar(
    caminho: Path,
    *,
    encoding_override: str = "auto",
    prompt_operador: bool = True,
    base_dir_db: Path | None = None,
) -> ResultadoImportacao:
    """
    Importa um arquivo EFD-Contribuições para o banco SQLite.

    Args:
        caminho: Caminho para o arquivo .txt/.sped.
        encoding_override: "auto", "utf8" ou "latin1".
        prompt_operador: Pede confirmação ao operador em caso de encoding suspeito.
        base_dir_db: Diretório base para data/db (útil em testes).

    Returns:
        ResultadoImportacao com contagens, encoding detectado e status.
    """
    arquivo_str = str(caminho.resolve())

    res_enc = detectar_encoding(
        caminho, override=encoding_override, prompt_operador=prompt_operador
    )
    codec = "utf-8" if res_enc.encoding == "utf8" else "latin-1"

    texto = caminho.read_text(encoding=codec, errors="strict")
    linhas_raw = texto.splitlines()
    total_linhas = len(linhas_raw)
    logger.info(
        "Arquivo %s: %d linhas (encoding=%s confiança=%s)",
        caminho.name, total_linhas, res_enc.encoding, res_enc.confianca,
    )

    ctx: dict = {}
    c100_atual: int | None = None   # linha_arquivo do C100 corrente no bloco C
    c180_atual: dict | None = None  # {linha_arquivo, ind_oper} do C180 corrente
    d200_atual: dict | None = None  # {linha_arquivo, ind_oper} do D200 corrente
    m210_linha: int = 0             # linha_arquivo do M210 corrente
    m610_linha: int = 0             # linha_arquivo do M610 corrente

    contagens_reais: dict[str, int] = {}
    erros_parse: list[str] = []

    reg0000 = None
    reg0110 = None
    reg0111 = None
    regs_0200: list = []
    regs_c100: list = []
    regs_c170: list = []
    regs_c181: list = []
    regs_c185: list = []
    regs_d201: list = []
    regs_d205: list = []
    regs_f100: list = []
    regs_f120: list = []
    regs_f130: list = []
    regs_f150: list = []
    regs_f600: list = []
    regs_f700: list = []
    regs_f800: list = []
    regs_m100: list = []
    regs_m105: list = []
    regs_m200: list = []
    regs_m210: list = []
    regs_m215: list = []
    regs_m500: list = []
    regs_m505: list = []
    regs_m600: list = []
    regs_m610: list = []
    regs_m615: list = []
    regs_1100: list = []
    regs_1500: list = []
    regs_9900: list = []
    reg9999 = None

    for num_linha, linha_raw in enumerate(linhas_raw, start=1):
        linha = linha_raw.strip()
        if not linha:
            continue

        campos = linha.split("|")
        if len(campos) < 2:
            logger.warning("Linha %d sem separador |: %r", num_linha, linha[:40])
            continue

        reg_tipo = campos[1].strip().upper()
        contagens_reais[reg_tipo] = contagens_reais.get(reg_tipo, 0) + 1

        if reg_tipo not in _TIPOS_CONHECIDOS:
            logger.debug("Registro desconhecido linha %d: %s (ignorado)", num_linha, reg_tipo)
            continue

        try:
            if reg_tipo == "0000":
                reg0000 = parsear_0000(campos, num_linha, arquivo_str)
                ctx["cnpj_declarante"] = reg0000.cnpj
                ctx["dt_ini_periodo"] = reg0000.dt_ini
                ctx["dt_fin_periodo"] = reg0000.dt_fin
                ctx["ano_mes"] = _ano_mes(reg0000.dt_ini)
                ctx["ano_calendario"] = _ano_calendario(reg0000.dt_ini)
                ctx["cod_ver"] = reg0000.cod_ver

            elif reg_tipo == "0110":
                if not ctx:
                    erros_parse.append("0110 encontrado antes do 0000")
                    continue
                reg0110 = parsear_0110(campos, num_linha, arquivo_str)

            elif reg_tipo == "0111":
                if not ctx:
                    continue
                reg0111 = parsear_0111(campos, num_linha, arquivo_str)

            elif reg_tipo == "0200":
                if not ctx:
                    continue
                regs_0200.append(parsear_0200(campos, num_linha, arquivo_str))

            elif reg_tipo == "C100":
                if not ctx:
                    erros_parse.append(f"C100 linha {num_linha} sem contexto 0000")
                    continue
                r = parsear_c100(campos, num_linha, arquivo_str)
                c100_atual = num_linha
                c180_atual = None  # C100 fecha qualquer bloco C180 anterior
                regs_c100.append(r)

            elif reg_tipo == "C170":
                if not ctx:
                    continue
                if c100_atual is None:
                    msg = f"C170 órfão na linha {num_linha} — sem C100 pai (CLAUDE.md §7.2)"
                    erros_parse.append(msg)
                    logger.warning(msg)
                    continue
                r = parsear_c170(campos, num_linha, arquivo_str, c100_atual)
                regs_c170.append(r)

            elif reg_tipo == "C180":
                # Registro-pai da NFC-e consolidada — rastreia linha e IND_OPER
                c100_atual = None  # C180 não é filho de C100
                c180_atual = {
                    "linha_arquivo": num_linha,
                    "ind_oper": campos[2].strip() if len(campos) > 2 else "",
                }

            elif reg_tipo == "C181":
                if not ctx:
                    continue
                if c180_atual is None:
                    logger.warning("C181 órfão na linha %d — sem C180 pai", num_linha)
                    continue
                r = parsear_c181(
                    campos, num_linha, arquivo_str,
                    c180_atual["linha_arquivo"], c180_atual["ind_oper"],
                )
                regs_c181.append(r)

            elif reg_tipo == "C185":
                if not ctx:
                    continue
                if c180_atual is None:
                    logger.warning("C185 órfão na linha %d — sem C180 pai", num_linha)
                    continue
                r = parsear_c185(
                    campos, num_linha, arquivo_str,
                    c180_atual["linha_arquivo"], c180_atual["ind_oper"],
                )
                regs_c185.append(r)

            elif reg_tipo == "D200":
                # Registro-pai de serviços de transporte consolidados
                d200_atual = {
                    "linha_arquivo": num_linha,
                    "ind_oper": campos[2].strip() if len(campos) > 2 else "",
                }

            elif reg_tipo == "D201":
                if not ctx:
                    continue
                if d200_atual is None:
                    logger.warning("D201 órfão na linha %d — sem D200 pai", num_linha)
                    continue
                r = parsear_d201(
                    campos, num_linha, arquivo_str,
                    d200_atual["linha_arquivo"], d200_atual["ind_oper"],
                )
                regs_d201.append(r)

            elif reg_tipo == "D205":
                if not ctx:
                    continue
                if d200_atual is None:
                    logger.warning("D205 órfão na linha %d — sem D200 pai", num_linha)
                    continue
                r = parsear_d205(
                    campos, num_linha, arquivo_str,
                    d200_atual["linha_arquivo"], d200_atual["ind_oper"],
                )
                regs_d205.append(r)

            elif reg_tipo == "F100":
                if not ctx:
                    continue
                regs_f100.append(parsear_f100(campos, num_linha, arquivo_str))

            elif reg_tipo == "F120":
                if not ctx:
                    continue
                regs_f120.append(parsear_f120(campos, num_linha, arquivo_str))

            elif reg_tipo == "F130":
                if not ctx:
                    continue
                regs_f130.append(parsear_f130(campos, num_linha, arquivo_str))

            elif reg_tipo == "F150":
                if not ctx:
                    continue
                regs_f150.append(parsear_f150(campos, num_linha, arquivo_str))

            elif reg_tipo == "F600":
                if not ctx:
                    continue
                regs_f600.append(parsear_f600(campos, num_linha, arquivo_str))

            elif reg_tipo == "F700":
                if not ctx:
                    continue
                regs_f700.append(parsear_f700(campos, num_linha, arquivo_str))

            elif reg_tipo == "F800":
                if not ctx:
                    continue
                regs_f800.append(parsear_f800(campos, num_linha, arquivo_str))

            elif reg_tipo == "M100":
                if not ctx:
                    continue
                regs_m100.append(parsear_m100(campos, num_linha, arquivo_str))

            elif reg_tipo == "M105":
                if not ctx:
                    continue
                regs_m105.append(parsear_m105(campos, num_linha, arquivo_str))

            elif reg_tipo == "M500":
                if not ctx:
                    continue
                regs_m500.append(parsear_m500(campos, num_linha, arquivo_str))

            elif reg_tipo == "M505":
                if not ctx:
                    continue
                regs_m505.append(parsear_m505(campos, num_linha, arquivo_str))

            elif reg_tipo == "M210":
                if not ctx:
                    continue
                r = parsear_m210(campos, num_linha, arquivo_str)
                m210_linha = num_linha
                regs_m210.append(r)

            elif reg_tipo == "M215":
                if not ctx:
                    continue
                r = parsear_m215(campos, num_linha, arquivo_str, m210_linha)
                regs_m215.append(r)

            elif reg_tipo == "M610":
                if not ctx:
                    continue
                r = parsear_m610(campos, num_linha, arquivo_str)
                m610_linha = num_linha
                regs_m610.append(r)

            elif reg_tipo == "M615":
                if not ctx:
                    continue
                r = parsear_m615(campos, num_linha, arquivo_str, m610_linha)
                regs_m615.append(r)

            elif reg_tipo == "1100":
                if not ctx:
                    continue
                regs_1100.append(parsear_1100(campos, num_linha, arquivo_str))

            elif reg_tipo == "1500":
                if not ctx:
                    continue
                regs_1500.append(parsear_1500(campos, num_linha, arquivo_str))

            elif reg_tipo == "M200":
                if not ctx:
                    continue
                regs_m200.append(parsear_m200(campos, num_linha, arquivo_str))
                c100_atual = None  # bloco C encerrado ao entrar no M
                c180_atual = None

            elif reg_tipo == "M600":
                if not ctx:
                    continue
                regs_m600.append(parsear_m600(campos, num_linha, arquivo_str))

            elif reg_tipo == "9900":
                if not ctx:
                    continue
                regs_9900.append(parsear_9900(campos, num_linha, arquivo_str))

            elif reg_tipo == "9999":
                reg9999 = parsear_9999(campos, num_linha, arquivo_str)

        except Exception as exc:
            msg = f"Erro ao parsear linha {num_linha} ({reg_tipo}): {exc}"
            logger.error(msg)
            erros_parse.append(msg)

    # --- Validação do 0000 ---
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
            divergencias_bloco9=["Registro 0000 ausente — arquivo rejeitado"],
            sucesso=False,
            mensagem="Registro 0000 não encontrado. Arquivo não reconhecível.",
        )

    # --- Validação Bloco 9 (cruzamento 01) ---
    contagens_declaradas: dict[str, int] = {r.reg_blc: r.qtd_reg_blc for r in regs_9900}
    divergencias_bloco9: list[str] = []

    for reg_dec, qtd_dec in contagens_declaradas.items():
        qtd_real = contagens_reais.get(reg_dec, 0)
        if qtd_real != qtd_dec:
            divergencias_bloco9.append(
                f"{reg_dec}: declarado={qtd_dec} real={qtd_real}"
            )

    if reg9999:
        # 9999.QTD_LIN inclui a própria linha 9999
        if reg9999.qtd_lin != total_linhas:
            divergencias_bloco9.append(
                f"9999.QTD_LIN={reg9999.qtd_lin} ≠ linhas lidas={total_linhas}"
            )

    # --- Persistência ---
    cnpj = ctx["cnpj_declarante"]
    ano_cal = ctx["ano_calendario"]
    arquivo_hash = _sha256(caminho)

    repo = Repositorio(cnpj, ano_cal, base_dir=base_dir_db)
    repo.criar_banco()

    tem_erro = bool(erros_parse)
    tem_div_bloco9 = bool(divergencias_bloco9)
    status = "ok" if not tem_erro and not tem_div_bloco9 else "parcial"

    conn = repo.conexao()
    try:
        with conn:
            repo.registrar_importacao(
                conn,
                sped_tipo="efd_contribuicoes",
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
            repo.atualizar_sped_contexto(
                conn,
                cnpj=cnpj,
                ano_calendario=ano_cal,
                disponibilidade_efd_contrib="importada",
            )
            repo.inserir_0000(conn, reg0000, ctx)
            if reg0110:
                repo.inserir_0110(conn, reg0110, ctx)
            if reg0111:
                repo.inserir_0111(conn, reg0111, ctx)
            for r in regs_0200:
                repo.inserir_0200(conn, r, ctx)
            for r in regs_c100:
                repo.inserir_c100(conn, r, ctx)
            for r in regs_c170:
                repo.inserir_c170(conn, r, ctx)
            for r in regs_c181:
                repo.inserir_c181(conn, r, ctx)
            for r in regs_c185:
                repo.inserir_c185(conn, r, ctx)
            for r in regs_d201:
                repo.inserir_d201(conn, r, ctx)
            for r in regs_d205:
                repo.inserir_d205(conn, r, ctx)
            for r in regs_f100:
                repo.inserir_f100(conn, r, ctx)
            for r in regs_f120:
                repo.inserir_f120(conn, r, ctx)
            for r in regs_f130:
                repo.inserir_f130(conn, r, ctx)
            for r in regs_f150:
                repo.inserir_f150(conn, r, ctx)
            for r in regs_f600:
                repo.inserir_f600(conn, r, ctx)
            for r in regs_f700:
                repo.inserir_f700(conn, r, ctx)
            for r in regs_f800:
                repo.inserir_f800(conn, r, ctx)
            for r in regs_m100:
                repo.inserir_m100(conn, r, ctx)
            for r in regs_m105:
                repo.inserir_m105(conn, r, ctx)
            for r in regs_m200:
                repo.inserir_m200(conn, r, ctx)
            for r in regs_m210:
                repo.inserir_m210(conn, r, ctx)
            for r in regs_m215:
                repo.inserir_m215(conn, r, ctx)
            for r in regs_m500:
                repo.inserir_m500(conn, r, ctx)
            for r in regs_m505:
                repo.inserir_m505(conn, r, ctx)
            for r in regs_m600:
                repo.inserir_m600(conn, r, ctx)
            for r in regs_m610:
                repo.inserir_m610(conn, r, ctx)
            for r in regs_m615:
                repo.inserir_m615(conn, r, ctx)
            for r in regs_1100:
                repo.inserir_1100(conn, r, ctx)
            for r in regs_1500:
                repo.inserir_1500(conn, r, ctx)
            for r in regs_9900:
                repo.inserir_9900(conn, r, ctx)
    finally:
        conn.close()

    todas_divergencias = divergencias_bloco9 + erros_parse
    sucesso = status == "ok"
    mensagem = (
        "Importação concluída com sucesso."
        if sucesso
        else f"{len(todas_divergencias)} problema(s): " + "; ".join(todas_divergencias[:3])
    )

    logger.info(
        "%s CNPJ=%s AC=%d status=%s 0200=%d C100=%d C170=%d C181=%d D201=%d"
        " F100=%d F120=%d F130=%d F150=%d F600=%d F700=%d F800=%d"
        " M100=%d M105=%d M200=%d M500=%d M505=%d M210=%d M610=%d M215=%d"
        " 1100=%d 1500=%d divBloco9=%d erros=%d",
        caminho.name, cnpj, ano_cal, status,
        len(regs_0200), len(regs_c100), len(regs_c170), len(regs_c181), len(regs_d201),
        len(regs_f100), len(regs_f120), len(regs_f130), len(regs_f150),
        len(regs_f600), len(regs_f700), len(regs_f800),
        len(regs_m100), len(regs_m105), len(regs_m200), len(regs_m500), len(regs_m505),
        len(regs_m210), len(regs_m610), len(regs_m215),
        len(regs_1100), len(regs_1500),
        len(divergencias_bloco9), len(erros_parse),
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
        mensagem=mensagem,
    )
