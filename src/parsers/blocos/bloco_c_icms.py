"""Parser do Bloco C da EFD ICMS/IPI: registros C100 e C170.

EFD ICMS/IPI C170 tem 38 campos (vs 37 da EFD-Contribuições):
  campo extra [38] = VL_ABAT_NT.
  PIS/COFINS: campos [25]-[36] — mesmas posições semânticas.
  CFOP início '7' → exportação → CR-37.
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegIcmsC100, RegIcmsC170

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


def parsear_c100_icms(
    campos: list[str], linha_arquivo: int, arquivo_origem: str
) -> RegIcmsC100:
    """C100 EFD ICMS/IPI — apenas IND_OPER é necessário para rastrear hierarquia."""
    return RegIcmsC100(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_oper=_g(campos, 2),
    )


def parsear_c170_icms(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    c100_linha_arquivo: int,
) -> RegIcmsC170:
    """
    C170 EFD ICMS/IPI — 38 campos:
    [1]=REG [2]=NUM_ITEM [3]=COD_ITEM [4]=DESCR_COMPL [5]=QTD [6]=UNID [7]=VL_ITEM
    [8]=VL_DESC [9]=IND_MOV [10]=CST_ICMS [11]=CFOP [12]=COD_NAT [13]=VL_BC_ICMS
    [14]=ALIQ_ICMS [15]=VL_ICMS [16]=VL_BC_ICMS_ST [17]=ALIQ_ST [18]=VL_ICMS_ST
    [19]=VL_IPI [20]=CST_IPI [21]=COD_ENQ [22]=VL_BC_IPI [23]=ALIQ_IPI [24]=VL_IPI_SAIDA
    [25]=CST_PIS [26]=VL_BC_PIS [27]=ALIQ_PIS [28]=QUANT_BC_PIS [29]=ALIQ_PIS_QUANT
    [30]=VL_PIS [31]=CST_COFINS [32]=VL_BC_COFINS [33]=ALIQ_COFINS [34]=QUANT_BC_COFINS
    [35]=ALIQ_COFINS_QUANT [36]=VL_COFINS [37]=COD_CTA [38]=VL_ABAT_NT
    """
    return RegIcmsC170(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        c100_linha_arquivo=c100_linha_arquivo,
        num_item=_g(campos, 2),
        cod_item=_g(campos, 3),
        cfop=_g(campos, 11),
        cst_icms=_g(campos, 10),
        vl_item=_dec(_g(campos, 7)),
        vl_bc_icms=_dec(_g(campos, 13)),
        aliq_icms=_dec(_g(campos, 14)),
        vl_icms=_dec(_g(campos, 15)),
        cst_pis=_g(campos, 25),
        vl_bc_pis=_dec(_g(campos, 26)),
        aliq_pis=_dec(_g(campos, 27)),
        vl_pis=_dec(_g(campos, 30)),
        cst_cofins=_g(campos, 31),
        vl_bc_cofins=_dec(_g(campos, 32)),
        aliq_cofins=_dec(_g(campos, 33)),
        vl_cofins=_dec(_g(campos, 36)),
        cod_cta=_g(campos, 37),
    )
