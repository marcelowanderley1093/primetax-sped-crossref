"""
Toast — notificação não-bloqueante (Bloco 5 §C7).

Aparece no canto inferior direito da janela pai, auto-dismisses em 8s
(12s para erros). Pilha até 3 simultâneos. Suporta uma ação opcional
(ex: "Abrir documento" após gerar parecer).

Filosofia: NUNCA rouba foco do teclado. O auditor pode estar digitando
numa tabela quando um Toast aparece — Toast não pode interromper isso.
"""

from __future__ import annotations

import weakref
from dataclasses import dataclass
from enum import Enum
from typing import Callable

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class ToastLevel(Enum):
    SUCCESS = "success"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ToastAction:
    label: str
    callback: Callable[[], None]


_CORES_FUNDO: dict[ToastLevel, str] = {
    ToastLevel.SUCCESS: "#2D7D5A",
    ToastLevel.INFO: "#2E5C8A",
    ToastLevel.WARNING: "#C28B2F",
    ToastLevel.ERROR: "#B23A3A",
}

_DURACAO_PADRAO_MS: dict[ToastLevel, int] = {
    ToastLevel.SUCCESS: 8_000,
    ToastLevel.INFO: 8_000,
    ToastLevel.WARNING: 10_000,
    ToastLevel.ERROR: 12_000,
}

_ICONES: dict[ToastLevel, str] = {
    # Glifos Unicode até substituirmos por SVG Lucide.
    ToastLevel.SUCCESS: "✓",
    ToastLevel.INFO: "ⓘ",
    ToastLevel.WARNING: "⚠",
    ToastLevel.ERROR: "✕",
}

_MARGEM = 16
_GAP_ENTRE_TOASTS = 8
_MAX_SIMULTANEOS = 3


