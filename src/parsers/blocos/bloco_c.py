"""Parser do Bloco C da EFD-Contribuições: registros C100, C170, C181, C185."""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegC100, RegC170, RegC181, RegC185

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


def _data(s: str) -> str:
    """DDMMAAAA → YYYY-MM-DD."""
    s = s.strip()
    if len(s) == 8 and s.isdigit():
        return f"{s[4:8]}-{s[2:4]}-{s[0:2]}"
    return s


def _g(campos: list[str], i: int) -> str:
    return campos[i].strip() if i < len(campos) else ""


def parsear_c100(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegC100:
    """
    Layout EFD-Contribuições C100 (campos simplificados vs SPED Fiscal):
    |C100|IND_OPER|IND_EMIT|COD_PART|COD_MOD|COD_SIT|SER|NUM_DOC|
     CHV_NFE|DT_DOC|VL_DOC|...
    Posições chave: [2]=IND_OPER [3]=IND_EMIT [4]=COD_PART [5]=COD_MOD
                    [6]=COD_SIT [7]=SER [8]=NUM_DOC [9]=CHV_NFE
                    [10]=DT_DOC [11]=VL_DOC
    """
    return RegC100(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        ind_oper=_g(campos, 2),
        ind_emit=_g(campos, 3),
        cod_part=_g(campos, 4),
        cod_mod=_g(campos, 5),
        cod_sit=_g(campos, 6),
        ser=_g(campos, 7),
        num_doc=_g(campos, 8),
        chave_nfe=_g(campos, 9),
        dt_doc=_data(_g(campos, 10)),
        vl_doc=_dec(_g(campos, 11)),
    )


def parsear_c181(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    c180_linha_arquivo: int,
    ind_oper: str,
) -> RegC181:
    """
    Layout C181 (EFD-Contribuições — PIS detalhe NFC-e consolidada):
    [1]=REG [2]=CST_PIS [3]=CFOP [4]=VL_ITEM [5]=VL_DESC [6]=VL_BC_PIS
    [7]=ALIQ_PIS [8]=QUANT_BC_PIS [9]=ALIQ_PIS_QUANT [10]=VL_PIS [11]=COD_CTA
    """
    return RegC181(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        c180_linha_arquivo=c180_linha_arquivo,
        ind_oper=ind_oper,
        cst_pis=_g(campos, 2),
        cfop=_g(campos, 3),
        vl_item=_dec(_g(campos, 4)),
        vl_desc=_dec(_g(campos, 5)),
        vl_bc_pis=_dec(_g(campos, 6)),
        aliq_pis=_dec(_g(campos, 7)),
        quant_bc_pis=_dec(_g(campos, 8)),
        aliq_pis_quant=_dec(_g(campos, 9)),
        vl_pis=_dec(_g(campos, 10)),
        cod_cta=_g(campos, 11),
    )


def parsear_c185(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    c180_linha_arquivo: int,
    ind_oper: str,
) -> RegC185:
    """
    Layout C185 (EFD-Contribuições — COFINS detalhe NFC-e consolidada):
    [1]=REG [2]=CST_COFINS [3]=CFOP [4]=VL_ITEM [5]=VL_DESC [6]=VL_BC_COFINS
    [7]=ALIQ_COFINS [8]=QUANT_BC_COFINS [9]=ALIQ_COFINS_QUANT [10]=VL_COFINS [11]=COD_CTA
    """
    return RegC185(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        c180_linha_arquivo=c180_linha_arquivo,
        ind_oper=ind_oper,
        cst_cofins=_g(campos, 2),
        cfop=_g(campos, 3),
        vl_item=_dec(_g(campos, 4)),
        vl_desc=_dec(_g(campos, 5)),
        vl_bc_cofins=_dec(_g(campos, 6)),
        aliq_cofins=_dec(_g(campos, 7)),
        quant_bc_cofins=_dec(_g(campos, 8)),
        aliq_cofins_quant=_dec(_g(campos, 9)),
        vl_cofins=_dec(_g(campos, 10)),
        cod_cta=_g(campos, 11),
    )


def parsear_c170(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    c100_linha_arquivo: int,
) -> RegC170:
    """
    Layout C170 (EFD-Contribuições):
    [1]=REG [2]=NUM_ITEM [3]=COD_ITEM [4]=DESCR_COMPL [5]=QTD [6]=UNID
    [7]=VL_ITEM [8]=VL_DESC [9]=IND_MOV [10]=CST_ICMS [11]=CFOP
    [12]=COD_NAT [13]=VL_BC_ICMS [14]=ALIQ_ICMS [15]=VL_ICMS
    [16]=VL_BC_ICMS_ST [17]=ALIQ_ST [18]=VL_ICMS_ST [19]=IND_APUR
    [20]=CST_IPI [21]=COD_ENQ [22]=VL_BC_IPI [23]=ALIQ_IPI [24]=VL_IPI
    [25]=CST_PIS [26]=VL_BC_PIS [27]=ALIQ_PIS [28]=QUANT_BC_PIS
    [29]=ALIQ_PIS_QUANT [30]=VL_PIS [31]=CST_COFINS [32]=VL_BC_COFINS
    [33]=ALIQ_COFINS [34]=QUANT_BC_COFINS [35]=ALIQ_COFINS_QUANT
    [36]=VL_COFINS [37]=COD_CTA
    """
    return RegC170(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        c100_linha_arquivo=c100_linha_arquivo,
        num_item=_g(campos, 2),
        cod_item=_g(campos, 3),
        vl_item=_dec(_g(campos, 7)),
        vl_desc=_dec(_g(campos, 8)),
        cfop=_g(campos, 11),
        vl_icms=_dec(_g(campos, 15)),
        vl_icms_st=_dec(_g(campos, 18)),
        cst_pis=_g(campos, 25),
        vl_bc_pis=_dec(_g(campos, 26)),
        aliq_pis=_dec(_g(campos, 27)),
        quant_bc_pis=_dec(_g(campos, 28)),
        aliq_pis_quant=_dec(_g(campos, 29)),
        vl_pis=_dec(_g(campos, 30)),
        cst_cofins=_g(campos, 31),
        vl_bc_cofins=_dec(_g(campos, 32)),
        aliq_cofins=_dec(_g(campos, 33)),
        quant_bc_cofins=_dec(_g(campos, 34)),
        aliq_cofins_quant=_dec(_g(campos, 35)),
        vl_cofins=_dec(_g(campos, 36)),
        cod_cta=_g(campos, 37),
    )
