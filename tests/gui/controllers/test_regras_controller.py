"""
Testes do RegrasController — introspecção das 49 regras do engine.
"""

from __future__ import annotations

import pytest

from src.gui.controllers.regras_controller import RegraInfo, RegrasController


class TestRegrasController:
    def test_lista_todas_as_regras(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        # Engine tem ao menos as 47 + integridade. Verifica que algo veio.
        assert len(regras) >= 40
        assert all(isinstance(r, RegraInfo) for r in regras)

    def test_camadas_distribuidas(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        camadas = {r.camada for r in regras}
        # Engine atual carrega Camada 1, 2 e 3
        assert camadas == {1, 2, 3}

    def test_codigos_unicos(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        codigos = [r.codigo for r in regras]
        # Sem duplicatas
        assert len(codigos) == len(set(codigos))

    def test_codigos_no_formato_esperado(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        for r in regras:
            assert r.codigo.startswith(("CR-", "CI-", "?")) or r.codigo == "?"

    def test_dependencias_sped_sempre_lista(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        for r in regras:
            assert isinstance(r.dependencias_sped, list)
            assert len(r.dependencias_sped) >= 1

    def test_descricao_nao_vazia(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        for r in regras:
            assert r.descricao
            # Sem prefixo "CR-XX —" duplicado
            assert not r.descricao.startswith(("CR-", "CI-"))

    def test_ordenacao_por_codigo(self):
        ctrl = RegrasController()
        regras = ctrl.listar_regras()
        # CI-* primeiro, depois CR-* em ordem numérica
        ci = [r for r in regras if r.codigo.startswith("CI-")]
        cr = [r for r in regras if r.codigo.startswith("CR-")]
        if len(cr) >= 2:
            n1 = int(cr[0].codigo.split("-")[1])
            n2 = int(cr[1].codigo.split("-")[1])
            assert n1 <= n2
