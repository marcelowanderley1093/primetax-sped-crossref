"""
Testes do cruzamento CR-25 — Saldo de crédito acumulado disponível (1100/1500).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  1100 SLD_CRED_FIM=50.000 + 1500 SLD_CRED_FIM=230.000 →
  CR-25 gera 2 Oportunidades (ambas severidade 'alto').

Fixture negativo (202602):
  1100 SLD_CRED_FIM=0 + 1500 SLD_CRED_FIM=0 → CR-25 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_25_saldo_credito_1100
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


class TestCruzamento25SaldoCredito1100:
    def test_saldo_acumulado_gera_oportunidades(
        self, fixture_sprint5_cr25_positivo, tmp_path
    ):
        """1100 e 1500 com SLD_CRED_FIM > R$ 10.000 → CR-25 gera 2 oportunidades 'alto'."""
        repo, conn = _importar(fixture_sprint5_cr25_positivo, tmp_path)
        try:
            ops, divs = cruzamento_25_saldo_credito_1100.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 2
        assert divs == []
        for op in ops:
            assert op.codigo_regra == "CR-25"
            assert op.severidade == "alto"

        pis_op = next(o for o in ops if o.evidencia[0]["registro"] == "1100")
        cofins_op = next(o for o in ops if o.evidencia[0]["registro"] == "1500")
        assert pis_op.evidencia[0]["campos_chave"]["sld_cred_fim"] == pytest.approx(50000.0)
        assert cofins_op.evidencia[0]["campos_chave"]["sld_cred_fim"] == pytest.approx(230000.0)

    def test_saldo_zero_nao_dispara(
        self, fixture_sprint5_cr25_negativo, tmp_path
    ):
        """1100 e 1500 com SLD_CRED_FIM=0 → CR-25 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr25_negativo, tmp_path)
        try:
            ops, divs = cruzamento_25_saldo_credito_1100.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
