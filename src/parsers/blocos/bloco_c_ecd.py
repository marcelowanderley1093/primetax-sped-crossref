"""
Parsers dos registros do Bloco C da ECD (Leiaute 9 — ADE Cofis 01/2026).

O Bloco C preserva dados da ECD imediatamente anterior. É gerado pelo PGE
ao recuperar o arquivo anterior e é a única ponte confiável entre exercícios
quando houve mudança de plano de contas (0000.IND_MUDANC_PC='1').

Registros cobertos nesta versão: C050, C155.
Não cobertos por enquanto (não-críticos para classificação §16.2):
  C040, C051, C052, C150, C600, C650.
"""

from decimal import Decimal, InvalidOperation

from src.models.registros import RegEcdC050, RegEcdC155


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
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def parsear_c050(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdC050:
    """C050 — estrutura idêntica ao I050 (plano de contas recuperado)."""
    return RegEcdC050(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="C050",
        dt_alt=_data(_g(campos, 2)),
        cod_nat=_g(campos, 3),
        ind_cta=_g(campos, 4),
        nivel=_g(campos, 5),
        cod_cta=_g(campos, 6),
        cod_cta_sup=_g(campos, 7),
        cta=_g(campos, 8),
    )


def parsear_c155(
    campos: list[str], num_linha: int, arquivo_str: str
) -> RegEcdC155:
    """C155 — saldos finais do exercício anterior (sem VL_DEB/VL_CRED)."""
    return RegEcdC155(
        linha_arquivo=num_linha,
        arquivo_origem=arquivo_str,
        reg="C155",
        cod_cta=_g(campos, 2),
        cod_ccus=_g(campos, 3),
        vl_sld_ini=_dec(_g(campos, 4)),
        ind_dc_ini=_g(campos, 5),
        vl_sld_fin=_dec(_g(campos, 6)),
        ind_dc_fin=_g(campos, 7),
    )
