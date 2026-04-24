"""
Regra: Tese 69 (RE 574.706/PR) em registros consolidados NFC-e (C181) e
serviços de transporte (D201).

Base legal:
    RE 574.706/PR (Tema 69 STF) — exclusão do ICMS da base de PIS/COFINS.
    Lei 10.637/2002, art. 1º (PIS não-cumulativo — base de cálculo).
    Lei 10.833/2003, art. 1º (COFINS não-cumulativa — base de cálculo).
    Seção 12 do Manual EFD-Contribuições: nos registros C181/C185 (NFC-e
    consolidada), a exclusão do ICMS deve ser feita via VL_DESC. Nos
    registros D201/D205 (transporte), via redução direta de VL_BC_PIS/
    VL_BC_COFINS (não há campo VL_ICMS explícito).
    Vigência da tese: a partir de 15/03/2017 (modulação do RE 574.706).

Limites desta implementação (Sprint 2):
    Impacto monetário = 0 (qualitativo). C181/D201 não têm campo VL_ICMS,
    impossibilitando cálculo sem cruzamento com EFD ICMS/IPI (Sprint 6+).
    CR-07 (C170) deve ser executado em conjunto para estimativa monetária.
"""

from decimal import Decimal

from src.tables.cst_pis import CST_TESE_69

# CSTs de COFINS equivalentes aos de PIS para a Tese 69
CST_COFINS_TESE_69 = {"01", "02", "03", "05"}


def check_c181_tese69(item: dict) -> dict | None:
    """
    Verifica se um C181 indica ICMS incluído na base do PIS (Tese 69).

    Sinal: CST_PIS ∈ {01,02,03,05} AND ind_oper == "1" (saída) AND vl_desc == 0.
    Quando VL_DESC == 0, a empresa não aplicou qualquer desconto/exclusão na
    base, sugerindo que o ICMS está embutido em VL_BC_PIS.

    Retorna dict com campos de evidência, ou None se não há sinal.
    """
    cst = item.get("cst_pis", "").strip()
    ind_oper = item.get("ind_oper", "").strip()
    vl_item = float(item.get("vl_item", 0) or 0)
    vl_desc = float(item.get("vl_desc", 0) or 0)
    vl_bc_pis = float(item.get("vl_bc_pis", 0) or 0)
    aliq_pis = float(item.get("aliq_pis", 0) or 0)

    if cst not in CST_TESE_69:
        return None
    if ind_oper != "1":
        return None
    if vl_item <= 0:
        return None
    # Sinal: VL_DESC == 0 com VL_ITEM > 0 → não houve exclusão de ICMS via VL_DESC
    if vl_desc != 0:
        return None

    return {
        "registro": "C181",
        "bloco": "C",
        "cst_pis": cst,
        "vl_item": vl_item,
        "vl_desc_declarado": vl_desc,
        "vl_bc_pis_declarado": vl_bc_pis,
        "aliq_pis": aliq_pis,
        "arquivo_origem": item.get("arquivo_origem", ""),
        "linha_arquivo": item.get("linha_arquivo", 0),
        "cnpj_declarante": item.get("cnpj_declarante", ""),
        "ano_mes": item.get("ano_mes", 0),
        "c180_linha_arquivo": item.get("c180_linha_arquivo", 0),
        "sinal": "vl_desc_zero_com_cst_tese69",
    }


def check_d201_tese69(item: dict) -> dict | None:
    """
    Verifica se um D201 indica ICMS incluído na base do PIS em serviço de transporte.

    Sinal: CST_PIS ∈ {01,02,03,05} AND ind_oper == "1" (saída) AND
           vl_bc_pis == vl_item (base de cálculo igual ao valor total).
    Nos documentos de transporte, o ICMS incidente deveria reduzir VL_BC_PIS.
    Quando VL_BC_PIS == VL_ITEM, a empresa não fez essa dedução.

    Retorna dict com campos de evidência, ou None se não há sinal.
    """
    cst = item.get("cst_pis", "").strip()
    ind_oper = item.get("ind_oper", "").strip()
    vl_item = float(item.get("vl_item", 0) or 0)
    vl_bc_pis = float(item.get("vl_bc_pis", 0) or 0)
    aliq_pis = float(item.get("aliq_pis", 0) or 0)

    if cst not in CST_TESE_69:
        return None
    if ind_oper != "1":
        return None
    if vl_item <= 0:
        return None
    # Sinal: VL_BC_PIS == VL_ITEM → ICMS não foi deduzido da base
    # Tolerância de R$ 0,01 para arredondamentos
    if abs(vl_bc_pis - vl_item) > 0.01:
        return None

    return {
        "registro": "D201",
        "bloco": "D",
        "cst_pis": cst,
        "vl_item": vl_item,
        "vl_bc_pis_declarado": vl_bc_pis,
        "aliq_pis": aliq_pis,
        "arquivo_origem": item.get("arquivo_origem", ""),
        "linha_arquivo": item.get("linha_arquivo", 0),
        "cnpj_declarante": item.get("cnpj_declarante", ""),
        "ano_mes": item.get("ano_mes", 0),
        "d200_linha_arquivo": item.get("d200_linha_arquivo", 0),
        "sinal": "vl_bc_pis_igual_vl_item",
    }
