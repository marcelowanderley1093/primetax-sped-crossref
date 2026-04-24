"""
Testes do cruzamento CR-08 — Tese 69 em C181 (NFC-e consolidada).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  C181 com CST_PIS=01, VL_ITEM=50000, VL_DESC=0, VL_BC_PIS=50000
  Sinal: VL_DESC==0 com CST elegível → oportunidade qualitativa detectada.
  Impacto = 0 (quantificação requer EFD ICMS/IPI Sprint 6+).

Fixture negativo:
  C181 com VL_DESC=4500 (exclusão de ICMS feita via VL_DESC)
  VL_BC_PIS = VL_ITEM - VL_DESC = 45500 → base corretamente reduzida.
  Não deve gerar oportunidade.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_08_tese69_c181
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


class TestCruzamento08Tese69C181:
    def test_positivo_vl_desc_zero_detecta_oportunidade(
        self, fixture_sprint2_c181_positivo, tmp_path
    ):
        """C181 com VL_DESC=0 e CST_PIS=01 (saída) → CR-08 dispara."""
        repo, conn = _importar_e_abrir(fixture_sprint2_c181_positivo, tmp_path)
        try:
            ops, divs = cruzamento_08_tese69_c181.executar(
                repo, conn, "00000000000100", 202508, 2025
            )
        finally:
            conn.close()
        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-08"
        assert op.severidade == "medio"
        # Impacto qualitativo — Sprint 2 não calcula valor monetário sem EFD ICMS/IPI
        assert op.valor_impacto_conservador == Decimal("0")
        assert op.valor_impacto_maximo == Decimal("0")
        ev = op.evidencia[0]
        assert ev["cst_pis"] == "01"
        assert ev["sinal"] == "vl_desc_zero_com_cst_tese69"

    def test_negativo_vl_desc_preenchido_sem_oportunidade(
        self, fixture_sprint2_c181_negativo, tmp_path
    ):
        """C181 com VL_DESC > 0 (ICMS excluído via VL_DESC) → CR-08 não dispara."""
        repo, conn = _importar_e_abrir(fixture_sprint2_c181_negativo, tmp_path)
        try:
            ops, divs = cruzamento_08_tese69_c181.executar(
                repo, conn, "00000000000100", 202509, 2025
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []

    def test_cst_entrada_ignorada(self, tmp_path):
        """C181 com IND_OPER=0 (entrada) não deve gerar oportunidade CR-08."""
        arq = tmp_path / "c181_entrada.txt"
        arq.write_text(
            "|0000|006|0||0|01122025|31122025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            # C180 com IND_OPER=0 (entrada)
            "|C180|0|0|00000000000100|PART001|01122025|31122025|01|10000,00|165,00|0,00|760,00|0,00|65|\n"
            "|C181|01|1102|10000,00|0,00|10000,00|1,65|0,00|0,00|165,00|\n"
            "|C185|01|1102|10000,00|0,00|10000,00|7,60|0,00|0,00|760,00|\n"
            "|M200|0,00|0,00|0,00|0,00|10000,00|\n"
            "|M600|0,00|0,00|0,00|0,00|10000,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|C180|1|\n|9900|C181|1|\n|9900|C185|1|\n"
            "|9900|M200|1|\n|9900|M600|1|\n|9900|9900|9|\n|9900|9999|1|\n|9999|17|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, _ = cruzamento_08_tese69_c181.executar(
                repo, conn, "00000000000100", 202512, 2025
            )
        finally:
            conn.close()
        assert ops == []

    def test_cst_nao_elegivel_ignorado(self, tmp_path):
        """C181 com CST_PIS=06 (alíquota zero) não ativa Tese 69."""
        arq = tmp_path / "c181_cst06.txt"
        arq.write_text(
            "|0000|006|0||0|01012026|31012026|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|C180|1|0|00000000000100|PART001|01012026|31012026|01|10000,00|0,00|0,00|0,00|0,00|65|\n"
            "|C181|06|5102|10000,00|0,00|0,00|0,00|0,00|0,00|0,00|\n"
            "|C185|06|5102|10000,00|0,00|0,00|0,00|0,00|0,00|0,00|\n"
            "|M200|0,00|0,00|0,00|0,00|10000,00|\n"
            "|M600|0,00|0,00|0,00|0,00|10000,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|C180|1|\n|9900|C181|1|\n|9900|C185|1|\n"
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
            ops, _ = cruzamento_08_tese69_c181.executar(
                repo, conn, "00000000000100", 202601, 2026
            )
        finally:
            conn.close()
        assert ops == []
