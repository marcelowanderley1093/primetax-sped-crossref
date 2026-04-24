"""CR-40 — COD_CTA em C170/F100/F120/F130/M105 × I050 (ECD): validação de existência.

Base legal:
  Art. 3º Lei 10.637/2002 e Lei 10.833/2003 — crédito PIS/COFINS exige correto registro
  contábil dos bens e serviços. IN RFB 1.252/2012 — campos COD_CTA nos registros da
  EFD-Contribuições devem referenciar contas do plano de contas da ECD (I050).
  CLAUDE.md §7.6 — COD_CTA é a chave universal de cruzamento EFD×ECD.
  Divergência entre COD_CTA informado na EFD e contas disponíveis na ECD indica: (a) erro
  de preenchimento da EFD (conta inexistente), (b) mudança de plano de contas não tratada,
  ou (c) inconsistência que pode comprometer a validade do crédito perante auditoria fiscal.
  Vigência: desde a implantação do SPED-Contribuições (2012).

Lógica:
  1. Coleta COD_CTA distintos usados em efd_contrib_c170 para o ano-calendário.
  2. Coleta COD_CTA do plano de contas analítico (IND_CTA='A') da ECD (ecd_i050).
  3. COD_CTA de C170 não presente em I050 → conta "fantasma" → divergência.

Dependência: ecd (CLAUDE.md §18).
modo_degradado_suportado: False (CLAUDE.md §16.3) — objeto é conta individual.
"""

from src.crossref.common.disponibilidade_sped import verificar_dependencias

CODIGO_REGRA = "CR-40"


def executar(repo, conn, cnpj: str, ano_mes: int, ano_calendario: int):
    """Retorna (oportunidades, divergencias)."""
    from src.models.registros import Divergencia

    disp = verificar_dependencias(repo, conn, ["ecd"])
    if disp["ecd"] != "importada":
        return [], []

    c170_ctas = repo.consultar_c170_cod_cta(conn, cnpj, ano_calendario)
    if not c170_ctas:
        return [], []

    i050_registros = repo.consultar_ecd_i050(conn, cnpj, ano_calendario)
    contas_analiticas = {
        r["cod_cta"] for r in i050_registros
        if r.get("ind_cta") == "A"
    }

    if not contas_analiticas:
        return [], []

    ctas_efd = {r["cod_cta"] for r in c170_ctas}
    ctas_ausentes = ctas_efd - contas_analiticas

    if not ctas_ausentes:
        return [], []

    descricao = (
        f"{len(ctas_ausentes)} COD_CTA referenciados em C170 da EFD-Contribuições "
        f"não encontrados no plano de contas analítico da ECD (I050.IND_CTA='A') "
        f"do AC {ano_calendario}: {sorted(ctas_ausentes)[:10]}{'...' if len(ctas_ausentes) > 10 else ''}. "
        f"Verificar se há mudança de plano de contas não conciliada ou preenchimento incorreto."
    )

    divergencias = [
        Divergencia(
            codigo_regra=CODIGO_REGRA,
            descricao=descricao,
            severidade="medio",
            evidencia=[{
                "registro": "C170/I050",
                "campos_chave": {
                    "ctas_ausentes_ecd": sorted(ctas_ausentes),
                    "qtd_ctas_ausentes": len(ctas_ausentes),
                    "qtd_ctas_efd_total": len(ctas_efd),
                    "qtd_contas_analiticas_ecd": len(contas_analiticas),
                    "ano_calendario": ano_calendario,
                },
            }],
        )
    ]
    return [], divergencias
