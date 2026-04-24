"""Parser do Bloco H da EFD ICMS/IPI: inventário (H005 e H010).

H010.VL_ITEM_IR > 0 → valor do item para IR com ICMS excluído → CR-36.

Base legal:
  Convênio ICMS 143/2006; Ajuste SINIEF 02/2009.
  Art. 3º §1º Lei 10.637/2002 e Lei 10.833/2003 — crédito sobre estoque de abertura.
  Manual EFD ICMS/IPI v3.2.2: 'O montante desse imposto [ICMS recuperável],
  destacado em nota fiscal, deve ser excluído do valor dos estoques para
  efeito do imposto de renda.'
"""

import logging
from decimal import Decimal, InvalidOperation

from src.models.registros import RegIcmsH005, RegIcmsH010

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


def parsear_h005(
    campos: list[str], linha_arquivo: int, arquivo_origem: str
) -> RegIcmsH005:
    """
    H005 — Totais do Inventário:
    [1]=REG [2]=DT_INV [3]=VL_INV [4]=MOT_INV
    """
    return RegIcmsH005(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        dt_inv=_data(_g(campos, 2)),
        vl_inv=_dec(_g(campos, 3)),
        mot_inv=_g(campos, 4),
    )


def parsear_h010(
    campos: list[str],
    linha_arquivo: int,
    arquivo_origem: str,
    h005_linha_arquivo: int,
) -> RegIcmsH010:
    """
    H010 — Item do Inventário:
    [1]=REG [2]=COD_ITEM [3]=UNID [4]=QTD [5]=VL_UNIT [6]=VL_ITEM
    [7]=IND_PROP [8]=COD_PART [9]=TXT_COMPL [10]=COD_CTA [11]=VL_ITEM_IR
    """
    return RegIcmsH010(
        linha_arquivo=linha_arquivo,
        arquivo_origem=arquivo_origem,
        reg=_g(campos, 1),
        h005_linha_arquivo=h005_linha_arquivo,
        cod_item=_g(campos, 2),
        unid=_g(campos, 3),
        qtd=_dec(_g(campos, 4)),
        vl_unit=_dec(_g(campos, 5)),
        vl_item=_dec(_g(campos, 6)),
        ind_prop=_g(campos, 7),
        cod_part=_g(campos, 8),
        txt_compl=_g(campos, 9),
        cod_cta=_g(campos, 10),
        vl_item_ir=_dec(_g(campos, 11)),
    )
