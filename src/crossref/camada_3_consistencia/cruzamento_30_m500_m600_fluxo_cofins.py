"""CR-30 — Consistência vertical: Σ M500.VL_CRED_DESC = M600.VL_TOT_CRED_DESC (COFINS).

Base legal:
  IN RFB 1.252/2012 — leiaute EFD-Contribuições: o campo VL_TOT_CRED_DESC do registro M600
  deve ser exatamente igual à soma dos campos VL_CRED_DESC de todos os registros M500 do
  mesmo período (espelho da relação M100↔M200 para o PIS — CR-29).

Lógica do cruzamento:
  Se M600.VL_TOT_CRED_DESC ≠ Σ M500.VL_CRED_DESC (diferença > R$ 1,00):
    → Divergencia severidade "medio".
  Se não há M600 no período → retorna vazio.

Tolerância: R$ 1,00.
"""

from decimal import Decimal

_TOLERANCIA = Decimal("1.00")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    m600 = repo.consultar_m600_por_periodo(conn, cnpj, ano_mes)
    if m600 is None:
        return [], []

    m500s = repo.consultar_m500_por_periodo(conn, cnpj, ano_mes)

    soma_m500 = sum(Decimal(str(r["vl_cred_desc"] or 0)) for r in m500s)
    tot_m600 = Decimal(str(m600["vl_tot_cred_desc"] or 0))

    diff = abs(tot_m600 - soma_m500)
    if diff <= _TOLERANCIA:
        return [], []

    sentido = "M600 > Σ M500" if tot_m600 > soma_m500 else "Σ M500 > M600"
    descricao = (
        f"M600.VL_TOT_CRED_DESC={float(tot_m600):.2f} ≠ Σ M500.VL_CRED_DESC={float(soma_m500):.2f}"
        f" (diferença={float(diff):.2f}, {sentido})."
        f" Inconsistência vertical na escrituração de créditos COFINS do período."
    )

    return [], [
        Divergencia(
            codigo_regra="CR-30",
            descricao=descricao,
            severidade="medio",
            evidencia=[{
                "registro": "M600/M500",
                "arquivo": m600["arquivo_origem"],
                "linha": m600["linha_arquivo"],
                "campos_chave": {
                    "soma_vl_cred_desc_m500": float(soma_m500),
                    "vl_tot_cred_desc_m600": float(tot_m600),
                    "divergencia_absoluta": float(diff),
                    "sentido": sentido,
                    "qtd_m500": len(m500s),
                },
            }],
        )
    ]
