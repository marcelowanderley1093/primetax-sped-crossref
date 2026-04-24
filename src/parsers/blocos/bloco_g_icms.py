"""Parser do Bloco G da EFD ICMS/IPI: CIAP (Controle do ICMS sobre Ativo Imobilizado).

Registros G110 (apuração por período) e G125 (movimentação bem a bem).
VL_PARC_PASS (G125) > 0 → ICMS sendo recuperado via CIAP → CR-35.

Base legal:
  Ajuste SINIEF 8/1997 — obrigatoriedade do CIAP.
  Art. 20 §§5º-7º ADCT (CF/88) — direito ao crédito de ICMS sobre imobilizado.
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegIcmsG110, RegIcmsG125

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


def parsear_g110(
    campos: list[str], linha_arquivo: int, arquivo_origem: str
) -> RegIcmsG110:
    """
    G110 — Apuração do ICMS a Recuperar por Período:
    [1]=REG [2]=DT_INI [3]=DT_FIN [4]=SALDO_IN_ICMS [5]=SOM_PARC [6]=VL_TRIB_EXP
    [7]=VL_TOTAL [8]=IND_PER_SAI [9]=ICMS_APROP [10]=SOM_ICMS_OC
    """
    return RegIcmsG110(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        dt_ini=_data(_g(campos, 2)),
        dt_fin=_data(_g(campos, 3)),
        saldo_in_icms=_dec(_g(campos, 4)),
        som_parc=_dec(_g(campos, 5)),
        vl_trib_exp=_dec(_g(campos, 6)),
        vl_total=_dec(_g(campos, 7)),
        ind_per_sai=_dec(_g(campos, 8)),
        icms_aprop=_dec(_g(campos, 9)),
        som_icms_oc=_dec(_g(campos, 10)),
    )


def parsear_g125(
    campos: list[str], linha_arquivo: int, arquivo_origem: str
) -> RegIcmsG125:
    """
    G125 — Movimentação de Bem do Imobilizado (CIAP):
    [1]=REG [2]=COD_IND_BEM [3]=IDENT_BEM [4]=DT_MOV [5]=TIPO_MOV
    [6]=VL_IMOB_ICMS_OP [7]=VL_IMOB_ICMS_ST [8]=VL_IMOB_ICMS_FRT
    [9]=VL_IMOB_ICMS_DIF [10]=NUM_PARC [11]=VL_PARC_PASS
    """
    return RegIcmsG125(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        cod_ind_bem=_g(campos, 2),
        ident_bem=_g(campos, 3),
        dt_mov=_data(_g(campos, 4)),
        tipo_mov=_g(campos, 5),
        vl_imob_icms_op=_dec(_g(campos, 6)),
        vl_imob_icms_st=_dec(_g(campos, 7)),
        vl_imob_icms_frt=_dec(_g(campos, 8)),
        vl_imob_icms_dif=_dec(_g(campos, 9)),
        num_parc=_g(campos, 10),
        vl_parc_pass=_dec(_g(campos, 11)),
    )
