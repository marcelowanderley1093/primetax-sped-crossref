"""
Testes do cruzamento CR-29 — Consistência vertical Σ M100.VL_CRED_DESC = M200.VL_TOT_CRED_DESC.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture consistente (negativo):
  M100 VL_CRED_DESC=500 → M200.VL_TOT_CRED_DESC=500 → diferença=0 → sem CR-29.

Fixture divergente (positivo):
  M100 VL_CRED_DESC=500 → M200.VL_TOT_CRED_DESC=700 → diferença=200 > 1 → CR-29 dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_3_consistencia import cruzamento_29_m100_m200_fluxo_pis
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


class TestCruzamento29M100M200FluxoPis:
    def test_consistente_sem_divergencia(
        self, fixture_sprint4_m100_consistente, tmp_path
    ):
        """Σ M100.VL_CRED_DESC = M200.VL_TOT_CRED_DESC → CR-29 não dispara."""
        repo, conn = _importar(fixture_sprint4_m100_consistente, tmp_path)
        try:
            ops, divs = cruzamento_29_m100_m200_fluxo_pis.executar(
                repo, conn, _CNPJ, 202509, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_divergente_gera_divergencia(
        self, fixture_sprint4_m100_divergente, tmp_path
    ):
        """M100 soma 500 mas M200 declara 700 → diferença 200 → CR-29 dispara."""
        repo, conn = _importar(fixture_sprint4_m100_divergente, tmp_path)
        try:
            ops, divs = cruzamento_29_m100_m200_fluxo_pis.executar(
                repo, conn, _CNPJ, 202510, _ANO
            )
        finally:
            conn.close()

        assert len(divs) == 1
        assert ops == []
        div = divs[0]
        assert div.codigo_regra == "CR-29"
        assert div.severidade == "medio"
        ev = div.evidencia[0]
        ck = ev["campos_chave"]
        assert ck["soma_vl_cred_desc_m100"] == pytest.approx(500.0)
        assert ck["vl_tot_cred_desc_m200"] == pytest.approx(700.0)
        assert ck["divergencia_absoluta"] == pytest.approx(200.0)

    def test_periodo_sem_m200_retorna_vazio(self, tmp_path):
        """Período sem M200 → CR-29 retorna listas vazias."""
        arq = tmp_path / "sem_m200.txt"
        arq.write_text(
            f"|0000|006|0||0|01122025|31122025|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_29_m100_m200_fluxo_pis.executar(
                repo, conn, _CNPJ, 202512, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
