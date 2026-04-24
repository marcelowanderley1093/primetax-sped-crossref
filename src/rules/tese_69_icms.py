"""
Tese 69 — Exclusão do ICMS da base de cálculo do PIS/COFINS.

Base legal:
  RE 574.706/PR (Tema 69 STF) — Plenário 15/03/2017: ICMS não integra
    a base de cálculo das contribuições PIS/COFINS. Marco temporal fixado
    em modulação pelo STF: fatos geradores a partir de 15/03/2017.
  Parecer SEI 7698/2021/ME (PGFN) — operacionalização administrativa;
    limita a recuperação a 01/2018 para créditos ainda não litigados.
  IN RFB 1.252/2012 — leiaute EFD-Contribuições; campos C170.

Código da regra: CR-07
Camada: 2 — Oportunidade
Severidade: alto
CSTs ativadoras: {01, 02, 03, 05} — saídas ad valorem (CST_TESE_69)
Escopo: C100.IND_OPER = "1" (saídas) com CST_PIS ∈ CST_TESE_69

Opção (b) — dois resultados paralelos por item C170 (decisão do operador, 2026):
  base_exclusao_conservadora = VL_ITEM - VL_DESC - VL_ICMS
    Exclui somente VL_ICMS (campo 15, ICMS próprio). Lastro: Parecer SEI 7698/2021/ME.
  base_exclusao_maxima = VL_ITEM - VL_DESC - VL_ICMS - VL_ICMS_ST
    Exclui também VL_ICMS_ST (campo 18). Tese pendente no STJ; não tem Parecer PGFN.
"""

from decimal import Decimal

from src.tables.cst_pis import CST_TESE_69

CODIGO_REGRA = "CR-07"
DESCRICAO = "Tese 69 — ICMS indevidamente incluído na base de PIS/COFINS (C170)"
SEVERIDADE = "alto"

_ZERO = Decimal("0")
_CEM = Decimal("100")


def calcular_oportunidade_item(item: dict) -> dict | None:
    """
    Calcula a oportunidade Tese 69 para um único item C170.

    Args:
        item: dict com campos da tabela efd_contrib_c170 (valores como float do SQLite).

    Returns:
        dict com os campos da oportunidade, ou None se não há diferença.
    """
    cst_pis: str = item.get("cst_pis", "")
    if cst_pis not in CST_TESE_69:
        return None

    vl_item = Decimal(str(item.get("vl_item", 0)))
    vl_desc = Decimal(str(item.get("vl_desc", 0)))
    vl_icms = Decimal(str(item.get("vl_icms", 0)))
    vl_icms_st = Decimal(str(item.get("vl_icms_st", 0)))
    vl_bc_pis = Decimal(str(item.get("vl_bc_pis", 0)))
    vl_bc_cofins = Decimal(str(item.get("vl_bc_cofins", 0)))
    aliq_pis = Decimal(str(item.get("aliq_pis", 0)))
    aliq_cofins = Decimal(str(item.get("aliq_cofins", 0)))
    cst_cofins: str = item.get("cst_cofins", "")

    base_sem_icms_proprio = vl_item - vl_desc - vl_icms
    base_sem_icms_total = vl_item - vl_desc - vl_icms - vl_icms_st

    # PIS
    delta_pis_cons = max(_ZERO, vl_bc_pis - base_sem_icms_proprio)
    delta_pis_max = max(_ZERO, vl_bc_pis - base_sem_icms_total)

    # COFINS (base pode diferir em casos raros de CSTs distintas)
    delta_cofins_cons = max(_ZERO, vl_bc_cofins - base_sem_icms_proprio)
    delta_cofins_max = max(_ZERO, vl_bc_cofins - base_sem_icms_total)

    if delta_pis_cons == _ZERO and delta_cofins_cons == _ZERO:
        return None  # ICMS já está fora da base — sem oportunidade

    aliq_pis_frac = aliq_pis / _CEM
    aliq_cofins_frac = aliq_cofins / _CEM

    imp_conservador = (delta_pis_cons * aliq_pis_frac + delta_cofins_cons * aliq_cofins_frac)
    imp_maximo = (delta_pis_max * aliq_pis_frac + delta_cofins_max * aliq_cofins_frac)

    return {
        "codigo_regra": CODIGO_REGRA,
        "descricao": DESCRICAO,
        "severidade": SEVERIDADE,
        "valor_impacto_conservador": imp_conservador.quantize(Decimal("0.01")),
        "valor_impacto_maximo": imp_maximo.quantize(Decimal("0.01")),
        "evidencia": {
            "arquivo_origem": item.get("arquivo_origem", ""),
            "linha_arquivo": item.get("linha_arquivo", 0),
            "bloco": "C",
            "registro": "C170",
            "cnpj_declarante": item.get("cnpj_declarante", ""),
            "ano_mes": item.get("ano_mes", 0),
            "campos_chave": {
                "num_item": item.get("num_item", ""),
                "cod_item": item.get("cod_item", ""),
                "cst_pis": cst_pis,
                "cst_cofins": cst_cofins,
                "vl_item": str(vl_item),
                "vl_desc": str(vl_desc),
                "vl_icms": str(vl_icms),
                "vl_icms_st": str(vl_icms_st),
                "vl_bc_pis_declarado": str(vl_bc_pis),
                "vl_bc_cofins_declarado": str(vl_bc_cofins),
                "base_sem_icms_proprio": str(base_sem_icms_proprio),
                "base_sem_icms_total": str(base_sem_icms_total),
                "delta_pis_conservador": str(delta_pis_cons),
                "delta_pis_maximo": str(delta_pis_max),
                "delta_cofins_conservador": str(delta_cofins_cons),
                "delta_cofins_maximo": str(delta_cofins_max),
                "aliq_pis": str(aliq_pis),
                "aliq_cofins": str(aliq_cofins),
                "c100_linha_arquivo": item.get("c100_linha_arquivo", 0),
            },
        },
    }
