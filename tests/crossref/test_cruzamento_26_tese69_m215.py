"""
Testes do cruzamento CR-26 — Tese 69 via M215/M615 (ajuste de base agregado).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (reutiliza efd_contrib_tese69_positivo.txt):
  VL_ITEM=10000, VL_ICMS=1000, VL_BC_PIS=10000 (ICMS na base).
  Sem M215 → gap = 1000 → conservador = máximo = 92,50.

Fixture negativo (efd_contrib_sprint2_m215_negativo.txt):
  Mesma estrutura C170, mas com M215.VL_AJ_BC=1000 (IND_AJ_BC="0").
  ICMS totalmente declarado como redução de base → gap = 0 → sem oportunidade.

Condição de ativação:
  CR-26 só ativa para DT_INI >= 2019-01-01 (leiaute 3.1.0).
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_26_tese69_m215
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes
from src.rules.tese_69_ajuste_base import calcular_gap_m215


def _importar_e_abrir(caminho: Path, tmp_path: Path, ano_calendario: int = 2025):
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=db_dir,
    )
    repo = Repositorio("00000000000100", ano_calendario, base_dir=db_dir)
    conn = repo.conexao()
    return repo, conn


class TestCalcGapM215:
    """Testes unitários da função de cálculo (sem banco)."""

    def _c170(self, **kwargs) -> dict:
        base = {
            "cst_pis": "01",
            "vl_item": 10000.0,
            "vl_icms": 1000.0,
            "vl_bc_pis": 10000.0,
            "vl_pis": 165.0,
            "vl_bc_cofins": 10000.0,
            "vl_cofins": 760.0,
            "aliq_pis": 1.65,
            "aliq_cofins": 7.60,
        }
        base.update(kwargs)
        return base

    def test_positivo_sem_m215_gap_total(self):
        """Sem M215: gap = VL_ICMS inteiro → impacto = 92,50."""
        resultado = calcular_gap_m215([self._c170()], [], [], "2025-01-01")
        assert resultado is not None
        assert resultado["valor_impacto_conservador"] == Decimal("92.50")
        assert resultado["valor_impacto_maximo"] == Decimal("92.50")

    def test_negativo_m215_cobre_tudo_gap_zero(self):
        """M215.VL_AJ_BC == VL_ICMS → gap = 0 → sem oportunidade."""
        m215 = [{"vl_aj_bc": 1000.0}]
        m615 = [{"vl_aj_bc": 1000.0}]
        resultado = calcular_gap_m215([self._c170()], m215, m615, "2025-01-01")
        assert resultado is None

    def test_m215_parcial_gap_residual(self):
        """M215 cobre 600 de 1000 → gap = 400 → impacto conservador < máximo."""
        m215 = [{"vl_aj_bc": 600.0}]
        m615 = [{"vl_aj_bc": 600.0}]
        resultado = calcular_gap_m215([self._c170()], m215, m615, "2025-01-01")
        assert resultado is not None
        # conservador: gap 400 × (1,65% + 7,60%) = 400 × 9,25% = 37,00
        assert resultado["valor_impacto_conservador"] == Decimal("37.00")
        # máximo: icms 1000 × 9,25% = 92,50
        assert resultado["valor_impacto_maximo"] == Decimal("92.50")

    def test_periodo_anterior_2019_nao_ativa(self):
        """CR-26 não deve ativar para DT_INI < 2019-01-01."""
        resultado = calcular_gap_m215([self._c170()], [], [], "2018-12-01")
        assert resultado is None

    def test_sem_itens_elegiveis_nao_ativa(self):
        """C170 sem CSTs elegíveis → sem oportunidade."""
        item_nao_elegivel = self._c170(cst_pis="06")
        resultado = calcular_gap_m215([item_nao_elegivel], [], [], "2025-01-01")
        assert resultado is None


class TestCruzamento26ComBanco:
    """Testes de integração com banco SQLite real."""

    def test_positivo_sem_m215_oportunidade_detectada(
        self, fixture_tese69_positivo, tmp_path
    ):
        """Fixture tese69_positivo: VL_ICMS=1000, sem M215 → CR-26 dispara."""
        repo, conn = _importar_e_abrir(fixture_tese69_positivo, tmp_path)
        try:
            ops, divs = cruzamento_26_tese69_m215.executar(
                repo, conn, "00000000000100", 202501, 2025
            )
        finally:
            conn.close()
        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-26"
        assert op.severidade == "alto"
        assert op.valor_impacto_conservador == Decimal("92.50")
        assert op.valor_impacto_maximo == Decimal("92.50")

    def test_negativo_m215_cobre_icms_sem_oportunidade(
        self, fixture_sprint2_m215_negativo, tmp_path
    ):
        """M215.VL_AJ_BC == VL_ICMS → gap = 0 → CR-26 não dispara."""
        repo, conn = _importar_e_abrir(fixture_sprint2_m215_negativo, tmp_path)
        try:
            ops, divs = cruzamento_26_tese69_m215.executar(
                repo, conn, "00000000000100", 202503, 2025
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []
