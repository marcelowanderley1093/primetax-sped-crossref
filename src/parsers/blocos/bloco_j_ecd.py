"""
Parsers dos registros do Bloco J da ECD (Demonstrações Contábeis).

Registros cobertos: J005, J100, J150.
"""

from decimal import Decimal, InvalidOperation

from src.models.registros import RegEcdJ005, RegEcdJ100, RegEcdJ150


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
    """J150 — DRE. Layout real do Leiaute 9 (ADE Cofis 01/2026):
       REG | COD_AGL | IND_COD_AGL | NIVEL_AGL | COD_AGL_SUP |
       DESCR_COD_AGL | VL_CTA | IND_DC_CTA | IND_GRP_DRE
    Diferente do que documentações antigas sugeriam (VL_CTA_INI/FIN
    separados). Aqui só há VL_CTA e IND_DC_CTA. Para preservar o schema
    atual sem migração, replicamos VL_CTA em vl_cta_ini E vl_cta_fin —
    a interpretação de "valor do período" é única."""
    nu_ordem_cod = _g(campos, 2)
    vl = _dec(_g(campos, 7))
    dc = _g(campos, 8)
    return RegEcdJ150(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="J150",
        j005_linha_arquivo=j005_linha,
        nu_ordem=nu_ordem_cod,
        cod_agl=nu_ordem_cod,        # COD_AGL é o mesmo de NU_ORDEM no SPED
        ind_cod_agl=_g(campos, 3),
        nivel_agl=_g(campos, 4),
        cod_agl_sup=_g(campos, 5),
        descr_cod_agl=_g(campos, 6),
        vl_cta_ini=vl,
        ind_dc_ini=dc,
        vl_cta_fin=vl,
        ind_dc_fin=dc,
        ind_grp_dre=_g(campos, 9),
    )


def parsear_j100(
    campos: list[str], num_linha: int, arquivo_str: str, j005_linha: int
) -> RegEcdJ100:
    """J100 — Balanço Patrimonial. Layout real do Leiaute 9:
       REG | COD_AGL | IND_COD_AGL | NIVEL_AGL | COD_AGL_SUP |
       IND_GRP_BAL | DESCR_COD_AGL | VL_CTA_INI | IND_DC_INI |
       VL_CTA_FIN | IND_DC_FIN
    NU_ORDEM canônico do leiaute é o próprio COD_AGL — guardamos no
    campo nu_ordem para não quebrar o schema."""
    cod = _g(campos, 2)
    return RegEcdJ100(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="J100",
        j005_linha_arquivo=j005_linha,
        nu_ordem=cod,                # COD_AGL = NU_ORDEM neste SPED
        cod_agl=cod,
        ind_cod_agl=_g(campos, 3),
        nivel_agl=_g(campos, 4),
        cod_agl_sup=_g(campos, 5),
        ind_grp_bal=_g(campos, 6),
        descr_cod_agl=_g(campos, 7),
        vl_cta_ini=_dec(_g(campos, 8)),
        ind_dc_ini=_g(campos, 9),
        vl_cta_fin=_dec(_g(campos, 10)),
        ind_dc_fin=_g(campos, 11),
    )
