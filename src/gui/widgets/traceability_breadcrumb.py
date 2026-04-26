"""
TraceabilityBreadcrumb — trilha de rastreabilidade fiscal (§1 CLAUDE.md).

Componente de Nível 1 do design system (Bloco 5 §C4). Implementa
visualmente o princípio da rastreabilidade em 3 cliques: cliente →
competência → cruzamento → arquivo → linha.

Cada segmento é clicável (exceto o último, que é o estado atual).
Clique em segmento faz **pop até o segmento** (decisão residual #30 —
assumido: semântica natural de breadcrumb).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget


@dataclass
class BreadcrumbSegment:
    """Um nível do breadcrumb."""
    label: str
    target_tela: str | None = None
    payload: dict = field(default_factory=dict)


_COR_LINK = "#008C95"
_COR_LINK_HOVER = "#00A4AE"
_COR_ATUAL = "#53565A"
_COR_SEP = "#787A80"


class TraceabilityBreadcrumb(QWidget):
    """Trilha horizontal de segmentos clicáveis separados por `›`.

    Inclui um botão "← Voltar" no início (Alt+← também funciona globalmente).
    Sinal `voltar_solicitado` é emitido quando o botão é clicado — MainWindow
    conecta no `_voltar()` global.
    """

    segment_clicked = Signal(int)         # índice do segmento clicado
    voltar_solicitado = Signal()          # botão "← Voltar" clicado
    # Quando o segmento clicado tem `target_tela` definido, esse signal
    # é emitido pra MainWindow navegar para a tela correspondente.
    target_tela_clicked = Signal(str, dict)  # (target_tela, payload)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._segments: list[BreadcrumbSegment] = []
        self._mostrar_voltar: bool = True

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._layout.setSpacing(4)

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(28)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def segments(self) -> list[BreadcrumbSegment]:
        return list(self._segments)

    def set_segments(self, segments: list[BreadcrumbSegment]) -> None:
        self._segments = list(segments)
        self._render()

    def push(self, segment: BreadcrumbSegment) -> None:
        self._segments.append(segment)
        self._render()

    def pop(self) -> BreadcrumbSegment | None:
        if not self._segments:
            return None
        removed = self._segments.pop()
        self._render()
        return removed

    def clear(self) -> None:
        self._segments = []
        self._render()

    # ------------------------------------------------------------
    # Render
    # ------------------------------------------------------------

    def set_voltar_visivel(self, visivel: bool) -> None:
        """Liga/desliga o botão Voltar (default: ligado). Útil para
        T1 (home) onde Voltar não faz sentido."""
        self._mostrar_voltar = visivel
        self._render()

    def _render(self) -> None:
        # Limpa layout
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        if self._mostrar_voltar:
            self._layout.addWidget(self._build_voltar_btn())
            self._layout.addWidget(self._build_separator())

        total = len(self._segments)
        for i, seg in enumerate(self._segments):
            is_last = (i == total - 1)
            self._layout.addWidget(self._build_segment(i, seg, is_last))
            if not is_last:
                self._layout.addWidget(self._build_separator())

        self._layout.addStretch(1)

    def _build_voltar_btn(self) -> QWidget:
        btn = QPushButton("← Voltar")
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        btn.setToolTip("Voltar (Alt+←)")
        btn.setStyleSheet(
            f"""
            QPushButton {{
                color: {_COR_LINK};
                font-size: 10pt;
                font-weight: 500;
                padding: 2px 8px;
                background: transparent;
                border: 1px solid {_COR_LINK};
                border-radius: 2px;
            }}
            QPushButton:hover {{
                color: #FFFFFF;
                background: {_COR_LINK};
            }}
            QPushButton:focus {{
                outline: 1px solid {_COR_LINK};
            }}
            """
        )
        btn.clicked.connect(self.voltar_solicitado)
        return btn

    def _build_segment(
        self, idx: int, seg: BreadcrumbSegment, is_last: bool
    ) -> QWidget:
        if is_last:
            lbl = QLabel(seg.label)
            lbl.setStyleSheet(
                f"color: {_COR_ATUAL}; font-size: 10pt; font-weight: 500;"
                "background: transparent;"
            )
            return lbl

        btn = QPushButton(seg.label)
        btn.setFlat(True)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                color: {_COR_LINK};
                font-size: 10pt;
                padding: 2px 4px;
                background: transparent;
                border: none;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {_COR_LINK_HOVER};
                text-decoration: underline;
            }}
            QPushButton:focus {{
                outline: 1px solid {_COR_LINK};
            }}
            """
        )
        btn.clicked.connect(lambda _=False, i=idx: self._on_segment_clicked(i))
        return btn

    def _build_separator(self) -> QWidget:
        sep = QLabel("›")
        sep.setStyleSheet(
            f"color: {_COR_SEP}; font-size: 12pt; background: transparent;"
        )
        return sep

    # ------------------------------------------------------------
    # Ações
    # ------------------------------------------------------------

    def _on_segment_clicked(self, idx: int) -> None:
        # Pop até o segmento (semântica de truncamento — decisão #30).
        if idx >= len(self._segments):
            return
        seg = self._segments[idx]
        self._segments = self._segments[: idx + 1]
        self._render()
        self.segment_clicked.emit(idx)
        # Se o segmento tem target_tela, dispara navegação real.
        if seg.target_tela:
            self.target_tela_clicked.emit(seg.target_tela, dict(seg.payload))
