"""
T2 — Tela de Importação de SPEDs (Bloco 3 §3.2).

Drop zone para arquivos + fila + log estruturado + ProgressIndicator.
Usa ImportacaoController para rodar parse em thread separada.

Esta iteração entrega o caminho feliz (drop, importa, recarrega T1).
Confirmação interativa de encoding suspeito (modal pré-fila) e
pause/retomar ficam para iteração seguinte — por enquanto, encoding
'auto' do parser detecta UTF-8 ou Latin-1 com fallback.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.importacao_controller import ImportacaoController
from src.gui.threading.parser_worker import ResultadoArquivo
from src.gui.widgets import (
    BadgeStatus,
    ColumnSpec,
    DataTable,
    InlineMessage,
    MessageLevel,
    ProgressIndicator,
    ProgressMode,
    ProgressState,
    Toast,
)

logger = logging.getLogger(__name__)


_SUFIXOS_SPED = {".txt", ".sped", ".efd", ".ecd", ".ecf"}


class _DropZone(QFrame):
    """Frame que aceita drag-and-drop de arquivos. Sinal `arquivos_soltados`."""

    arquivos_soltados = Signal(list)
    clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("DropZone")
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._aplicar_qss(False)

        v = QVBoxLayout(self)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.setSpacing(4)
        v.setContentsMargins(20, 20, 20, 20)

        self._icon = QLabel("⬇")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet(
            "color: #008C95; font-size: 26pt; background: transparent;"
        )
        v.addWidget(self._icon)

        self._titulo = QLabel("Arraste arquivos SPED aqui")
        self._titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._titulo.setStyleSheet(
            "color: #53565A; font-size: 11pt; font-weight: 500; background: transparent;"
        )
        v.addWidget(self._titulo)

        self._sub = QLabel("ou clique para selecionar")
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._sub.setStyleSheet(
            "color: #787A80; font-size: 9pt; background: transparent;"
        )
        v.addWidget(self._sub)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(ev)

    def dragEnterEvent(self, ev: QDragEnterEvent) -> None:  # noqa: N802
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()
            self._aplicar_qss(True)

    def dragLeaveEvent(self, ev) -> None:  # noqa: N802
        self._aplicar_qss(False)
        super().dragLeaveEvent(ev)

    def dropEvent(self, ev: QDropEvent) -> None:  # noqa: N802
        urls = ev.mimeData().urls()
        paths = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
        # Expande diretórios para listar arquivos com sufixos SPED
        expandidos: list[Path] = []
        for p in paths:
            if p.is_file():
                expandidos.append(p)
            elif p.is_dir():
                for sub in sorted(p.rglob("*")):
                    if sub.is_file() and sub.suffix.lower() in _SUFIXOS_SPED:
                        expandidos.append(sub)
        self._aplicar_qss(False)
        if expandidos:
            self.arquivos_soltados.emit(expandidos)
            ev.acceptProposedAction()

    def _aplicar_qss(self, hovering: bool) -> None:
        bg = "#E6F3F4" if hovering else "#FFFFFF"
        border_color = "#008C95"
        border_style = "solid" if hovering else "dashed"
        self.setStyleSheet(
            f"""
            #DropZone {{
                background: {bg};
                border: 2px {border_style} {border_color};
                border-radius: 4px;
            }}
            #DropZone:hover {{ background: #E6F3F4; }}
            """
        )


class T2Importacao(QWidget):
    """Tela de importação de SPEDs.

    Sinal `importacao_concluida(int sucessos)` é emitido após cada lote;
    consumidor (MainWindow) usa para recarregar T1.
    """

    importacao_concluida = Signal(int)

    def __init__(
        self,
        controller: ImportacaoController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller or ImportacaoController()
        self._fila: list[Path] = []
        self._em_execucao = False

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        # Header
        titulo = QLabel("Importação de SPEDs")
        titulo.setStyleSheet(
            "color: #008C95; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(titulo)

        # Drop zone
        self._drop = _DropZone()
        self._drop.arquivos_soltados.connect(self._adicionar_a_fila)
        self._drop.clicked.connect(self._abrir_picker)
        v.addWidget(self._drop)

        # Aviso (placeholder oculto — InlineMessage só quando relevante)
        self._aviso_wrapper = QWidget()
        self._aviso_layout = QVBoxLayout(self._aviso_wrapper)
        self._aviso_layout.setContentsMargins(0, 0, 0, 0)
        self._aviso_layout.setSpacing(6)
        v.addWidget(self._aviso_wrapper)

        # Tabela da fila
        self._tabela = DataTable(
            columns=self._construir_colunas(),
            rows=[],
            with_search=False,
            with_export=False,
            empty_message="Nenhum arquivo na fila. Arraste SPEDs acima.",
        )
        self._tabela.setMinimumHeight(180)
        v.addWidget(self._tabela, 1)

        # Progresso
        self._progress = ProgressIndicator(mode=ProgressMode.DETERMINATE)
        self._progress.set_cancellable(True)
        self._progress.cancel_requested.connect(self._on_cancelar)
        v.addWidget(self._progress)

        # Footer com botões
        footer = QHBoxLayout()
        footer.setSpacing(8)
        footer.addStretch()

        self._btn_limpar = QPushButton("Limpar fila")
        self._btn_limpar.setStyleSheet(self._qss_btn_secundario())
        self._btn_limpar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_limpar.clicked.connect(self._limpar_fila)
        footer.addWidget(self._btn_limpar)

        self._btn_iniciar = QPushButton("Iniciar importação")
        self._btn_iniciar.setStyleSheet(self._qss_btn_primario())
        self._btn_iniciar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_iniciar.clicked.connect(self._iniciar)
        self._btn_iniciar.setEnabled(False)
        footer.addWidget(self._btn_iniciar)

        wrap = QWidget()
        wrap.setLayout(footer)
        v.addWidget(wrap)

        # Conexões com controller
        self._controller.arquivo_iniciado.connect(self._on_arquivo_iniciado)
        self._controller.log_event.connect(self._on_log_event)
        self._controller.arquivo_concluido.connect(self._on_arquivo_concluido)
        self._controller.lote_concluido.connect(self._on_lote_concluido)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def add_arquivos(self, arquivos: list[Path]) -> None:
        self._adicionar_a_fila(arquivos)

    def shutdown(self) -> None:
        self._controller.shutdown()

    # ------------------------------------------------------------
    # Fila
    # ------------------------------------------------------------

    def _abrir_picker(self) -> None:
        dialog = QFileDialog(self, "Selecionar arquivos SPED")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        dialog.setNameFilter("SPED (*.txt *.sped *.efd *.ecd *.ecf);;Todos (*.*)")
        if dialog.exec():
            paths = [Path(p) for p in dialog.selectedFiles()]
            self._adicionar_a_fila(paths)

    def _adicionar_a_fila(self, arquivos: list[Path]) -> None:
        novos = []
        for arq in arquivos:
            if arq in self._fila:
                continue
            self._fila.append(arq)
            novos.append(self._linha_fila(arq, "pendente"))

        if novos:
            for n in novos:
                self._tabela.add_row(n)
            self._btn_iniciar.setEnabled(not self._em_execucao)
            self._progress.append_log(
                "INFO",
                f"{len(novos)} arquivo(s) adicionado(s) à fila",
            )

    def _limpar_fila(self) -> None:
        if self._em_execucao:
            return
        self._fila.clear()
        self._tabela.set_rows([])
        self._btn_iniciar.setEnabled(False)

    def _iniciar(self) -> None:
        if self._em_execucao or not self._fila:
            return
        self._em_execucao = True
        self._btn_iniciar.setEnabled(False)
        self._btn_limpar.setEnabled(False)
        self._progress.set_label(f"Importando {len(self._fila)} arquivo(s)...")
        self._progress.set_state(ProgressState.RUNNING)
        self._progress.set_progress(0, len(self._fila))
        self._controller.importar_lote(list(self._fila))

    def _on_cancelar(self) -> None:
        if not self._em_execucao:
            return
        self._controller.cancelar()
        self._progress.append_log("WARNING", "Cancelamento solicitado.")

    # ------------------------------------------------------------
    # Slots dos signals do controller
    # ------------------------------------------------------------

    def _on_arquivo_iniciado(self, arquivo: str, tipo_sped: str) -> None:
        self._atualizar_status_linha(arquivo, "processando", BadgeStatus.EM_PROCESSO)
        self._progress.set_label(f"{Path(arquivo).name}  ·  {tipo_sped}")

    def _on_log_event(self, arquivo: str, level: str, message: str) -> None:
        prefixo = f"{Path(arquivo).name}  " if arquivo else ""
        self._progress.append_log(level, f"{prefixo}{message}")

    def _on_arquivo_concluido(self, resultado: ResultadoArquivo) -> None:
        if resultado.sucesso:
            self._atualizar_status_linha(
                str(resultado.arquivo), "ok", BadgeStatus.OK,
                tipo_sped=resultado.tipo_sped, cnpj=resultado.cnpj,
            )
        else:
            self._atualizar_status_linha(
                str(resultado.arquivo), "falhou", BadgeStatus.ALTO,
                tipo_sped=resultado.tipo_sped, cnpj=resultado.cnpj,
            )
        # Avança a barra: contar quantos não-pendentes
        concluidos = sum(
            1 for r in self._tabela._model.rows()
            if r.get("status") in {"ok", "falhou", "cancelado"}
        )
        self._progress.set_progress(concluidos, len(self._fila))

    def _on_lote_concluido(self, total: int, sucessos: int, falhas: int) -> None:
        self._em_execucao = False
        self._btn_iniciar.setEnabled(False)
        self._btn_limpar.setEnabled(True)
        self._progress.set_label(
            f"Lote concluído — {sucessos} sucesso(s), {falhas} falha(s)"
        )
        if falhas == 0 and sucessos > 0:
            self._progress.set_state(ProgressState.SUCCESS)
            Toast.show_success(
                self.window(),
                f"{sucessos} arquivo(s) importado(s) com sucesso.",
            )
        elif falhas > 0 and sucessos > 0:
            self._progress.set_state(ProgressState.SUCCESS)
            Toast.show_warning(
                self.window(),
                f"{sucessos} sucesso(s), {falhas} falha(s) — verifique o log.",
            )
        elif falhas > 0:
            self._progress.set_state(ProgressState.ERROR)
            Toast.show_error(
                self.window(),
                f"Todos os {falhas} arquivo(s) falharam — verifique o log.",
            )
        else:
            self._progress.set_state(ProgressState.IDLE)

        self.importacao_concluida.emit(sucessos)

    # ------------------------------------------------------------
    # Helpers de tabela
    # ------------------------------------------------------------

    @staticmethod
    def _construir_colunas() -> list[ColumnSpec]:
        return [
            ColumnSpec(id="nome", header="Arquivo", kind="text", width=280),
            ColumnSpec(id="status_badge", header="Status", kind="badge", width=130),
            ColumnSpec(id="tipo_sped", header="Tipo", kind="text", width=130),
            ColumnSpec(id="cnpj", header="CNPJ", kind="text", width=160),
        ]

    def _linha_fila(self, arquivo: Path, status: str) -> dict:
        return {
            "_path": str(arquivo),
            "nome": arquivo.name,
            "status": status,
            "status_badge": BadgeStatus.PENDENTE,
            "tipo_sped": "—",
            "cnpj": "—",
        }

    def _atualizar_status_linha(
        self,
        arquivo_path: str,
        novo_status: str,
        badge: BadgeStatus,
        *,
        tipo_sped: str = "",
        cnpj: str = "",
    ) -> None:
        patch = {"status": novo_status, "status_badge": badge}
        if tipo_sped:
            patch["tipo_sped"] = self._label_tipo(tipo_sped)
        if cnpj:
            patch["cnpj"] = self._formatar_cnpj(cnpj)
        self._tabela.update_row(
            lambda r: r.get("_path") == arquivo_path,
            patch,
        )

    @staticmethod
    def _label_tipo(tipo: str) -> str:
        mapa = {
            "efd_contribuicoes": "EFD-Contribuições",
            "efd_icms_ipi": "EFD ICMS/IPI",
            "ecd": "ECD",
            "ecf": "ECF",
        }
        return mapa.get(tipo, tipo)

    @staticmethod
    def _formatar_cnpj(c: str) -> str:
        if len(c) != 14 or not c.isdigit():
            return c
        return f"{c[:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:]}"

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

    @staticmethod
    def _qss_btn_secundario() -> str:
        return """
        QPushButton {
            background: #FFFFFF; color: #008C95; border: 1px solid #008C95;
            border-radius: 2px; padding: 8px 14px;
            font-size: 10pt; font-weight: 500;
        }
        QPushButton:hover { background: #E6F3F4; }
        QPushButton:disabled { color: #787A80; border-color: #D1D3D6; }
        """
