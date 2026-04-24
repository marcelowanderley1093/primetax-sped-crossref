"""
Testes do cruzamento CR-27 — Bens imobilizados com IND_UTIL=9 e crédito lançado.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  F120 IND_UTIL=9 (vedado), VL_PIS=82,50 → crédito indevido → CR-27 dispara como Divergencia.

Fixture negativo:
  F120 IND_UTIL=1 (produção), VL_PIS=82,50 → uso permitido → CR-27 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_27_imob_uso_vedado
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


class TestCruzamento27ImobUsoVedado:
    def test_ind_util_9_com_credito_gera_divergencia(
        self, fixture_sprint4_imob_vedado, tmp_path
    ):
        """F120 IND_UTIL=9 com VL_PIS=82,50 → CR-27 dispara como Divergencia."""
        repo, conn = _importar(fixture_sprint4_imob_vedado, tmp_path)
        try:
            ops, divs = cruzamento_27_imob_uso_vedado.executar(
                repo, conn, _CNPJ, 202507, _ANO
            )
        finally:
            conn.close()

        assert len(divs) == 1
        assert ops == []
        div = divs[0]
        assert div.codigo_regra == "CR-27"
        assert div.severidade == "alto"
        ev = div.evidencia[0]
        assert ev["campos_chave"]["ind_util_bem_imob"] == "9"
        assert ev["campos_chave"]["vl_pis_indevido"] == pytest.approx(82.50)

    def test_ind_util_1_permitido_sem_divergencia(
        self, fixture_sprint4_f120_negativo, tmp_path
    ):
        """F120 IND_UTIL=1 (produção) com VL_PIS=82,50 → CR-27 não dispara."""
        repo, conn = _importar(fixture_sprint4_f120_negativo, tmp_path)
        try:
            ops, divs = cruzamento_27_imob_uso_vedado.executar(
                repo, conn, _CNPJ, 202502, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
