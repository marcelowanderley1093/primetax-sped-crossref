"""
Testes do DiagnosticoController — leitura síncrona + execução do motor.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from src.gui.controllers.diagnostico_controller import (
    DiagnosticoController,
    DiagnosticoView,
)


class TestCarregarDiagnosticoVazio:
    def test_banco_inexistente_retorna_view_vazia(self, qtbot, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctrl = DiagnosticoController()
        view = ctrl.carregar_diagnostico("00000000000999", 2025)
        assert isinstance(view, DiagnosticoView)
        assert view.total_oportunidades == 0
        assert view.total_divergencias == 0
        ctrl.shutdown()


class TestCarregarDiagnosticoComSpedReal:
    def test_le_oportunidades_de_fixture_importada(
        self, qtbot, fixture_tese69_positivo, tmp_path, monkeypatch
    ):
        # Importa fixture no tmp_path → cria banco real
        monkeypatch.chdir(tmp_path)
        from src.parsers import efd_contribuicoes
        efd_contribuicoes.importar(
            fixture_tese69_positivo,
            encoding_override="utf8",
            prompt_operador=False,
        )

        # Roda diagnóstico no main thread (sem worker)
        from src.crossref.engine import Motor
        from src.db.repo import Repositorio
        repo = Repositorio("00000000000100", 2025)
        motor = Motor(repo)
        motor.diagnosticar_ano(2025)

        ctrl = DiagnosticoController()
        view = ctrl.carregar_diagnostico("00000000000100", 2025)

        # Deve ter ao menos 1 oportunidade (CR-07 da Tese 69)
        assert view.total_oportunidades >= 1
        # Cruzamentos cobertos (49 do _METADATA_REGRAS)
        assert len(view.cruzamentos) >= 30
        # CR-07 deve aparecer com severidade alto
        cr07 = next((c for c in view.cruzamentos if c.codigo_regra == "CR-07"), None)
        assert cr07 is not None
        assert cr07.achados >= 1

        ctrl.shutdown()


class TestSeveridadeDominante:
    def test_alto_vence_medio(self):
        from src.gui.controllers.diagnostico_controller import DiagnosticoController as DC
        assert DC._severidade_dominante(["medio", "alto", "baixo"]) == "alto"

    def test_lista_vazia_retorna_ok(self):
        from src.gui.controllers.diagnostico_controller import DiagnosticoController as DC
        assert DC._severidade_dominante([]) == "ok"
