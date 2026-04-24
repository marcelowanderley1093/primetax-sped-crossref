"""
ProgressIndicator — barra de progresso + label + log expandível (Bloco 5 §C9).

Componente de Nível 1. Usado em T2 (importação) e em T3 (re-rodar
diagnóstico). Composição:

  ┌──────────────────────────────────────────────────────────────┐
  │ Importando efd_contrib_202501.txt                            │
  │ [████████████░░░░░░░░] 75%  12.3k / 16.5k linhas             │
  │ [▼ Log estruturado — 23 eventos]   [Pausar] [Cancelar]       │
  │   09:47:12 INFO  Encoding detectado: UTF-8 (alto)            │
  │   09:47:13 INFO  Registro 0000 validado                      │
  │   ...                                                        │
  └──────────────────────────────────────────────────────────────┘

Cancelamento e pause emitem signals; o consumidor (controller) decide
o que fazer. Nunca cancela silenciosamente.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ProgressMode(Enum):
    DETERMINATE = "determinate"
    INDETERMINATE = "indeterminate"


class ProgressState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


_COR_PRIMARY = "#008C95"
_COR_SUCCESS = "#2D7D5A"
_COR_WARNING = "#C28B2F"
_COR_ERROR = "#B23A3A"
_COR_INFO = "#2E5C8A"
_COR_TEXT = "#53565A"
_COR_TEXT_SEC = "#787A80"
_COR_BG = "#F7F7F8"
_COR_BORDER = "#D1D3D6"

_CORES_LOG = {
    "INFO": _COR_TEXT_SEC,
    "WARNING": _COR_WARNING,
    "ERROR": _COR_ERROR,
    "SUCCESS": _COR_SUCCESS,
    "DEBUG": _COR_INFO,
}


class ProgressIndicator(QWidget):
    """Barra + label + log estruturado expansível.

    Signals:
      cancel_requested — botão "Cancelar" clicado.
      pause_requested(bool) — botão "Pausar/Continuar" alternou.
    """

    cancel_requested = Signal()
    pause_requested = Signal(bool)

    def __init__(
        self,
        mode: ProgressMode = ProgressMode.DETERMINATE,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._mode = mode
        self._state = ProgressState.IDLE
        self._log_count = 0
        self._cancellable = True
        self._pausable = False

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        # Label da operação atual
        self._label = QLabel("")
        self._label.setStyleSheet(
            f"color: {_COR_TEXT}; font-size: 10pt; background: transparent;"
        )
        v.addWidget(self._label)

        # Linha com progresso + sub-label
        progress_row = QHBoxLayout()
        progress_row.setSpacing(10)

        self._bar = QProgressBar()
        self._bar.setFixedHeight(8)
        self._bar.setTextVisible(False)
        self._configurar_modo()
        self._aplicar_qss_bar()
        progress_row.addWidget(self._bar, 1)

        self._sublabel = QLabel("")
        self._sublabel.setStyleSheet(
            f"color: {_COR_TEXT_SEC}; font-size: 9pt; background: transparent;"
        )
        self._sublabel.setMinimumWidth(180)
        progress_row.addWidget(self._sublabel)

        wrap_progress = QWidget()
        wrap_progress.setLayout(progress_row)
        v.addWidget(wrap_progress)

        # Linha de controle (toggle log + botões)
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self._btn_log = QPushButton("▸ Log estruturado — 0 eventos")
        self._btn_log.setFlat(True)
        self._btn_log.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_log.setStyleSheet(
            f"QPushButton {{ color: {_COR_TEXT_SEC}; font-size: 9pt; "
            "background: transparent; border: none; text-align: left; padding: 2px 0px; } "
            f"QPushButton:hover {{ color: {_COR_PRIMARY}; }}"
        )
        self._btn_log.clicked.connect(self._toggle_log)
        ctrl_row.addWidget(self._btn_log)

        ctrl_row.addStretch()

        self._btn_pause = QPushButton("Pausar")
        self._btn_pause.setStyleSheet(self._qss_btn_secundario())
        self._btn_pause.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_pause.clicked.connect(self._on_pause)
        self._btn_pause.setVisible(False)
        ctrl_row.addWidget(self._btn_pause)

        self._btn_cancel = QPushButton("Cancelar")
        self._btn_cancel.setStyleSheet(self._qss_btn_secundario())
        self._btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_cancel.clicked.connect(self.cancel_requested)
        self._btn_cancel.setVisible(False)
        ctrl_row.addWidget(self._btn_cancel)

        wrap_ctrl = QWidget()
        wrap_ctrl.setLayout(ctrl_row)
        v.addWidget(wrap_ctrl)

        # Log estruturado (oculto por default)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(120)
        self._log.setMaximumHeight(220)
        self._log.setVisible(False)
        self._log.setStyleSheet(
            f"QTextEdit {{ background: {_COR_BG}; color: {_COR_TEXT}; "
            f"border: 1px solid {_COR_BORDER}; border-radius: 2px; "
            "font-family: 'JetBrains Mono', Consolas, monospace; font-size: 9pt; }}"
        )
        v.addWidget(self._log)

        self.set_state(ProgressState.IDLE)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def set_progress(self, current: int, total: int) -> None:
        if self._mode != ProgressMode.DETERMINATE:
            return
        self._bar.setRange(0, max(total, 1))
        self._bar.setValue(current)
        pct = (current * 100) // max(total, 1)
        self._sublabel.setText(
            f"{pct}%  {self._fmt_thousands(current)} / {self._fmt_thousands(total)}"
        )

    def set_label(self, text: str) -> None:
        self._label.setText(text)

    def append_log(self, level: str, message: str) -> None:
        self._log_count += 1
        level = level.upper()
        cor = _CORES_LOG.get(level, _COR_TEXT_SEC)
        ts = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<div><span style="color:{_COR_TEXT_SEC}">{ts}</span> '
            f'<span style="color:{cor}; font-weight:600">{level:7s}</span> '
            f'<span style="color:{_COR_TEXT}">{self._escape_html(message)}</span></div>'
        )
        self._log.append(html)
        self._btn_log.setText(
            f"{'▾' if self._log.isVisible() else '▸'} "
            f"Log estruturado — {self._log_count} evento{'s' if self._log_count != 1 else ''}"
        )

    def set_state(self, state: ProgressState) -> None:
        self._state = state
        is_running = state == ProgressState.RUNNING
        is_paused = state == ProgressState.PAUSED

        self._btn_pause.setVisible((is_running or is_paused) and self._pausable)
        self._btn_cancel.setVisible((is_running or is_paused) and self._cancellable)

        if is_paused:
            self._btn_pause.setText("Continuar")
        else:
            self._btn_pause.setText("Pausar")

        if state == ProgressState.SUCCESS:
            self._sublabel.setText(self._sublabel.text() + "  · concluído")
            self._sublabel.setStyleSheet(
                f"color: {_COR_SUCCESS}; font-size: 9pt; background: transparent;"
            )
        elif state == ProgressState.ERROR:
            self._sublabel.setStyleSheet(
                f"color: {_COR_ERROR}; font-size: 9pt; background: transparent;"
            )
        elif state == ProgressState.CANCELLED:
            self._sublabel.setText(self._sublabel.text() + "  · cancelado")
            self._sublabel.setStyleSheet(
                f"color: {_COR_TEXT_SEC}; font-size: 9pt; background: transparent;"
            )
        else:
            self._sublabel.setStyleSheet(
                f"color: {_COR_TEXT_SEC}; font-size: 9pt; background: transparent;"
            )

    def set_pausable(self, value: bool) -> None:
        self._pausable = value

    def set_cancellable(self, value: bool) -> None:
        self._cancellable = value

    def expand_log(self, expanded: bool = True) -> None:
        self._log.setVisible(expanded)
        prefix = "▾" if expanded else "▸"
        self._btn_log.setText(
            f"{prefix} Log estruturado — {self._log_count} evento"
            f"{'s' if self._log_count != 1 else ''}"
        )

    def state(self) -> ProgressState:
        return self._state

    def log_count(self) -> int:
        return self._log_count

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _toggle_log(self) -> None:
        self.expand_log(not self._log.isVisible())

    def _on_pause(self) -> None:
        if self._state == ProgressState.RUNNING:
            self.set_state(ProgressState.PAUSED)
            self.pause_requested.emit(True)
        elif self._state == ProgressState.PAUSED:
            self.set_state(ProgressState.RUNNING)
            self.pause_requested.emit(False)

    def _configurar_modo(self) -> None:
        if self._mode == ProgressMode.INDETERMINATE:
            self._bar.setRange(0, 0)
        else:
            self._bar.setRange(0, 100)
            self._bar.setValue(0)

    def _aplicar_qss_bar(self) -> None:
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{
                background: {_COR_BG};
                border: 1px solid {_COR_BORDER};
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background: {_COR_PRIMARY};
                border-radius: 1px;
            }}
            """
        )

    @staticmethod
    def _qss_btn_secundario() -> str:
        return f"""
        QPushButton {{
            background: #FFFFFF;
            color: {_COR_PRIMARY};
            border: 1px solid {_COR_PRIMARY};
            border-radius: 2px;
            padding: 4px 12px;
            font-size: 9pt;
        }}
        QPushButton:hover {{ background: #E6F3F4; }}
        """

    @staticmethod
    def _fmt_thousands(n: int) -> str:
        return f"{n:,}".replace(",", ".")

    @staticmethod
    def _escape_html(s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )
