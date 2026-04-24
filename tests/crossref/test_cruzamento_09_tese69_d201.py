"""
Testes do cruzamento CR-09 — Tese 69 em D201 (serviços de transporte).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  D201 com CST_PIS=01, VL_ITEM=20000, VL_BC_PIS=20000
  Sinal: VL_BC_PIS == VL_ITEM → ICMS não foi deduzido da base.

Fixture negativo:
  D201 com VL_BC_PIS=18000 < VL_ITEM=20000
  Base reduzida (ICMS deduzido) → não deve gerar oportunidade.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_09_tese69_d201
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes


def _importar_e_abrir(caminho: Path, tmp_path: Path):
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=db_dir,
    )
    repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
    conn = repo.conexao()
    return repo, conn


class TestCruzamento09Tese69D201:
    def test_positivo_vl_bc_igual_vl_item(
        self, fixture_sprint2_d201_positivo, tmp_path
    ):
        """D201 com VL_BC_PIS==VL_ITEM (saída) → CR-09 dispara."""
        repo, conn = _importar_e_abrir(fixture_sprint2_d201_positivo, tmp_path)
        try:
            ops, divs = cruzamento_09_tese69_d201.executar(
                repo, conn, "00000000000100", 202510, 2025
            )
        finally:
            conn.close()
        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-09"
        assert op.severidade == "medio"
        assert op.valor_impacto_conservador == Decimal("0")
        ev = op.evidencia[0]
        assert ev["cst_pis"] == "01"
        assert ev["sinal"] == "vl_bc_pis_igual_vl_item"
        assert ev["vl_item"] == pytest.approx(20000.0)

    def test_negativo_base_reduzida_sem_oportunidade(
        self, fixture_sprint2_d201_negativo, tmp_path
    ):
        """D201 com VL_BC_PIS < VL_ITEM (ICMS deduzido) → CR-09 não dispara."""
        repo, conn = _importar_e_abrir(fixture_sprint2_d201_negativo, tmp_path)
        try:
            ops, divs = cruzamento_09_tese69_d201.executar(
                repo, conn, "00000000000100", 202511, 2025
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []

    def test_cst_entrada_ignorada(self, tmp_path):
        """D201 com IND_OPER=0 (entrada) não deve gerar oportunidade."""
        arq = tmp_path / "d201_entrada.txt"
        arq.write_text(
            "|0000|006|0||0|01022026|28022026|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|D200|0|1||01022026|28022026|01|10000,00|\n"
            "|D201|01|10000,00|10000,00|1,65|0,00|0,00|165,00|\n"
            "|D205|01|10000,00|10000,00|7,60|0,00|0,00|760,00|\n"
            "|M200|0,00|0,00|0,00|0,00|10000,00|\n"
            "|M600|0,00|0,00|0,00|0,00|10000,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|D200|1|\n|9900|D201|1|\n|9900|D205|1|\n"
            "|9900|M200|1|\n|9900|M600|1|\n|9900|9900|9|\n|9900|9999|1|\n|9999|17|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2026, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, _ = cruzamento_09_tese69_d201.executar(
                repo, conn, "00000000000100", 202602, 2026
            )
        finally:
            conn.close()
        # IND_OPER=0 → entrada → não ativa Tese 69
        assert ops == []
