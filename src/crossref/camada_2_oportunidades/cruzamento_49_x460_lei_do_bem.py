"""CR-49 — X460 (ECF): Lei do Bem — dispêndios P&D sem exclusão aproveitada.

Base legal:
  Lei 11.196/2005, arts. 17 a 26 (Lei do Bem) — incentivos fiscais à inovação
  tecnológica para PJs do Lucro Real. Permite exclusão no IRPJ/CSLL de 60% a
  80% dos dispêndios com P&D (art. 19), com acréscimos por pesquisador
  contratado (art. 19-A) e depreciação/amortização integral no ano (art. 17).
  Decreto 5.798/2006 — regulamentação.
  ADE Cofis 02/2026 §20 — registro X460 da ECF.

Lógica:
  1. PJ declara dispêndios com inovação tecnológica nos registros X460.
  2. A exclusão correspondente (30%-60% a 80% dos dispêndios) deve aparecer
     como lançamento no M300 (Parte A do e-Lalur) com IND_RELACAO='2'
     (exclusão) referenciando um código de exclusão da tabela dinâmica.
  3. X460 com VALOR > threshold e nenhuma exclusão correspondente no M300 =
     benefício fiscal declarado mas não aproveitado → oportunidade de
     retificação com recuperação da base IRPJ/CSLL.

Limitação:
  Sem acesso à tabela dinâmica dos códigos M300 específicos de Lei do Bem,
  o cruzamento detecta a ausência total de exclusões M300 (TIPO_LANCAMENTO='E')
  no ano. Em versões futuras, com a tabela dinâmica M300 codificada, o
  match pode ser feito por código específico (análogo a CR-46).

Dependência: ecf apenas (CLAUDE.md §18).
modo_degradado_suportado: N/A — dentro do próprio SPED ECF.
"""

from decimal import Decimal

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-49"
DEPENDENCIAS_SPED = ["ecf"]
_THRESHOLD_VALOR = Decimal("1000")  # R$ 1.000 mínimo para reportar


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Oportunidade

    disp = verificar_dependencias(repo, conn, ["ecf"])
    if disp["ecf"] != "importada":
        return [], []

    x460 = repo.consultar_ecf_x460(conn, cnpj, ano_calendario)
    if not x460:
        return [], []

    total_x460 = sum(
        Decimal(str(r.get("valor") or 0)) for r in x460
    )
    if total_x460 < _THRESHOLD_VALOR:
        return [], []

    # Verifica se há exclusões M300 no período
    m300 = repo.consultar_ecf_m300(conn, cnpj, ano_calendario)
    exclusoes_m300 = [
        r for r in m300 if (r.get("tipo_lancamento") or "").strip().upper() == "E"
    ]
    total_exclusoes = sum(
        Decimal(str(r.get("valor") or 0)) for r in exclusoes_m300
    )

    # Estimativa do benefício aproveitável: 60% dos dispêndios (patamar mínimo
    # da Lei do Bem, art. 19 — pode chegar a 80% com multiplicadores).
    beneficio_estimado = total_x460 * Decimal("0.60")

    if total_exclusoes >= beneficio_estimado:
        return [], []  # provável que a exclusão já foi aproveitada

    oportunidades = [
        Oportunidade(
            codigo_regra=CODIGO_REGRA,
            descricao=(
                f"ECF do AC {ano_calendario} declara R$ {float(total_x460):,.2f} em "
                f"dispêndios com inovação tecnológica (X460 — Lei do Bem), mas o M300 "
                f"apresenta apenas R$ {float(total_exclusoes):,.2f} em exclusões (total, "
                f"não discriminadas por benefício). Estimativa conservadora de exclusão "
                f"aplicável: R$ {float(beneficio_estimado):,.2f} (60% dos dispêndios — "
                f"patamar mínimo do art. 19 da Lei 11.196/2005). Verificar se a "
                f"exclusão Lei do Bem foi efetivamente registrada no e-Lalur."
            ),
            severidade="alto",
            valor_impacto_conservador=beneficio_estimado * Decimal("0.15"),
            valor_impacto_maximo=beneficio_estimado * Decimal("0.25"),
            evidencia=[{
                "registro": "X460 × M300",
                "arquivo": x460[0].get("arquivo_origem", ""),
                "linha": x460[0].get("linha_arquivo", 0),
                "campos_chave": {
                    "total_x460_declarado": float(total_x460),
                    "total_exclusoes_m300": float(total_exclusoes),
                    "beneficio_estimado_60pct": float(beneficio_estimado),
                    "qtd_linhas_x460": len(x460),
                    "ano_calendario": ano_calendario,
                },
            }],
        )
    ]
    return oportunidades, []
