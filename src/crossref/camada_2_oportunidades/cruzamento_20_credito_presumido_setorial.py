"""CR-20 — Créditos presumidos setoriais não aproveitados (CST 60-67).

Base legal:
  CST 60-66: aquisição de insumos com tributação monofásica — crédito presumido admitido
  por legislação setorial específica:
    - Café torrado/solúvel: Lei 12.599/2012, art. 5º (alíquota 3,0% PIS / 13,8% COFINS).
    - Soja e biodiesel: Lei 12.865/2013 (alíquotas específicas).
    - Bebidas frias (cervejas, refrigerantes): Lei 13.097/2015, art. 14-26
      (suspensão / alíquota zero para revendedores, crédito para industriais).
  Art. 3º das Leis 10.637/2002 e 10.833/2003: base legal geral do creditamento.

Lógica do cruzamento:
  C170 com CST_PIS entre 60 e 67 (monofásico) + VL_BC_PIS > 0 + ALIQ_PIS > 0
  mas VL_PIS = 0 → crédito presumido setorial não aproveitado.
  O valor estimado usa a alíquota declarada (que deve ser a alíquota setorial correta).
"""

from decimal import Decimal

CODIGO_REGRA = "CR-20"

_CST_MONOFASICO = {str(i).zfill(2) for i in range(60, 68)}  # 60-67
_ZERO = Decimal("0.01")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    registros = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        if cst_pis not in _CST_MONOFASICO:
            continue

        vl_bc = Decimal(str(r.get("vl_bc_pis") or 0))
        aliq = Decimal(str(r.get("aliq_pis") or 0))
        vl_pis = Decimal(str(r.get("vl_pis") or 0))

        if vl_bc <= _ZERO or aliq <= _ZERO or vl_pis > _ZERO:
            continue

        impacto_pis = (vl_bc * aliq / Decimal("100")).quantize(Decimal("0.01"))
        if impacto_pis <= _ZERO:
            continue

        vl_bc_cofins = Decimal(str(r.get("vl_bc_cofins") or 0))
        aliq_cofins = Decimal(str(r.get("aliq_cofins") or 0))
        vl_cofins = Decimal(str(r.get("vl_cofins") or 0))
        impacto_cofins = Decimal("0")
        if vl_bc_cofins > _ZERO and aliq_cofins > _ZERO and vl_cofins <= _ZERO:
            impacto_cofins = (vl_bc_cofins * aliq_cofins / Decimal("100")).quantize(Decimal("0.01"))

        descricao = (
            f"C170 linha {r['linha_arquivo']}: CST_PIS {cst_pis} (monofásico)"
            f" com VL_BC_PIS={float(vl_bc):.2f} e ALIQ_PIS={float(aliq):.4f}%"
            f" mas VL_PIS=0 — crédito presumido setorial de R$ {float(impacto_pis):.2f}"
            f" não aproveitado. Verificar legislação setorial aplicável."
        )
        oportunidades.append(Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="alto",
            valor_impacto_conservador=impacto_pis,
            valor_impacto_maximo=impacto_pis + impacto_cofins,
            evidencia=[{
                "registro": "C170",
                "arquivo": r["arquivo_origem"],
                "linha": r["linha_arquivo"],
                "campos_chave": {
                    "cst_pis": cst_pis,
                    "vl_bc_pis": float(vl_bc),
                    "aliq_pis": float(aliq),
                    "vl_pis_declarado": float(vl_pis),
                    "impacto_pis": float(impacto_pis),
                },
            }],
        ))

    return oportunidades, []
