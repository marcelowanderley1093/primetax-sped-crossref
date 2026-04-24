"""
Testes do cruzamento CR-10 — Coerência CST × alíquota × valor PIS no C170.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CST_PIS=50, VL_BC_PIS=1000, ALIQ_PIS=1,65%, VL_PIS=0 →
  crédito de R$ 16,50 não aproveitado → CR-10 dispara (Oportunidade).

Fixture negativo (202602):
  C170 CST_PIS=50, VL_BC_PIS=1000, VL_PIS=16,50 (correto) →
  CR-10 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_10_cst_aliquota_c170
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2026


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento10CstAliquotaC170:
    def test_credito_nao_aproveitado_gera_oportunidade(
        self, fixture_sprint5_cr10_positivo, tmp_path
    ):
        """C170 CST=50 com BC e alíquota mas VL_PIS=0 → CR-10 detecta crédito não aproveitado."""
        repo, conn = _importar(fixture_sprint5_cr10_positivo, tmp_path)
        try:
            ops, divs = cruzamento_10_cst_aliquota_c170.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-10"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cst_pis"] == "50"
        assert ck["vl_bc_pis"] == pytest.approx(1000.0)
        assert ck["vl_pis_declarado"] == pytest.approx(0.0)
        assert ck["vl_pis_esperado"] > 0.0

    def test_credito_correto_nao_dispara(
        self, fixture_sprint5_cr10_negativo, tmp_path
    ):
        """C170 CST=50 com VL_PIS preenchido corretamente → CR-10 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr10_negativo, tmp_path)
        try:
            ops, divs = cruzamento_10_cst_aliquota_c170.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
