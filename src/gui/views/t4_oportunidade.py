"""
T4 — Oportunidade/Divergência detalhada (Bloco 3 §3.4).

Drill-down em uma regra (CR-XX) selecionada em T3. Mostra:
  - Header com regra + breadcrumb + base legal (truncada)
  - Resumo: total evidências, impactos, revisadas
  - DataTable de evidências (uma linha por elemento de `evidencia_json`)
    com checkbox de revisão por linha (decisão #12)
  - DetailPanel à direita: campos_chave + nota editável (auto-save 800ms)

Esta primeira iteração deixa para depois:
  - Drill-down até T5 (visualizador de SPED) — link emite signal mas T5
    ainda não existe; mostra Toast informativo
  - Multi-seleção de evidências para "marcar todas como revisadas"
"""

from __future__ import annotations

import logging
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.oportunidade_controller import (
    EvidenciaRow,
    OportunidadeController,
    RegraDetalhe,
)
from src.gui.widgets import (
    BadgeStatus,
    BreadcrumbSegment,
    ColumnSpec,
    DataTable,
    EmptyState,
    StatusBadge,
    Toast,
    TraceabilityBreadcrumb,
)


logger = logging.getLogger(__name__)


_NOTA_DEBOUNCE_MS = 800


class T4Oportunidade(QWidget):
    """View T4 — drill-down em uma regra de cruzamento."""

    abrir_sped = Signal(dict)   # payload p/ T5: arquivo, linha, bloco, registro

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cliente: ClienteRow | None = None
        self._codigo_atual: str = ""
        self._controller: OportunidadeController | None = None
        self._evidencias: list[EvidenciaRow] = []
        self._evidencia_selecionada: EvidenciaRow | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        # Header (título + breadcrumb)
        self._titulo = QLabel("Oportunidade")
        self._titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        v.addWidget(self._breadcrumb)

        # Stacked: empty vs. conteúdo
        self._stack = QStackedWidget()
        self._empty = EmptyState(
            title="Nenhuma regra selecionada",
            description=(
                "Acesse esta tela via duplo-clique numa linha de cruzamento "
                "em T3 (Diagnóstico)."
            ),
        )
        self._stack.addWidget(self._empty)

        self._conteudo = QWidget()
        cv = QHBoxLayout(self._conteudo)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(12)

        # Coluna principal — resumo + tabela de evidências
        col_main = QVBoxLayout()
        col_main.setSpacing(8)

        self._resumo = QLabel("")
        self._resumo.setWordWrap(True)
        self._resumo.setStyleSheet(
            "color: #53565A; font-size: 11pt; "
            "background: #F7F7F8; border: 1px solid #D1D3D6; "
            "border-radius: 4px; padding: 12px;"
        )
        col_main.addWidget(self._resumo)

        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=True,
            with_export=True,
            empty_message="Nenhuma evidência para esta regra.",
        )
        self._tabela.setMinimumHeight(360)
        self._tabela.row_selected.connect(self._on_evidencia_selecionada)
        self._tabela.row_activated.connect(self._on_evidencia_ativada)
        col_main.addWidget(self._tabela, 1)

        # Footer com botão "Marcar todas revisadas"
        footer = QHBoxLayout()
        self._btn_marcar_todas = QPushButton("Marcar todas como revisadas")
        self._btn_marcar_todas.setStyleSheet(self._qss_btn_secundario())
        self._btn_marcar_todas.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_marcar_todas.clicked.connect(self._marcar_todas_revisadas)
        footer.addStretch()
        footer.addWidget(self._btn_marcar_todas)
        wrap_footer = QWidget()
        wrap_footer.setLayout(footer)
        col_main.addWidget(wrap_footer)

        wrap_main = QWidget()
        wrap_main.setLayout(col_main)
        cv.addWidget(wrap_main, 3)

        # Painel lateral — detalhes da evidência selecionada
        self._painel = QWidget()
        self._painel.setMinimumWidth(280)
        self._painel.setStyleSheet(
            "background: #F7F7F8; border: 1px solid #D1D3D6; border-radius: 4px;"
        )
        pv = QVBoxLayout(self._painel)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.setSpacing(8)

        self._painel_titulo = QLabel("Detalhe da evidência")
        self._painel_titulo.setStyleSheet(
            "color: #53565A; font-size: 12pt; font-weight: 600; background: transparent;"
        )
        pv.addWidget(self._painel_titulo)

        self._painel_corpo = QLabel(
            "Selecione uma evidência na tabela para ver detalhes e adicionar nota."
        )
        self._painel_corpo.setWordWrap(True)
        self._painel_corpo.setStyleSheet(
            "color: #787A80; font-size: 10pt; background: transparent;"
        )
        pv.addWidget(self._painel_corpo)

        # Nota editável (decisão #12)
        nota_label = QLabel("Nota do auditor")
        nota_label.setStyleSheet(
            "color: #53565A; font-size: 10pt; font-weight: 600; "
            "margin-top: 8px; background: transparent;"
        )
        pv.addWidget(nota_label)

        self._nota_edit = QPlainTextEdit()
        self._nota_edit.setPlaceholderText(
            "Texto livre — auto-salvo após 800ms sem digitação"
        )
        self._nota_edit.setMinimumHeight(120)
        self._nota_edit.setStyleSheet(
            "QPlainTextEdit { background: #FFFFFF; border: 1px solid #D1D3D6; "
            "border-radius: 2px; padding: 6px; color: #53565A; font-size: 10pt; } "
            "QPlainTextEdit:focus { border-color: #008C95; }"
        )
        self._nota_edit.setEnabled(False)
        self._nota_edit.textChanged.connect(self._on_nota_edit)
        pv.addWidget(self._nota_edit)

        self._nota_status = QLabel("")
        self._nota_status.setStyleSheet(
            "color: #787A80; font-size: 9pt; background: transparent;"
        )
        pv.addWidget(self._nota_status)

        # Botão "Marcar revisada" no painel
        self._btn_revisar = QPushButton("Marcar como revisada")
        self._btn_revisar.setStyleSheet(self._qss_btn_primario())
        self._btn_revisar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_revisar.clicked.connect(self._toggle_revisao)
        self._btn_revisar.setEnabled(False)
        pv.addWidget(self._btn_revisar)

        # Botão "Abrir no SPED" (T5)
        self._btn_sped = QPushButton("Abrir no SPED (T5)")
        self._btn_sped.setStyleSheet(self._qss_btn_secundario())
        self._btn_sped.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_sped.clicked.connect(self._abrir_no_sped)
        self._btn_sped.setEnabled(False)
        pv.addWidget(self._btn_sped)

        pv.addStretch()
        cv.addWidget(self._painel, 2)

        self._stack.addWidget(self._conteudo)
        v.addWidget(self._stack, 1)

        # Timer de debounce para auto-save da nota
        self._nota_timer = QTimer(self)
        self._nota_timer.setSingleShot(True)
        self._nota_timer.timeout.connect(self._salvar_nota)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar(self, cliente: ClienteRow, codigo_regra: str) -> None:
        """Carrega evidências de uma regra para o cliente."""
        self._cliente = cliente
        self._codigo_atual = codigo_regra

        self._controller = OportunidadeController(
            cnpj=cliente.cnpj,
            ano_calendario=cliente.ano_calendario,
        )
        detalhe, evidencias = self._controller.carregar_regra(codigo_regra)
        self._evidencias = evidencias

        self._titulo.setText(f"{codigo_regra} · {detalhe.descricao_curta}")
        self._breadcrumb.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(
                label=f"{cliente.razao_social} × {cliente.ano_calendario}",
                target_tela="T3",
            ),
            BreadcrumbSegment(label="Diagnóstico", target_tela="T3"),
            BreadcrumbSegment(label=codigo_regra),
        ])

        self._popular_resumo(detalhe)
        self._popular_tabela(evidencias)
        self._stack.setCurrentWidget(self._conteudo)
        self._limpar_painel()

    def cliente_atual(self) -> ClienteRow | None:
        return self._cliente

    def codigo_atual(self) -> str:
        return self._codigo_atual

    # ------------------------------------------------------------
    # Internos — exibição
    # ------------------------------------------------------------

    def _popular_resumo(self, det: RegraDetalhe) -> None:
        sev_label = {
            "alto": "ALTO", "medio": "MÉDIO", "baixo": "BAIXO",
            "ok": "OK", "pendente": "PENDENTE", "na": "N/A",
        }.get(det.severidade_predominante, det.severidade_predominante.upper())

        base_legal_resumo = (
            (det.base_legal[:240] + "...") if len(det.base_legal) > 240
            else det.base_legal
        ) or "(base legal não disponível na introspecção)"

        self._resumo.setText(
            f"<b>Severidade predominante:</b> {sev_label}<br>"
            f"<b>Evidências:</b> {det.total_evidencias}  ·  "
            f"<b>Revisadas:</b> {det.revisadas} / {det.total_evidencias}  ·  "
            f"<b>Impacto conservador:</b> R$ {self._fmt_brl(det.impacto_conservador_total)}  ·  "
            f"<b>Impacto máximo:</b> R$ {self._fmt_brl(det.impacto_maximo_total)}<br>"
            f"<span style='color:#787A80'>{self._html_escape(base_legal_resumo)}</span>"
        )

    def _popular_tabela(self, evs: list[EvidenciaRow]) -> None:
        rows = []
        for i, e in enumerate(evs):
            rows.append({
                "_idx": i,
                "revisada": "✓" if e.revisada else "",
                "arquivo": Path(e.arquivo).name if e.arquivo else "—",
                "linha": e.linha if e.linha else "—",
                "bloco": e.bloco or "—",
                "registro": e.registro or "—",
                "campos": self._sumarizar_campos(e.campos_chave),
                "impacto": e.impacto_conservador,
            })
        self._tabela.set_rows(rows)

    @staticmethod
    def _sumarizar_campos(campos: dict) -> str:
        if not campos:
            return ""
        partes = []
        for chave, valor in list(campos.items())[:3]:
            partes.append(f"{chave}={valor}")
        sufixo = "..." if len(campos) > 3 else ""
        return ", ".join(partes) + sufixo

    @staticmethod
    def _construir_colunas() -> list[ColumnSpec]:
        return [
            ColumnSpec(id="revisada", header="✓", kind="text", width=40),
            ColumnSpec(id="arquivo", header="Arquivo", kind="text", width=240),
            ColumnSpec(id="linha", header="Linha", kind="int", width=80),
            ColumnSpec(id="bloco", header="Bloco", kind="text", width=70),
            ColumnSpec(id="registro", header="Registro", kind="text", width=90),
            ColumnSpec(id="campos", header="Campos-chave (sumário)", kind="text", width=320),
            ColumnSpec(id="impacto", header="Impacto", kind="money", width=130),
        ]

    # ------------------------------------------------------------
    # Internos — interação com painel lateral
    # ------------------------------------------------------------

    def _on_evidencia_selecionada(self, row_dict: dict) -> None:
        idx = row_dict.get("_idx", -1)
        if idx < 0 or idx >= len(self._evidencias):
            return
        ev = self._evidencias[idx]
        self._evidencia_selecionada = ev

        # Re-popula painel
        nome_arq = Path(ev.arquivo).name if ev.arquivo else "—"
        corpo_html = (
            f"<b>Arquivo:</b> {self._html_escape(nome_arq)}<br>"
            f"<b>Linha:</b> {ev.linha}<br>"
            f"<b>Bloco / Registro:</b> {ev.bloco} / {ev.registro}<br><br>"
            f"<b>Campos-chave:</b><br>"
        )
        if ev.campos_chave:
            for chave, valor in ev.campos_chave.items():
                corpo_html += (
                    f"&nbsp;&nbsp;<span style='color:#787A80'>{self._html_escape(str(chave))}:</span> "
                    f"{self._html_escape(str(valor))}<br>"
                )
        else:
            corpo_html += "<i>nenhum</i>"
        self._painel_corpo.setText(corpo_html)

        # Carrega nota sem disparar auto-save
        self._nota_edit.blockSignals(True)
        self._nota_edit.setPlainText(ev.nota or "")
        self._nota_edit.blockSignals(False)
        self._nota_edit.setEnabled(True)
        self._nota_status.setText("")

        self._btn_revisar.setEnabled(True)
        self._btn_revisar.setText(
            "Desmarcar revisada" if ev.revisada else "Marcar como revisada"
        )
        self._btn_sped.setEnabled(bool(ev.arquivo and ev.linha))

    def _on_evidencia_ativada(self, row_dict: dict) -> None:
        # Duplo-clique = abrir SPED se houver arquivo+linha; senão noop.
        idx = row_dict.get("_idx", -1)
        if idx < 0 or idx >= len(self._evidencias):
            return
        ev = self._evidencias[idx]
        if ev.arquivo and ev.linha:
            self.abrir_sped.emit({
                "arquivo": ev.arquivo,
                "linha": ev.linha,
                "bloco": ev.bloco,
                "registro": ev.registro,
            })

    def _limpar_painel(self) -> None:
        self._evidencia_selecionada = None
        self._painel_corpo.setText(
            "Selecione uma evidência na tabela para ver detalhes e adicionar nota."
        )
        self._nota_edit.blockSignals(True)
        self._nota_edit.clear()
        self._nota_edit.blockSignals(False)
        self._nota_edit.setEnabled(False)
        self._btn_revisar.setEnabled(False)
        self._btn_revisar.setText("Marcar como revisada")
        self._btn_sped.setEnabled(False)
        self._nota_status.setText("")

    # ------------------------------------------------------------
    # Internos — ações de revisão
    # ------------------------------------------------------------

    def _on_nota_edit(self) -> None:
        self._nota_status.setText("salvando...")
        self._nota_timer.start(_NOTA_DEBOUNCE_MS)

    def _salvar_nota(self) -> None:
        if self._evidencia_selecionada is None or self._controller is None:
            return
        ev = self._evidencia_selecionada
        nota = self._nota_edit.toPlainText()
        try:
            self._controller.salvar_nota(ev.achado_id, ev.tabela, nota)
        except Exception as exc:  # noqa: BLE001
            self._nota_status.setText(f"erro: {exc}")
            return
        # Atualiza estado em memória da linha selecionada
        ev.nota = nota.strip() if nota.strip() else ""
        self._nota_status.setText("salvo")

    def _toggle_revisao(self) -> None:
        if self._evidencia_selecionada is None or self._controller is None:
            return
        ev = self._evidencia_selecionada
        try:
            if ev.revisada:
                self._controller.desmarcar_revisada(ev.achado_id, ev.tabela)
            else:
                self._controller.marcar_revisada(ev.achado_id, ev.tabela)
        except Exception as exc:  # noqa: BLE001
            Toast.show_error(self.window(), f"Falha ao atualizar revisão: {exc}")
            return

        # Recarrega lista para sincronizar todas as evidências do mesmo achado_id
        if self._cliente is not None:
            self.carregar(self._cliente, self._codigo_atual)
        Toast.show_success(
            self.window(),
            "Revisão atualizada." if ev.revisada else "Achado marcado como revisado.",
        )

    def _marcar_todas_revisadas(self) -> None:
        if self._controller is None or not self._evidencias:
            return
        # Marca cada achado_id distinto presente nas evidências visíveis
        rows_visiveis = self._tabela.visible_rows()
        achado_ids: set[tuple[int, str]] = set()
        for r in rows_visiveis:
            idx = r.get("_idx", -1)
            if 0 <= idx < len(self._evidencias):
                ev = self._evidencias[idx]
                achado_ids.add((ev.achado_id, ev.tabela))

        for achado_id, tabela in achado_ids:
            try:
                self._controller.marcar_revisada(achado_id, tabela)
            except Exception as exc:  # noqa: BLE001
                Toast.show_error(self.window(), f"Erro em {achado_id}: {exc}")

        if self._cliente is not None:
            self.carregar(self._cliente, self._codigo_atual)
        Toast.show_success(
            self.window(),
            f"{len(achado_ids)} achado(s) marcado(s) como revisado(s).",
        )

    def _abrir_no_sped(self) -> None:
        if self._evidencia_selecionada is None:
            return
        ev = self._evidencia_selecionada
        self.abrir_sped.emit({
            "arquivo": ev.arquivo,
            "linha": ev.linha,
            "bloco": ev.bloco,
            "registro": ev.registro,
        })

    # ------------------------------------------------------------
    # Helpers de formatação
    # ------------------------------------------------------------

    @staticmethod
    def _fmt_brl(v: Decimal) -> str:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return "0,00"
        return f"{f:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    @staticmethod
    def _html_escape(s: str) -> str:
        return (
            s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
        )

    @staticmethod
    def _qss_btn_primario() -> str:
        return """
        QPushButton {
            background: #008C95; color: #FFFFFF; border: none;
            border-radius: 2px; padding: 6px 14px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #00A4AE; }
        QPushButton:pressed { background: #006F76; }
        QPushButton:disabled { background: #B3D7DA; color: #FFFFFF; }
        """

    @staticmethod
    def _qss_btn_secundario() -> str:
        return """
        QPushButton {
            background: #FFFFFF; color: #008C95; border: 1px solid #008C95;
            border-radius: 2px; padding: 6px 14px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #E6F3F4; }
        QPushButton:disabled { color: #787A80; border-color: #D1D3D6; }
        """
