"""
Cruzamento 02 — Unicidade de M200 e M600.

Base legal: IN RFB 1.252/2012, leiaute EFD-Contribuições — cada arquivo
  mensal deve conter exatamente um registro M200 (resumo PIS) e um M600
  (resumo COFINS). Mais de um indica duplicidade de importação ou arquivo
  corrompido.

Camada: 1 — Integridade estrutural.
"""

import logging

from src.models.registros import Divergencia

logger = logging.getLogger(__name__)

CODIGO_REGRA = "CI-02"
SEVERIDADE = "alto"


def executar(
    repo,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> list[Divergencia]:
    divergencias: list[Divergencia] = []

    qtd_m200 = repo.contar_m200(conn, cnpj, ano_mes)
    qtd_m600 = repo.contar_m600(conn, cnpj, ano_mes)

    if qtd_m200 != 1:
        msg = f"M200: esperado 1 registro, encontrado {qtd_m200}"
        logger.warning("CI-02 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"Unicidade M200/M600 — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{"cnpj_declarante": cnpj, "ano_mes": ano_mes,
                            "registro": "M200", "quantidade": qtd_m200}],
            )
        )

    if qtd_m600 != 1:
        msg = f"M600: esperado 1 registro, encontrado {qtd_m600}"
        logger.warning("CI-02 %s %d: %s", cnpj, ano_mes, msg)
        divergencias.append(
            Divergencia(
                codigo_regra=CODIGO_REGRA,
                descricao=f"Unicidade M200/M600 — {msg}",
                severidade=SEVERIDADE,
                evidencia=[{"cnpj_declarante": cnpj, "ano_mes": ano_mes,
                            "registro": "M600", "quantidade": qtd_m600}],
            )
        )

    return divergencias
