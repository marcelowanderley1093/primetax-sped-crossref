"""
Testes do cruzamento CR-30 — Consistência vertical Σ M500.VL_CRED_DESC = M600.VL_TOT_CRED_DESC.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture consistente (negativo):
  M500 VL_CRED_DESC=500 → M600.VL_TOT_CRED_DESC=500 → diferença=0 → sem CR-30.

Fixture divergente (positivo):
  M500 VL_CRED_DESC=500 → M600.VL_TOT_CRED_DESC=800 → diferença=300 > 1 → CR-30 dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_3_consistencia import cruzamento_30_m500_m600_fluxo_cofins
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2025


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento30M500M600FluxoCofins:
    def test_consistente_sem_divergencia(
        self, fixture_sprint4_m100_consistente, tmp_path
    ):
        """Σ M500.VL_CRED_DESC = M600.VL_TOT_CRED_DESC → CR-30 não dispara."""
        repo, conn = _importar(fixture_sprint4_m100_consistente, tmp_path)
        try:
            ops, divs = cruzamento_30_m500_m600_fluxo_cofins.executar(
                repo, conn, _CNPJ, 202509, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_divergente_gera_divergencia(
        self, fixture_sprint4_m100_divergente, tmp_path
    ):
        """M500 soma 500 mas M600 declara 800 → diferença 300 → CR-30 dispara."""
        repo, conn = _importar(fixture_sprint4_m100_divergente, tmp_path)
        try:
            ops, divs = cruzamento_30_m500_m600_fluxo_cofins.executar(
                repo, conn, _CNPJ, 202510, _ANO
            )
        finally:
            conn.close()

        assert len(divs) == 1
        assert ops == []
        div = divs[0]
        assert div.codigo_regra == "CR-30"
        assert div.severidade == "medio"
        ev = div.evidencia[0]
        ck = ev["campos_chave"]
        assert ck["soma_vl_cred_desc_m500"] == pytest.approx(500.0)
        assert ck["vl_tot_cred_desc_m600"] == pytest.approx(800.0)
        assert ck["divergencia_absoluta"] == pytest.approx(300.0)
