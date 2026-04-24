"""Parsers para Bloco M da ECF — e-Lalur e e-Lacs (M300, M312, M350, M362, M500).

Base legal: Lei 12.973/2014; IN RFB 1.700/2017; ADE Cofis 02/2026 §12.
M300: Parte A do e-Lalur (IRPJ) — adições, exclusões, compensações.
M312: números de lançamento contábil (ECD) vinculados a M310 filho de M300.
M350: Parte A do e-Lacs (CSLL) — espelho do M300.
M362: equivalente ao M312 para CSLL.
M500: controle de saldos da Parte B (visão sintética anual).
"""

from decimal import Decimal

from src.models.registros import (
    RegEcfM300,
    RegEcfM312,
    RegEcfM350,
    RegEcfM362,
    RegEcfM500,
)


def _d(s: str) -> Decimal:
    return Decimal(s.replace(",", ".")) if s.strip() else Decimal("0")


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_m300(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfM300:
    return RegEcfM300(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="M300",
        codigo=_g(campos, 2),
        descricao=_g(campos, 3),
        tipo_lancamento=_g(campos, 4),
        ind_relacao=_g(campos, 5),
        valor=_d(_g(campos, 6)),
        hist_lan_lal=_g(campos, 7),
    )


def parsear_m312(
    campos: list[str], num_linha: int, arquivo_str: str, m300_linha: int
) -> RegEcfM312:
    return RegEcfM312(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="M312",
        m300_linha_arquivo=m300_linha,
        num_lcto=_g(campos, 2),
    )


def parsear_m350(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfM350:
    return RegEcfM350(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="M350",
        codigo=_g(campos, 2),
        descricao=_g(campos, 3),
        tipo_lancamento=_g(campos, 4),
        ind_relacao=_g(campos, 5),
        valor=_d(_g(campos, 6)),
        hist_lan_lal=_g(campos, 7),
    )


def parsear_m362(
    campos: list[str], num_linha: int, arquivo_str: str, m350_linha: int
) -> RegEcfM362:
    return RegEcfM362(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="M362",
        m350_linha_arquivo=m350_linha,
        num_lcto=_g(campos, 2),
    )


def parsear_m500(campos: list[str], num_linha: int, arquivo_str: str) -> RegEcfM500:
    return RegEcfM500(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="M500",
        cod_cta_b=_g(campos, 2),
        cod_tributo=_g(campos, 3),
        sd_ini_lal=_d(_g(campos, 4)),
        ind_sd_ini_lal=_g(campos, 5),
        vl_lcto_parte_a=_d(_g(campos, 6)),
        ind_vl_lcto_parte_a=_g(campos, 7),
        vl_lcto_parte_b=_d(_g(campos, 8)),
        ind_vl_lcto_parte_b=_g(campos, 9),
        sd_fim_lal=_d(_g(campos, 10)),
        ind_sd_fim_lal=_g(campos, 11),
    )
