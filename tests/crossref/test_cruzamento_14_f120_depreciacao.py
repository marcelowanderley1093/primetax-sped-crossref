"""
Testes do cruzamento CR-14 — Crédito sobre encargos de depreciação não aproveitado (F120).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  F120 IND_UTIL=1, VL_BC_PIS=5000, ALIQ_PIS=1,65, VL_PIS=0 → crédito de R$ 82,50 não aproveitado.

Fixture negativo:
  F120 IND_UTIL=1, VL_PIS=82,50 → crédito já aproveitado → CR-14 não dispara.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_14_f120_depreciacao
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


class TestCruzamento14F120Depreciacao:
    def test_credito_nao_aproveitado_gera_oportunidade(
        self, fixture_sprint4_f120_positivo, tmp_path
    ):
        """F120 VL_PIS=0 com VL_BC_PIS=5000 e ALIQ=1,65% → CR-14 dispara."""
        repo, conn = _importar(fixture_sprint4_f120_positivo, tmp_path)
        try:
            ops, divs = cruzamento_14_f120_depreciacao.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-14"
        assert op.severidade == "medio"
        ev = op.evidencia[0]
        assert ev["campos_chave"]["vl_bc_pis"] == pytest.approx(5000.0)
        assert ev["campos_chave"]["credito_pis_esperado"] == pytest.approx(82.50)
        assert ev["campos_chave"]["vl_pis_declarado"] == pytest.approx(0.0)
        assert op.valor_impacto_conservador == Decimal("82.50")

    def test_credito_ja_aproveitado_sem_oportunidade(
        self, fixture_sprint4_f120_negativo, tmp_path
    ):
        """F120 VL_PIS=82,50 → crédito já aproveitado → CR-14 não dispara."""
        repo, conn = _importar(fixture_sprint4_f120_negativo, tmp_path)
        try:
            ops, divs = cruzamento_14_f120_depreciacao.executar(
                repo, conn, _CNPJ, 202502, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_periodo_sem_f120_retorna_vazio(self, tmp_path):
        """Período sem nenhum F120 → CR-14 retorna listas vazias."""
        arq = tmp_path / "sem_f120.txt"
        arq.write_text(
            f"|0000|006|0||0|01112025|30112025|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_14_f120_depreciacao.executar(
                repo, conn, _CNPJ, 202511, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
