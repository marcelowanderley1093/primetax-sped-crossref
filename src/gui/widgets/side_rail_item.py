"""
SideRailItem — item do rail lateral esquerdo (Bloco 5 §C18).

Botão 92×100px com ícone vetorial (QPainter) e label de texto empilhados.
Estado ativo: border-left teal de 2px + ícone/label teal + fundo subtle.
Suporte a badge opcional no canto superior direito.

Decisão (revisão pós-Sprint 1):
  - Label visível embaixo do ícone, em vez de só tooltip — auditor que
    abre o app uma vez por semana não memoriza glifos abstratos.
  - Ícones desenhados via QPainter (linhas, polígonos), não glifos
    unicode. Glifos como ▦ ⊕ ⊙ não renderizam consistentemente em
    fontes diferentes; QPainter é zero-config e profissional.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.gui.widgets.icons import IconName, paint_icon
from src.gui.widgets.status_badge import BadgeStatus, _CORES as _BADGE_CORES


_COR_INATIVO = QColor(0x78, 0x7A, 0x80)
_COR_ATIVO = QColor(0x00, 0x8C, 0x95)
_COR_DISABLED = QColor(0xC4, 0xC5, 0xC7)
_COR_HOVER_BG = "#F0F0F1"
_COR_ATIVO_BG = "#E6F3F4"
_COR_BORDER_ATIVO = "#008C95"


class _IconArea(QWidget):
    """Sub-widget que pinta o ícone vetorial. Tamanho fixo 22×22 — porte
    discreto pra caber 10 itens de rail em telas <= 900px de altura útil."""

    def __init__(self, icon: IconName, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._icon = icon
        self._color = _COR_INATIVO
        self.setFixedSize(22, 22)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, ev) -> None:  # noqa: N802
        painter = QPainter(self)
        rect = QRect(0, 0, self.width(), self.height())
        paint_icon(painter, rect, self._icon, self._color, stroke_width=1.5)


class SideRailItem(QFrame):
    """Item clicável do side rail. Sinal `activated_with_tela` para roteamento."""

    activated_with_tela = Signal(str)

    def __init__(
        self,
        icon: IconName,
        tela_id: str,
        label: str,
        shortcut: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._tela_id = tela_id
        self._label_text = label
        self._icon_name = icon
        self._is_active = False
        self._enabled = True
        self._badge_text: str | None = None
        self._badge_status = BadgeStatus.BAIXO

        self.setFixedSize(92, 78)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        v = QVBoxLayout(self)
        v.setContentsMargins(0, 8, 0, 8)
        v.setSpacing(3)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_widget = _IconArea(icon)
        # Centraliza horizontalmente; o widget tem 32px e o item tem 92px.
        v.addWidget(self._icon_widget, 0, Qt.AlignmentFlag.AlignHCenter)

        self._lbl_text = QLabel(label)
        self._lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_text.setWordWrap(False)
        v.addWidget(self._lbl_text)

        tip = label if not shortcut else f"{label}  ·  {shortcut}"
        self.setToolTip(tip)

        self._aplicar_qss()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def tela_id(self) -> str:
        return self._tela_id

    def set_active(self, active: bool) -> None:
        self._is_active = active
        self._aplicar_qss()

    def setEnabled(self, enabled: bool) -> None:  # noqa: N802
        self._enabled = enabled
        super().setEnabled(enabled)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if enabled
            else Qt.CursorShape.ArrowCursor
        )
        self._aplicar_qss()

    def isEnabled(self) -> bool:  # noqa: N802
        return self._enabled

    def set_badge(
        self, text: str | None, status: BadgeStatus = BadgeStatus.BAIXO
    ) -> None:
        self._badge_text = text
        self._badge_status = status
        self.update()

    # ------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------

    def mousePressEvent(self, ev) -> None:  # noqa: N802 (Qt API)
        if self._enabled and ev.button() == Qt.MouseButton.LeftButton:
            self.activated_with_tela.emit(self._tela_id)
        super().mousePressEvent(ev)

    def paintEvent(self, ev) -> None:  # noqa: N802
        super().paintEvent(ev)
        if not self._badge_text:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cor = _BADGE_CORES.get(self._badge_status, QColor(0x00, 0x8C, 0x95))
        size = 8
        x = self.width() - size - 10
        y = 8
        painter.setBrush(cor)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(x, y, size, size)
        painter.end()

    # ------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------

    def _aplicar_qss(self) -> None:
        if not self._enabled:
            cor_icon = _COR_DISABLED
            cor_label = "#C4C5C7"
            bg = "transparent"
            border_left = "border-left: 2px solid transparent;"
        elif self._is_active:
            cor_icon = _COR_ATIVO
            cor_label = "#008C95"
            bg = _COR_ATIVO_BG
            border_left = f"border-left: 2px solid {_COR_BORDER_ATIVO};"
        else:
            cor_icon = _COR_INATIVO
            cor_label = "#787A80"
            bg = "transparent"
            border_left = "border-left: 2px solid transparent;"

        self._icon_widget.set_color(cor_icon)

        self.setStyleSheet(
            f"""
            SideRailItem {{
                background: {bg};
                {border_left}
                border-top: none;
                border-right: none;
                border-bottom: none;
            }}
            SideRailItem:hover {{
                background: {_COR_HOVER_BG};
            }}
            """
        )
        self._lbl_text.setStyleSheet(
            f"color: {cor_label}; font-size: 8pt; "
            f"font-weight: 500; background: transparent;"
        )
