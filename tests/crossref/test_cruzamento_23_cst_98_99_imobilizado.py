"""
Testes do cruzamento CR-23 — CST 98/99 em C170 para ativo imobilizado.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CST_PIS=98 + VL_BC_PIS=50.000 + VL_PIS=0 →
  possível imobilizado escriturado incorretamente no C → CR-23 gera Divergência.

Fixture negativo (202602):
  C170 CST_PIS=98 + VL_PIS > 0 → CR-23 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_23_cst_98_99_imobilizado
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


class TestCruzamento23Cst9899Imobilizado:
    def test_cst98_sem_vl_pis_gera_divergencia(
        self, fixture_sprint5_cr23_positivo, tmp_path
    ):
        """C170 CST=98 com VL_BC > 0 mas VL_PIS=0 → CR-23 sinaliza escrituração incorreta."""
        repo, conn = _importar(fixture_sprint5_cr23_positivo, tmp_path)
        try:
            ops, divs = cruzamento_23_cst_98_99_imobilizado.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) >= 1
        div = divs[0]
        assert div.codigo_regra == "CR-23"
        assert div.severidade == "medio"
        ck = div.evidencia[0]["campos_chave"]
        assert ck["cst_pis"] == "98"
        assert ck["vl_bc_pis"] == pytest.approx(50000.0)
        assert ck["vl_pis"] == pytest.approx(0.0)

    def test_cst98_com_vl_pis_nao_dispara(
        self, fixture_sprint5_cr23_negativo, tmp_path
    ):
        """C170 CST=98 com VL_PIS preenchido → CR-23 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr23_negativo, tmp_path)
        try:
            ops, divs = cruzamento_23_cst_98_99_imobilizado.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
