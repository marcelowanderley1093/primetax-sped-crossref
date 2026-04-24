"""CR-32 — Consistência entre VL_BC_PIS de crédito (C170/F100, CST 50-67) e M105.

Base legal:
  Art. 3º da Lei 10.637/2002: base de cálculo dos créditos PIS deve ser escriturada
  analiticamente no bloco C/F e consolidada no M105 por NAT_BC_CRED.
  IN RFB 1.252/2012: Σ C170.VL_BC_PIS (CST 50-67) + Σ F100.VL_BC_PIS (CST 50-67)
  deve igualar Σ M105.VL_BC_PIS_TOT (todas as naturezas de base de crédito).
  CLAUDE.md §8.3 cruzamento 32.

Lógica do cruzamento:
  Compara:
    LHS = Σ C170.VL_BC_PIS (cst_pis ∈ 50-67) + Σ F100.VL_BC_PIS (cst_pis ∈ 50-67)
    RHS = Σ M105.VL_BC_PIS_TOT (todos os registros M105 do período)
  |LHS - RHS| > R$ 1,00 → Divergência.
  LHS > RHS: M105 subdeclarado (créditos de C170/F100 não reportados no M105).
  LHS < RHS: M105 superdeclarado (créditos no M105 sem lastro em C170/F100).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-32"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

_TOLERANCIA = Decimal("1.00")


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    soma_c170 = repo.soma_vl_bc_pis_credito_c170(conn, cnpj, ano_mes)
    soma_f100 = repo.soma_vl_bc_pis_credito_f100(conn, cnpj, ano_mes)
    soma_m105 = repo.soma_vl_bc_pis_tot_m105(conn, cnpj, ano_mes)

    if soma_m105 == Decimal("0") and soma_c170 == Decimal("0") and soma_f100 == Decimal("0"):
        return [], []

    lhs = soma_c170 + soma_f100
    divergencia_abs = abs(lhs - soma_m105)

    if divergencia_abs <= _TOLERANCIA:
        return [], []

    sentido = "subdeclarado" if lhs > soma_m105 else "superdeclarado"
    descricao = (
        f"Período {ano_mes}: Σ VL_BC_PIS crédito (C170+F100, CST 50-67)"
        f" = R$ {float(lhs):.2f} vs. Σ M105.VL_BC_PIS_TOT = R$ {float(soma_m105):.2f}."
        f" Divergência R$ {float(divergencia_abs):.2f} (M105 {sentido})."
    )
    evidencia = [{
        "registro": "M105 × C170/F100",
        "arquivo": "",
        "linha": 0,
        "campos_chave": {
            "soma_c170_vl_bc_pis_credito": float(soma_c170),
            "soma_f100_vl_bc_pis_credito": float(soma_f100),
            "soma_lhs": float(lhs),
            "soma_m105_vl_bc_pis_tot": float(soma_m105),
            "divergencia_absoluta": float(divergencia_abs),
            "sentido_m105": sentido,
        },
    }]

    logger.info(
        "CR-32 %s %d: C170+F100=%.2f M105=%.2f diff=%.2f (%s)",
        cnpj, ano_mes, float(lhs), float(soma_m105), float(divergencia_abs), sentido,
    )
    return [], [Divergencia(
        codigo_regra=CODIGO_REGRA,
        descricao=descricao,
        severidade="medio",
        evidencia=evidencia,
    )]
