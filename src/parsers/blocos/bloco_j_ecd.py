"""
Parsers dos registros do Bloco J da ECD (Demonstrações Contábeis).

Registros cobertos: J005, J150.
"""

from decimal import Decimal, InvalidOperation

from src.models.registros import RegEcdJ005, RegEcdJ150


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


def parsear_j005(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdJ005:
    return RegEcdJ005(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="J005",
        dt_ini=_data(_g(campos, 2)),
        dt_fin=_data(_g(campos, 3)),
        id_dem=_g(campos, 4),
    )


def parsear_j150(
    campos: list[str], num_linha: int, arquivo_str: str, j005_linha: int
) -> RegEcdJ150:
    return RegEcdJ150(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="J150",
        j005_linha_arquivo=j005_linha,
        nu_ordem=_g(campos, 2),
        cod_agl=_g(campos, 3),
        ind_cod_agl=_g(campos, 4),
        nivel_agl=_g(campos, 5),
        cod_agl_sup=_g(campos, 6),
        descr_cod_agl=_g(campos, 7),
        vl_cta_ini=_dec(_g(campos, 8)),
        ind_dc_ini=_g(campos, 9),
        vl_cta_fin=_dec(_g(campos, 10)),
        ind_dc_fin=_g(campos, 11),
        ind_grp_dre=_g(campos, 12),
    )
