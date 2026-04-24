"""CR-14 — Crédito de PIS/COFINS sobre Encargos de Depreciação não aproveitado (F120).

Base legal:
  Art. 3º, VI da Lei 10.637/2002 (PIS) e Lei 10.833/2003 (COFINS): bens do ativo
  imobilizado adquiridos para uso na produção de bens ou prestação de serviços geram
  crédito calculado sobre os encargos de depreciação e amortização.
  Lei 10.865/2004, art. 31: vedação para imobilizado adquirido antes de 01/05/2004.
  Vigência: 01/2003 (PIS) e 02/2004 (COFINS) para o regime não-cumulativo.

Lógica do cruzamento:
  Para cada F120 com IND_UTIL_BEM_IMOB ∈ {1, 2, 3} (produção, serviços, locação):
    Se VL_BC_PIS > 0 E VL_PIS = 0 → crédito não foi aproveitado → Oportunidade.
  Valor do impacto: VL_BC_PIS × ALIQ_PIS / 100 (cálculo esperado).

  Nota: IND_UTIL_BEM_IMOB = 9 (uso vedado com crédito indevido) é tratado pelo CR-27.
"""

from decimal import Decimal


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    registros = repo.consultar_f120_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        ind_util = str(r["ind_util_bem_imob"] or "").strip()
        if ind_util not in {"1", "2", "3"}:
            continue

        vl_bc_pis = Decimal(str(r["vl_bc_pis"] or 0))
        vl_pis = Decimal(str(r["vl_pis"] or 0))
        aliq_pis = Decimal(str(r["aliq_pis"] or 0))

        if vl_bc_pis <= 0:
            continue
        if vl_pis > Decimal("0.01"):
            continue

        credito_esperado = (vl_bc_pis * aliq_pis / Decimal("100")).quantize(Decimal("0.01"))
        if credito_esperado <= 0:
            continue

        vl_cofins = Decimal(str(r["vl_cofins"] or 0))
        vl_bc_cofins = Decimal(str(r["vl_bc_cofins"] or 0))
        aliq_cofins = Decimal(str(r["aliq_cofins"] or 0))
        cofins_esperado = (vl_bc_cofins * aliq_cofins / Decimal("100")).quantize(Decimal("0.01"))
        impacto_cofins = cofins_esperado if vl_cofins <= Decimal("0.01") else Decimal("0")

        descricao = (
            f"F120 — bem '{r.get('desc_bem_imob') or r.get('ident_bem_imob')}' com encargo"
            f" de depreciação R$ {float(r['vl_oper_dep']):.2f}: crédito PIS de"
            f" R$ {float(credito_esperado):.2f} não aproveitado (VL_PIS=0)."
            f" IND_UTIL={ind_util}."
        )
        oportunidades.append(
            Oportunidade(
                codigo_regra="CR-14",
                descricao=descricao,
                severidade="medio",
                valor_impacto_conservador=credito_esperado,
                valor_impacto_maximo=credito_esperado + impacto_cofins,
                evidencia=[{
                    "registro": "F120",
                    "arquivo": r["arquivo_origem"],
                    "linha": r["linha_arquivo"],
                    "campos_chave": {
                        "desc_bem_imob": r.get("desc_bem_imob") or "",
                        "ident_bem_imob": r.get("ident_bem_imob") or "",
                        "ind_util_bem_imob": ind_util,
                        "vl_oper_dep": float(r["vl_oper_dep"] or 0),
                        "vl_bc_pis": float(vl_bc_pis),
                        "aliq_pis": float(aliq_pis),
                        "credito_pis_esperado": float(credito_esperado),
                        "vl_pis_declarado": float(vl_pis),
                    },
                }],
            )
        )

    return oportunidades, []
