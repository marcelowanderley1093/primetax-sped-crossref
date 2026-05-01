"""
StatCard — card de métrica para topo de T3 (Painel de Diagnóstico).

Componente de Nível 1 do design system (Bloco 5 §C11). Usado nos 4 cards
de topo de T3: Oportunidades, Divergências, Pendências, Limitações
Estruturais. Decisão residual #32 — sparkline de tendência deixado
fora da v1 (assumido).

Três textos hierarquizados:
  title — texto secondary pequeno
  primary_value — grande e bold, cor primary
  secondary_value (opcional) — texto medium com cor de status
  hint (opcional) — texto secondary, fica abaixo

Se `clickable=True`, card inteiro vira clicável (filtra T3 por ex.) —
hover muda fundo para surface.secondary, cursor vira pointer, emite
signal `clicked`.
"""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QEnterEvent, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


_COR_TITULO = "#787A80"
_COR_VALOR = "#53565A"
_COR_HINT = "#787A80"
_COR_BORDA = "#D1D3D6"
_COR_FUNDO = "#FFFFFF"
_COR_FUNDO_HOVER = "#F7F7F8"

_CORES_STATUS: dict[str, str] = {
    "normal": "#53565A",
    "success": "#2D7D5A",
    "warning": "#C28B2F",
    "error": "#B23A3A",
    "info": "#2E5C8A",
    "primary": "#008C95",
}


class StatCard(QFrame):
    """Card de estatística com title + valor principal + valor secundário + hint."""

    clicked = Signal()

    def __init__(
        self,
        title: str,
        *,
        clickable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._clickable = clickable
        self._hovering = False

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedHeight(96)
        self.setMinimumWidth(200)

        v = QVBoxLayout(self)
        v.setContentsMargins(14, 10, 14, 10)
        v.setSpacing(4)

        self._title = QLabel(title.upper())
        self._title.setStyleSheet(
            f"color: {_COR_TITULO}; font-size: 9pt; "
            "letter-spacing: 0.5px; font-weight: 600; background: transparent;"
        )
        v.addWidget(self._title)

        self._primary = QLabel("—")
        self._primary.setStyleSheet(
            f"color: {_COR_VALOR}; font-size: 22pt; font-weight: 700; "
            "background: transparent;"
        )
        self._primary.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        v.addWidget(self._primary)

        self._secondary = QLabel("")
        self._secondary.setStyleSheet(
            f"color: {_COR_VALOR}; font-size: 10pt; background: transparent;"
        )
        self._secondary.setVisible(False)
        v.addWidget(self._secondary)

        self._hint = QLabel("")
        self._hint.setStyleSheet(
            f"color: {_COR_HINT}; font-size: 9pt; background: transparent;"
        )
        self._hint.setVisible(False)
        v.addWidget(self._hint)
        v.addStretch()

        if clickable:
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._update_style()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def set_primary_value(self, value: str) -> None:
        self._primary.setText(value)

    def set_secondary_value(
        self,
        value: str,
        style: Literal["normal", "success", "warning", "error", "info", "primary"] = "normal",
    ) -> None:
        cor = _CORES_STATUS.get(style, _COR_VALOR)
        self._secondary.setText(value)
        self._secondary.setStyleSheet(
            f"color: {cor}; font-size: 10pt; background: transparent;"
        )
        self._secondary.setVisible(bool(value))

    def set_hint(self, hint: str) -> None:
        self._hint.setText(hint)
        self._hint.setVisible(bool(hint))

    def is_clickable(self) -> bool:
        return self._clickable

    # ------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------

    def mousePressEvent(self, ev: QMouseEvent) -> None:  # noqa: N802
        if self._clickable and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(ev)

    def enterEvent(self, ev: QEnterEvent) -> None:  # noqa: N802
        if self._clickable:
            self._hovering = True
            self._update_style()
        super().enterEvent(ev)

    def leaveEvent(self, ev) -> None:  # noqa: N802
        if self._clickable:
            self._hovering = False
            self._update_style()
        super().leaveEvent(ev)

    # ------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------

    def _update_style(self) -> None:
        fundo = _COR_FUNDO_HOVER if self._hovering else _COR_FUNDO
        self.setStyleSheet(
            f"""
            StatCard {{
                background: {fundo};
                border: 1px solid {_COR_BORDA};
                border-radius: 4px;
            }}
            """
        )
