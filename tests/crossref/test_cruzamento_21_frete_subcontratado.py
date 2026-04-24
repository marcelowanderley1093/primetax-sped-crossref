"""
Testes do cruzamento CR-21 — Crédito presumido de transporte subcontratado (CFOP 1352/2352).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CFOP=1352 + CST_PIS=70 (sem crédito) + VL_ITEM=8.000 →
  crédito presumido de frete não aproveitado → CR-21 dispara.

Fixture negativo (202602):
  C170 CFOP=1352 + CST_PIS=50 (com crédito já declarado) →
  CR-21 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_21_frete_subcontratado
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


class TestCruzamento21FreteSubcontratado:
    def test_cfop1352_cst70_gera_oportunidade(
        self, fixture_sprint5_cr21_positivo, tmp_path
    ):
        """CFOP=1352 + CST=70 + VL_ITEM > 0 → CR-21 detecta frete sem crédito presumido."""
        repo, conn = _importar(fixture_sprint5_cr21_positivo, tmp_path)
        try:
            ops, divs = cruzamento_21_frete_subcontratado.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-21"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cfop"] == "1352"
        assert ck["cst_pis"] == "70"
        assert ck["vl_item"] == pytest.approx(8000.0)
        assert ck["impacto_pis"] > 0.0

    def test_cfop1352_cst50_nao_dispara(
        self, fixture_sprint5_cr21_negativo, tmp_path
    ):
        """CFOP=1352 + CST=50 (crédito já declarado) → CR-21 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr21_negativo, tmp_path)
        try:
            ops, divs = cruzamento_21_frete_subcontratado.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
