"""
Testes dos componentes complementares de Nível 0/1 (Bloco 5 §C7, §C12, §C13, §C14).

Cobertura:
  - Toast: factories show_*, dismissed signal, pilha limitada a 3.
  - EmptyState: render simples, ações primária/secundária, signals.
  - FilterChip: toggle, signal toggled_with_id, set_count.
  - InlineMessage: 4 levels, ação, dismiss.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

from src.gui.widgets import (
    EmptyState,
    FilterChip,
    InlineMessage,
    MessageLevel,
    Toast,
    ToastAction,
    ToastLevel,
)


# --------------------------------------------------------------------
# Toast
# --------------------------------------------------------------------

class TestToast:
    def test_show_success_emite_widget(self, qtbot):
        win = QMainWindow()
        win.resize(800, 600)
        qtbot.addWidget(win)
        win.show()

        t = Toast.show_success(win, "Diagnóstico concluído")
        qtbot.addWidget(t)
        assert t.level() == ToastLevel.SUCCESS
        assert "Diagnóstico" in t.message()

    def test_show_error_usa_duracao_maior(self, qtbot):
        win = QMainWindow()
        qtbot.addWidget(win)
        t_error = Toast.show_error(win, "Falha")
        qtbot.addWidget(t_error)
        t_info = Toast.show_info(win, "Info")
        qtbot.addWidget(t_info)
        # erro tem duração ≥ info
        assert t_error._duration_ms >= t_info._duration_ms

    def test_dismiss_emite_signal(self, qtbot):
        win = QMainWindow()
        qtbot.addWidget(win)
        win.show()
        t = Toast.show_warning(win, "Atenção")
        qtbot.addWidget(t)
        with qtbot.waitSignal(t.dismissed, timeout=1000):
            t.dismiss()

    def test_action_callback_dispara_e_dismiss(self, qtbot):
        win = QMainWindow()
        qtbot.addWidget(win)
        win.show()

        chamadas = []
        action = ToastAction(label="Abrir", callback=lambda: chamadas.append("ok"))
        t = Toast.show_info(win, "Documento gerado", action=action)
        qtbot.addWidget(t)

        t._on_action()  # invoca diretamente — equivalente ao clique do botão
        assert chamadas == ["ok"]

    def test_pilha_limita_a_3_simultaneos(self, qtbot):
        # Limpa stack antes
        Toast._ativos.clear()

        win = QMainWindow()
        qtbot.addWidget(win)
        win.show()

        toasts = []
        for i in range(5):
            t = Toast.show_info(win, f"Mensagem {i}")
            qtbot.addWidget(t)
            toasts.append(t)

        ativos = Toast._ativos_vivos()
        # Não deve passar de 3 simultâneos visíveis
        assert len(ativos) <= 3


# --------------------------------------------------------------------
# EmptyState
# --------------------------------------------------------------------

class TestEmptyState:
    def test_renderiza_titulo_e_descricao(self, qtbot):
        es = EmptyState(
            title="Nenhum cliente importado",
            description="Arraste um SPED para começar.",
        )
        qtbot.addWidget(es)
        assert es._title_label.text() == "Nenhum cliente importado"
        assert es._description_label.text() == "Arraste um SPED para começar."

    def test_sem_descricao_nao_cria_label(self, qtbot):
        es = EmptyState(title="Vazio")
        qtbot.addWidget(es)
        assert es._description_label is None

    def test_acao_primaria_emite_signal(self, qtbot):
        es = EmptyState(
            title="Sem dados",
            primary_action_label="Importar agora",
        )
        qtbot.addWidget(es)
        with qtbot.waitSignal(es.primary_action, timeout=500):
            es._btn_primary.click()

    def test_set_title_atualiza(self, qtbot):
        es = EmptyState(title="Antigo")
        qtbot.addWidget(es)
        es.set_title("Novo")
        assert es._title_label.text() == "Novo"


# --------------------------------------------------------------------
# FilterChip
# --------------------------------------------------------------------

class TestFilterChip:
    def test_inicio_inativo(self, qtbot):
        chip = FilterChip("Alto", "alto")
        qtbot.addWidget(chip)
        assert not chip.isChecked()

    def test_toggle_emite_signal_com_id(self, qtbot):
        chip = FilterChip("Alto", "alto")
        qtbot.addWidget(chip)
        with qtbot.waitSignal(chip.toggled_with_id, timeout=500) as blocker:
            chip.click()
        assert blocker.args == ["alto", True]

    def test_label_renderiza_check_quando_ativo(self, qtbot):
        chip = FilterChip("Alto", "alto")
        qtbot.addWidget(chip)
        assert "✓" not in chip.text()
        chip.setChecked(True)
        assert "✓" in chip.text()

    def test_set_count_renderiza_no_label(self, qtbot):
        chip = FilterChip("Alto", "alto")
        qtbot.addWidget(chip)
        chip.set_count(34)
        assert "(34)" in chip.text()

    def test_set_count_none_remove(self, qtbot):
        chip = FilterChip("Alto", "alto")
        qtbot.addWidget(chip)
        chip.set_count(34)
        chip.set_count(None)
        assert "(" not in chip.text()


# --------------------------------------------------------------------
# InlineMessage
# --------------------------------------------------------------------

class TestInlineMessage:
    def test_quatro_levels_renderizam(self, qtbot):
        for lvl in MessageLevel:
            im = InlineMessage(lvl, f"Aviso {lvl.value}")
            qtbot.addWidget(im)
            assert im.level() == lvl

    def test_acao_emite_signal(self, qtbot):
        im = InlineMessage(
            MessageLevel.WARNING,
            "Reconciliação pendente",
            action_label="Abrir T6",
        )
        qtbot.addWidget(im)
        assert im._action_btn is not None
        with qtbot.waitSignal(im.action_triggered, timeout=500):
            im._action_btn.click()

    def test_dismissible_remove_e_emite(self, qtbot):
        im = InlineMessage(
            MessageLevel.INFO,
            "Mensagem temporária",
            dismissible=True,
        )
        qtbot.addWidget(im)
        assert im._close_btn is not None
        with qtbot.waitSignal(im.dismissed, timeout=500):
            im._close_btn.click()

    def test_set_message_atualiza_label(self, qtbot):
        im = InlineMessage(MessageLevel.SUCCESS, "Antes")
        qtbot.addWidget(im)
        im.set_message("Depois")
        assert im._msg_label.text() == "Depois"
