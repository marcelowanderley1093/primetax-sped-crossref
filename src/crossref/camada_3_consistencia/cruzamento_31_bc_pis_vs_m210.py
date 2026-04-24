"""
CR-31 — Consistência entre VL_BC_PIS dos itens (C170) e VL_BC_CONT do M210.

Base legal:
  Lei 10.637/2002 art. 1º — PIS/Pasep não-cumulativo; base de cálculo.
  IN RFB 1.252/2012 — leiaute EFD-Contribuições; registros C170 e M210.
  CLAUDE.md §8.3 cruzamento 31: "Σ VL_BC_PIS dos itens com CST de débito,
    agrupado por CST e alíquota, = M210.VL_BC_CONT".

Lógica Sprint 3 (versão simplificada — totais agregados):
  Σ C170.VL_BC_PIS (saídas, CST ∈ {01,02,03,05}) vs. Σ M210.VL_BC_CONT.
  Divergência > TOLERANCIA → anomalia a investigar.

Nota: a versão completa (Sprint 5) detalha por COD_CONT (CST × alíquota),
  exigindo tabela de decodificação COD_CONT → CST. Na versão atual, a comparação
  de totais detecta divergências materiais que valem ser investigadas.

Tolerância: R$ 1,00 (ruídos de arredondamento em operações com centavos).
"""

from __future__ import annotations

import logging
from decimal import Decimal

from src.db.repo import Repositorio
from src.models.registros import Divergencia, Oportunidade

logger = logging.getLogger(__name__)
CODIGO_REGRA = "CR-31"
DEPENDENCIAS_SPED = ["efd_contribuicoes"]

# CSTs que geram débito de PIS/Pasep no regime não-cumulativo (contribuição positiva)
_CST_DEBITO_PIS = {"01", "02", "03", "05"}

# Tolerância para divergência de arredondamento
_TOLERANCIA = Decimal("1.00")


def executar(
    repo: Repositorio,
    conn,
    cnpj: str,
    ano_mes: int,
    ano_calendario: int,
) -> tuple[list[Oportunidade], list[Divergencia]]:
    """
    Compara Σ VL_BC_PIS dos C170 com CST de débito (saídas) vs.
    Σ VL_BC_CONT declarado nos registros M210 do mesmo período.

    Divergência material indica base de PIS subdeclarada ou superdeclarada no M210.
    """
    # Mapa C100.linha_arquivo → ind_oper para filtrar apenas saídas
    c100_ind_oper = repo.consultar_c100_ind_oper(conn, cnpj, ano_mes)
    c170_items = repo.consultar_c170_por_periodo(conn, cnpj, ano_mes)
    m210_items = repo.consultar_m210_por_periodo(conn, cnpj, ano_mes)

    if not m210_items:
        # Sem M210 no período: impossível validar — não é divergência do CR-31
        return [], []

    soma_c170 = Decimal("0")
    contagem_itens = 0
    for item in c170_items:
        cst = str(item.get("cst_pis", "")).strip()
        if cst not in _CST_DEBITO_PIS:
            continue
        if c100_ind_oper.get(item["c100_linha_arquivo"], "") != "1":
            continue  # somente saídas
        vl_bc = Decimal(str(item.get("vl_bc_pis", "0") or "0"))
        soma_c170 += vl_bc
        contagem_itens += 1

    soma_m210 = sum(
        Decimal(str(item.get("vl_bc_cont", "0") or "0"))
        for item in m210_items
    )

    divergencia_abs = abs(soma_c170 - soma_m210)
    if divergencia_abs <= _TOLERANCIA:
        logger.debug(
            "CR-31 %s %d: bases aderentes (C170=%.2f M210=%.2f diff=%.2f)",
            cnpj, ano_mes, soma_c170, soma_m210, divergencia_abs,
        )
        return [], []

    sentido = "subdeclarada" if soma_c170 > soma_m210 else "superdeclarada"
    evidencia = {
        "bloco": "M",
        "registro": "M210",
        "linha_arquivo": m210_items[0]["linha_arquivo"],
        "arquivo_origem": m210_items[0]["arquivo_origem"],
        "cnpj_declarante": cnpj,
        "ano_mes": ano_mes,
        "campos_chave": {
            "soma_vl_bc_pis_c170": float(soma_c170),
            "soma_vl_bc_cont_m210": float(soma_m210),
            "divergencia_absoluta": float(divergencia_abs),
            "sentido": sentido,
            "itens_c170_analisados": contagem_itens,
            "registros_m210": len(m210_items),
            "nota": (
                f"Base PIS {sentido} no M210 em relação à soma dos C170 "
                f"tributáveis (CST {sorted(_CST_DEBITO_PIS)}). "
                "Verificar: (a) itens D100/C181 não incluídos nesta análise; "
                "(b) ajustes de base via M215; (c) documentos com CST não-padrão."
            ),
        },
    }

    div = Divergencia(
        codigo_regra=CODIGO_REGRA,
        descricao=(
            f"Período {ano_mes}: Σ VL_BC_PIS (C170 débito) = R$ {soma_c170:.2f} "
            f"vs. Σ VL_BC_CONT (M210) = R$ {soma_m210:.2f}. "
            f"Divergência de R$ {divergencia_abs:.2f} ({sentido})."
        ),
        severidade="medio",
        evidencia=[evidencia],
    )

    logger.info(
        "CR-31 %s %d: divergência %.2f (C170=%.2f M210=%.2f)",
        cnpj, ano_mes, divergencia_abs, soma_c170, soma_m210,
    )
    return [], [div]
