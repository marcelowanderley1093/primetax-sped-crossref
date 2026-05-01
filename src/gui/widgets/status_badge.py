"""
StatusBadge — pill de status com variantes pré-definidas.

Componente primitivo de Nível 0 do design system Primetax (Bloco 5 §C3).
Usado em T3 (matriz de cruzamentos), T4 (severidade da oportunidade),
T6 (estado de reconciliação), T8 (auditoria de importações).

Renderizado via paintEvent customizado: fundo tom subtle + borda 1px +
texto em text.primary. Cor derivada do enum BadgeStatus. Altura fixa 22px.

Identidade visual Primetax (CLAUDE.md §3) é respeitada: ALTO (error)
só para fragilidade crítica, perda de prazo prescricional ou encoding
rejeitado — não para divergências comuns.
"""

from __future__ import annotations

from enum import Enum

from PySide6.QtCore import (
    Property,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QPainter,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget


class BadgeStatus(Enum):
    OK = "ok"
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"
    NA = "na"
    DEGRADADO = "degradado"
    PENDENTE = "pendente"
    EM_PROCESSO = "em_processo"
    REVISADO = "revisado"


# Cor principal de cada estado (derivada da paleta do Bloco 2).
_CORES: dict[BadgeStatus, QColor] = {
    BadgeStatus.OK:          QColor(0x2D, 0x7D, 0x5A),  # success
    BadgeStatus.ALTO:        QColor(0xB2, 0x3A, 0x3A),  # error
    BadgeStatus.MEDIO:       QColor(0xC2, 0x8B, 0x2F),  # warning
    BadgeStatus.BAIXO:       QColor(0x2E, 0x5C, 0x8A),  # info
    BadgeStatus.NA:          QColor(0x78, 0x7A, 0x80),  # text.secondary
    BadgeStatus.DEGRADADO:   QColor(0xC2, 0x8B, 0x2F),  # warning
    BadgeStatus.PENDENTE:    QColor(0x2E, 0x5C, 0x8A),  # info
    BadgeStatus.EM_PROCESSO: QColor(0x00, 0x8C, 0x95),  # primary
    BadgeStatus.REVISADO:    QColor(0x2D, 0x7D, 0x5A),  # success
}

_ROTULOS_PADRAO: dict[BadgeStatus, str] = {
    BadgeStatus.OK:          "OK",
    BadgeStatus.ALTO:        "ALTO",
    BadgeStatus.MEDIO:       "MÉDIO",
    BadgeStatus.BAIXO:       "BAIXO",
    BadgeStatus.NA:          "N/A",
    BadgeStatus.DEGRADADO:   "DEGRADADO",
    BadgeStatus.PENDENTE:    "PENDENTE",
    BadgeStatus.EM_PROCESSO: "PROCESSANDO",
    BadgeStatus.REVISADO:    "REVISADO",
}

_COR_TEXTO = QColor(0x53, 0x56, 0x5A)  # text.primary


class StatusBadge(QWidget):
    """Pill de status com altura fixa (22px), cor conforme BadgeStatus.

    O texto exibido é:
      - o `text` passado no construtor, se informado
      - caso contrário, o rótulo padrão do estado (OK, ALTO, etc.)

    `set_pulse(True)` anima opacidade 1.0 ↔ 0.6 em loop — útil para
    estado EM_PROCESSO.
    """

    _ALTURA = 22
    _PADDING_H = 8
    _RADIUS = 2

    def __init__(
        self,
        status: BadgeStatus,
        text: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._status = status
        self._text = text or _ROTULOS_PADRAO[status]
        self._opacity = 1.0
        self._pulse_anim: QPropertyAnimation | None = None

        self.setFixedHeight(self._ALTURA)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._atualizar_largura()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def set_status(self, status: BadgeStatus) -> None:
        self._status = status
        if self._text in _ROTULOS_PADRAO.values():
            self._text = _ROTULOS_PADRAO[status]
        self._atualizar_largura()
        self.update()

    def status(self) -> BadgeStatus:
        return self._status

    def set_text(self, text: str) -> None:
        self._text = text
        self._atualizar_largura()
        self.update()

    def text(self) -> str:
        return self._text

    def set_pulse(self, enabled: bool) -> None:
        if enabled and self._pulse_anim is None:
            anim = QPropertyAnimation(self, b"opacity_prop")
            anim.setDuration(1200)
            anim.setStartValue(1.0)
            anim.setKeyValueAt(0.5, 0.6)
            anim.setEndValue(1.0)
            anim.setLoopCount(-1)
            anim.start()
            self._pulse_anim = anim
        elif not enabled and self._pulse_anim is not None:
            self._pulse_anim.stop()
            self._pulse_anim = None
            self._opacity = 1.0
            self.update()

    # ------------------------------------------------------------
    # Qt property usada pela animação
    # ------------------------------------------------------------

    def _get_opacity(self) -> float:
        return self._opacity

    def _set_opacity(self, v: float) -> None:
        self._opacity = v
        self.update()

    opacity_prop = Property(float, _get_opacity, _set_opacity)

    # ------------------------------------------------------------
    # Tamanho e pintura
    # ------------------------------------------------------------

    def sizeHint(self) -> QSize:
        return QSize(self._largura_calculada, self._ALTURA)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def _font(self) -> QFont:
        f = QFont()
        f.setPointSize(9)
        f.setWeight(QFont.Weight.Medium)
        f.setCapitalization(QFont.Capitalization.AllUppercase)
        return f

    def _atualizar_largura(self) -> None:
        fm = QFontMetrics(self._font())
        text_w = fm.horizontalAdvance(self._text)
        self._largura_calculada = text_w + self._PADDING_H * 2
        self.updateGeometry()
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 (Qt API)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setOpacity(self._opacity)

        cor = _CORES[self._status]
        fundo = QColor(cor)
        fundo.setAlphaF(0.12)

        rect = QRect(0, 0, self.width(), self.height())
        painter.setBrush(fundo)
        painter.setPen(QPen(cor, 1))
        painter.drawRoundedRect(
            rect.adjusted(0, 0, -1, -1), self._RADIUS, self._RADIUS
        )

        painter.setPen(_COR_TEXTO)
        painter.setFont(self._font())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()
