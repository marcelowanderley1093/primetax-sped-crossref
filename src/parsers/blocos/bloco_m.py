"""Parser do Bloco M: M200/M600 (Sprint 1); M215/M615 (Sprint 2); M210/M610 (Sprint 3);
M100/M500 (Sprint 4 — CR-29/CR-30); M105/M505 (Sprint 5 — CR-32/CR-34).
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import (
    RegM100, RegM105, RegM200, RegM210, RegM215,
    RegM500, RegM505, RegM600, RegM610, RegM615,
)

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


def parsear_m200(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM200:
    """
    Layout M200 (PIS — resumo apuração, 13 campos):
    [2]=VL_TOT_CONT_NC_PER  [3]=VL_TOT_CRED_DESC  [12]=VL_REC_BRT_TOTAL
    Campo 3 = Σ M100.VL_CRED_DESC — usado no CR-29 (Sprint 4+).
    """
    return RegM200(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        vl_tot_cont_nc_per=_dec(_g(campos, 2)),
        vl_tot_cred_desc=_dec(_g(campos, 3)),
        vl_rec_brt_total=_dec(_g(campos, 12)),
    )


def parsear_m600(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM600:
    """
    Layout M600 (COFINS — resumo apuração): estrutura idêntica ao M200.
    [2]=VL_TOT_CONT_NC_PER  [3]=VL_TOT_CRED_DESC  [12]=VL_REC_BRT_TOTAL
    Campo 3 = Σ M500.VL_CRED_DESC — usado no CR-30 (Sprint 4+).
    """
    return RegM600(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        vl_tot_cont_nc_per=_dec(_g(campos, 2)),
        vl_tot_cred_desc=_dec(_g(campos, 3)),
        vl_rec_brt_total=_dec(_g(campos, 12)),
    )


def parsear_m105(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM105:
    """
    Layout M105 (Detalhamento da Base PIS por NAT_BC_CRED, 10 campos):
    [1]=REG [2]=NAT_BC_CRED [3]=VL_BC_PIS_TOT [4]=VL_BC_MINUT [5]=VL_BC_MINDT
    [6]=VL_BC_MEXP [7]=VL_AMT_PARC_FORN [8]=VL_BC_ISENTA [9]=VL_BC_OUTRAS [10]=DESC_COMPL

    CR-32: Σ VL_BC_PIS_TOT deve conferir com Σ C170/F100.VL_BC_PIS (CST 50-67).
    """
    return RegM105(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        nat_bc_cred=_g(campos, 2),
        vl_bc_pis_tot=_dec(_g(campos, 3)),
        vl_bc_minut=_dec(_g(campos, 4)),
        vl_bc_mindt=_dec(_g(campos, 5)),
        vl_bc_mexp=_dec(_g(campos, 6)),
        vl_amt_parc_forn=_dec(_g(campos, 7)),
        vl_bc_isenta=_dec(_g(campos, 8)),
        vl_bc_outras=_dec(_g(campos, 9)),
        desc_compl=_g(campos, 10),
    )


def parsear_m505(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM505:
    """
    Layout M505 (Detalhamento da Base COFINS por NAT_BC_CRED, 10 campos):
    Estrutura idêntica ao M105 — campo 3 = VL_BC_COFINS_TOT.
    CR-34: Σ VL_BC_COFINS_TOT deve conferir com Σ C170/F100.VL_BC_COFINS (CST 50-67).
    """
    return RegM505(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        nat_bc_cred=_g(campos, 2),
        vl_bc_cofins_tot=_dec(_g(campos, 3)),
        vl_bc_minut=_dec(_g(campos, 4)),
        vl_bc_mindt=_dec(_g(campos, 5)),
        vl_bc_mexp=_dec(_g(campos, 6)),
        vl_amt_parc_forn=_dec(_g(campos, 7)),
        vl_bc_isenta=_dec(_g(campos, 8)),
        vl_bc_outras=_dec(_g(campos, 9)),
        desc_compl=_g(campos, 10),
    )


def parsear_m100(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM100:
    """
    Layout M100 (Crédito PIS por tipo, 15 campos):
    [2]=COD_CRED [3]=IND_CRED_ORI [4]=VL_BC_PIS [5]=ALIQ_PIS [6]=QUANT_BC_PIS
    [7]=ALIQ_PIS_QUANT [8]=VL_CRED_DISP [9]=VL_AJUS_ACRES [10]=VL_AJUS_REDUC
    [11]=VL_CRED_DIFER [12]=VL_CRED_DIFER_ANT [13]=IND_APRO
    [14]=VL_CRED_DESC → Σ = M200.VL_TOT_CRED_DESC  [15]=SLD_CRED
    """
    return RegM100(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_cred=_g(campos, 2),
        ind_cred_ori=_g(campos, 3),
        vl_bc_pis=_dec(_g(campos, 4)),
        aliq_pis=_dec(_g(campos, 5)),
        quant_bc_pis=_dec(_g(campos, 6)),
        aliq_pis_quant=_dec(_g(campos, 7)),
        vl_cred_disp=_dec(_g(campos, 8)),
        vl_ajus_acres=_dec(_g(campos, 9)),
        vl_ajus_reduc=_dec(_g(campos, 10)),
        vl_cred_difer=_dec(_g(campos, 11)),
        vl_cred_difer_ant=_dec(_g(campos, 12)),
        ind_apro=_g(campos, 13),
        vl_cred_desc=_dec(_g(campos, 14)),
        sld_cred=_dec(_g(campos, 15)),
    )


def parsear_m500(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM500:
    """
    Layout M500 (Crédito COFINS por tipo, 15 campos):
    Estrutura idêntica ao M100 — campo 4 = VL_BC_COFINS, campo 5 = ALIQ_COFINS.
    [14]=VL_CRED_DESC → Σ = M600.VL_TOT_CRED_DESC
    """
    return RegM500(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_cred=_g(campos, 2),
        ind_cred_ori=_g(campos, 3),
        vl_bc_cofins=_dec(_g(campos, 4)),
        aliq_cofins=_dec(_g(campos, 5)),
        quant_bc_cofins=_dec(_g(campos, 6)),
        aliq_cofins_quant=_dec(_g(campos, 7)),
        vl_cred_disp=_dec(_g(campos, 8)),
        vl_ajus_acres=_dec(_g(campos, 9)),
        vl_ajus_reduc=_dec(_g(campos, 10)),
        vl_cred_difer=_dec(_g(campos, 11)),
        vl_cred_difer_ant=_dec(_g(campos, 12)),
        ind_apro=_g(campos, 13),
        vl_cred_desc=_dec(_g(campos, 14)),
        sld_cred=_dec(_g(campos, 15)),
    )


def parsear_m210(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM210:
    """
    Layout M210 (Contribuição do Período — PIS/Pasep, por COD_CONT):
    [1]=REG [2]=COD_CONT [3]=VL_REC_BRT [4]=VL_BC_CONT [5]=ALIQ_PIS
    [6]=QUANT_BC_PIS [7]=ALIQ_PIS_QUANT [8]=VL_CONT_APU
    [9]=VL_AJUS_ACRES [10]=VL_AJUS_REDUC [11]=VL_CONT_DIFER
    [12]=VL_CONT_DIFER_ANT [13]=VL_CONT_PER

    COD_CONT mapeia para CST + alíquota. VL_BC_CONT é a base de cálculo
    declarada para esse grupo — usada no cruzamento CR-31.
    """
    return RegM210(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_cont=_g(campos, 2),
        vl_rec_brt=_dec(_g(campos, 3)),
        vl_bc_cont=_dec(_g(campos, 4)),
        aliq_pis=_dec(_g(campos, 5)),
        vl_cont_apu=_dec(_g(campos, 8)),
        vl_ajus_reduc=_dec(_g(campos, 10)),
        vl_cont_per=_dec(_g(campos, 13)),
    )


def parsear_m610(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> RegM610:
    """
    Layout M610 (Contribuição do Período — COFINS, por COD_CONT):
    estrutura idêntica ao M210 (campo 5 = ALIQ_COFINS em vez de ALIQ_PIS).
    """
    return RegM610(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_cont=_g(campos, 2),
        vl_rec_brt=_dec(_g(campos, 3)),
        vl_bc_cont=_dec(_g(campos, 4)),
        aliq_cofins=_dec(_g(campos, 5)),
        vl_cont_apu=_dec(_g(campos, 8)),
        vl_ajus_reduc=_dec(_g(campos, 10)),
        vl_cont_per=_dec(_g(campos, 13)),
    )


def parsear_m215(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    m210_linha_arquivo: int,
) -> RegM215:
    """
    Layout M215 (ajuste à base de cálculo do PIS — filho de M210):
    [1]=REG [2]=IND_AJ_BC [3]=VL_AJ_BC [4]=COD_AJ_BC [5]=NUM_DOC
    [6]=DESCR_AJ_BC [7]=DT_REF [8]=COD_CTA [9]=CNPJ [10]=INFO_COMPL

    IND_AJ_BC: "0"=redução da base, "1"=acréscimo.
    Leiaute EFD-Contribuições 3.1.0+ (DT_INI >= 01/2019). CLAUDE.md §5.2.
    """
    return RegM215(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        m210_linha_arquivo=m210_linha_arquivo,
        ind_aj_bc=_g(campos, 2),
        vl_aj_bc=_dec(_g(campos, 3)),
        cod_aj_bc=_g(campos, 4),
        num_doc=_g(campos, 5),
        descr_aj_bc=_g(campos, 6),
        dt_ref=_g(campos, 7),
        cod_cta=_g(campos, 8),
        cnpj_ref=_g(campos, 9),
    )


def parsear_m615(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    m610_linha_arquivo: int,
) -> RegM615:
    """
    Layout M615 (ajuste à base de cálculo da COFINS — filho de M610):
    estrutura idêntica ao M215.
    """
    return RegM615(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        m610_linha_arquivo=m610_linha_arquivo,
        ind_aj_bc=_g(campos, 2),
        vl_aj_bc=_dec(_g(campos, 3)),
        cod_aj_bc=_g(campos, 4),
        num_doc=_g(campos, 5),
        descr_aj_bc=_g(campos, 6),
        dt_ref=_g(campos, 7),
        cod_cta=_g(campos, 8),
        cnpj_ref=_g(campos, 9),
    )
