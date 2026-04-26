"""
T0 — Visualizador de regras de cruzamento (read-only).

Lista as 49 regras ativas no motor (`src.crossref.engine`) com seus
metadados: código, camada, descrição, base legal, dependências de
SPED e sprint de origem. Permite ao auditor entender o que o sistema
cobre antes de rodar qualquer diagnóstico.

Não permite edição — adicionar regra é fluxo de código (slash command
`/novo-cruzamento` → revisão → merge), conforme CLAUDE.md §11.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.regras_controller import RegraInfo, RegrasController
from src.gui.widgets import (
    BadgeStatus,
    BreadcrumbSegment,
    ColumnSpec,
    DataTable,
    StatCard,
    TraceabilityBreadcrumb,
)


logger = logging.getLogger(__name__)


_CAMADAS_LABEL = {
    1: "Integridade",
    2: "Oportunidade",
    3: "Consistência",
}

_SEVERIDADE_PARA_BADGE = {
    "alto": BadgeStatus.ALTO,
    "medio": BadgeStatus.MEDIO,
    "médio": BadgeStatus.MEDIO,
    "baixo": BadgeStatus.BAIXO,
    "ok": BadgeStatus.OK,
    "n/a": BadgeStatus.NA,
    "—": BadgeStatus.NA,
    "": BadgeStatus.NA,
}


class T0Regras(QWidget):
    """Visualizador read-only das 49 regras de cruzamento."""

    def __init__(
        self,
        controller: RegrasController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller or RegrasController()
        self._regras: list[RegraInfo] = []
        self._regra_selecionada: RegraInfo | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        # Header
        self._titulo = QLabel("Regras de Cruzamento")
        self._titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        self._breadcrumb.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(label="Regras"),
        ])
        v.addWidget(self._breadcrumb)

        # Cards de resumo (totais por camada)
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_total = StatCard(title="Total de regras")
        self._card_camada1 = StatCard(title="Camada 1 (integridade)")
        self._card_camada2 = StatCard(title="Camada 2 (oportunidade)")
        self._card_camada3 = StatCard(title="Camada 3 (consistência)")
        for c in (
            self._card_total, self._card_camada1,
            self._card_camada2, self._card_camada3,
        ):
            cards_row.addWidget(c)
        wrap_cards = QWidget()
        wrap_cards.setLayout(cards_row)
        v.addWidget(wrap_cards)

        # Corpo: tabela à esquerda + painel detalhe à direita
        corpo = QHBoxLayout()
        corpo.setSpacing(12)

        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=True,
            with_export=True,
            empty_message="Nenhuma regra encontrada (motor vazio?).",
        )
        self._tabela.setMinimumHeight(360)
        self._tabela.row_selected.connect(self._on_regra_selecionada)
        corpo.addWidget(self._tabela, 3)

        # Painel detalhe — usa QTextBrowser em vez de QLabel porque o
        # QLabel não quebra strings longas (ex: REGRA_COMPATIBILIDADE_K155_E155
        # ou caminhos Python como src.crossref.camada_2_oportunidades.cruzamento_X)
        # e força overflow horizontal clipado. QTextBrowser quebra
        # naturalmente e tem scroll vertical embutido.
        painel = QWidget()
        painel.setStyleSheet(
            "background: #F7F7F8; border: 1px solid #D1D3D6; border-radius: 4px;"
        )
        pv = QVBoxLayout(painel)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.setSpacing(8)

        self._painel_titulo = QLabel("Detalhe da regra")
        self._painel_titulo.setStyleSheet(
            "color: #53565A; font-size: 12pt; font-weight: 600; "
            "background: transparent; border: none;"
        )
        pv.addWidget(self._painel_titulo)

        self._painel_corpo = QTextBrowser()
        self._painel_corpo.setOpenExternalLinks(False)
        self._painel_corpo.setHtml(
            "<p style='color:#53565A'>"
            "Selecione uma regra na tabela para ver código, base legal, "
            "dependências de SPED e sprint de origem."
            "</p>"
        )
        # Força wrap em qualquer caractere quando não houver espaço — evita
        # overflow horizontal causado por identificadores longos.
        self._painel_corpo.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        self._painel_corpo.setStyleSheet(
            "QTextBrowser { background: #FFFFFF; "
            "border: 1px solid #E5E6E8; border-radius: 2px; "
            "color: #53565A; font-size: 10pt; padding: 8px; }"
        )
        pv.addWidget(self._painel_corpo, 1)

        painel.setMinimumWidth(340)
        corpo.addWidget(painel, 2)

        wrap_corpo = QWidget()
        wrap_corpo.setLayout(corpo)
        v.addWidget(wrap_corpo, 1)

        self._carregar_regras()

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------

    def _carregar_regras(self) -> None:
        try:
            self._regras = self._controller.listar_regras()
        except Exception as exc:  # noqa: BLE001
            logger.exception("falha ao introspectar regras")
            self._regras = []

        rows = []
        for r in self._regras:
            rows.append({
                "_codigo": r.codigo,
                "codigo": r.codigo,
                "camada": _CAMADAS_LABEL.get(r.camada, str(r.camada)),
                "descricao": r.descricao,
                "severidade": _SEVERIDADE_PARA_BADGE.get(
                    r.severidade.lower(), BadgeStatus.NA
                ),
                "deps": ", ".join(r.dependencias_sped),
                "sprint": r.sprint or "—",
            })
        self._tabela.set_rows(rows)
        self._popular_cards()

    def _popular_cards(self) -> None:
        total = len(self._regras)
        c1 = sum(1 for r in self._regras if r.camada == 1)
        c2 = sum(1 for r in self._regras if r.camada == 2)
        c3 = sum(1 for r in self._regras if r.camada == 3)
        self._card_total.set_primary_value(str(total))
        self._card_total.set_secondary_value("regras ativas no motor", style="normal")
        self._card_camada1.set_primary_value(str(c1))
        self._card_camada2.set_primary_value(str(c2))
        self._card_camada3.set_primary_value(str(c3))

    def _on_regra_selecionada(self, row_dict: dict) -> None:
        codigo = row_dict.get("_codigo")
        regra = next(
            (r for r in self._regras if r.codigo == codigo), None,
        )
        self._regra_selecionada = regra
        if regra is None:
            return

        deps_html = ", ".join(
            f"<code>{self._html_escape(d)}</code>" for d in regra.dependencias_sped
        )
        # Quebra o caminho do módulo em pontos pra permitir wrap em
        # viewport estreito (QTextBrowser respeita word-wrap em pontos
        # de quebra naturais — pontos não são, mas espaços invisíveis sim).
        modulo_quebravel = regra.modulo_path.replace(".", ".​")
        self._painel_corpo.setHtml(
            f"<p><b style='font-size:13pt;color:#008C95'>{regra.codigo}</b></p>"
            f"<p><b>{self._html_escape(regra.descricao)}</b></p>"
            f"<p><span style='color:#787A80'>Camada:</span> "
            f"{regra.camada} — {_CAMADAS_LABEL.get(regra.camada, '')}</p>"
            f"<p><span style='color:#787A80'>Sprint de origem:</span> "
            f"{regra.sprint or 'não documentado'}</p>"
            f"<p><span style='color:#787A80'>Severidade típica:</span> "
            f"{regra.severidade or '—'}</p>"
            f"<p><span style='color:#787A80'>SPEDs requeridos:</span> "
            f"{deps_html}</p>"
            f"<p><span style='color:#787A80'>Base legal:</span><br>"
            f"{self._html_escape(regra.base_legal)}</p>"
            f"<p><span style='color:#787A80; font-size:9pt'>Módulo: "
            f"<code>{self._html_escape(modulo_quebravel)}</code></span></p>"
        )

    @staticmethod
    def _construir_colunas() -> list[ColumnSpec]:
        # Descrição é a ÚLTIMA coluna — stretchLastSection=True do DataTable
        # faz ela tomar todo espaço restante, evitando scroll horizontal
        # e garantindo que as outras colunas (códgio, severidade, etc.)
        # fiquem sempre visíveis.
        return [
            ColumnSpec(id="codigo", header="Código", kind="text", width=70),
            ColumnSpec(id="camada", header="Camada", kind="text", width=120),
            ColumnSpec(id="severidade", header="Severidade", kind="badge", width=110),
            ColumnSpec(id="sprint", header="Sprint", kind="text", width=80),
            ColumnSpec(id="deps", header="SPEDs", kind="text", width=160),
            ColumnSpec(id="descricao", header="Descrição", kind="text", width=400),
        ]

    @staticmethod
    def _html_escape(s: str) -> str:
        return (
            (s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
