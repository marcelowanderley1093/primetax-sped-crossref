"""
Testes do cruzamento CR-15 — Crédito sobre valor de aquisição do imobilizado não aproveitado (F130).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  F130 IND_UTIL=1, VL_BC_PIS=5000, ALIQ_PIS=1,65, VL_PIS=0 → crédito de R$ 82,50 não aproveitado.

Fixture negativo:
  F130 IND_UTIL=1, VL_PIS=82,50 → crédito já aproveitado → CR-15 não dispara.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_15_f130_aquisicao
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


class TestCruzamento15F130Aquisicao:
    def test_credito_nao_aproveitado_gera_oportunidade(
        self, fixture_sprint4_f130_positivo, tmp_path
    ):
        """F130 VL_PIS=0 com VL_BC_PIS=5000 → crédito de R$ 82,50 não aproveitado."""
        repo, conn = _importar(fixture_sprint4_f130_positivo, tmp_path)
        try:
            ops, divs = cruzamento_15_f130_aquisicao.executar(
                repo, conn, _CNPJ, 202503, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-15"
        assert op.severidade == "medio"
        ev = op.evidencia[0]
        assert ev["campos_chave"]["credito_pis_esperado"] == pytest.approx(82.50)
        assert ev["campos_chave"]["vl_pis_declarado"] == pytest.approx(0.0)
        assert op.valor_impacto_conservador == Decimal("82.50")

    def test_credito_ja_aproveitado_sem_oportunidade(
        self, fixture_sprint4_f130_negativo, tmp_path
    ):
        """F130 VL_PIS=82,50 → já aproveitado → CR-15 não dispara."""
        repo, conn = _importar(fixture_sprint4_f130_negativo, tmp_path)
        try:
            ops, divs = cruzamento_15_f130_aquisicao.executar(
                repo, conn, _CNPJ, 202504, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
