"""
Cruzamento 05 — Hierarquia pai-filho (C170 ← C100).

Base legal: IN RFB 1.252/2012, leiaute EFD-Contribuições — o registro C170
  (item do documento fiscal) é filho do C100 (documento fiscal) e deve ter
  um C100 correspondente no mesmo arquivo.  Arquivo com C170 órfão indica
  corrupção estrutural (CLAUDE.md §7.2 — "C170 órfão é arquivo corrompido").

Sprint 1 verifica apenas C170 ← C100.
Sprints futuros: M105 ← M100, I250 ← I200, M305 ← M300 (outros SPEDs).

Camada: 1 — Integridade estrutural.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-05"
SEVERIDADE = "alto"


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    divergencias: list[Divergencia] = []

    c100_linhas = repo.consultar_c100_linhas(conn, cnpj, ano_mes)
    c170_refs = repo.consultar_c170_c100_refs(conn, cnpj, ano_mes)

    orfaos = c170_refs - c100_linhas
    if orfaos:
        msg = (
            f"{len(orfaos)} referência(s) de C170 a C100 inexistente(s):"
            f" linhas {sorted(orfaos)[:5]}{'...' if len(orfaos) > 5 else ''}"
        )
        logger.warning("CI-05 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"C170 órfão — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{
                    "cnpj_declarante": cnpj,
                    "ano_mes": ano_mes,
                    "c100_linhas_ausentes": sorted(orfaos),
                }],
            )
        )

    return divergencias
