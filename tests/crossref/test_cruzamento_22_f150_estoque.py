"""
Testes do cruzamento CR-22 — Crédito presumido sobre estoque de abertura não aproveitado (F150).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  F150 VL_BC_MEN_EST=10.000, VL_CRED_PIS=0 → crédito PIS de R$ 65,00 (0,65%) não aproveitado.

Fixture negativo:
  F150 VL_CRED_PIS=65,00 → crédito já aproveitado → CR-22 não dispara.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_22_f150_estoque
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


class TestCruzamento22F150Estoque:
    def test_credito_nao_aproveitado_gera_oportunidade(
        self, fixture_sprint4_f150_positivo, tmp_path
    ):
        """F150 VL_CRED_PIS=0 com VL_BC_MEN_EST=10.000 → CR-22 dispara."""
        repo, conn = _importar(fixture_sprint4_f150_positivo, tmp_path)
        try:
            ops, divs = cruzamento_22_f150_estoque.executar(
                repo, conn, _CNPJ, 202505, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-22"
        assert op.severidade == "medio"
        ev = op.evidencia[0]
        assert ev["campos_chave"]["vl_bc_men_est"] == pytest.approx(10000.0)
        assert ev["campos_chave"]["credito_pis_esperado"] == pytest.approx(65.0)
        assert ev["campos_chave"]["vl_cred_pis_declarado"] == pytest.approx(0.0)
        assert op.valor_impacto_conservador == Decimal("65.00")

    def test_credito_ja_aproveitado_sem_oportunidade(
        self, fixture_sprint4_f150_negativo, tmp_path
    ):
        """F150 VL_CRED_PIS=65,00 → já aproveitado → CR-22 não dispara."""
        repo, conn = _importar(fixture_sprint4_f150_negativo, tmp_path)
        try:
            ops, divs = cruzamento_22_f150_estoque.executar(
                repo, conn, _CNPJ, 202506, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
