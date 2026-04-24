"""CR-29 — Consistência vertical: Σ M100.VL_CRED_DESC = M200.VL_TOT_CRED_DESC (PIS).

Base legal:
  IN RFB 1.252/2012 — leiaute EFD-Contribuições: o campo VL_TOT_CRED_DESC do registro M200
  deve ser exatamente igual à soma dos campos VL_CRED_DESC de todos os registros M100 do
  mesmo período. Divergência entre esses valores indica inconsistência interna no arquivo,
  configurando risco de autuação por erros de escrituração.

Lógica do cruzamento:
  Se M200.VL_TOT_CRED_DESC ≠ Σ M100.VL_CRED_DESC (diferença > R$ 1,00):
    → Divergencia severidade "medio".
  Se não há M200 no período → retorna vazio (nada a validar).
  Se não há M100 no período mas M200 declara créditos descontados > 0 → diferença = VL_TOT_CRED_DESC.

Tolerância: R$ 1,00 (mesmo critério de CR-31, para absorver arredondamentos).
"""

from decimal import Decimal

_TOLERANCIA = Decimal("1.00")


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    m200 = repo.consultar_m200_por_periodo(conn, cnpj, ano_mes)
    if m200 is None:
        return [], []

    m100s = repo.consultar_m100_por_periodo(conn, cnpj, ano_mes)

    soma_m100 = sum(Decimal(str(r["vl_cred_desc"] or 0)) for r in m100s)
    tot_m200 = Decimal(str(m200["vl_tot_cred_desc"] or 0))

    diff = abs(tot_m200 - soma_m100)
    if diff <= _TOLERANCIA:
        return [], []

    sentido = "M200 > Σ M100" if tot_m200 > soma_m100 else "Σ M100 > M200"
    descricao = (
        f"M200.VL_TOT_CRED_DESC={float(tot_m200):.2f} ≠ Σ M100.VL_CRED_DESC={float(soma_m100):.2f}"
        f" (diferença={float(diff):.2f}, {sentido})."
        f" Inconsistência vertical na escrituração de créditos PIS do período."
    )

    return [], [
        Divergencia(
            codigo_regra="CR-29",
            descricao=descricao,
            severidade="medio",
            evidencia=[{
                "registro": "M200/M100",
                "arquivo": m200["arquivo_origem"],
                "linha": m200["linha_arquivo"],
                "campos_chave": {
                    "soma_vl_cred_desc_m100": float(soma_m100),
                    "vl_tot_cred_desc_m200": float(tot_m200),
                    "divergencia_absoluta": float(diff),
                    "sentido": sentido,
                    "qtd_m100": len(m100s),
                },
            }],
        )
    ]
