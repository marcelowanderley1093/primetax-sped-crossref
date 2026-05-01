"""Testes do ProgressIndicator (Bloco 5 §C9)."""

from __future__ import annotations

from src.gui.widgets import ProgressIndicator, ProgressMode, ProgressState


class TestProgressIndicator:
    def test_estado_inicial(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        assert p.state() == ProgressState.IDLE
        assert p.log_count() == 0

    def test_set_progress_atualiza_label(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.set_progress(50, 200)
        assert p._bar.value() == 50
        assert "25%" in p._sublabel.text()
        assert "200" in p._sublabel.text()

    def test_append_log_incrementa_contador(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.append_log("INFO", "Iniciando")
        p.append_log("WARNING", "Cuidado")
        p.append_log("ERROR", "Falha")
        assert p.log_count() == 3
        assert "3 eventos" in p._btn_log.text()

    def test_state_running_mostra_botao_cancel_se_cancellable(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.set_cancellable(True)
        p.set_state(ProgressState.RUNNING)
        assert not p._btn_cancel.isHidden()

    def test_state_running_oculta_pause_se_nao_pausable(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.set_pausable(False)
        p.set_state(ProgressState.RUNNING)
        assert p._btn_pause.isHidden()

    def test_cancel_emite_signal(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.set_cancellable(True)
        p.set_state(ProgressState.RUNNING)
        with qtbot.waitSignal(p.cancel_requested, timeout=500):
            p._btn_cancel.click()

    def test_pause_alterna_estado_e_emite(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        p.set_pausable(True)
        p.set_state(ProgressState.RUNNING)
        with qtbot.waitSignal(p.pause_requested, timeout=500) as blocker:
            p._btn_pause.click()
        assert blocker.args[0] is True
        assert p.state() == ProgressState.PAUSED

    def test_expand_log_alterna_visibilidade(self, qtbot):
        p = ProgressIndicator()
        qtbot.addWidget(p)
        assert p._log.isHidden()
        p.expand_log(True)
        assert not p._log.isHidden()
        p.expand_log(False)
        assert p._log.isHidden()

    def test_modo_indeterminate(self, qtbot):
        p = ProgressIndicator(mode=ProgressMode.INDETERMINATE)
        qtbot.addWidget(p)
        # range 0-0 indica modo indeterminado no QProgressBar
        assert p._bar.minimum() == 0
        assert p._bar.maximum() == 0
