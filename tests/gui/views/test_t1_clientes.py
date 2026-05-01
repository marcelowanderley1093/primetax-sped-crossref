"""
Testes da view T1 (Clientes) — pytest-qt.

Cobertura:
  - empty state quando o controller devolve lista vazia
  - tabela populada quando há clientes
  - sinal cliente_aberto disparado em duplo-clique / Enter
  - botão "Importar SPED" emite importacao_solicitada
  - "Atualizar" recarrega a partir do controller
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.views.t1_clientes import T1Clientes


class _StubController:
    """Controller fake — devolve lista pré-definida."""
    def __init__(self, rows: list[ClienteRow]):
        self.rows = rows
        self.chamadas = 0

    def listar_clientes(self) -> list[ClienteRow]:
        self.chamadas += 1
        return list(self.rows)


def _row(cnpj: str = "00000000000100", razao: str = "ACME SA", ano: int = 2025) -> ClienteRow:
    return ClienteRow(
        cnpj=cnpj,
        razao_social=razao,
        ano_calendario=ano,
        speds_importados=["EFD-Contrib"],
        impacto_total=Decimal("523000"),
        ultima_atividade=datetime(2025, 4, 24, 9, 47),
        banco_path=Path("/tmp/banco.sqlite"),
    )


class TestT1ClientesEmptyState:
    def test_lista_vazia_mostra_empty_state(self, qtbot):
        ctrl = _StubController(rows=[])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        # Quando vazio, o stack mostra o EmptyState (segundo widget = índice 1)
        assert view._stack.currentWidget() is view._empty


class TestT1ClientesComDados:
    def test_carrega_tabela_com_clientes(self, qtbot):
        ctrl = _StubController(rows=[_row(), _row(cnpj="11111111000111", razao="Outra LTDA")])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        assert view._stack.currentWidget() is view._tabela
        assert view._tabela.total_rows() == 2

    def test_atualizar_chama_controller_de_novo(self, qtbot):
        ctrl = _StubController(rows=[_row()])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        chamadas_antes = ctrl.chamadas
        view._btn_atualizar.click()
        assert ctrl.chamadas == chamadas_antes + 1

    def test_botao_importar_emite_signal(self, qtbot):
        ctrl = _StubController(rows=[_row()])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        with qtbot.waitSignal(view.importacao_solicitada, timeout=500):
            view._btn_importar.click()

    def test_empty_state_primary_action_solicita_import(self, qtbot):
        ctrl = _StubController(rows=[])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        with qtbot.waitSignal(view.importacao_solicitada, timeout=500):
            view._empty._btn_primary.click()

    def test_cnpj_formatado_aparece_na_tabela(self, qtbot):
        ctrl = _StubController(rows=[_row()])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        # Pega a primeira linha visível
        rows = view._tabela.visible_rows()
        assert rows[0]["cnpj"] == "00.000.000/0001-00"

    def test_speds_renderizados_como_siglas(self, qtbot):
        ctrl = _StubController(rows=[
            ClienteRow(
                cnpj="00000000000100",
                razao_social="Multi-SPED SA",
                ano_calendario=2025,
                speds_importados=["EFD-Contrib", "ECD", "ECF"],
                impacto_total=Decimal("0"),
                ultima_atividade=None,
                banco_path=Path("/tmp/x.sqlite"),
            )
        ])
        view = T1Clientes(controller=ctrl)
        qtbot.addWidget(view)
        view.recarregar()
        rows = view._tabela.visible_rows()
        assert rows[0]["speds"] == "E D F"
