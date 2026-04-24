"""CR-12 — CST 70-75 (aquisição sem crédito) com base de cálculo positiva — auditoria individual.

Base legal:
  Art. 3º, II da Lei 10.637/2002 e art. 3º, II da Lei 10.833/2003 (insumos).
  Art. 3º, VII da Lei 10.637/2002 e art. 3º, VII da Lei 10.833/2003 (bens/serviços recebidos
  em devolução). REsp 1.221.170/PR (Tema 779 STJ): conceito ampliado de insumo.
  IN RFB 1.009/2010: CST 70-75 indicam aquisição de bens/serviços sem direito a crédito.

Lógica do cruzamento:
  CST 70-75 significa que o contribuinte declarou que não há crédito na operação.
  Porém, quando VL_BC_PIS > 0 está preenchido (base declarada), o próprio contribuinte
  reconheceu uma base tributável — o que pode indicar reclassificação possível sob
  REsp 1.221.170/PR ou eventual equívoco na classificação do CST.
  Oportunidade qualitativa (sem impacto calculável automático) — cada item deve ser
  revisado individualmente pelo auditor.
"""

from decimal import Decimal

CODIGO_REGRA = "CR-12"

_CST_SEM_CREDITO = {"70", "71", "72", "73", "74", "75"}
_ZERO = Decimal("0.01")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    from src.models.registros import Oportunidade

    registros = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        cst_pis = str(r.get("cst_pis") or "").strip().zfill(2)
        if cst_pis not in _CST_SEM_CREDITO:
            continue

        vl_bc = Decimal(str(r.get("vl_bc_pis") or 0))
        if vl_bc <= _ZERO:
            continue

        aliq = Decimal(str(r.get("aliq_pis") or 0))
        impacto_pis = Decimal("0")
        impacto_cofins = Decimal("0")

        if aliq > _ZERO:
            impacto_pis = (vl_bc * aliq / Decimal("100")).quantize(Decimal("0.01"))
            vl_bc_cofins = Decimal(str(r.get("vl_bc_cofins") or 0))
            aliq_cofins = Decimal(str(r.get("aliq_cofins") or 0))
            if vl_bc_cofins > _ZERO and aliq_cofins > _ZERO:
                impacto_cofins = (vl_bc_cofins * aliq_cofins / Decimal("100")).quantize(Decimal("0.01"))

        descricao = (
            f"C170 linha {r['linha_arquivo']}: CST_PIS {cst_pis}"
            f" (aquisição sem crédito) com VL_BC_PIS={float(vl_bc):.2f}."
            f" Revisar se item qualifica como insumo sob REsp 1.221.170/PR."
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
                    "cst_pis": cst_pis,
                    "vl_bc_pis": float(vl_bc),
                    "aliq_pis": float(aliq),
                    "cfop": r.get("cfop") or "",
                },
            }],
        ))

    return oportunidades, []
