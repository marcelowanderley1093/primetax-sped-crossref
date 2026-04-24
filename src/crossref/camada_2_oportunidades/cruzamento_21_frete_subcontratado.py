"""CR-21 — Crédito presumido de transporte de carga subcontratado (CFOP 1352/2352).

Base legal:
  Art. 3º, §§ 19-20 da Lei 10.833/2003 (redação dada pela Lei 11.051/2004):
  transportadora optante pelo Simples Nacional ou pessoa física pode subcontratar
  transportadora não optante; a empresa embarcadora/tomadora do serviço tem direito
  a crédito presumido de PIS/COFINS sobre o valor do frete pago.
  CFOP 1352 (aquisição de serviço de transporte — dentro do estado) e
  2352 (aquisição de serviço de transporte — fora do estado):
  indicam subcontratação tributada sujeita ao crédito presumido.

Lógica do cruzamento:
  C170 com CFOP 1352 ou 2352 + CST_PIS 70-75 (sem crédito declarado) + VL_ITEM > 0 →
  possível crédito presumido de frete subcontratado não aproveitado.
  Alíquota presumida: 1,65% PIS (não-cumulativo padrão) × VL_ITEM.
"""

from decimal import Decimal

CODIGO_REGRA = "CR-21"

_CFOP_FRETE = {"1352", "2352"}
_CST_SEM_CREDITO = {"70", "71", "72", "73", "74", "75"}
_ALIQ_PIS = Decimal("0.0165")
_ALIQ_COFINS = Decimal("0.076")
_ZERO = Decimal("0.01")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    registros = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        cfop = str(r.get("cfop") or "").strip()
        if cfop not in _CFOP_FRETE:
            continue

        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        if cst_pis not in _CST_SEM_CREDITO:
            continue

        vl_item = Decimal(str(r.get("vl_item") or 0))
        vl_desc = Decimal(str(r.get("vl_desc") or 0))
        base = (vl_item - vl_desc).quantize(Decimal("0.01"))
        if base <= _ZERO:
            continue

        impacto_pis = (base * _ALIQ_PIS).quantize(Decimal("0.01"))
        impacto_cofins = (base * _ALIQ_COFINS).quantize(Decimal("0.01"))

        descricao = (
            f"C170 linha {r['linha_arquivo']}: CFOP {cfop} (transporte subcontratado)"
            f" com CST_PIS {cst_pis} (sem crédito declarado) e VL_ITEM=R$ {float(vl_item):.2f}."
            f" Crédito presumido PIS potencial: R$ {float(impacto_pis):.2f}"
            f" (art. 3º §19-20 Lei 10.833/2003)."
        )
        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            valor_impacto_conservador=impacto_pis,
            valor_impacto_maximo=impacto_pis + impacto_cofins,
            evidencia=[{
                "registro": "C170",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cfop": cfop,
                    "cst_pis": cst_pis,
                    "vl_item": float(vl_item),
                    "base_frete": float(base),
                    "impacto_pis": float(impacto_pis),
                    "impacto_cofins": float(impacto_cofins),
                },
            }],
        ))

    return oportunidades, []
