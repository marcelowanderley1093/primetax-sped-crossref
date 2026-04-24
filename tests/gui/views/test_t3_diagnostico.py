"""
Testes da view T3 (Diagnóstico) — usa controller stub.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.diagnostico_controller import (
    CruzamentoRow,
    DiagnosticoView,
)
from src.gui.threading.diagnostico_worker import ResultadoDiagnostico
from src.gui.views.t3_diagnostico import T3Diagnostico


class _StubController(QObject):
    diagnostico_iniciado = Signal(str, int)
    diagnostico_log = Signal(str, str)
    diagnostico_concluido = Signal(object)

    def __init__(self, view: DiagnosticoView | None = None):
        super().__init__()
        self._view = view or DiagnosticoView(
            total_oportunidades=0, total_divergencias=0,
            impacto_conservador_total=Decimal("0"),
            impacto_maximo_total=Decimal("0"),
            pendencias_recuperaveis=0, limitacoes_estruturais=0,
            cruzamentos=[],
        )
        self.solicitacoes = []

    def carregar_diagnostico(self, cnpj, ano):
        return self._view

    def diagnosticar(self, cnpj, ano):
        self.solicitacoes.append((cnpj, ano))

    def shutdown(self):
        pass


def _cliente() -> ClienteRow:
    return ClienteRow(
        cnpj="00000000000100",
        razao_social="ACME SA",
        ano_calendario=2025,
        speds_importados=["EFD-Contrib"],
        impacto_total=Decimal("0"),
        ultima_atividade=datetime(2025, 4, 24),
        banco_path=Path("/tmp/x.sqlite"),
    )


class TestT3SemCliente:
    def test_inicial_mostra_empty_state(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        assert t3._stack.currentWidget() is t3._empty
        assert not t3._btn_rerodar.isEnabled()


class TestT3ComCliente:
    def test_carregar_cliente_atualiza_titulo(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.carregar_cliente(_cliente())
        assert "ACME SA" in t3._titulo.text()
        assert "2025" in t3._titulo.text()

    def test_carregar_cliente_mostra_conteudo(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.carregar_cliente(_cliente())
        assert t3._stack.currentWidget() is t3._conteudo
        assert t3._btn_rerodar.isEnabled()

    def test_view_com_oportunidades_popula_cards(self, qtbot):
        view = DiagnosticoView(
            total_oportunidades=12,
            total_divergencias=3,
            impacto_conservador_total=Decimal("847520"),
            impacto_maximo_total=Decimal("1200000"),
            pendencias_recuperaveis=8,
            limitacoes_estruturais=2,
            cruzamentos=[
                CruzamentoRow("CR-07", "Tese 69", "alto", 127, Decimal("523000")),
                CruzamentoRow("CR-19", "Retenções", "alto", 2, Decimal("45000")),
            ],
        )
        ctrl = _StubController(view=view)
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.carregar_cliente(_cliente())
        assert "12" in t3._card_op._primary.text()
        assert "3" in t3._card_div._primary.text()
        assert "8" in t3._card_pend._primary.text()
        assert "2" in t3._card_lim._primary.text()

    def test_rerodar_chama_controller(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.carregar_cliente(_cliente())
        t3._rerodar()
        assert ctrl.solicitacoes == [("00000000000100", 2025)]
        assert t3._em_execucao is True
        assert not t3._btn_rerodar.isEnabled()

    def test_rerodar_concluido_sucesso_emite_signal(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.show()  # window() necessária para Toast
        t3.carregar_cliente(_cliente())
        t3._rerodar()

        with qtbot.waitSignal(t3.rerodada_concluida, timeout=500):
            ctrl.diagnostico_concluido.emit(ResultadoDiagnostico(
                cnpj="00000000000100",
                ano_calendario=2025,
                sucesso=True,
                sumario={"meses": [
                    {"oportunidades_camada2": 10, "divergencias_camada1": 2},
                ]},
            ))
        assert t3._em_execucao is False

    def test_rerodar_concluido_falha_nao_quebra(self, qtbot):
        ctrl = _StubController()
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.show()
        t3.carregar_cliente(_cliente())
        t3._rerodar()

        ctrl.diagnostico_concluido.emit(ResultadoDiagnostico(
            cnpj="00000000000100",
            ano_calendario=2025,
            sucesso=False,
            mensagem="erro qualquer",
        ))
        assert t3._em_execucao is False
        assert t3._btn_rerodar.isEnabled()

    def test_aviso_inline_quando_sem_diagnostico(self, qtbot):
        # Simula cliente importado mas ainda não diagnosticado:
        # cruzamentos todos em "pendente"
        view = DiagnosticoView(
            total_oportunidades=0, total_divergencias=0,
            impacto_conservador_total=Decimal("0"),
            impacto_maximo_total=Decimal("0"),
            pendencias_recuperaveis=2, limitacoes_estruturais=0,
            cruzamentos=[
                CruzamentoRow("CR-01", "Integridade", "pendente", 0, Decimal("0")),
                CruzamentoRow("CR-07", "Tese 69", "pendente", 0, Decimal("0")),
            ],
        )
        ctrl = _StubController(view=view)
        t3 = T3Diagnostico(controller=ctrl)
        qtbot.addWidget(t3)
        t3.carregar_cliente(_cliente())
        # Inline aviso deve estar presente
        assert t3._inline_aviso is not None
