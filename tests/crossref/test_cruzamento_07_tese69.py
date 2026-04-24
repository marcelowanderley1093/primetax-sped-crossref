"""
Testes do cruzamento 07 — Tese 69 (ICMS na base de PIS/COFINS em C170).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Opção (b): dois valores paralelos — conservador (VL_ICMS) e máximo (VL_ICMS+ST).

Fixture positivo:
  VL_ITEM=10000, VL_DESC=0, VL_ICMS=1000, VL_ICMS_ST=0
  VL_BC_PIS=10000 (ICMS incluído na base — não deduziu os 1000)
  Delta conservador = 10000 - (10000 - 0 - 1000) = 1000
  PIS recuperável = 1000 × 1,65% = 16,50
  COFINS recuperável = 1000 × 7,60% = 76,00
  Impacto conservador = 92,50

Fixture negativo:
  VL_ITEM=10000, VL_DESC=0, VL_ICMS=1000, VL_BC_PIS=9000
  Base correta declarada — sem oportunidade.
"""

from decimal import Decimal

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_07_tese69_c170
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes
from src.rules.tese_69_icms import calcular_oportunidade_item


def _importar_e_abrir(caminho, tmp_path):
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


class TestCalcOportunidadeItem:
    """Testes unitários da função de cálculo (sem banco)."""

    def _item(self, **kwargs) -> dict:
        base = {
            "cst_pis": "01",
            "cst_cofins": "01",
            "vl_item": 10000.0,
            "vl_desc": 0.0,
            "vl_icms": 1000.0,
            "vl_icms_st": 0.0,
            "vl_bc_pis": 10000.0,
            "vl_bc_cofins": 10000.0,
            "aliq_pis": 1.65,
            "aliq_cofins": 7.60,
            "num_item": "01",
            "cod_item": "PROD001",
            "arquivo_origem": "teste.txt",
            "linha_arquivo": 5,
            "cnpj_declarante": "00000000000100",
            "ano_mes": 202501,
            "c100_linha_arquivo": 3,
        }
        base.update(kwargs)
        return base

    def test_positivo_icms_na_base_gera_oportunidade(self):
        """ICMS na base → oportunidade com impacto > 0."""
        resultado = calcular_oportunidade_item(self._item())
        assert resultado is not None
        # Delta = 1000, PIS = 1000 × 1.65% = 16.50
        # COFINS = 1000 × 7.60% = 76.00, total = 92.50
        assert resultado["valor_impacto_conservador"] == Decimal("92.50")
        assert resultado["valor_impacto_maximo"] == Decimal("92.50")

    def test_negativo_icms_fora_da_base_nenhuma_oportunidade(self):
        """VL_BC_PIS = VL_ITEM - VL_ICMS → sem oportunidade."""
        resultado = calcular_oportunidade_item(self._item(vl_bc_pis=9000.0, vl_bc_cofins=9000.0))
        assert resultado is None

    def test_cst_fora_tese69_ignorado(self):
        """CST 06 (alíquota zero) não está em CST_TESE_69 → sem oportunidade."""
        resultado = calcular_oportunidade_item(self._item(cst_pis="06"))
        assert resultado is None

    def test_cst_99_ignorado(self):
        """CST 99 (outras entradas) não ativa Tese 69."""
        resultado = calcular_oportunidade_item(self._item(cst_pis="99"))
        assert resultado is None

    def test_positivo_com_icms_st_opcao_b(self):
        """Com VL_ICMS_ST: conservador usa só VL_ICMS, máximo usa VL_ICMS+ST."""
        resultado = calcular_oportunidade_item(
            self._item(vl_icms=800.0, vl_icms_st=200.0, vl_bc_pis=10000.0, vl_bc_cofins=10000.0)
        )
        assert resultado is not None
        # Conservador: delta = 10000 - (10000 - 800) = 800
        #   PIS = 800 × 0.0165 = 13.20, COFINS = 800 × 0.076 = 60.80 → 74.00
        assert resultado["valor_impacto_conservador"] == Decimal("74.00")
        # Máximo: delta = 10000 - (10000 - 800 - 200) = 1000
        #   PIS = 1000 × 0.0165 = 16.50, COFINS = 1000 × 0.076 = 76.00 → 92.50
        assert resultado["valor_impacto_maximo"] == Decimal("92.50")

    def test_cst_02_ativa_tese69(self):
        """CST 02 está em CST_TESE_69 — deve gerar oportunidade."""
        resultado = calcular_oportunidade_item(self._item(cst_pis="02"))
        assert resultado is not None

    def test_cst_03_ativa_tese69(self):
        """CST 03 está em CST_TESE_69 — deve gerar oportunidade."""
        resultado = calcular_oportunidade_item(self._item(cst_pis="03"))
        assert resultado is not None

    def test_cst_05_ativa_tese69(self):
        """CST 05 está em CST_TESE_69 — deve gerar oportunidade."""
        resultado = calcular_oportunidade_item(self._item(cst_pis="05"))
        assert resultado is not None

    def test_evidencia_contem_campos_chave(self):
        """Evidência deve conter todos os campos necessários para rastreabilidade."""
        resultado = calcular_oportunidade_item(self._item())
        assert resultado is not None
        ev = resultado["evidencia"]
        assert ev["arquivo_origem"] == "teste.txt"
        assert ev["linha_arquivo"] == 5
        assert ev["bloco"] == "C"
        assert ev["registro"] == "C170"
        chave = ev["campos_chave"]
        assert "vl_icms" in chave
        assert "vl_bc_pis_declarado" in chave
        assert "base_sem_icms_proprio" in chave


