"""
Testes da view T7 (Parecer Word) — usa controller stub.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Signal

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.threading.parecer_worker import ResultadoParecer
from src.gui.views.t7_parecer import T7Parecer


class _StubController(QObject):
    iniciado = Signal(str, int, str)
    log_event = Signal(str, str)
    concluido = Signal(object)

    def __init__(self, contagens: dict | None = None):
        super().__init__()
        self._contagens = contagens or {
            "tema-69": 12,
            "insumos": 0,
            "retencoes": 5,
            "imobilizado": 0,
            "prescricao-quinquenal": 0,
            "lei-14789-subvencoes": 0,
            "compensacao-prejuizos": 0,
            "creditos-extemporaneos": 0,
            "lei-do-bem": 1,
        }
        self.disparos: list[tuple] = []

    def listar_teses(self):
        # Só retorna os códigos presentes em _contagens (mesmo formato real)
        from src.reports.word_parecer import _TESES
        return [(c, _TESES.get(c, {})) for c in self._contagens]

    def achados_por_tese(self, cnpj, ano):
        return dict(self._contagens)

    def gerar(self, cnpj, ano, tese, destino, consultor):
        self.disparos.append((cnpj, ano, tese, destino, consultor))

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


class TestT7SemCliente:
    def test_inicial_mostra_empty(self, qtbot):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        assert t7._stack.currentWidget() is t7._empty


class TestT7ComCliente:
    def test_carregar_cliente_popula_combo(self, qtbot):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.carregar_cliente(_cliente())
        assert t7._stack.currentWidget() is t7._conteudo
        # 9 teses no stub (mesma quantidade do _TESES real)
        assert t7._combo_tese.count() == 9

    def test_tese_com_mais_achados_fica_em_primeiro(self, qtbot):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.carregar_cliente(_cliente())
        # tema-69 tem 12 achados (maior); deve ser o primeiro
        assert t7._combo_tese.itemData(0) == "tema-69"

    def test_label_inclui_contagem_de_achados(self, qtbot):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.carregar_cliente(_cliente())
        primeiro = t7._combo_tese.itemText(0)
        assert "12 achado" in primeiro

    def test_zero_achados_total_mostra_aviso(self, qtbot):
        ctrl = _StubController(contagens={
            "tema-69": 0, "insumos": 0, "retencoes": 0,
            "imobilizado": 0, "prescricao-quinquenal": 0,
            "lei-14789-subvencoes": 0, "compensacao-prejuizos": 0,
            "creditos-extemporaneos": 0, "lei-do-bem": 0,
        })
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.carregar_cliente(_cliente())
        assert t7._aviso_widget is not None

    def test_consultor_persistido_em_qsettings(self, qtbot):
        from PySide6.QtCore import QSettings
        s = QSettings("Primetax Solutions", "SpedCrossref")
        s.setValue("Parecer/consultor", "Marcelo Wanderley")
        try:
            ctrl = _StubController()
            t7 = T7Parecer(controller=ctrl)
            qtbot.addWidget(t7)
            assert t7._input_consultor.text() == "Marcelo Wanderley"
        finally:
            s.remove("Parecer/consultor")

    def test_gerar_dispara_controller(self, qtbot, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.carregar_cliente(_cliente())
        t7._on_gerar_clicado()

        assert len(ctrl.disparos) == 1
        cnpj, ano, tese, destino, consultor = ctrl.disparos[0]
        assert cnpj == "00000000000100"
        assert ano == 2025
        assert tese == "tema-69"
        assert "parecer_tema_69.docx" in str(destino)

    def test_concluido_sucesso_emite_signal(self, qtbot, tmp_path):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.show()  # Toast precisa de window()
        t7.carregar_cliente(_cliente())
        t7._on_gerar_clicado()

        destino_falso = tmp_path / "parecer.docx"
        destino_falso.write_bytes(b"docx fake")

        with qtbot.waitSignal(t7.parecer_gerado, timeout=500) as blocker:
            ctrl.concluido.emit(ResultadoParecer(
                cnpj="00000000000100", ano_calendario=2025,
                tese="tema-69", sucesso=True, destino=destino_falso,
            ))
        assert blocker.args[0] == destino_falso
        assert t7._em_execucao is False

    def test_concluido_falha_nao_quebra(self, qtbot):
        ctrl = _StubController()
        t7 = T7Parecer(controller=ctrl)
        qtbot.addWidget(t7)
        t7.show()
        t7.carregar_cliente(_cliente())
        t7._on_gerar_clicado()

        ctrl.concluido.emit(ResultadoParecer(
            cnpj="00000000000100", ano_calendario=2025,
            tese="tema-69", sucesso=False, mensagem="erro qualquer",
        ))
        assert t7._em_execucao is False
        assert t7._btn_gerar.isEnabled()
