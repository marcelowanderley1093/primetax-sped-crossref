"""CR-11 — TIPO_ITEM '07' (uso e consumo) com CFOP de insumo em C170.

Base legal:
  REsp 1.221.170/PR (Tema 779 STJ): conceito de insumo para fins de crédito PIS/COFINS
  não-cumulativo abrange todos os bens e serviços essenciais ou relevantes para a atividade
  da empresa, superando a restrição a MP/embalagem/PI do art. 3º, II das Leis 10.637/2002
  e 10.833/2003 interpretados restritivamente.
  Art. 3º, II da Lei 10.637/2002 e art. 3º, II da Lei 10.833/2003: crédito sobre insumos.

Lógica do cruzamento:
  Itens classificados como TIPO_ITEM='07' (Outros / uso e consumo) em 0200, mas que
  aparecem no C170 com CFOP de insumo (primeiro dígito 1/2/3 e sufixo típico de compra
  para uso/consumo produtivo) e CST 70-75 (aquisição sem crédito) →
  candidatos a reclassificação como insumo sob REsp 1.221.170/PR, gerando
  crédito de 1,65% (PIS) e 7,6% (COFINS).
"""

from decimal import Decimal

CODIGO_REGRA = "CR-11"

_ALIQ_PIS = Decimal("0.0165")
_ALIQ_COFINS = Decimal("0.076")
_CST_SEM_CREDITO = {"70", "71", "72", "73", "74", "75"}

_CFOP_INSUMO_PREFIXOS = {
    "1101", "1102", "1111", "1116", "1117", "1118", "1120", "1121", "1122",
    "1401", "1403",
    "2101", "2102", "2111", "2116", "2117", "2118", "2120", "2121", "2122",
    "2401", "2403",
    "3101", "3102",
}


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    registros = repo.consultar_c170_com_tipo_item(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []

    for r in registros:
        tipo_item = str(r.get("tipo_item") or "").strip()
        if tipo_item != "07":
            continue

        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        if cst_pis not in _CST_SEM_CREDITO:
            continue

        cfop = str(r.get("cfop") or "").strip()
        if cfop not in _CFOP_INSUMO_PREFIXOS:
            continue

        vl_item = Decimal(str(r.get("vl_item") or 0))
        vl_desc = Decimal(str(r.get("vl_desc") or 0))
        base_potencial = (vl_item - vl_desc).quantize(Decimal("0.01"))
        if base_potencial <= Decimal("0.01"):
            continue

        impacto_pis = (base_potencial * _ALIQ_PIS).quantize(Decimal("0.01"))
        impacto_cofins = (base_potencial * _ALIQ_COFINS).quantize(Decimal("0.01"))

        descricao = (
            f"C170 linha {r['linha_arquivo']}: item '{r.get('cod_item') or ''}'"
            f" classificado como TIPO_ITEM=07 (uso/consumo) com CFOP {cfop}"
            f" e CST_PIS {cst_pis} (sem crédito). Sob REsp 1.221.170/PR, pode ser"
            f" reclassificado como insumo — crédito PIS potencial R$ {float(impacto_pis):.2f}."
        )

        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="alto",
            valor_impacto_conservador=impacto_pis,
            valor_impacto_maximo=impacto_pis + impacto_cofins,
            evidencia=[{
                "registro": "C170 × 0200",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cod_item": r.get("cod_item") or "",
                    "tipo_item": tipo_item,
                    "cfop": cfop,
                    "cst_pis": cst_pis,
                    "vl_item": float(vl_item),
                    "base_potencial": float(base_potencial),
                    "impacto_pis": float(impacto_pis),
                    "impacto_cofins": float(impacto_cofins),
                },
            }],
        ))

    return oportunidades, []
