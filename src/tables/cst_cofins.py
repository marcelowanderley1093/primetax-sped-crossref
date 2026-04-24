"""
Tabela CST-COFINS — Código de Situação Tributária.
Fonte: Anexo Único da IN RFB nº 1.009/2010.

Estrutura idêntica à CST-PIS. Divergência sistemática CST_PIS ≠ CST_COFINS no mesmo
C170 pode indicar erro de classificação (cruzamento 10).
"""

from src.tables.cst_pis import (  # noqa: F401 — re-exporta a mesma tabela
    DESCRICOES,
    CST_DEBITO,
    CST_CREDITO,
    CST_SEM_CREDITO,
    CST_TESE_69,
    eh_valido,
    descricao,
)
