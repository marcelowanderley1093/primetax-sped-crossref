"""
Testes do cruzamento CR-18 — Crédito PIS/COFINS recebido em evento corporativo (F800).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  F800 VL_CRED_PIS_TRANS=50.000 → CR-18 sinaliza crédito recebido para verificação.

Fixture negativo (202602):
  F800 VL_CRED_PIS_TRANS=0 → CR-18 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_18_f800_evento_corporativo
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


class TestCruzamento18F800EventoCorporativo:
    def test_credito_transferido_gera_oportunidade(
        self, fixture_sprint5_cr18_positivo, tmp_path
    ):
        """F800 com VL_CRED_PIS_TRANS > 0 → CR-18 sinaliza crédito para verificar aproveitamento."""
        repo, conn = _importar(fixture_sprint5_cr18_positivo, tmp_path)
        try:
            ops, divs = cruzamento_18_f800_evento_corporativo.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-18"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["vl_cred_pis_trans"] == pytest.approx(50000.0)

    def test_f800_sem_credito_nao_dispara(
        self, fixture_sprint5_cr18_negativo, tmp_path
    ):
        """F800 com VL_CRED_PIS_TRANS=0 → CR-18 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr18_negativo, tmp_path)
        try:
            ops, divs = cruzamento_18_f800_evento_corporativo.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
