"""CR-33 — Consistência entre VL_BC_COFINS de débito (C170, CST 01-05) e M610.VL_BC_CONT.

Base legal:
  Art. 1º da Lei 10.833/2003: COFINS não-cumulativa; base de cálculo.
  IN RFB 1.252/2012: Σ C170.VL_BC_COFINS (CST 01-05, saídas) deve corresponder
  ao Σ M610.VL_BC_CONT declarado por COD_CONT.
  CLAUDE.md §8.3 cruzamento 33.

Lógica do cruzamento:
  Análoga ao CR-31 (PIS vs M210), mas para COFINS vs M610.
  Σ C170.VL_BC_COFINS (CST 01-05, somente saídas IND_OPER='1')
  vs. Σ M610.VL_BC_CONT.
  |LHS - RHS| > R$ 1,00 → Divergência.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-33"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

_CST_DEBITO_COFINS = {"01", "02", "03", "04", "05"}
_TOLERANCIA = Decimal("1.00")


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    c100_ind_oper = repo.consultar_c100_ind_oper(conn, cnpj, ano_mes)
    c170_items = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    m610_items = repo.consultar_m610_por_periodo(conn, cnpj, ano_mes)

    if not m610_items:
        return [], []

    soma_c170 = Decimal("0")
    contagem_itens = 0
    for item in c170_items:
        cst = str(item.get("cst_cofins", "")).strip()
        if cst not in _CST_DEBITO_COFINS:
            continue
        if c100_ind_oper.get(item["c100_linha_arquivo"], "") != "1":
            continue
        vl_bc = Decimal(str(item.get("vl_bc_cofins", "0") or "0"))
        soma_c170 += vl_bc
        contagem_itens += 1

    soma_m610 = sum(
        Decimal(str(item.get("vl_bc_cont", "0") or "0"))
        for item in m610_items
    )

    divergencia_abs = abs(soma_c170 - soma_m610)
    if divergencia_abs <= _TOLERANCIA:
        return [], []

    sentido = "subdeclarada" if soma_c170 > soma_m610 else "superdeclarada"
    evidencia = [{
        "registro": "M610",
        "arquivo": m610_items[0]["arquivo_origem"],
        "linha": m610_items[0]["linha_arquivo"],
        "campos_chave": {
            "soma_vl_bc_cofins_c170": float(soma_c170),
            "soma_vl_bc_cont_m610": float(soma_m610),
            "divergencia_absoluta": float(divergencia_abs),
            "sentido": sentido,
            "itens_c170_analisados": contagem_itens,
            "registros_m610": len(m610_items),
        },
    }]

    logger.info(
        "CR-33 %s %d: C170=%.2f M610=%.2f diff=%.2f (%s)",
        cnpj, ano_mes, float(soma_c170), float(soma_m610), float(divergencia_abs), sentido,
    )
    return [], [Divergencia(
        codigo_regra=CODIGO_REGRA,
        descricao=(
            f"Período {ano_mes}: Σ VL_BC_COFINS (C170 débito, CST 01-05)"
            f" = R$ {float(soma_c170):.2f} vs. Σ VL_BC_CONT (M610)"
            f" = R$ {float(soma_m610):.2f}."
            f" Divergência de R$ {float(divergencia_abs):.2f} ({sentido})."
        ),
        severidade="medio",
        evidencia=evidencia,
    )]
