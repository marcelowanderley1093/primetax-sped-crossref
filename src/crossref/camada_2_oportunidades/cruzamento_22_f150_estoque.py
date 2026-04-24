"""CR-22 — Crédito Presumido sobre Estoque de Abertura não aproveitado (F150).

Base legal:
  Art. 11 da Lei 10.637/2002 e art. 12 da Lei 10.833/2003: PJ que passou a se sujeitar
  ao regime não-cumulativo do PIS/COFINS tem direito a crédito presumido de 0,65% (PIS)
  e 3,0% (COFINS) sobre o estoque de abertura de bens adquiridos de PJ domiciliada no país,
  descontado em 12 parcelas mensais iguais e sucessivas a partir do ingresso no regime.
  IN RFB 1.252/2012: obrigatoriedade de escrituração no registro F150.

Lógica do cruzamento:
  Para cada F150 onde VL_CRED_PIS = 0 E VL_BC_MEN_EST > 0:
    O contribuinte tem base de estoque mas não aproveitou o crédito → Oportunidade.
  Valor conservador: VL_BC_MEN_EST × 0,0065 (PIS, alíquota fixa Art. 11 Lei 10.637/2002).
  Valor máximo: inclui COFINS = VL_BC_MEN_EST × 0,03.

  Note: se VL_CRED_PIS > 0, o crédito foi aproveitado — sem oportunidade.
"""

from decimal import Decimal

_ALIQ_PIS_FIXA = Decimal("0.0065")
_ALIQ_COFINS_FIXA = Decimal("0.03")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    registros = repo.consultar_f150_por_periodo(conn, cnpj, ano_mes)
    if not registros:
        return [], []

    oportunidades = []
    for r in registros:
        vl_bc_men = Decimal(str(r["vl_bc_men_est"] or 0))
        vl_cred_pis = Decimal(str(r["vl_cred_pis"] or 0))
        vl_cred_cofins = Decimal(str(r["vl_cred_cofins"] or 0))

        if vl_bc_men <= 0:
            continue
        if vl_cred_pis > Decimal("0.01"):
            continue

        credito_pis = (vl_bc_men * _ALIQ_PIS_FIXA).quantize(Decimal("0.01"))
        credito_cofins = (vl_bc_men * _ALIQ_COFINS_FIXA).quantize(Decimal("0.01"))
        impacto_conservador = credito_pis
        impacto_maximo = credito_pis + (credito_cofins if vl_cred_cofins <= Decimal("0.01") else Decimal("0"))

        descricao = (
            f"F150 — estoque de abertura '{r.get('desc_est') or 'sem descrição'}':"
            f" base mensal R$ {float(vl_bc_men):.2f}; crédito PIS"
            f" de R$ {float(credito_pis):.2f} (0,65%) não aproveitado (VL_CRED_PIS=0)."
        )
        oportunidades.append(
            Oportunidade(
                codigo_regra="CR-22",
                descricao=descricao,
                severidade="medio",
                valor_impacto_conservador=impacto_conservador,
                valor_impacto_maximo=impacto_maximo,
                evidencia=[{
                    "registro": "F150",
                    "arquivo": r["arquivo_origem"],
                    "linha": r["linha_arquivo"],
                    "campos_chave": {
                        "desc_est": r.get("desc_est") or "",
                        "vl_bc_men_est": float(vl_bc_men),
                        "credito_pis_esperado": float(credito_pis),
                        "credito_cofins_esperado": float(credito_cofins),
                        "vl_cred_pis_declarado": float(vl_cred_pis),
                        "vl_cred_cofins_declarado": float(vl_cred_cofins),
                    },
                }],
            )
        )

    return oportunidades, []
