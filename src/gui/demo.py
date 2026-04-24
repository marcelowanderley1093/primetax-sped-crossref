"""
Galeria visual dos componentes — `python -m src.gui.demo`.

"Living design system": exibe todos os componentes implementados lado a
lado, com variantes de estado. Usado para inspeção visual rápida durante
desenvolvimento. Não é parte do produto final.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.gui.widgets import (
    BadgeStatus,
    BreadcrumbSegment,
    CodigoLinkButton,
    SearchField,
    SpedType,
    StatCard,
    StatusBadge,
    TraceabilityBreadcrumb,
    VersionLabel,
)


def _section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-size: 14pt; font-weight: 600; color: #008C95; margin-top: 16px;"
    )
    return lbl


def _row_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet("color: #787A80; font-size: 10pt;")
    lbl.setMinimumWidth(180)
    return lbl


def _divider() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setStyleSheet("color: #D1D3D6;")
    return line


class DemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Primetax — Galeria de Componentes (Nível 0)")
        self.resize(960, 720)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: #F7F7F8; border: none;")

        root = QWidget()
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(24, 20, 24, 20)
        vbox.setSpacing(8)

        hdr = QLabel("Primetax SPED Cross-Reference")
        hdr.setStyleSheet(
            "font-size: 20pt; font-weight: 600; color: #53565A;"
        )
        vbox.addWidget(hdr)

        sub = QLabel(
            "Galeria de componentes — Nível 0 do design system. "
            "Cada seção mostra o componente em suas variantes principais."
        )
        sub.setStyleSheet("color: #787A80; font-size: 11pt;")
        sub.setWordWrap(True)
        vbox.addWidget(sub)

        self._montar_status_badge(vbox)
        vbox.addWidget(_divider())
        self._montar_version_label(vbox)
        vbox.addWidget(_divider())
        self._montar_codigo_link_button(vbox)
        vbox.addWidget(_divider())
        self._montar_search_field(vbox)
        vbox.addWidget(_divider())
        self._montar_breadcrumb(vbox)
        vbox.addWidget(_divider())
        self._montar_stat_cards(vbox)

        vbox.addStretch()
        scroll.setWidget(root)
        self.setCentralWidget(scroll)

    # ------------------------------------------------------------
    def _montar_status_badge(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("StatusBadge — 9 variantes"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        for i, status in enumerate(BadgeStatus):
            row, col = divmod(i, 3)
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(12)
            h.addWidget(_row_label(status.name))
            h.addWidget(StatusBadge(status))
            h.addStretch()
            grid.addWidget(container, row, col)

        wrap = QWidget()
        wrap.setLayout(grid)
        parent.addWidget(wrap)

        # Exemplo com pulso animado
        pulse_row = QHBoxLayout()
        pulse_row.addWidget(_row_label("EM_PROCESSO (pulse)"))
        badge_pulse = StatusBadge(BadgeStatus.EM_PROCESSO)
        badge_pulse.set_pulse(True)
        pulse_row.addWidget(badge_pulse)

        # Exemplo com texto customizado
        pulse_row.addWidget(_row_label("texto customizado"))
        pulse_row.addWidget(StatusBadge(BadgeStatus.ALTO, text="Perda em 42 dias"))
        pulse_row.addStretch()

        wrap2 = QWidget()
        wrap2.setLayout(pulse_row)
        parent.addWidget(wrap2)

    # ------------------------------------------------------------
    def _montar_version_label(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("VersionLabel — 4 tipos SPED × corrente/desatualizada"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        casos = [
            (SpedType.EFD_CONTRIB, "3.1.0", "atual"),
            (SpedType.EFD_CONTRIB, "2.9.0", "desatualizada"),
            (SpedType.EFD_ICMS, "3.2.2", "atual"),
            (SpedType.EFD_ICMS, "2.8.0", "desatualizada"),
            (SpedType.ECD, "9.00", "atual"),
            (SpedType.ECD, "8.00", "desatualizada"),
            (SpedType.ECF, "0012", "atual"),
            (SpedType.ECF, "0011", "desatualizada"),
        ]
        for i, (tipo, ver, nota) in enumerate(casos):
            row, col = divmod(i, 2)
            container = QWidget()
            h = QHBoxLayout(container)
            h.setContentsMargins(0, 0, 0, 0)
            h.addWidget(_row_label(f"{tipo.name} ({nota})"))
            h.addWidget(VersionLabel(tipo, ver))
            h.addStretch()
            grid.addWidget(container, row, col)

        wrap = QWidget()
        wrap.setLayout(grid)
        parent.addWidget(wrap)

    # ------------------------------------------------------------
    def _montar_codigo_link_button(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("CodigoLinkButton — link para linha do SPED"))

        h = QHBoxLayout()
        h.setSpacing(24)
        h.addWidget(_row_label("Não-visitado"))
        btn_fresh = CodigoLinkButton("efd_contrib_202501.txt", 1847, "C", "C170")
        btn_fresh.open_sped.connect(self._ao_abrir_sped)
        h.addWidget(btn_fresh)

        h.addWidget(_row_label("Visitado"))
        btn_visited = CodigoLinkButton("efd_contrib_202501.txt", 2014, "C", "C170")
        btn_visited.mark_visited(True)
        h.addWidget(btn_visited)

        h.addWidget(_row_label("Linha grande"))
        h.addWidget(CodigoLinkButton("ecd_2025.txt", 127843, "I", "I155"))

        h.addStretch()
        wrap = QWidget()
        wrap.setLayout(h)
        parent.addWidget(wrap)

        hint = QLabel(
            "Clique em qualquer link acima — o signal open_sped é emitido e "
            "o estado visitado é persistido em QSettings."
        )
        hint.setStyleSheet("color: #787A80; font-size: 10pt; margin-top: 4px;")
        hint.setWordWrap(True)
        parent.addWidget(hint)

        self._status_label = QLabel("(Clique um link para testar o signal)")
        self._status_label.setStyleSheet(
            "color: #008C95; font-size: 11pt; font-family: 'JetBrains Mono', Consolas;"
            "padding: 6px; background: #E6F3F4; border-radius: 2px;"
        )
        parent.addWidget(self._status_label)

    def _ao_abrir_sped(self, payload: dict) -> None:
        self._status_label.setText(
            f"open_sped emitido: arquivo={payload['arquivo']}  "
            f"linha={payload['linha']}  bloco={payload['bloco']}  "
            f"registro={payload['registro']}"
        )

    # ------------------------------------------------------------
    # Nível 1 — SearchField, TraceabilityBreadcrumb, StatCard
    # ------------------------------------------------------------

    def _montar_search_field(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("SearchField — filtro com debounce 150ms"))

        self._sf_query = QLabel("Digite acima para testar (min 2 chars, 150ms debounce)")
        self._sf_query.setStyleSheet(
            "color: #008C95; font-family: 'JetBrains Mono', Consolas; font-size: 10pt;"
            "padding: 6px; background: #E6F3F4; border-radius: 2px;"
        )

        sf = SearchField(placeholder="Filtrar 127 linhas...")
        sf.query_changed.connect(
            lambda q: self._sf_query.setText(f"query_changed: '{q}'")
        )
        sf.cleared.connect(
            lambda: self._sf_query.setText("cleared")
        )
        sf.set_match_count(0, 127)

        parent.addWidget(sf)
        parent.addWidget(self._sf_query)

    def _montar_breadcrumb(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("TraceabilityBreadcrumb — rastreabilidade §1"))

        bc = TraceabilityBreadcrumb()
        bc.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(label="ACME × 2025", target_tela="T3"),
            BreadcrumbSegment(label="CR-07 Tese 69", target_tela="T4"),
            BreadcrumbSegment(label="efd_contrib_202501.txt", target_tela="T5"),
            BreadcrumbSegment(label="L1847"),  # último = atual
        ])
        parent.addWidget(bc)

        self._bc_status = QLabel(
            "Clique num segmento — o breadcrumb faz pop até ali (decisão #30)"
        )
        self._bc_status.setStyleSheet(
            "color: #008C95; font-family: 'JetBrains Mono', Consolas; font-size: 10pt;"
            "padding: 6px; background: #E6F3F4; border-radius: 2px;"
        )
        bc.segment_clicked.connect(
            lambda i: self._bc_status.setText(
                f"segment_clicked({i}) → breadcrumb truncado: "
                f"{' › '.join(s.label for s in bc.segments())}"
            )
        )
        parent.addWidget(self._bc_status)

    def _montar_stat_cards(self, parent: QVBoxLayout) -> None:
        parent.addWidget(_section_title("StatCard — 4 cards de topo de T3"))

        row = QHBoxLayout()
        row.setSpacing(12)

        c1 = StatCard(title="Oportunidades", clickable=True)
        c1.set_primary_value("12")
        c1.set_secondary_value("R$ 847.520 conservador", style="success")
        c1.set_hint("R$ 1.2M máximo")
        c1.clicked.connect(lambda: self._sc_status.setText("Card 'Oportunidades' clicado"))
        row.addWidget(c1)

        c2 = StatCard(title="Divergências", clickable=True)
        c2.set_primary_value("3")
        c2.set_secondary_value("Alto: 1", style="error")
        c2.set_hint("Médio: 2")
        c2.clicked.connect(lambda: self._sc_status.setText("Card 'Divergências' clicado"))
        row.addWidget(c2)

        c3 = StatCard(title="Pendências", clickable=True)
        c3.set_primary_value("8")
        c3.set_secondary_value("aguardando ECF", style="warning")
        c3.set_hint("e EFD-ICMS")
        c3.clicked.connect(lambda: self._sc_status.setText("Card 'Pendências' clicado"))
        row.addWidget(c3)

        c4 = StatCard(title="Limitações", clickable=False)
        c4.set_primary_value("2")
        c4.set_secondary_value("inaplicáveis", style="info")
        c4.set_hint("(Simples Nacional)")
        row.addWidget(c4)

        wrap = QWidget()
        wrap.setLayout(row)
        parent.addWidget(wrap)

        self._sc_status = QLabel(
            "Clique num card clickable (os 3 primeiros); o quarto não é clicável"
        )
        self._sc_status.setStyleSheet(
            "color: #008C95; font-family: 'JetBrains Mono', Consolas; font-size: 10pt;"
            "padding: 6px; background: #E6F3F4; border-radius: 2px;"
        )
        parent.addWidget(self._sc_status)


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Primetax SPED Cross-Reference — Demo")
    app.setOrganizationName("Primetax Solutions")
    window = DemoWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
