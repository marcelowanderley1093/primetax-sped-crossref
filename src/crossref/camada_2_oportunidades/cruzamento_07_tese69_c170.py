"""
Cruzamento 07 — Tese 69: ICMS indevidamente na base de PIS/COFINS em C170.

Base legal:
  RE 574.706/PR (Tema 69 STF) — exclusão do ICMS da base do PIS/COFINS.
  Parecer SEI 7698/2021/ME (PGFN) — operacionalização; marco 01/2018.
  IN RFB 1.252/2012 — leiaute C170 da EFD-Contribuições.

Camada: 2 — Oportunidade.
Cruzamento-âncora do Sprint 1 (CLAUDE.md §8.2, item 7).

Dependências SPED: ["efd_contribuicoes"] — Sprint 1, sem inter-SPED.
Modo degradado: N/A — cruzamento intra-EFD-Contribuições.
"""

import logging

from src.models.registros import Divergencia, Oportunidade
from src.rules.tese_69_icms import CODIGO_REGRA, DESCRICAO, SEVERIDADE, calcular_oportunidade_item

logger = logging.getLogger(__name__)

DEPENDENCIAS_SPED = ["efd_contribuicoes"]


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Executa o cruzamento 07 para um período (cnpj, ano_mes).

    Retorna (oportunidades, divergencias). Divergencias são vazias para
    este cruzamento — as incongruências geram Oportunidades, não Divergencias.
    """
    oportunidades: list[Oportunidade] = []

    # Mapa C100.linha_arquivo → ind_oper (saída = "1")
    c100_ind_oper = repo.consultar_c100_ind_oper(conn, cnpj, ano_mes)

    itens = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)

    total_itens = len(itens)
    total_oportunidades = 0

    for item in itens:
        # Somente saídas (ind_oper = "1") — ICMS aparece na base de saídas
        if c100_ind_oper.get(item["c100_linha_arquivo"], "") != "1":
            continue

        resultado = calcular_oportunidade_item(item)
        if resultado is None:
            continue

        total_oportunidades += 1
        oportunidades.append(
            Oportunidade(
                codigo_regra=resultado["codigo_regra"],
                descricao=resultado["descricao"],
                severidade=resultado["severidade"],
                valor_impacto_conservador=resultado["valor_impacto_conservador"],
                valor_impacto_maximo=resultado["valor_impacto_maximo"],
                evidencia=[resultado["evidencia"]],
            )
        )

    logger.info(
        "CR-07 %s %d: %d itens analisados, %d oportunidades",
        cnpj, ano_mes, total_itens, total_oportunidades,
    )

    return oportunidades, []
