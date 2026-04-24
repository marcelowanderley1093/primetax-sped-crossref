"""
Testes do cruzamento CR-19 — Retenções prescritas ou com prescrição iminente.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Cenário positivo (prescrito):
  F600 DT_RET=2015-06-15, saldo=3000 → prescreve 2020-06-15 → já expirado → Divergencia.

Cenário negativo (não-prescrito, não-iminente):
  F600 DT_RET=2024-06-01, saldo=1500 → prescreve 2029-06-01 → mais de 12 meses → sem resultado.

Cenário de período não-recente:
  Dois períodos importados (202406, 202408) → CR-19 só executa no último (202408).
  Chamada com ano_mes=202406 → retorno vazio (skip early-return).
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_19_retencoes_prescritas
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2024


def _importar(caminho: Path, db_dir: Path) -> Repositorio:
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    return Repositorio(_CNPJ, _ANO, base_dir=db_dir)


class TestCruzamento19RetencaoPrescritas:
    def test_prescrito_gera_divergencia(
        self, fixture_sprint3_f600_prescrito, tmp_path
    ):
        """F600 DT_RET=2015-06-15 → prescrito → CR-19 retorna Divergencia severidade critico."""
        db_dir = tmp_path / "db"
        repo = _importar(fixture_sprint3_f600_prescrito, db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_19_retencoes_prescritas.executar(
                repo, conn, _CNPJ, 202408, _ANO
            )
        finally:
            conn.close()

        assert divs, "Deve haver pelo menos uma divergência de prescrição expirada"
        assert ops == []  # prescrito gera Divergencia, não Oportunidade
        div = divs[0]
        assert div.codigo_regra == "CR-19"
        assert div.severidade == "critico"
        assert "prescrita" in div.descricao.lower()
        assert "PIS" in div.descricao
        ev = div.evidencia[0]
        assert ev["campos_chave"]["tributo"] == "PIS"
        assert ev["campos_chave"]["saldo_perdido"] == pytest.approx(3000.0)

    def test_nao_prescrito_nao_iminente_sem_resultado(
        self, fixture_sprint3_f600_positivo, tmp_path
    ):
        """F600 DT_RET=2024-06-01 (prescreve 2029) → não dispara CR-19."""
        db_dir = tmp_path / "db"
        repo = _importar(fixture_sprint3_f600_positivo, db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_19_retencoes_prescritas.executar(
                repo, conn, _CNPJ, 202406, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_periodo_nao_recente_ignorado(
        self,
        fixture_sprint3_f600_positivo,
        fixture_sprint3_f600_prescrito,
        tmp_path,
    ):
        """Dois períodos importados — CR-19 ignora chamada com ano_mes < max."""
        db_dir = tmp_path / "db"
        # Importa período de junho (202406) e agosto (202408) no mesmo banco
        efd_contribuicoes.importar(
            fixture_sprint3_f600_positivo,
            encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir,
        )
        efd_contribuicoes.importar(
            fixture_sprint3_f600_prescrito,
            encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            # Chama com período MAIS ANTIGO (202406) — deve ignorar (202408 é o mais recente)
            ops, divs = cruzamento_19_retencoes_prescritas.executar(
                repo, conn, _CNPJ, 202406, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == [], "CR-19 deve ser silencioso para períodos não-recentes"

    def test_periodo_recente_com_prescrito_detecta(
        self,
        fixture_sprint3_f600_positivo,
        fixture_sprint3_f600_prescrito,
        tmp_path,
    ):
        """Mesmo banco com dois períodos — chamada no mais recente (202408) detecta prescrito."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint3_f600_positivo,
            encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir,
        )
        efd_contribuicoes.importar(
            fixture_sprint3_f600_prescrito,
            encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_19_retencoes_prescritas.executar(
                repo, conn, _CNPJ, 202408, _ANO  # período mais recente
            )
        finally:
            conn.close()

        # f600_prescrito tem DT_RET=2015-06-15 → prescrito → Divergencia
        assert len(divs) >= 1
