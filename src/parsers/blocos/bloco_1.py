"""Parser do Bloco 1 da EFD-Contribuições: 1100/1500 (carry-forward de créditos).

Sprint 5: CR-25 (saldo de crédito acumulado disponível para compensação).
Base legal: Art. 3º Lei 10.637/2002; Lei 9.430/1996 (compensação de créditos).
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import Reg1100, Reg1500

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


def parsear_1100(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg1100:
    """
    Layout 1100 (Controle de Créditos PIS/Pasep, 18 campos):
    [1]=REG [2]=PER_APU_CRED [3]=ORIG_CRED [4]=CNPJ_SUC [5]=COD_CRED
    [6]=VL_CRED_APU [7]=VL_CRED_EXT_APU [8]=VL_TOT_CRED_APU
    [9]=VL_CRED_DESC_PA_ANT [10]=VL_CRED_PER_PA_ANT [11]=VL_CRED_DCOMP_PA_ANT
    [12]=SD_CRED_DISP_EFD [13]=VL_CRED_DESC_EFD [14]=VL_CRED_PER_EFD
    [15]=VL_CRED_DCOMP_EFD [16]=VL_CRED_TRANS [17]=VL_CRED_OUT [18]=SLD_CRED_FIM

    SLD_CRED_FIM > 0 → crédito disponível para compensação → CR-25.
    """
    return Reg1100(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        per_apu_cred=_g(campos, 2),
        orig_cred=_g(campos, 3),
        cnpj_suc=_g(campos, 4),
        cod_cred=_g(campos, 5),
        vl_cred_apu=_dec(_g(campos, 6)),
        vl_cred_ext_apu=_dec(_g(campos, 7)),
        vl_tot_cred_apu=_dec(_g(campos, 8)),
        vl_cred_desc_pa_ant=_dec(_g(campos, 9)),
        vl_cred_per_pa_ant=_dec(_g(campos, 10)),
        vl_cred_dcomp_pa_ant=_dec(_g(campos, 11)),
        sd_cred_disp_efd=_dec(_g(campos, 12)),
        vl_cred_desc_efd=_dec(_g(campos, 13)),
        vl_cred_per_efd=_dec(_g(campos, 14)),
        vl_cred_dcomp_efd=_dec(_g(campos, 15)),
        vl_cred_trans=_dec(_g(campos, 16)),
        vl_cred_out=_dec(_g(campos, 17)),
        sld_cred_fim=_dec(_g(campos, 18)),
    )


def parsear_1500(campos: list[str], linha_arquivo: int, arquivo_origem: str) -> Reg1500:
    """
    Layout 1500 (Controle de Créditos COFINS): estrutura idêntica ao 1100.
    SLD_CRED_FIM > 0 → crédito COFINS disponível para compensação → CR-25.
    """
    return Reg1500(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        per_apu_cred=_g(campos, 2),
        orig_cred=_g(campos, 3),
        cnpj_suc=_g(campos, 4),
        cod_cred=_g(campos, 5),
        vl_cred_apu=_dec(_g(campos, 6)),
        vl_cred_ext_apu=_dec(_g(campos, 7)),
        vl_tot_cred_apu=_dec(_g(campos, 8)),
        vl_cred_desc_pa_ant=_dec(_g(campos, 9)),
        vl_cred_per_pa_ant=_dec(_g(campos, 10)),
        vl_cred_dcomp_pa_ant=_dec(_g(campos, 11)),
        sd_cred_disp_efd=_dec(_g(campos, 12)),
        vl_cred_desc_efd=_dec(_g(campos, 13)),
        vl_cred_per_efd=_dec(_g(campos, 14)),
        vl_cred_dcomp_efd=_dec(_g(campos, 15)),
        vl_cred_trans=_dec(_g(campos, 16)),
        vl_cred_out=_dec(_g(campos, 17)),
        sld_cred_fim=_dec(_g(campos, 18)),
    )
