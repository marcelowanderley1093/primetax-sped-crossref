"""Parser do Bloco D da EFD-Contribuições: registros D201, D205.

Sprint 2: suporte a Tese 69 em documentos de serviços de transporte.
D200 é o registro-pai (consolidação por serviço); D201/D205 são os detalhes PIS/COFINS.
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegD201, RegD205

logger = logging.getLogger(__name__)


def _dec(s: str) -> Decimal:
    s = s.strip()
    if not s:
        return Decimal("0")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return Decimal("0")


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_d201(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    d200_linha_arquivo: int,
    ind_oper: str,
) -> RegD201:
    """
    Layout D201 (EFD-Contribuições — PIS detalhe transporte):
    [1]=REG [2]=CST_PIS [3]=VL_ITEM [4]=VL_BC_PIS [5]=ALIQ_PIS
    [6]=QUANT_BC_PIS [7]=ALIQ_PIS_QUANT [8]=VL_PIS [9]=COD_CTA

    Sinal Tese 69: VL_BC_PIS == VL_ITEM → ICMS não foi excluído da base.
    Em D200/D201 não há campo VL_ICMS explícito — o ICMS deveria reduzir VL_BC_PIS.
    """
    return RegD201(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        d200_linha_arquivo=d200_linha_arquivo,
        ind_oper=ind_oper,
        cst_pis=_g(campos, 2),
        vl_item=_dec(_g(campos, 3)),
        vl_bc_pis=_dec(_g(campos, 4)),
        aliq_pis=_dec(_g(campos, 5)),
        quant_bc_pis=_dec(_g(campos, 6)),
        aliq_pis_quant=_dec(_g(campos, 7)),
        vl_pis=_dec(_g(campos, 8)),
        cod_cta=_g(campos, 9),
    )


def parsear_d205(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    d200_linha_arquivo: int,
    ind_oper: str,
) -> RegD205:
    """
    Layout D205 (EFD-Contribuições — COFINS detalhe transporte):
    [1]=REG [2]=CST_COFINS [3]=VL_ITEM [4]=VL_BC_COFINS [5]=ALIQ_COFINS
    [6]=QUANT_BC_COFINS [7]=ALIQ_COFINS_QUANT [8]=VL_COFINS [9]=COD_CTA
    """
    return RegD205(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        d200_linha_arquivo=d200_linha_arquivo,
        ind_oper=ind_oper,
        cst_cofins=_g(campos, 2),
        vl_item=_dec(_g(campos, 3)),
        vl_bc_cofins=_dec(_g(campos, 4)),
        aliq_cofins=_dec(_g(campos, 5)),
        quant_bc_cofins=_dec(_g(campos, 6)),
        aliq_cofins_quant=_dec(_g(campos, 7)),
        vl_cofins=_dec(_g(campos, 8)),
        cod_cta=_g(campos, 9),
    )