class TestCruzamento07ComBanco:
    """Testes de integração com banco SQLite real (usando tmp_path)."""

    def test_positivo_oportunidade_detectada(self, fixture_tese69_positivo, tmp_path):
        """Fixture positivo: ICMS na base → cruzamento 07 dispara."""
        repo, conn = _importar_e_abrir(fixture_tese69_positivo, tmp_path)
        try:
            ops, divs = cruzamento_07_tese69_c170.executar(
                repo, conn, "00000000000100", 202501, 2025
            )
        finally:
            conn.close()
        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-07"
        assert op.severidade == "alto"
        assert op.valor_impacto_conservador == Decimal("92.50")

    def test_negativo_base_correta_sem_oportunidade(self, fixture_tese69_negativo, tmp_path):
        """Fixture negativo: ICMS já excluído da base → nenhuma oportunidade."""
        repo, conn = _importar_e_abrir(fixture_tese69_negativo, tmp_path)
        try:
            ops, divs = cruzamento_07_tese69_c170.executar(
                repo, conn, "00000000000100", 202501, 2025
            )
        finally:
            conn.close()
        assert len(ops) == 0
        assert divs == []

    def test_somente_saidas_ativam_regra(self, tmp_path):
        """Entrada (IND_OPER=0) com CST 01 não deve gerar oportunidade."""
        arq = tmp_path / "entrada_cst01.txt"
        arq.write_text(
            "|0000|006|0||0|01072025|31072025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|C100|0|0|FORN001|55|00|001|000001240|||01072025|10000,00|\n"
            "|C170|01|PROD001||1|UN|10000,00|0,00||00|1102||1000,00|10,00|1000,00||0,00|0,00||00|||0,00|0,00|50|10000,00|1,65|0,00|0,00|165,00|50|10000,00|7,60|0,00|0,00|760,00||\n"
            "|M200|0,00|0,00|0,00|0,00|0,00|\n"
            "|M600|0,00|0,00|0,00|0,00|0,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|C100|1|\n|9900|C170|1|\n"
            "|9900|M200|1|\n|9900|M600|1|\n|9900|9900|7|\n|9900|9999|1|\n|9999|15|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, _ = cruzamento_07_tese69_c170.executar(
                repo, conn, "00000000000100", 202507, 2025
            )
        finally:
            conn.close()
        # CST 50 (crédito de entrada) — não está em CST_TESE_69, e é entrada
        assert len(ops) == 0
