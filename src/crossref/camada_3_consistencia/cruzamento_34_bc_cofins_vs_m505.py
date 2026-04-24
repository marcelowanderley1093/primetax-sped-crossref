"""CR-34 — Consistência entre VL_BC_COFINS de crédito (C170/F100, CST 50-67) e M505.

Base legal:
  Art. 3º da Lei 10.833/2003: base de cálculo dos créditos COFINS deve ser escriturada
  analiticamente no bloco C/F e consolidada no M505 por NAT_BC_CRED.
  IN RFB 1.252/2012: Σ C170.VL_BC_COFINS (CST 50-67) + Σ F100.VL_BC_COFINS (CST 50-67)
  deve igualar Σ M505.VL_BC_COFINS_TOT.
  CLAUDE.md §8.3 cruzamento 34.

Lógica do cruzamento:
  Análoga ao CR-32 (PIS crédito vs M105), mas para COFINS vs M505.
  LHS = Σ C170.VL_BC_COFINS (cst_cofins ∈ 50-67) + Σ F100.VL_BC_COFINS (cst_cofins ∈ 50-67)
  RHS = Σ M505.VL_BC_COFINS_TOT
  |LHS - RHS| > R$ 1,00 → Divergência.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-34"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

_TOLERANCIA = Decimal("1.00")


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    soma_c170 = repo.soma_vl_bc_cofins_credito_c170(conn, cnpj, ano_mes)
    soma_f100 = repo.soma_vl_bc_cofins_credito_f100(conn, cnpj, ano_mes)
    soma_m505 = repo.soma_vl_bc_cofins_tot_m505(conn, cnpj, ano_mes)

    if soma_m505 == Decimal("0") and soma_c170 == Decimal("0") and soma_f100 == Decimal("0"):
        return [], []

    lhs = soma_c170 + soma_f100
    divergencia_abs = abs(lhs - soma_m505)

    if divergencia_abs <= _TOLERANCIA:
        return [], []

    sentido = "subdeclarado" if lhs > soma_m505 else "superdeclarado"
    descricao = (
        f"Período {ano_mes}: Σ VL_BC_COFINS crédito (C170+F100, CST 50-67)"
        f" = R$ {float(lhs):.2f} vs. Σ M505.VL_BC_COFINS_TOT = R$ {float(soma_m505):.2f}."
        f" Divergência R$ {float(divergencia_abs):.2f} (M505 {sentido})."
    )
    evidencia = [{
        "registro": "M505 × C170/F100",
        "arquivo": "",
        "linha": 0,
        "campos_chave": {
            "soma_c170_vl_bc_cofins_credito": float(soma_c170),
            "soma_f100_vl_bc_cofins_credito": float(soma_f100),
            "soma_lhs": float(lhs),
            "soma_m505_vl_bc_cofins_tot": float(soma_m505),
            "divergencia_absoluta": float(divergencia_abs),
            "sentido_m505": sentido,
        },
    }]

    logger.info(
        "CR-34 %s %d: C170+F100=%.2f M505=%.2f diff=%.2f (%s)",
        cnpj, ano_mes, float(lhs), float(soma_m505), float(divergencia_abs), sentido,
    )
    return [], [Divergencia(
        codigo_regra=CODIGO_REGRA,
        descricao=descricao,
        severidade="medio",
        evidencia=evidencia,
    )]
