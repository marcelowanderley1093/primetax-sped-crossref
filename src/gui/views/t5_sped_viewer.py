"""
T5 — Visualizador de SPED (Bloco 3 §3.5).

Tela-âncora da rastreabilidade fiscal (princípio §1 do CLAUDE.md).
Exibe a linha original do arquivo SPED com contexto e decompõe os
campos do registro para inspeção.

Layout:
  ┌─ Breadcrumb ───────────────────────────────────────────┐
  │ [↑ pai C100 L1720]  [◀◀ N anterior]  [N próximo ▶▶]    │
  ├─ Contexto (esquerda) ─┬─ Campos do registro (direita) ─┤
  │ L1845  |C170|...     │ #  Nome     Valor              │
  │ L1846  |C170|...     │ 1  REG      C170               │
  │ ▶L1847 |C170|042|... │ 2  campo[2] 001                │
  │ L1848  |C170|...     │ 3  campo[3] PROD-A-102         │
  │ ...                  │ ...                            │
  └──────────────────────┴────────────────────────────────┘

Atalhos:
  N            — próxima ocorrência do mesmo registro
  Shift+N      — anterior ocorrência
  Ctrl+↑       — saltar para registro pai (ex: C170 → C100)
  Backspace    — voltar (T4 ou tela anterior)
  Ctrl+F       — busca interna (delegada ao QListWidget)

Princípio §2 do CLAUDE.md: SPED original imutável — esta tela é
read-only por design.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.sped_viewer_controller import (
    ContextoLinha,
    SpedViewerController,
)
from src.gui.widgets import (
    BreadcrumbSegment,
    ColumnSpec,
    DataTable,
    EmptyState,
    Toast,
    TraceabilityBreadcrumb,
)


logger = logging.getLogger(__name__)


_COR_ALVO_BG = "#E6F3F4"
_COR_PARENT_BG = "#FFF9C4"
_COR_LINHA_NUM = "#787A80"
_COR_TEXTO = "#53565A"


class T5SpedViewer(QWidget):
    """Visualizador de linha SPED com contexto e decomposição de campos."""

    voltar_solicitado = Signal()  # navegação Backspace

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controller = SpedViewerController()
        self._cliente: ClienteRow | None = None
        self._codigo_origem: str = ""
        self._payload_atual: dict | None = None
        self._contexto: ContextoLinha | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        # Header
        self._titulo = QLabel("Visualizador SPED")
        self._titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        v.addWidget(self._breadcrumb)

        # Stacked: empty vs. conteúdo
        self._stack = QStackedWidget()
        self._empty = EmptyState(
            title="Nenhuma linha de SPED selecionada",
            description=(
                "Acesse esta tela via duplo-clique em uma evidência em T4 "
                "(Oportunidade)."
            ),
        )
        self._stack.addWidget(self._empty)

        # Conteúdo principal
        self._conteudo = QWidget()
        cv = QVBoxLayout(self._conteudo)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(8)

        # Barra de navegação
        nav_row = QHBoxLayout()
        nav_row.setSpacing(8)

        self._btn_voltar = QPushButton("← Voltar")
        self._btn_voltar.setStyleSheet(self._qss_btn_secundario())
        self._btn_voltar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_voltar.clicked.connect(self.voltar_solicitado)
        nav_row.addWidget(self._btn_voltar)

        self._btn_pai = QPushButton("↑ Registro pai")
        self._btn_pai.setStyleSheet(self._qss_btn_secundario())
        self._btn_pai.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_pai.clicked.connect(self._ir_para_pai)
        self._btn_pai.setEnabled(False)
        nav_row.addWidget(self._btn_pai)

        self._btn_anterior = QPushButton("◀◀ Anterior (Shift+N)")
        self._btn_anterior.setStyleSheet(self._qss_btn_secundario())
        self._btn_anterior.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_anterior.clicked.connect(self._ocorrencia_anterior)
        nav_row.addWidget(self._btn_anterior)

        self._btn_proximo = QPushButton("Próxima (N) ▶▶")
        self._btn_proximo.setStyleSheet(self._qss_btn_secundario())
        self._btn_proximo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_proximo.clicked.connect(self._ocorrencia_proxima)
        nav_row.addWidget(self._btn_proximo)

        nav_row.addStretch()

        self._info_arquivo = QLabel("")
        self._info_arquivo.setStyleSheet(
            "color: #787A80; font-size: 9pt; font-family: 'JetBrains Mono', Consolas;"
        )
        nav_row.addWidget(self._info_arquivo)

        wrap_nav = QWidget()
        wrap_nav.setLayout(nav_row)
        cv.addWidget(wrap_nav)

        # Splitter horizontal: contexto (esquerda) + campos (direita)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Contexto
        self._contexto_widget = QListWidget()
        self._contexto_widget.setStyleSheet(self._qss_contexto())
        self._contexto_widget.setMinimumWidth(420)
        font_mono = QFont("JetBrains Mono, Consolas, Courier New")
        font_mono.setStyleHint(QFont.StyleHint.Monospace)
        font_mono.setPointSize(9)
        self._contexto_widget.setFont(font_mono)
        self._contexto_widget.itemDoubleClicked.connect(self._on_linha_double_clicked)
        splitter.addWidget(self._contexto_widget)

        # Campos
        self._tabela_campos = DataTable(
            columns=[
                ColumnSpec(id="indice", header="#", kind="int", width=50),
                ColumnSpec(id="nome", header="Campo", kind="text", width=140),
                ColumnSpec(id="valor", header="Valor", kind="text", width=320),
            ],
            rows=[],
            with_search=False,
            with_export=False,
            empty_message="Selecione uma linha à esquerda.",
        )
        self._tabela_campos.setMinimumWidth(360)
        splitter.addWidget(self._tabela_campos)

        splitter.setSizes([520, 460])
        cv.addWidget(splitter, 1)

        self._stack.addWidget(self._conteudo)
        v.addWidget(self._stack, 1)

        # Atalhos
        QShortcut(QKeySequence("N"), self, activated=self._ocorrencia_proxima)
        QShortcut(QKeySequence("Shift+N"), self, activated=self._ocorrencia_anterior)
        QShortcut(QKeySequence("Ctrl+Up"), self, activated=self._ir_para_pai)
        QShortcut(QKeySequence("Backspace"), self, activated=self.voltar_solicitado)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar(
        self,
        cliente: ClienteRow,
        codigo_origem: str,
        payload: dict,
    ) -> None:
        """Abre a linha alvo do SPED indicado pelo payload.

        payload: dict com keys arquivo, linha, bloco, registro
        """
        self._cliente = cliente
        self._codigo_origem = codigo_origem
        self._payload_atual = dict(payload)

        arquivo = Path(payload.get("arquivo", ""))
        linha = int(payload.get("linha", 0) or 0)

        if not arquivo or not linha:
            Toast.show_error(self.window(), "Caminho ou linha de SPED inválido.")
            self._stack.setCurrentWidget(self._empty)
            return

        try:
            ctx = self._controller.carregar_arquivo(arquivo, linha)
        except FileNotFoundError as exc:
            Toast.show_error(self.window(), str(exc))
            self._stack.setCurrentWidget(self._empty)
            return
        except IndexError as exc:
            Toast.show_error(self.window(), str(exc))
            self._stack.setCurrentWidget(self._empty)
            return

        self._contexto = ctx
        self._popular_breadcrumb(arquivo, linha)
        self._popular_titulo(arquivo, linha, ctx.reg_alvo)
        self._popular_contexto(ctx)
        self._popular_campos(ctx)
        self._info_arquivo.setText(
            f"{arquivo.name}  ·  L{linha} de {ctx.total_linhas}  ·  "
            f"reg {ctx.reg_alvo}"
        )
        self._btn_pai.setEnabled(ctx.parent_linha is not None)
        if ctx.parent_linha is not None:
            self._btn_pai.setText(
                f"↑ Registro pai {ctx.parent_reg} L{ctx.parent_linha}"
            )
        else:
            self._btn_pai.setText("↑ Registro pai (n/d)")

        self._stack.setCurrentWidget(self._conteudo)

    # ------------------------------------------------------------
    # Internos — render
    # ------------------------------------------------------------

    def _popular_breadcrumb(self, arquivo: Path, linha: int) -> None:
        segmentos = []
        if self._cliente:
            segmentos.extend([
                BreadcrumbSegment(label="Home", target_tela="T1"),
                BreadcrumbSegment(
                    label=f"{self._cliente.razao_social} × {self._cliente.ano_calendario}",
                    target_tela="T3",
                ),
            ])
        if self._codigo_origem:
            segmentos.append(BreadcrumbSegment(
                label=self._codigo_origem, target_tela="T4",
            ))
        segmentos.extend([
            BreadcrumbSegment(label=arquivo.name),
            BreadcrumbSegment(label=f"L{linha}"),
        ])
        self._breadcrumb.set_segments(segmentos)

    def _popular_titulo(self, arquivo: Path, linha: int, reg: str) -> None:
        self._titulo.setText(f"{reg or '—'} · {arquivo.name} · L{linha}")

    def _popular_contexto(self, ctx: ContextoLinha) -> None:
        self._contexto_widget.clear()
        for i, raw in enumerate(ctx.linhas):
            n_linha = ctx.linha_offset + i
            prefixo = ">" if n_linha == ctx.linha_alvo else " "
            texto = f"{prefixo} L{n_linha:>6}  {raw}"
            item = QListWidgetItem(texto)
            if n_linha == ctx.linha_alvo:
                item.setBackground(self._cor(_COR_ALVO_BG))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            elif ctx.parent_linha and n_linha == ctx.parent_linha:
                item.setBackground(self._cor(_COR_PARENT_BG))
            item.setData(Qt.ItemDataRole.UserRole, n_linha)
            self._contexto_widget.addItem(item)

        # Centraliza na linha alvo
        self._contexto_widget.setCurrentRow(ctx.linha_alvo_idx)

    def _popular_campos(self, ctx: ContextoLinha) -> None:
        rows = []
        for c in ctx.campos:
            rows.append({
                "indice": c.indice,
                "nome": c.nome,
                "valor": c.valor,
            })
        self._tabela_campos.set_rows(rows)

    @staticmethod
    def _cor(hex_str: str):
        from PySide6.QtGui import QColor
        return QColor(hex_str)

    # ------------------------------------------------------------
    # Internos — navegação
    # ------------------------------------------------------------

    def _ir_para_pai(self) -> None:
        if not self._contexto or self._contexto.parent_linha is None:
            return
        if not self._payload_atual:
            return
        novo = dict(self._payload_atual)
        novo["linha"] = self._contexto.parent_linha
        novo["registro"] = self._contexto.parent_reg
        self.carregar(self._cliente, self._codigo_origem, novo)

    def _ocorrencia_proxima(self) -> None:
        if not self._contexto or not self._payload_atual:
            return
        prox = self._controller.proxima_ocorrencia(
            Path(self._payload_atual["arquivo"]),
            self._contexto.linha_alvo,
            self._contexto.reg_alvo,
        )
        if prox is None:
            Toast.show_info(
                self.window(),
                f"Nenhuma ocorrência seguinte de {self._contexto.reg_alvo}.",
            )
            return
        novo = dict(self._payload_atual)
        novo["linha"] = prox
        self.carregar(self._cliente, self._codigo_origem, novo)

    def _ocorrencia_anterior(self) -> None:
        if not self._contexto or not self._payload_atual:
            return
        ant = self._controller.anterior_ocorrencia(
            Path(self._payload_atual["arquivo"]),
            self._contexto.linha_alvo,
            self._contexto.reg_alvo,
        )
        if ant is None:
            Toast.show_info(
                self.window(),
                f"Nenhuma ocorrência anterior de {self._contexto.reg_alvo}.",
            )
            return
        novo = dict(self._payload_atual)
        novo["linha"] = ant
        self.carregar(self._cliente, self._codigo_origem, novo)

    def _on_linha_double_clicked(self, item: QListWidgetItem) -> None:
        n_linha = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(n_linha, int) or not self._payload_atual:
            return
        novo = dict(self._payload_atual)
        novo["linha"] = n_linha
        self.carregar(self._cliente, self._codigo_origem, novo)

    # ------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------

    @staticmethod
    def _qss_contexto() -> str:
        return """
        QListWidget {
            background: #FFFFFF;
            color: #53565A;
            border: 1px solid #D1D3D6;
            border-radius: 2px;
            padding: 4px;
        }
        QListWidget::item {
            padding: 2px 6px;
        }
        QListWidget::item:hover {
            background: #F7F7F8;
        }
        QListWidget::item:selected {
            background: #E6F3F4;
            color: #53565A;
            border-left: 2px solid #008C95;
        }
        """

    @staticmethod
    def _qss_btn_secundario() -> str:
        return """
        QPushButton {
            background: #FFFFFF; color: #008C95; border: 1px solid #008C95;
            border-radius: 2px; padding: 6px 12px;
            font-size: 9pt; font-weight: 500;
        }
        QPushButton:hover { background: #E6F3F4; }
        QPushButton:disabled { color: #787A80; border-color: #D1D3D6; }
        """
