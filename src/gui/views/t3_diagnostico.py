"""
T3 — Painel de Diagnóstico (Bloco 3 §3.3).

Visão macro do diagnóstico de um cliente × ano-calendário:
  - Header com Razão Social + AC + breadcrumb
  - 4 StatCards de topo (Oportunidades, Divergências, Pendências, Limitações)
  - DataTable com matriz de cruzamentos (CR-XX × status × achados × impacto)
  - Botão "Rerodar diagnóstico" (F5) — dispara DiagnosticoWorker em thread

Esta iteração entrega o caminho feliz: carregar dados existentes,
exibir, rerodar quando solicitado. Drill-down em CR específica
(navegação para T4) fica para a iteração seguinte.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.diagnostico_controller import (
    CruzamentoRow,
    DiagnosticoController,
    DiagnosticoView,
)
from src.gui.threading.diagnostico_worker import ResultadoDiagnostico
from src.gui.widgets import (
    BadgeStatus,
    BreadcrumbSegment,
    ColumnSpec,
    DataTable,
    EmptyState,
    InlineMessage,
    MessageLevel,
    ProgressIndicator,
    ProgressMode,
    ProgressState,
    StatCard,
    Toast,
    TraceabilityBreadcrumb,
)

logger = logging.getLogger(__name__)


_SEVERIDADE_PARA_BADGE = {
    "alto":     BadgeStatus.ALTO,
    "medio":    BadgeStatus.MEDIO,
    "baixo":    BadgeStatus.BAIXO,
    "ok":       BadgeStatus.OK,
    "pendente": BadgeStatus.PENDENTE,
    "na":       BadgeStatus.NA,
}


class T3Diagnostico(QWidget):
    """Painel de diagnóstico para um cliente × AC."""

    rerodada_concluida = Signal(int, int)   # oportunidades, divergencias

    def __init__(
        self,
        controller: DiagnosticoController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller or DiagnosticoController()
        self._cliente_atual: ClienteRow | None = None
        self._em_execucao = False

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        # Header
        self._titulo = QLabel("Diagnóstico")
        self._titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        v.addWidget(self._breadcrumb)

        # Stacked: empty state inicial vs. conteúdo
        self._stack = QStackedWidget()

        self._empty = EmptyState(
            title="Nenhum cliente selecionado",
            description=(
                "Selecione um cliente em T1 (Clientes) para ver o diagnóstico. "
                "Os 47+ cruzamentos são executados sobre os SPEDs já importados."
            ),
        )
        self._stack.addWidget(self._empty)

        # Conteúdo principal
        self._conteudo = QWidget()
        cv = QVBoxLayout(self._conteudo)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(12)

        # 4 StatCards de topo
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        self._card_op = StatCard(title="Oportunidades")
        self._card_div = StatCard(title="Divergências de Integridade")
        self._card_pend = StatCard(title="Pendências Recuperáveis")
        self._card_lim = StatCard(title="Limitações Estruturais")
        for c in (self._card_op, self._card_div, self._card_pend, self._card_lim):
            cards_row.addWidget(c)

        wrap_cards = QWidget()
        wrap_cards.setLayout(cards_row)
        cv.addWidget(wrap_cards)

        # Mensagem inline (ex: "diagnóstico não rodou ainda")
        self._inline_aviso: InlineMessage | None = None
        self._inline_wrapper = QWidget()
        self._inline_layout = QVBoxLayout(self._inline_wrapper)
        self._inline_layout.setContentsMargins(0, 0, 0, 0)
        self._inline_layout.setSpacing(0)
        cv.addWidget(self._inline_wrapper)

        # DataTable de cruzamentos
        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=True,
            with_export=True,
            empty_message="Nenhum cruzamento corresponde ao filtro.",
        )
        self._tabela.setMinimumHeight(280)
        cv.addWidget(self._tabela, 1)

        # ProgressIndicator (oculto até rerodar)
        self._progress = ProgressIndicator(mode=ProgressMode.INDETERMINATE)
        self._progress.set_cancellable(False)
        self._progress.setVisible(False)
        cv.addWidget(self._progress)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        self._btn_rerodar = QPushButton("Rerodar diagnóstico (F5)")
        self._btn_rerodar.setStyleSheet(self._qss_btn_primario())
        self._btn_rerodar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_rerodar.clicked.connect(self._rerodar)
        self._btn_rerodar.setEnabled(False)
        footer.addWidget(self._btn_rerodar)

        wrap_footer = QWidget()
        wrap_footer.setLayout(footer)
        cv.addWidget(wrap_footer)

        self._stack.addWidget(self._conteudo)

        v.addWidget(self._stack, 1)

        # Atalho F5
        QShortcut(QKeySequence("F5"), self, activated=self._rerodar)

        # Sinais do controller
        self._controller.diagnostico_iniciado.connect(self._on_diagnostico_iniciado)
        self._controller.diagnostico_log.connect(
            lambda lvl, msg: self._progress.append_log(lvl, msg)
        )
        self._controller.diagnostico_concluido.connect(self._on_diagnostico_concluido)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar_cliente(self, cliente: ClienteRow) -> None:
        """Troca o cliente atual da tela e atualiza tudo."""
        self._cliente_atual = cliente
        self._titulo.setText(f"{cliente.razao_social} · AC {cliente.ano_calendario}")
        self._breadcrumb.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(
                label=f"{cliente.razao_social} × {cliente.ano_calendario}",
            ),
            BreadcrumbSegment(label="Diagnóstico"),
        ])
        self._btn_rerodar.setEnabled(not self._em_execucao)
        self._stack.setCurrentWidget(self._conteudo)
        self._recarregar_dados()

    def cliente_atual(self) -> ClienteRow | None:
        return self._cliente_atual

    def shutdown(self) -> None:
        self._controller.shutdown()

    # ------------------------------------------------------------
    # Internos — leitura síncrona
    # ------------------------------------------------------------

    def _recarregar_dados(self) -> None:
        if self._cliente_atual is None:
            return
        view = self._controller.carregar_diagnostico(
            self._cliente_atual.cnpj, self._cliente_atual.ano_calendario
        )
        self._popular_cards(view)
        self._popular_tabela(view.cruzamentos)
        self._mostrar_aviso_inline(view)

    def _popular_cards(self, view: DiagnosticoView) -> None:
        self._card_op.set_primary_value(str(view.total_oportunidades))
        self._card_op.set_secondary_value(
            f"R$ {self._fmt_brl(view.impacto_conservador_total)} conservador",
            style="success",
        )
        self._card_op.set_hint(
            f"R$ {self._fmt_brl(view.impacto_maximo_total)} máximo"
        )

        self._card_div.set_primary_value(str(view.total_divergencias))
        self._card_div.set_secondary_value(
            "Camada 1 (integridade)" if view.total_divergencias else "—",
            style="error" if view.total_divergencias else "normal",
        )

        self._card_pend.set_primary_value(str(view.pendencias_recuperaveis))
        self._card_pend.set_secondary_value(
            "aguardando importação" if view.pendencias_recuperaveis else "—",
            style="warning" if view.pendencias_recuperaveis else "normal",
        )

        self._card_lim.set_primary_value(str(view.limitacoes_estruturais))
        self._card_lim.set_secondary_value(
            "inaplicáveis por opção fiscal" if view.limitacoes_estruturais else "—",
            style="info" if view.limitacoes_estruturais else "normal",
        )

    def _popular_tabela(self, cruzamentos: list[CruzamentoRow]) -> None:
        rows = []
        for cr in cruzamentos:
            rows.append({
                "codigo": cr.codigo_regra,
                "descricao": cr.descricao,
                "severidade": _SEVERIDADE_PARA_BADGE.get(cr.severidade, BadgeStatus.NA),
                "achados": cr.achados,
                "impacto": cr.impacto_conservador,
            })
        self._tabela.set_rows(rows)

    def _mostrar_aviso_inline(self, view: DiagnosticoView) -> None:
        # Limpa aviso anterior
        if self._inline_aviso is not None:
            self._inline_aviso.deleteLater()
            self._inline_aviso = None

        sem_dados = (
            view.total_oportunidades == 0
            and view.total_divergencias == 0
            and view.pendencias_recuperaveis == len(view.cruzamentos)
        )
        if sem_dados and view.cruzamentos:
            self._inline_aviso = InlineMessage(
                MessageLevel.INFO,
                "Diagnóstico ainda não foi executado para este cliente. "
                "Clique em 'Rerodar diagnóstico' (F5) para executar os 47+ cruzamentos.",
            )
            self._inline_layout.addWidget(self._inline_aviso)

    # ------------------------------------------------------------
    # Internos — execução do motor
    # ------------------------------------------------------------

    def _rerodar(self) -> None:
        if self._em_execucao or self._cliente_atual is None:
            return
        self._em_execucao = True
        self._btn_rerodar.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.set_state(ProgressState.RUNNING)
        self._progress.set_label(
            f"Rerodando diagnóstico de {self._cliente_atual.razao_social}..."
        )
        self._progress.expand_log(True)
        self._controller.diagnosticar(
            self._cliente_atual.cnpj, self._cliente_atual.ano_calendario
        )

    def _on_diagnostico_iniciado(self, cnpj: str, ano: int) -> None:
        # Apenas atualiza label do progress; controller já cuidou.
        pass

    def _on_diagnostico_concluido(self, resultado: ResultadoDiagnostico) -> None:
        self._em_execucao = False
        self._btn_rerodar.setEnabled(True)

        if resultado.sucesso:
            self._progress.set_state(ProgressState.SUCCESS)
            sumario = resultado.sumario or {}
            meses = sumario.get("meses", [])
            total_op = sum(m.get("oportunidades_camada2", 0) for m in meses)
            total_div = sum(m.get("divergencias_camada1", 0) for m in meses)
            Toast.show_success(
                self.window(),
                f"Diagnóstico concluído — {total_op} oportunidade(s), "
                f"{total_div} divergência(s).",
            )
            self.rerodada_concluida.emit(total_op, total_div)
        else:
            self._progress.set_state(ProgressState.ERROR)
            Toast.show_error(
                self.window(),
                f"Falha no diagnóstico: {resultado.mensagem}",
            )

        # Recarrega dados atualizados do banco
        self._recarregar_dados()

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @staticmethod
    def _construir_colunas() -> list[ColumnSpec]:
        return [
            ColumnSpec(id="codigo", header="Regra", kind="text", width=80),
            ColumnSpec(id="descricao", header="Descrição", kind="text", width=380),
            ColumnSpec(id="severidade", header="Status", kind="badge", width=130),
            ColumnSpec(id="achados", header="Achados", kind="int", width=80),
            ColumnSpec(id="impacto", header="Impacto Conservador", kind="money", width=170),
        ]

    @staticmethod
    def _fmt_brl(v: Decimal) -> str:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return "0,00"
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _qss_btn_primario() -> str:
        return """
        QPushButton {
            background: #008C95; color: #FFFFFF; border: none;
            border-radius: 2px; padding: 8px 16px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #00A4AE; }
        QPushButton:pressed { background: #006F76; }
        QPushButton:disabled { background: #B3D7DA; color: #FFFFFF; }
        """
