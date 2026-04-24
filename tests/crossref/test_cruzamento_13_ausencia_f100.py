"""
Testes do cruzamento CR-13 — Ausência de F100 em empresa não-cumulativa com receita.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  0110 COD_INC_TRIB=1 + M200 VL_REC_BRT_TOTAL=500.000 + sem F100 →
  CR-13 dispara (Oportunidade analítica).

Fixture negativo (202602):
  Mesmo regime + M200 com receita + F100 presente →
  CR-13 não dispara (empresa já declarou F100).
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_13_ausencia_f100
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


class TestCruzamento13AusenciaF100:
    def test_nao_cumulativo_sem_f100_gera_oportunidade(
        self, fixture_sprint5_cr13_positivo, tmp_path
    ):
        """Não-cumulativo com receita mas sem F100 → CR-13 sinaliza ausência analítica."""
        repo, conn = _importar(fixture_sprint5_cr13_positivo, tmp_path)
        try:
            ops, divs = cruzamento_13_ausencia_f100.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-13"
        assert op.severidade == "baixo"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cod_inc_trib"] == "1"
        assert ck["vl_rec_brt_total"] > 0.0
        assert ck["qtd_f100"] == 0

    def test_com_f100_nao_dispara(
        self, fixture_sprint5_cr13_negativo, tmp_path
    ):
        """F100 presente no período → CR-13 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr13_negativo, tmp_path)
        try:
            ops, divs = cruzamento_13_ausencia_f100.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_cumulativo_nao_dispara(self, tmp_path):
        """COD_INC_TRIB != '1' (regime cumulativo) → CR-13 não dispara."""
        arq = tmp_path / "cumulativo.txt"
        arq.write_text(
            f"|0000|006|0||0|01032026|31032026|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|3|1|0|0|\n"  # COD_INC_TRIB=3 (cumulativo)
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_13_ausencia_f100.executar(
                repo, conn, _CNPJ, 202603, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
