"""
InlineMessage — banner persistente de aviso dentro de uma tela (Bloco 5 §C14).

Diferente do Toast (efêmero, canto inferior), o InlineMessage fica
ancorado num lugar específico de uma view: avisos em T3 ("Reconciliação
SUSPEITA — abrir T6"), em T2 (confirmação de encoding), em T4 (modo
degradado para CR-XX).

Layout horizontal com border-left de 3px na cor do level. Não rouba foco.
Pode ter ação opcional (link à direita) e fechável opcional (X).
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class MessageLevel(Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


_PALETA: dict[MessageLevel, dict[str, str]] = {
    MessageLevel.SUCCESS: {"border": "#2D7D5A", "bg": "rgba(45, 125, 90, 0.10)", "icon": "✓"},
    MessageLevel.INFO:    {"border": "#2E5C8A", "bg": "rgba(46, 92, 138, 0.10)", "icon": "ⓘ"},
    MessageLevel.WARNING: {"border": "#C28B2F", "bg": "rgba(194, 139, 47, 0.10)", "icon": "⚠"},
    MessageLevel.ERROR:   {"border": "#B23A3A", "bg": "rgba(178, 58, 58, 0.10)", "icon": "✕"},
}

_COR_TEXTO = "#53565A"
_COR_LINK = "#008C95"


class InlineMessage(QFrame):
    """Banner persistente. Não desaparece automaticamente — só via dismiss/dismissible."""

    action_triggered = Signal()
    dismissed = Signal()

    def __init__(
        self,
        level: MessageLevel,
        message: str,
        *,
        action_label: str | None = None,
        dismissible: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._level = level
        self.setObjectName("InlineMessage")
        self.setMinimumHeight(40)
        self._aplicar_qss()

        h = QHBoxLayout(self)
        h.setContentsMargins(12, 8, 12, 8)
        h.setSpacing(10)

        paleta = _PALETA[level]

        icon_lbl = QLabel(paleta["icon"])
        icon_lbl.setStyleSheet(
            f"color: {paleta['border']}; font-size: 13pt; font-weight: 600; "
            "background: transparent;"
        )
        h.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            f"color: {_COR_TEXTO}; font-size: 10pt; background: transparent;"
        )
        msg_lbl.setWordWrap(True)
        h.addWidget(msg_lbl, 1)
        self._msg_label = msg_lbl

        if action_label:
            btn = QPushButton(action_label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.setStyleSheet(
                f"QPushButton {{ color: {_COR_LINK}; background: transparent; "
                "border: none; text-decoration: underline; font-size: 10pt; "
                "font-weight: 500; padding: 0px 4px; } "
                f"QPushButton:hover {{ color: #00A4AE; }}"
            )
            btn.clicked.connect(self.action_triggered)
            h.addWidget(btn)
            self._action_btn = btn
        else:
            self._action_btn = None

        if dismissible:
            close_btn = QPushButton("✕")
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setFlat(True)
            close_btn.setFixedSize(18, 18)
            close_btn.setStyleSheet(
                f"QPushButton {{ color: {_COR_TEXTO}; background: transparent; "
                "border: none; font-size: 10pt; } "
                "QPushButton:hover { color: #008C95; }"
            )
            close_btn.clicked.connect(self._on_dismiss)
            h.addWidget(close_btn)
            self._close_btn = close_btn
        else:
            self._close_btn = None

    # ------------------------------------------------------------
    # API
    # ------------------------------------------------------------

    def set_message(self, message: str) -> None:
        self._msg_label.setText(message)

    def level(self) -> MessageLevel:
        return self._level

    def dismiss(self) -> None:
        self._on_dismiss()

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _on_dismiss(self) -> None:
        self.hide()
        self.dismissed.emit()
        self.deleteLater()

    def _aplicar_qss(self) -> None:
        paleta = _PALETA[self._level]
        self.setStyleSheet(
            f"""
            #InlineMessage {{
                background: {paleta['bg']};
                border: none;
                border-left: 3px solid {paleta['border']};
                border-radius: 2px;
            }}
            """
        )
