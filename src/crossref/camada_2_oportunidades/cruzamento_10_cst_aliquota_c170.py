"""CR-10 — Coerência CST × alíquota × base no C170.

Base legal:
  Art. 3º da Lei 10.637/2002 e art. 3º da Lei 10.833/2003: direito ao crédito
  exige CST de crédito (50-66) com base de cálculo positiva e alíquota declarada.
  IN RFB 1.009/2010: tabela de CST-PIS e CST-COFINS.

Lógica do cruzamento:
  Oportunidade: CST 50-66 (crédito permitido) + VL_BC_PIS > 0 + ALIQ_PIS > 0
                mas VL_PIS = 0 → crédito calculável não foi aproveitado.
  Divergência:  CST 01-05 (débito) + VL_BC_PIS > 0 + ALIQ_PIS > 0
                mas VL_PIS = 0 → tributo deveria ter sido apurado.
  Ambas: impacto = VL_BC_PIS × ALIQ_PIS (recalculado).
"""

from decimal import Decimal

CODIGO_REGRA = "CR-10"

_CST_CREDITO = {str(i) for i in range(50, 67)}   # 50 a 66
_CST_DEBITO  = {"01", "02", "03", "04", "05"}
_ZERO = Decimal("0.01")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Divergencia, Oportunidade

    registros = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    divergencias = []

    for r in registros:
        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        vl_bc = Decimal(str(r.get("vl_bc_pis") or 0))
        aliq = Decimal(str(r.get("aliq_pis") or 0))
        vl_pis = Decimal(str(r.get("vl_pis") or 0))

        if vl_bc <= _ZERO or aliq <= _ZERO or vl_pis > _ZERO:
            continue

        credito_esperado = (vl_bc * aliq / Decimal("100")).quantize(Decimal("0.01"))
        if credito_esperado <= _ZERO:
            continue

        evidencia = [{
            "registro": "C170",
            "arquivo": r["arquivo_origem"],
            "linha": r["linha_arquivo"],
            "campos_chave": {
                "cst_pis": cst_pis,
                "vl_bc_pis": float(vl_bc),
                "aliq_pis": float(aliq),
                "vl_pis_declarado": float(vl_pis),
                "vl_pis_esperado": float(credito_esperado),
            },
        }]

        if cst_pis in _CST_CREDITO:
            descricao = (
                f"C170 linha {r['linha_arquivo']}: CST {cst_pis} (crédito) com"
                f" VL_BC_PIS={float(vl_bc):.2f} e ALIQ_PIS={float(aliq):.4f}%"
                f" mas VL_PIS=0 — crédito de R$ {float(credito_esperado):.2f} não aproveitado."
            )
            vl_bc_cofins = Decimal(str(r.get("vl_bc_cofins") or 0))
            aliq_cofins = Decimal(str(r.get("aliq_cofins") or 0))
            vl_cofins = Decimal(str(r.get("vl_cofins") or 0))
            impacto_cofins = Decimal("0")
            if vl_bc_cofins > _ZERO and aliq_cofins > _ZERO and vl_cofins <= _ZERO:
                impacto_cofins = (vl_bc_cofins * aliq_cofins / Decimal("100")).quantize(Decimal("0.01"))

            oportunidades.append(Oportunidade(
                codigo_regra=CODIGO_REGRA,
                descricao=descricao,
                severidade="alto",
                valor_impacto_conservador=credito_esperado,
                valor_impacto_maximo=credito_esperado + impacto_cofins,
                evidencia=evidencia,
            ))

        elif cst_pis in _CST_DEBITO:
            descricao = (
                f"C170 linha {r['linha_arquivo']}: CST {cst_pis} (débito) com"
                f" VL_BC_PIS={float(vl_bc):.2f} e ALIQ_PIS={float(aliq):.4f}%"
                f" mas VL_PIS=0 — PIS de R$ {float(credito_esperado):.2f} não apurado."
            )
            divergencias.append(Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=descricao,
                severidade="alto",
                evidencia=evidencia,
            ))

    return oportunidades, divergencias
