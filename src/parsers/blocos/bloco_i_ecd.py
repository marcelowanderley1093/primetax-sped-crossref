"""
Parsers dos registros do Bloco I da ECD (Leiaute 9 — ADE Cofis 01/2026).

Registros cobertos: I010, I050, I150, I155, I200.
"""

from decimal import Decimal, InvalidOperation

from src.models.registros import (
    RegEcdI010,
    RegEcdI050,
    RegEcdI150,
    RegEcdI155,
    RegEcdI200,
)


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def _dec(s: str) -> Decimal:
    s = s.strip().replace(",", ".")
    if not s:
        return Decimal("0")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _data(s: str) -> str:
    """DDMMAAAA → YYYY-MM-DD."""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def parsear_i010(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdI010:
    return RegEcdI010(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="I010",
        ind_esc=_g(campos, 2),
        cod_ver_lc=_g(campos, 3),
    )


def parsear_i050(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdI050:
    return RegEcdI050(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="I050",
        dt_alt=_data(_g(campos, 2)),
        cod_nat=_g(campos, 3),
        ind_cta=_g(campos, 4),
        nivel=_g(campos, 5),
        cod_cta=_g(campos, 6),
        cod_cta_sup=_g(campos, 7),
        cta=_g(campos, 8),
    )


def parsear_i150(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdI150:
    return RegEcdI150(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="I150",
        dt_ini=_data(_g(campos, 2)),
        dt_fin=_data(_g(campos, 3)),
    )


def parsear_i155(
    campos: list[str], num_linha: int, arquivo_str: str, i150_linha: int
) -> RegEcdI155:
    return RegEcdI155(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="I155",
        i150_linha_arquivo=i150_linha,
        cod_cta=_g(campos, 2),
        cod_ccus=_g(campos, 3),
        vl_sld_ini=_dec(_g(campos, 4)),
        ind_dc_ini=_g(campos, 5),
        vl_deb=_dec(_g(campos, 6)),
        vl_cred=_dec(_g(campos, 7)),
        vl_sld_fin=_dec(_g(campos, 8)),
        ind_dc_fin=_g(campos, 9),
    )


def parsear_i200(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdI200:
    return RegEcdI200(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="I200",
        num_lcto=_g(campos, 2),
        dt_lcto=_data(_g(campos, 3)),
        vl_lcto=_dec(_g(campos, 4)),
        ind_lcto=_g(campos, 5),
        dt_lcto_ext=_data(_g(campos, 6)),
    )
