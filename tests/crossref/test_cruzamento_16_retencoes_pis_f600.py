"""
Testes do cruzamento CR-16 — Retenções PIS na fonte não-compensadas (F600).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  F600 com DT_RET=2024-06-01, VL_RET_APU=3000, VL_RET_PER=1000, VL_RET_DCOMP=500
  Saldo = 1500 > 0, não-prescrito → CR-16 dispara com impacto R$ 1.500.

Fixture negativo:
  F600 com VL_RET_PER=3000 (saldo=0) → CR-16 não dispara.

Fixture prescrito:
  F600 com DT_RET=2015-06-15 (5 anos expirados) → CR-16 não dispara (prescrito vai para CR-19).
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_16_retencoes_pis_f600
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2024


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento16RetencoesPis:
    def test_positivo_saldo_nao_compensado_gera_oportunidade(
        self, fixture_sprint3_f600_positivo, tmp_path
    ):
        """F600 com saldo positivo não-prescrito → CR-16 dispara com R$ 1.500."""
        repo, conn = _importar(fixture_sprint3_f600_positivo, tmp_path)
        try:
            ops, divs = cruzamento_16_retencoes_pis_f600.executar(
                repo, conn, _CNPJ, 202406, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-16"
        assert op.severidade == "alto"
        assert op.valor_impacto_conservador == Decimal("1500.00")
        assert op.valor_impacto_maximo == Decimal("1500.00")
        ev = op.evidencia[0]
        assert ev["registro"] == "F600"
        assert ev["campos_chave"]["saldo_nao_compensado"] == pytest.approx(1500.0)
        assert ev["campos_chave"]["cnpj_fonte_pag"] == "11222333000181"

    def test_negativo_saldo_zero_sem_oportunidade(
        self, fixture_sprint3_f600_negativo, tmp_path
    ):
        """F600 com VL_RET_PER = VL_RET_APU (saldo=0) → CR-16 não dispara."""
        repo, conn = _importar(fixture_sprint3_f600_negativo, tmp_path)
        try:
            ops, divs = cruzamento_16_retencoes_pis_f600.executar(
                repo, conn, _CNPJ, 202407, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_prescrito_nao_gera_cr16(
        self, fixture_sprint3_f600_prescrito, tmp_path
    ):
        """F600 com DT_RET 5+ anos atrás → prescrito → CR-16 ignora (CR-19 trata)."""
        repo, conn = _importar(fixture_sprint3_f600_prescrito, tmp_path)
        try:
            ops, divs = cruzamento_16_retencoes_pis_f600.executar(
                repo, conn, _CNPJ, 202408, _ANO
            )
        finally:
            conn.close()

        assert ops == []  # prescrito é ignorado pelo CR-16
        assert divs == []

    def test_periodo_sem_f600_retorna_vazio(self, tmp_path):
        """Período sem nenhum registro F600 → CR-16 retorna listas vazias."""
        arq = tmp_path / "sem_f600.txt"
        arq.write_text(
            f"|0000|006|0||0|01112024|30112024|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_16_retencoes_pis_f600.executar(
                repo, conn, _CNPJ, 202411, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