class Toast(QWidget):
    """Notificação ephemeral. Use os métodos estáticos `show_*` em vez de instanciar."""

    dismissed = Signal()

    # Controle global da pilha — weak refs para não impedir GC quando dismissed.
    _ativos: list[weakref.ReferenceType[Toast]] = []

    def __init__(
        self,
        message: str,
        *,
        level: ToastLevel = ToastLevel.INFO,
        action: ToastAction | None = None,
        duration_ms: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent, Qt.WindowType.SubWindow)
        self._level = level
        self._duration_ms = duration_ms or _DURACAO_PADRAO_MS[level]
        self._action = action
        self._dismissing = False  # True a partir do início do fade-out

        # Não rouba foco em hipótese alguma
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.setStyleSheet(self._qss())
        self.setObjectName("Toast")

        h = QHBoxLayout(self)
        h.setContentsMargins(14, 10, 14, 10)
        h.setSpacing(10)

        icon_lbl = QLabel(_ICONES[level])
        icon_lbl.setStyleSheet("color: #FFFFFF; font-size: 14pt; font-weight: 600;")
        h.addWidget(icon_lbl)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet("color: #FFFFFF; font-size: 10pt;")
        msg_lbl.setWordWrap(False)
        h.addWidget(msg_lbl, 1)

        if action is not None:
            act_btn = QPushButton(action.label)
            act_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            act_btn.setFlat(True)
            act_btn.setStyleSheet(
                "QPushButton { color: #FFFFFF; background: transparent; "
                "border: none; text-decoration: underline; "
                "font-size: 10pt; font-weight: 500; padding: 0px 4px; } "
                "QPushButton:hover { color: #E6F3F4; }"
            )
            act_btn.clicked.connect(self._on_action)
            h.addWidget(act_btn)

        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFlat(True)
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet(
            "QPushButton { color: #FFFFFF; background: transparent; "
            "border: none; font-size: 11pt; } "
            "QPushButton:hover { color: #E6F3F4; }"
        )
        close_btn.clicked.connect(self.dismiss)
        h.addWidget(close_btn)

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._fade_in_anim: QPropertyAnimation | None = None
        self._fade_out_anim: QPropertyAnimation | None = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.dismiss)

        # Hover pausa o auto-dismiss
        self.installEventFilter(self)

    # ----------------------------------------------------------
    # API estática (preferida)
    # ----------------------------------------------------------

    @staticmethod
    def show_success(parent: QWidget, message: str, **kwargs) -> Toast:
        return Toast._show(parent, message, ToastLevel.SUCCESS, **kwargs)

    @staticmethod
    def show_info(parent: QWidget, message: str, **kwargs) -> Toast:
        return Toast._show(parent, message, ToastLevel.INFO, **kwargs)

    @staticmethod
    def show_warning(parent: QWidget, message: str, **kwargs) -> Toast:
        return Toast._show(parent, message, ToastLevel.WARNING, **kwargs)

    @staticmethod
    def show_error(parent: QWidget, message: str, **kwargs) -> Toast:
        return Toast._show(parent, message, ToastLevel.ERROR, **kwargs)

    @staticmethod
    def _show(
        parent: QWidget,
        message: str,
        level: ToastLevel,
        **kwargs,
    ) -> Toast:
        Toast._cleanup_dead_refs()
        # Limita a pilha — se já tem _MAX_SIMULTANEOS ativos, fecha o mais antigo
        ativos = Toast._ativos_vivos()
        while len(ativos) >= _MAX_SIMULTANEOS:
            mais_antigo = ativos.pop(0)
            mais_antigo.dismiss()

        t = Toast(message, level=level, parent=parent, **kwargs)
        Toast._ativos.append(weakref.ref(t))
        t._mostrar()
        return t

    # ----------------------------------------------------------
    # Ciclo de vida
    # ----------------------------------------------------------

    def _mostrar(self) -> None:
        self.adjustSize()
        self._reposicionar()
        self.show()
        self.raise_()

        self._fade_in_anim = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_in_anim.setDuration(180)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(0.96)
        self._fade_in_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in_anim.start()

        self._timer.start(self._duration_ms)

        # Reposiciona todos para empilhar
        Toast._reempilhar()

    def dismiss(self) -> None:
        if self._dismissing:
            return
        self._dismissing = True
        self._timer.stop()

        # Re-empilha imediatamente para que toasts subsequentes "subam"
        # antes mesmo do fade-out terminar.
        Toast._reempilhar()

        self._fade_out_anim = QPropertyAnimation(self._opacity, b"opacity")
        self._fade_out_anim.setDuration(160)
        self._fade_out_anim.setStartValue(self._opacity.opacity())
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out_anim.finished.connect(self._finalizar)
        self._fade_out_anim.start()

    def _finalizar(self) -> None:
        self.dismissed.emit()
        Toast._reempilhar()
        self.hide()
        self.deleteLater()

    def _on_action(self) -> None:
        if self._action:
            try:
                self._action.callback()
            finally:
                self.dismiss()

    # ----------------------------------------------------------
    # Posicionamento
    # ----------------------------------------------------------

    def _reposicionar(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        # Empilha de baixo para cima
        ativos = [t for t in Toast._ativos_vivos() if t is not self]
        offset_y = sum(t.height() + _GAP_ENTRE_TOASTS for t in ativos)

        x = parent.width() - self.width() - _MARGEM
        y = parent.height() - self.height() - _MARGEM - offset_y
        self.move(max(0, x), max(0, y))

    @classmethod
    def _reempilhar(cls) -> None:
        for t in cls._ativos_vivos():
            t._reposicionar()

    # ----------------------------------------------------------
    # Eventos / utilitários
    # ----------------------------------------------------------

    def eventFilter(self, obj, event):  # noqa: N802
        from PySide6.QtCore import QEvent
        if obj is self:
            if event.type() == QEvent.Type.Enter:
                # Pausa timer enquanto o usuário está com cursor em cima
                self._timer.stop()
            elif event.type() == QEvent.Type.Leave:
                # Retoma com tempo restante razoável
                self._timer.start(self._duration_ms // 2)
        return super().eventFilter(obj, event)

    def level(self) -> ToastLevel:
        return self._level

    def message(self) -> str:
        # Lê do segundo widget do layout (a label de mensagem)
        layout = self.layout()
        if layout and layout.count() >= 2:
            w = layout.itemAt(1).widget()
            if isinstance(w, QLabel):
                return w.text()
        return ""

    @classmethod
    def _ativos_vivos(cls) -> list[Toast]:
        """Retorna apenas toasts vivos e não em fade-out."""
        return [
            r() for r in cls._ativos
            if r() is not None and not r()._dismissing
        ]

    @classmethod
    def _cleanup_dead_refs(cls) -> None:
        cls._ativos = [r for r in cls._ativos if r() is not None]

    def _qss(self) -> str:
        cor = _CORES_FUNDO[self._level]
        return f"""
        #Toast {{
            background: {cor};
            border-radius: 4px;
        }}
        """
