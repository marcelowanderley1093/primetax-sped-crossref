"""
Testes do ParecerController — listagem de teses + contagem por tese.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.gui.controllers.parecer_controller import ParecerController


class TestListarTeses:
    def test_retorna_lista_nao_vazia(self):
        teses = ParecerController.listar_teses()
        assert len(teses) >= 8
        codigos = {codigo for codigo, _ in teses}
        # Teses esperadas (Sprint do parecer)
        assert "tema-69" in codigos
        assert "insumos" in codigos
        assert "lei-do-bem" in codigos


class TestAchadosPorTese:
    def test_banco_inexistente_retorna_zeros(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        contagens = ParecerController.achados_por_tese("00000000000999", 2025)
        assert all(v == 0 for v in contagens.values())

    def test_tese69_conta_cr07_em_fixture_real(
        self, fixture_tese69_positivo, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        from src.parsers import efd_contribuicoes
        efd_contribuicoes.importar(
            fixture_tese69_positivo,
            encoding_override="utf8",
            prompt_operador=False,
        )
        from src.crossref.engine import Motor
        from src.db.repo import Repositorio
        Motor(Repositorio("00000000000100", 2025)).diagnosticar_ano(2025)

        contagens = ParecerController.achados_por_tese("00000000000100", 2025)
        # Tese 69 deve ter ao menos 1 achado (CR-07 da fixture)
        assert contagens.get("tema-69", 0) >= 1
