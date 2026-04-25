"""
T8 — Auditoria & Logs forense (Bloco 3 §3.8).

Trilha de importações de SPED para um cliente × ano-calendário, com
detecção automática de REIMPORT (mesmo sped_tipo + período, hash
diferente do anterior). Suporta a postura forense exigida pelo modelo
de honorários de êxito da Primetax (CLAUDE.md §1.1, §4 princípio 1).

Operações são síncronas — `_importacoes` raramente passa de algumas
dezenas de linhas por cliente×AC. Sem QThread.

Decisão #21 (CLAUDE.md GUI Bloco 6): export CSV + .sha256 companheiro.
Esta iteração entrega CSV+SHA; assinatura digital A1 fica fora do escopo.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.auditoria_controller import (
    AuditoriaController,
    ImportacaoRow,
)
from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.widgets import (
    BadgeStatus,
    BreadcrumbSegment,
    ColumnSpec,
    DataTable,
    EmptyState,
    FilterChip,
    Toast,
    TraceabilityBreadcrumb,
)


logger = logging.getLogger(__name__)


_PRIMARY_COLOR = "#008C95"

_LABELS_STATUS_BADGE = {
    "ok": BadgeStatus.OK,
    "parcial": BadgeStatus.MEDIO,
    "rejeitado": BadgeStatus.ALTO,
}


class T8Auditoria(QWidget):
    """Tela de auditoria/logs — trilha forense da tabela `_importacoes`."""

    csv_exportado = Signal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cliente: ClienteRow | None = None
        self._controller: AuditoriaController | None = None
        self._linhas_brutas: list[ImportacaoRow] = []
        self._filtros_sped: set[str] = set()
        self._filtros_status: set[str] = set()
        self._filtro_reimport: bool = False
        self._linha_selecionada: ImportacaoRow | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(10)

        # Header
        self._titulo = QLabel("Auditoria & Logs")
        self._titulo.setStyleSheet(
            f"color: {_PRIMARY_COLOR}; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        v.addWidget(self._breadcrumb)

        # Stack: empty vs. conteúdo
        self._stack = QStackedWidget()
        self._empty = EmptyState(
            title="Nenhum cliente selecionado",
            description=(
                "Selecione um cliente em T1 (Clientes) para visualizar a "
                "trilha de importações e auditoria do ano-calendário."
            ),
        )
        self._stack.addWidget(self._empty)

        self._conteudo = QWidget()
        cv = QVBoxLayout(self._conteudo)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(10)

        # Linha de filtros (chips) ----------------------------------
        self._chips_wrapper = QWidget()
        chips_layout = QHBoxLayout(self._chips_wrapper)
        chips_layout.setContentsMargins(0, 0, 0, 0)
        chips_layout.setSpacing(6)

        chips_layout.addWidget(self._lbl_filtro("SPED:"))
        self._chips_sped: dict[str, FilterChip] = {}
        for cid, lbl in [
            ("efd_contribuicoes", "EFD-Contrib"),
            ("efd_icms", "EFD ICMS/IPI"),
            ("ecd", "ECD"),
            ("ecf", "ECF"),
        ]:
            chip = FilterChip(lbl, cid)
            chip.toggled_with_id.connect(self._on_chip_sped)
            self._chips_sped[cid] = chip
            chips_layout.addWidget(chip)

        chips_layout.addSpacing(12)
        chips_layout.addWidget(self._lbl_filtro("Status:"))
        self._chips_status: dict[str, FilterChip] = {}
        for cid, lbl in [
            ("ok", "OK"),
            ("parcial", "Parcial"),
            ("rejeitado", "Rejeitado"),
        ]:
            chip = FilterChip(lbl, cid)
            chip.toggled_with_id.connect(self._on_chip_status)
            self._chips_status[cid] = chip
            chips_layout.addWidget(chip)

        chips_layout.addSpacing(12)
        self._chip_reimport = FilterChip("Apenas REIMPORT", "reimport")
        self._chip_reimport.toggled_with_id.connect(self._on_chip_reimport)
        chips_layout.addWidget(self._chip_reimport)

        chips_layout.addStretch()
        cv.addWidget(self._chips_wrapper)

        # Conteúdo: tabela à esquerda, painel detalhe à direita ----
        corpo = QHBoxLayout()
        corpo.setSpacing(12)

        col_main = QVBoxLayout()
        col_main.setSpacing(8)

        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=True,
            with_export=False,
            empty_message="Nenhuma importação registrada para este cliente × AC.",
        )
        self._tabela.setMinimumHeight(380)
        self._tabela.row_selected.connect(self._on_linha_selecionada)
        col_main.addWidget(self._tabela, 1)

        # Footer com botão Exportar CSV+SHA
        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.addStretch()
        self._btn_export = QPushButton("Exportar CSV forense (CSV + .sha256)")
        self._btn_export.setStyleSheet(self._qss_btn_primario())
        self._btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export.clicked.connect(self._exportar_csv)
        footer.addWidget(self._btn_export)
        wrap_footer = QWidget()
        wrap_footer.setLayout(footer)
        col_main.addWidget(wrap_footer)

        wrap_main = QWidget()
        wrap_main.setLayout(col_main)
        corpo.addWidget(wrap_main, 3)

        # Painel lateral — detalhe da importação
        self._painel = QWidget()
        self._painel.setMinimumWidth(300)
        self._painel.setStyleSheet(
            "background: #F7F7F8; border: 1px solid #D1D3D6; border-radius: 4px;"
        )
        pv = QVBoxLayout(self._painel)
        pv.setContentsMargins(14, 12, 14, 12)
        pv.setSpacing(8)

        self._painel_titulo = QLabel("Detalhe da importação")
        self._painel_titulo.setStyleSheet(
            "color: #53565A; font-size: 12pt; font-weight: 600; background: transparent;"
        )
        pv.addWidget(self._painel_titulo)

        self._painel_corpo = QLabel(
            "Selecione uma linha para ver hash completo, "
            "histórico de reimportação e metadados."
        )
        self._painel_corpo.setWordWrap(True)
        self._painel_corpo.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._painel_corpo.setStyleSheet(
            "color: #53565A; font-size: 10pt; background: transparent;"
        )
        pv.addWidget(self._painel_corpo)

        self._btn_abrir_arquivo = QPushButton("Abrir pasta do arquivo")
        self._btn_abrir_arquivo.setStyleSheet(self._qss_btn_secundario())
        self._btn_abrir_arquivo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_abrir_arquivo.clicked.connect(self._abrir_pasta_arquivo)
        self._btn_abrir_arquivo.setEnabled(False)
        pv.addWidget(self._btn_abrir_arquivo)

        pv.addStretch()
        corpo.addWidget(self._painel, 2)

        wrap_corpo = QWidget()
        wrap_corpo.setLayout(corpo)
        cv.addWidget(wrap_corpo, 1)

        self._stack.addWidget(self._conteudo)
        v.addWidget(self._stack, 1)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar_cliente(self, cliente: ClienteRow) -> None:
        self._cliente = cliente
        self._controller = AuditoriaController(
            cnpj=cliente.cnpj,
            ano_calendario=cliente.ano_calendario,
        )
        self._titulo.setText(
            f"Auditoria · {cliente.razao_social} · AC {cliente.ano_calendario}"
        )
        self._breadcrumb.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(
                label=f"{cliente.razao_social} × {cliente.ano_calendario}",
                target_tela="T3",
            ),
            BreadcrumbSegment(label="Auditoria"),
        ])
        self._recarregar()
        self._stack.setCurrentWidget(self._conteudo)

    def cliente_atual(self) -> ClienteRow | None:
        return self._cliente

    # ------------------------------------------------------------
    # Internos — leitura e renderização
    # ------------------------------------------------------------

    def _recarregar(self) -> None:
        if self._controller is None:
            return
        try:
            self._linhas_brutas = self._controller.listar_importacoes()
        except Exception as exc:  # noqa: BLE001
            logger.exception("falha ao listar importações")
            Toast.show_error(self.window(), f"Falha ao ler trilha: {exc}")
            self._linhas_brutas = []
        self._aplicar_filtros()

    def _aplicar_filtros(self) -> None:
        rows: list[dict] = []
        for linha in self._linhas_brutas:
            if self._filtros_sped and linha.sped_tipo not in self._filtros_sped:
                continue
            if self._filtros_status and linha.status not in self._filtros_status:
                continue
            if self._filtro_reimport and not linha.is_reimport:
                continue
            rows.append(self._linha_para_dict(linha))
        self._tabela.set_rows(rows)
        self._limpar_painel()

    @staticmethod
    def _linha_para_dict(linha: ImportacaoRow) -> dict:
        ts = linha.importado_em.strftime("%Y-%m-%d %H:%M") if linha.importado_em else "—"
        periodo = f"{linha.dt_ini} → {linha.dt_fin}"
        hash_curto = (linha.arquivo_hash or "")[:10] + "…" if linha.arquivo_hash else "—"
        encoding_label = (
            f"{linha.encoding_origem} ({linha.encoding_confianca})"
            if linha.encoding_origem else "—"
        )
        status_badge = _LABELS_STATUS_BADGE.get(linha.status, BadgeStatus.NA)
        reimport_label = "REIMPORT" if linha.is_reimport else ""
        return {
            "_id": linha.id,
            "importado_em": ts,
            "sped_label": linha.sped_label,
            "periodo": periodo,
            "arquivo": linha.arquivo_nome,
            "hash": hash_curto,
            "encoding": encoding_label,
            "status": status_badge,
            "reimport": reimport_label,
        }

    @staticmethod
    def _construir_colunas() -> list[ColumnSpec]:
        return [
            ColumnSpec(id="importado_em", header="Importado em", kind="text", width=140),
            ColumnSpec(id="sped_label", header="SPED", kind="text", width=130),
            ColumnSpec(id="periodo", header="Período", kind="text", width=200),
            ColumnSpec(id="arquivo", header="Arquivo", kind="text", width=240),
            ColumnSpec(id="hash", header="Hash (8)", kind="text", width=120),
            ColumnSpec(id="encoding", header="Encoding", kind="text", width=140),
            ColumnSpec(id="status", header="Status", kind="badge", width=110),
            ColumnSpec(id="reimport", header="REIMPORT", kind="text", width=110),
        ]

    # ------------------------------------------------------------
    # Filtros (chips)
    # ------------------------------------------------------------

    def _on_chip_sped(self, chip_id: str, ativo: bool) -> None:
        if ativo:
            self._filtros_sped.add(chip_id)
        else:
            self._filtros_sped.discard(chip_id)
        self._aplicar_filtros()

    def _on_chip_status(self, chip_id: str, ativo: bool) -> None:
        if ativo:
            self._filtros_status.add(chip_id)
        else:
            self._filtros_status.discard(chip_id)
        self._aplicar_filtros()

    def _on_chip_reimport(self, _chip_id: str, ativo: bool) -> None:
        self._filtro_reimport = ativo
        self._aplicar_filtros()

    # ------------------------------------------------------------
    # Painel lateral
    # ------------------------------------------------------------

    def _on_linha_selecionada(self, row_dict: dict) -> None:
        rid = row_dict.get("_id")
        linha = next(
            (l for l in self._linhas_brutas if l.id == rid),
            None,
        )
        self._linha_selecionada = linha
        if linha is None:
            self._limpar_painel()
            return
        self._popular_painel(linha)

    def _popular_painel(self, linha: ImportacaoRow) -> None:
        ts = linha.importado_em.strftime("%Y-%m-%d %H:%M:%S") if linha.importado_em else "—"
        sha_full = linha.arquivo_hash or "—"
        encoding = (
            f"{linha.encoding_origem} · confiança {linha.encoding_confianca}"
            if linha.encoding_origem else "—"
        )
        ctx_reimport = ""
        if linha.is_reimport and linha.hash_anterior:
            ctx_reimport = (
                "<br><br><b style='color:#C28B2F'>⚠ REIMPORT</b><br>"
                f"<span style='color:#787A80'>Hash anterior:</span><br>"
                f"<code style='font-size:9pt'>{linha.hash_anterior}</code>"
            )

        path_arquivo = self._html_escape(linha.arquivo_origem)

        self._painel_corpo.setText(
            f"<b>{linha.sped_label}</b> — {linha.dt_ini} → {linha.dt_fin}<br>"
            f"<span style='color:#787A80'>Importado em:</span> {ts}<br>"
            f"<span style='color:#787A80'>Versão:</span> {linha.cod_ver or '—'}<br>"
            f"<span style='color:#787A80'>Encoding:</span> {encoding}<br>"
            f"<span style='color:#787A80'>Status:</span> {linha.status}<br><br>"
            f"<span style='color:#787A80'>Arquivo:</span><br>"
            f"<code style='font-size:9pt'>{path_arquivo}</code><br><br>"
            f"<span style='color:#787A80'>SHA-256:</span><br>"
            f"<code style='font-size:9pt'>{sha_full}</code>"
            f"{ctx_reimport}"
        )
        self._btn_abrir_arquivo.setEnabled(True)

    def _limpar_painel(self) -> None:
        self._linha_selecionada = None
        self._painel_corpo.setText(
            "Selecione uma linha para ver hash completo, "
            "histórico de reimportação e metadados."
        )
        self._btn_abrir_arquivo.setEnabled(False)

    def _abrir_pasta_arquivo(self) -> None:
        if self._linha_selecionada is None:
            return
        path = Path(self._linha_selecionada.arquivo_origem)
        pasta = path.parent
        if not pasta.exists():
            Toast.show_warning(
                self.window(),
                f"Pasta não encontrada: {pasta}",
            )
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta)))

    # ------------------------------------------------------------
    # Export CSV + SHA
    # ------------------------------------------------------------

    def _exportar_csv(self) -> None:
        if self._cliente is None or self._controller is None:
            return
        destino = (
            Path("data/output") / self._cliente.cnpj
            / str(self._cliente.ano_calendario)
            / "auditoria.csv"
        )
        try:
            csv_path = self._controller.exportar_csv(destino)
        except Exception as exc:  # noqa: BLE001
            logger.exception("falha ao exportar CSV de auditoria")
            Toast.show_error(self.window(), f"Falha ao exportar: {exc}")
            return
        sha_path = csv_path.with_suffix(csv_path.suffix + ".sha256")
        Toast.show_success(
            self.window(),
            f"CSV gerado: {csv_path.name} (+ {sha_path.name})",
        )
        self.csv_exportado.emit(csv_path)

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------

    @staticmethod
    def _lbl_filtro(text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet(
            "color: #787A80; font-size: 9pt; font-weight: 600;"
        )
        return l

    @staticmethod
    def _html_escape(s: str) -> str:
        return (
            (s or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _qss_btn_primario() -> str:
        return f"""
        QPushButton {{
            background: {_PRIMARY_COLOR}; color: #FFFFFF; border: none;
            border-radius: 2px; padding: 8px 16px;
            font-size: 10pt; font-weight: 500;
        }}
        QPushButton:hover {{ background: #00A4AE; }}
        QPushButton:pressed {{ background: #006F76; }}
        """

    @staticmethod
    def _qss_btn_secundario() -> str:
        return f"""
        QPushButton {{
            background: #FFFFFF; color: {_PRIMARY_COLOR};
            border: 1px solid {_PRIMARY_COLOR};
            border-radius: 2px; padding: 6px 12px;
            font-size: 10pt; font-weight: 500;
        }}
        QPushButton:hover {{ background: #E6F3F4; }}
        QPushButton:disabled {{ color: #B3D7DA; border-color: #B3D7DA; }}
        """
