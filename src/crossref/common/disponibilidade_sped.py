"""
Gestão de disponibilidade por SPED (CLAUDE.md §18).

Três estados por SPED × CNPJ × ano-calendário:
  "importada"              — arquivo presente e processado com sucesso.
  "pendente"               — estado neutro inicial; arquivo não importado.
  "estruturalmente_ausente" — ausência confirmada por declaração oficial
                              ou característica de regime da PJ.

Sprint 1: infraestrutura criada, semântica ativa a partir do Sprint 6.
Cada regra de detecção de ausência estrutural carrega referência legal
(CLAUDE.md §4, princípio 4).

Referências legais das ausências estruturais (§18.8):
  ECD Livro Caixa: art. 45 parágrafo único Lei 8.981/1995; IN RFB 2.003/2021.
  ECF Simples Nacional: IN RFB 2.004/2021.
  EFD ICMS/IPI (serviços ISS): Ajuste SINIEF 02/2009, cláusula 5ª.
  Bloco I financeiras: IN RFB 1.252/2012.
"""

import logging

logger = logging.getLogger(__name__)

_ESTADOS_VALIDOS = frozenset({"importada", "pendente", "estruturalmente_ausente"})

_CAMPO_POR_SPED = {
    "efd_contribuicoes": "disponibilidade_efd_contrib",
    "efd_icms": "disponibilidade_efd_icms",
    "ecd": "disponibilidade_ecd",
    "ecf": "disponibilidade_ecf",
    "bloco_i": "disponibilidade_bloco_i",
}


def obter_disponibilidade(repo, conn, sped: str) -> str:
    """Retorna o estado de disponibilidade para o SPED indicado."""
    campo = _CAMPO_POR_SPED.get(sped)
    if campo is None:
        raise ValueError(f"SPED desconhecido: {sped!r}")
    ctx = repo.consultar_sped_contexto(conn)
    if ctx is None:
        return "pendente"
    return ctx.get(campo, "pendente") or "pendente"


def atualizar_disponibilidade(repo, conn, sped: str, estado: str) -> None:
    """Atualiza o estado de disponibilidade para o SPED indicado."""
    if estado not in _ESTADOS_VALIDOS:
        raise ValueError(f"Estado inválido: {estado!r}")
    campo = _CAMPO_POR_SPED.get(sped)
    if campo is None:
        raise ValueError(f"SPED desconhecido: {sped!r}")
    repo.atualizar_sped_contexto(conn, **{campo: estado})
    logger.debug("Disponibilidade %s → %s (CNPJ=%s)", sped, estado, repo.cnpj)


def verificar_dependencias(repo, conn, dependencias: list[str]) -> dict[str, str]:
    """
    Retorna mapa sped → estado para cada SPED na lista de dependências.
    Usado pelo motor de cruzamentos para decidir se executa ou categoriza
    o cruzamento como pendente/estruturalmente_ausente.
    """
    return {sped: obter_disponibilidade(repo, conn, sped) for sped in dependencias}


def estado_efetivo(disponibilidades: dict[str, str]) -> str:
    """
    Retorna o estado mais restritivo dado um conjunto de disponibilidades.
    Regra (CLAUDE.md §18.3): estruturalmente_ausente > pendente > importada.
    """
    if "estruturalmente_ausente" in disponibilidades.values():
        return "estruturalmente_ausente"
    if "pendente" in disponibilidades.values():
        return "pendente"
    return "importada"
