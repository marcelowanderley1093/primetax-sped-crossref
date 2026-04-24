"""
Testes do cruzamento CR-12 — Auditoria individual de C170 com CST 70-75.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CST_PIS=70, VL_BC_PIS=5000 → CR-12 sinaliza para revisão.

Fixture negativo (202602):
  C170 CST_PIS=50 (com crédito aproveitado) → CR-12 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_12_cst_70_75_auditoria
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


class TestCruzamento12Cst7075Auditoria:
    def test_cst70_gera_oportunidade(
        self, fixture_sprint5_cr12_positivo, tmp_path
    ):
        """C170 CST=70 com VL_BC_PIS > 0 → CR-12 sinaliza item para revisão."""
        repo, conn = _importar(fixture_sprint5_cr12_positivo, tmp_path)
        try:
            ops, divs = cruzamento_12_cst_70_75_auditoria.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-12"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cst_pis"] == "70"
        assert ck["vl_bc_pis"] == pytest.approx(5000.0)

    def test_cst50_nao_dispara(
        self, fixture_sprint5_cr12_negativo, tmp_path
    ):
        """C170 com CST fora do intervalo 70-75 → CR-12 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr12_negativo, tmp_path)
        try:
            ops, divs = cruzamento_12_cst_70_75_auditoria.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
