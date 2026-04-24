"""
SideRailItem — item do rail lateral esquerdo (Bloco 5 §C18).

Botão quadrado 72×72px com ícone centralizado, tooltip e atalho.
Estado ativo é destacado com border-left teal de 2px e ícone teal.
Suporte a badge opcional no canto superior direito.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QToolButton, QWidget

from src.gui.widgets.status_badge import BadgeStatus, _CORES as _BADGE_CORES


_COR_INATIVO = "#787A80"
_COR_ATIVO = "#008C95"
_COR_HOVER_BG = "#F7F7F8"
_COR_BORDER_ATIVO = "#008C95"


class SideRailItem(QToolButton):
    """Item do side rail. Sinal `activated_with_tela` para roteamento."""

    activated_with_tela = Signal(str)

    def __init__(
        self,
        icon: str,
        tela_id: str,
        label: str,
        shortcut: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tela_id = tela_id
        self._label = label
        self._icon_text = icon
        self._is_active = False
        self._badge_text: str | None = None
        self._badge_status = BadgeStatus.BAIXO

        self.setText(icon)
        self.setFixedSize(72, 72)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setCheckable(True)
        self.setAutoExclusive(True)

        tip = label if not shortcut else f"{label}  ·  {shortcut}"
        self.setToolTip(tip)

        self.clicked.connect(lambda: self.activated_with_tela.emit(self._tela_id))
        self._aplicar_qss()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def tela_id(self) -> str:
        return self._tela_id

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self.setChecked(active)
        self._aplicar_qss()

    def set_badge(
        self, text: str | None, status: BadgeStatus = BadgeStatus.BAIXO
    ) -> None:
        self._badge_text = text
        self._badge_status = status
        self.update()

    # ------------------------------------------------------------
    # Pintura — desenha badge no canto se houver
    # ------------------------------------------------------------

    def paintEvent(self, ev) -> None:  # noqa: N802
        super().paintEvent(ev)
        if not self._badge_text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cor = _BADGE_CORES.get(self._badge_status, QColor(0x00, 0x8C, 0x95))
        # Pequeno disco no canto superior direito
        size = 8
        x = self.width() - size - 12
        y = 12
        painter.setBrush(cor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x, y, size, size)
        painter.end()

    def _aplicar_qss(self) -> None:
        cor_icon = _COR_ATIVO if self._is_active else _COR_INATIVO
        bg = _COR_HOVER_BG if self._is_active else "transparent"
        border = (
            f"border-left: 2px solid {_COR_BORDER_ATIVO};"
            if self._is_active
            else "border-left: 2px solid transparent;"
        )
        self.setStyleSheet(
            f"""
            QToolButton {{
                color: {cor_icon};
                background: {bg};
                {border}
                border-top: none;
                border-right: none;
                border-bottom: none;
                font-size: 22pt;
                padding: 0px;
            }}
            QToolButton:hover {{
                background: {_COR_HOVER_BG};
                color: {_COR_ATIVO};
            }}
            """
        )
