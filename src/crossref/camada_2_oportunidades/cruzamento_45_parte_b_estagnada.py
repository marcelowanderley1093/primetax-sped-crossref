"""CR-45 — M500 (ECF Parte B do e-Lalur/e-Lacs): saldo estagnado não aproveitado.

Base legal:
  Lei 12.973/2014 (art. 67) — a Parte B do e-Lalur controla adições temporárias
  (IND_SD_FIM_LAL='C', que serão excluídas futuramente) e exclusões futuras
  (IND_SD_FIM_LAL='D', que correspondem a valores já excluídos na Parte A mas
  ainda com saldo a reverter).
  Lei 9.065/1995, art. 15 — compensação de prejuízos fiscais limitada a 30% do lucro.
  IN RFB 1.700/2017 (art. 100) — prazo e forma de aproveitamento da Parte B.
  ADE Cofis 02/2026 §12.
  Vigência: desde AC 2014.

Lógica:
  Conta M500 com:
  - SD_FIM_LAL > 0 (saldo não-zero)
  - VL_LCTO_PARTE_A = 0 (nenhum movimento na Parte A no período)
  - VL_LCTO_PARTE_B = 0 (nenhum movimento na Parte B no período)
  - IND_SD_FIM_LAL = 'D' (natureza de exclusão futura — a PJ vai excluir mais tarde)
  → Exclusão pendente que não está sendo aproveitada. Alto valor potencial.

Exemplos de contas tipicamente estagnadas:
  - Provisões para contingência revertidas sem exclusão correspondente.
  - Subvenções para investimento (pré-Lei 14.789/2023) não controladas.
  - Prejuízos de controlada/coligada por equivalência patrimonial.

Dependência: ecf apenas (CLAUDE.md §18).
modo_degradado_suportado: N/A — ECF isolada.
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-45"
_THRESHOLD_SALDO = Decimal("1000")  # R$ 1.000 mínimo para reportar


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecf"])
    if disp["ecf"] != "importada":
        return [], []

    m500_registros = repo.consultar_ecf_m500(conn, cnpj, ano_calendario)
    if not m500_registros:
        return [], []

    oportunidades = []
    for r in m500_registros:
        sd_fim = Decimal(str(r.get("sd_fim_lal") or 0))
        vl_parte_a = Decimal(str(r.get("vl_lcto_parte_a") or 0))
        vl_parte_b = Decimal(str(r.get("vl_lcto_parte_b") or 0))
        ind_fim = r.get("ind_sd_fim_lal", "")

        if (
            sd_fim > _THRESHOLD_SALDO
            and vl_parte_a == Decimal("0")
            and vl_parte_b == Decimal("0")
            and ind_fim == "D"
        ):
            cod_tributo = r.get("cod_tributo", "")
            tributo_nome = "IRPJ" if cod_tributo == "I" else ("CSLL" if cod_tributo == "C" else cod_tributo)
            oportunidades.append(
                Oportunidade(
                    codigo_regra=CODIGO_REGRA,
                    descricao=(
                        f"Parte B do e-Lalur/e-Lacs estagnada: "
                        f"COD_CTA_B={r.get('cod_cta_b')} ({tributo_nome}) — "
                        f"saldo de R$ {float(sd_fim):,.2f} (exclusão futura, IND='D') "
                        f"sem movimentação em Parte A ou B no AC {ano_calendario}. "
                        f"Exclusão pendente não aproveitada. "
                        f"Verificar natureza da conta e possibilidade de aproveitamento "
                        f"(IN RFB 1.700/2017, art. 100)."
                    ),
                    severidade="alto",
                    valor_impacto_conservador=sd_fim,
                    valor_impacto_maximo=sd_fim,
                    evidencia=[{
                        "registro": "M500",
                        "arquivo": r.get("arquivo_origem", ""),
                        "linha": r.get("linha_arquivo"),
                        "campos_chave": {
                            "cod_cta_b": r.get("cod_cta_b"),
                            "cod_tributo": cod_tributo,
                            "sd_fim_lal": float(sd_fim),
                            "ind_sd_fim_lal": ind_fim,
                            "vl_lcto_parte_a": float(vl_parte_a),
                            "vl_lcto_parte_b": float(vl_parte_b),
                            "ano_calendario": ano_calendario,
                        },
                    }],
                )
            )

    return oportunidades, []
