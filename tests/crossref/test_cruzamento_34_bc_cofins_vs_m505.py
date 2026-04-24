"""
Testes do cruzamento CR-34 — Consistência Σ VL_BC_COFINS crédito (C170/F100) vs M505.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CST_COFINS=50 VL_BC_COFINS=1.000 + M505 VL_BC_COFINS_TOT=2.000 →
  divergência R$ 1.000 > R$ 1,00 → CR-34 dispara.

Fixture negativo (202602):
  C170 CST_COFINS=50 VL_BC_COFINS=1.000 + M505 VL_BC_COFINS_TOT=1.000 →
  diferença=0 → CR-34 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_3_consistencia import cruzamento_34_bc_cofins_vs_m505
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


class TestCruzamento34BcCofinsVsM505:
    def test_divergencia_c170_m505_dispara(
        self, fixture_sprint5_cr34_positivo, tmp_path
    ):
        """C170 soma 1.000, M505 declara 2.000 → divergência R$ 1.000 → CR-34 dispara."""
        repo, conn = _importar(fixture_sprint5_cr34_positivo, tmp_path)
        try:
            ops, divs = cruzamento_34_bc_cofins_vs_m505.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 1
        div = divs[0]
        assert div.codigo_regra == "CR-34"
        assert div.severidade == "medio"
        ck = div.evidencia[0]["campos_chave"]
        assert ck["soma_c170_vl_bc_cofins_credito"] == pytest.approx(1000.0)
        assert ck["soma_m505_vl_bc_cofins_tot"] == pytest.approx(2000.0)
        assert ck["divergencia_absoluta"] == pytest.approx(1000.0)
        assert ck["sentido_m505"] == "superdeclarado"

    def test_bases_consistentes_nao_dispara(
        self, fixture_sprint5_cr34_negativo, tmp_path
    ):
        """C170 soma 1.000, M505 declara 1.000 → diferença=0 → CR-34 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr34_negativo, tmp_path)
        try:
            ops, divs = cruzamento_34_bc_cofins_vs_m505.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_periodo_sem_m505_retorna_vazio(self, tmp_path):
        """Período sem M505 e sem C170 crédito COFINS → CR-34 retorna listas vazias."""
        arq = tmp_path / "sem_m505.txt"
        arq.write_text(
            f"|0000|006|0||0|01032026|31032026|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_34_bc_cofins_vs_m505.executar(
                repo, conn, _CNPJ, 202603, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
