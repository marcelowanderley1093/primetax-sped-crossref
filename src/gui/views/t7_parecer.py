"""
T7 — Geração de Parecer Word (Bloco 3 §3.7).

Wrapper sobre word_parecer.gerar() do core. Auditor escolhe tese,
confirma metadados (consultor, CRC/OAB) e dispara worker.

Dropdown lista as 8 teses já mapeadas em word_parecer._TESES;
pré-seleciona a tese com maior número de achados para o cliente atual.
Após sucesso: Toast com [Abrir documento] [Abrir pasta].

Cliente atual vem da MainWindow no momento do carregamento — T7 não
guarda múltiplos clientes; é tela "stateful" do contexto atual.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.parecer_controller import ParecerController
from src.gui.threading.parecer_worker import ResultadoParecer
from src.gui.widgets import (
    BreadcrumbSegment,
    EmptyState,
    InlineMessage,
    MessageLevel,
    ProgressIndicator,
    ProgressMode,
    ProgressState,
    Toast,
    ToastAction,
    TraceabilityBreadcrumb,
)


logger = logging.getLogger(__name__)


_PRIMARY_COLOR = "#008C95"


class T7Parecer(QWidget):
    """Tela de geração de parecer Word."""

    parecer_gerado = Signal(Path)

    def __init__(
        self,
        controller: ParecerController | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = controller or ParecerController()
        self._cliente: ClienteRow | None = None
        self._em_execucao = False
        self._settings = QSettings("Primetax Solutions", "SpedCrossref")
        self._ultimo_destino: Path | None = None

        v = QVBoxLayout(self)
        v.setContentsMargins(20, 16, 20, 16)
        v.setSpacing(12)

        # Header
        self._titulo = QLabel("Geração de Parecer")
        self._titulo.setStyleSheet(
            f"color: {_PRIMARY_COLOR}; font-size: 18pt; font-weight: 600;"
        )
        v.addWidget(self._titulo)

        self._breadcrumb = TraceabilityBreadcrumb()
        v.addWidget(self._breadcrumb)

        # Stacked: empty vs. conteúdo
        self._stack = QStackedWidget()
        self._empty = EmptyState(
            title="Nenhum cliente selecionado",
            description=(
                "Selecione um cliente em T1 (Clientes) e rode o diagnóstico "
                "antes de gerar o parecer."
            ),
        )
        self._stack.addWidget(self._empty)

        # Conteúdo principal
        self._conteudo = QWidget()
        cv = QVBoxLayout(self._conteudo)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(12)

        # Aviso sobre dados — placeholder oculto
        self._aviso_wrapper = QWidget()
        self._aviso_layout = QVBoxLayout(self._aviso_wrapper)
        self._aviso_layout.setContentsMargins(0, 0, 0, 0)
        self._aviso_layout.setSpacing(0)
        cv.addWidget(self._aviso_wrapper)
        self._aviso_widget: InlineMessage | None = None

        # Form
        form_card = QWidget()
        form_card.setObjectName("FormCard")
        form_card.setStyleSheet(
            "#FormCard { background: #FFFFFF; border: 1px solid #D1D3D6; "
            "border-radius: 4px; }"
        )
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(16, 14, 16, 14)
        form_layout.setSpacing(10)

        self._combo_tese = QComboBox()
        self._combo_tese.setStyleSheet(self._qss_input())
        self._combo_tese.setCursor(Qt.CursorShape.PointingHandCursor)
        self._combo_tese.currentIndexChanged.connect(self._on_tese_changed)
        form_layout.addRow("Tese:", self._combo_tese)

        self._lbl_descricao = QLabel("")
        self._lbl_descricao.setWordWrap(True)
        self._lbl_descricao.setStyleSheet(
            "color: #787A80; font-size: 9pt; padding: 4px 0px;"
        )
        form_layout.addRow("", self._lbl_descricao)

        self._input_consultor = QLineEdit()
        self._input_consultor.setStyleSheet(self._qss_input())
        self._input_consultor.setPlaceholderText("Nome completo do consultor responsável")
        self._input_consultor.setText(
            self._settings.value("Parecer/consultor", "", type=str)
        )
        self._input_consultor.editingFinished.connect(self._salvar_consultor)
        form_layout.addRow("Consultor:", self._input_consultor)

        self._input_crc = QLineEdit()
        self._input_crc.setStyleSheet(self._qss_input())
        self._input_crc.setPlaceholderText("Ex.: CRC 1SP 123456")
        self._input_crc.setText(self._settings.value("Parecer/crc", "", type=str))
        self._input_crc.editingFinished.connect(self._salvar_crc)
        form_layout.addRow("CRC / OAB:", self._input_crc)

        cv.addWidget(form_card)

        # ProgressIndicator (oculto até gerar)
        self._progress = ProgressIndicator(mode=ProgressMode.INDETERMINATE)
        self._progress.set_cancellable(False)
        self._progress.setVisible(False)
        cv.addWidget(self._progress)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()

        self._btn_abrir_anterior = QPushButton("Abrir último parecer")
        self._btn_abrir_anterior.setStyleSheet(self._qss_btn_secundario())
        self._btn_abrir_anterior.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_abrir_anterior.clicked.connect(self._abrir_ultimo)
        self._btn_abrir_anterior.setVisible(False)
        footer.addWidget(self._btn_abrir_anterior)

        self._btn_gerar = QPushButton("Gerar parecer (Ctrl+P)")
        self._btn_gerar.setStyleSheet(self._qss_btn_primario())
        self._btn_gerar.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_gerar.clicked.connect(self._on_gerar_clicado)
        footer.addWidget(self._btn_gerar)

        wrap_footer = QWidget()
        wrap_footer.setLayout(footer)
        cv.addWidget(wrap_footer)
        cv.addStretch()

        self._stack.addWidget(self._conteudo)
        v.addWidget(self._stack, 1)

        # Conexões com controller
        self._controller.iniciado.connect(self._on_iniciado)
        self._controller.log_event.connect(
            lambda lvl, msg: self._progress.append_log(lvl, msg)
        )
        self._controller.concluido.connect(self._on_concluido)

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def carregar_cliente(self, cliente: ClienteRow) -> None:
        self._cliente = cliente
        self._titulo.setText(
            f"Parecer · {cliente.razao_social} · AC {cliente.ano_calendario}"
        )
        self._breadcrumb.set_segments([
            BreadcrumbSegment(label="Home", target_tela="T1"),
            BreadcrumbSegment(
                label=f"{cliente.razao_social} × {cliente.ano_calendario}",
                target_tela="T3",
            ),
            BreadcrumbSegment(label="Parecer"),
        ])
        self._popular_combo_tese()
        self._stack.setCurrentWidget(self._conteudo)

    def cliente_atual(self) -> ClienteRow | None:
        return self._cliente

    def shutdown(self) -> None:
        self._controller.shutdown()

    # ------------------------------------------------------------
    # Internos — populando o formulário
    # ------------------------------------------------------------

    def _popular_combo_tese(self) -> None:
        if self._cliente is None:
            return
        self._combo_tese.blockSignals(True)
        self._combo_tese.clear()

        try:
            contagens = self._controller.achados_por_tese(
                self._cliente.cnpj, self._cliente.ano_calendario,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("falha ao contar achados por tese")
            contagens = {}

        teses = self._controller.listar_teses()
        # Ordena: maior número de achados primeiro; empate alfabético
        teses_ordenadas = sorted(
            teses,
            key=lambda kv: (-contagens.get(kv[0], 0), kv[0]),
        )

        for codigo, spec in teses_ordenadas:
            achados = contagens.get(codigo, 0)
            sufixo = (
                f"  ·  {achados} achado{'s' if achados != 1 else ''}"
                if achados else "  ·  sem achados"
            )
            label = f"{spec.get('nome', codigo)}{sufixo}"
            self._combo_tese.addItem(label, codigo)

        self._combo_tese.blockSignals(False)
        if self._combo_tese.count() > 0:
            self._combo_tese.setCurrentIndex(0)
            self._on_tese_changed(0)

        # Mostra aviso se não há nenhum achado
        total_achados = sum(contagens.values())
        self._mostrar_aviso(total_achados)

    def _mostrar_aviso(self, total_achados: int) -> None:
        if self._aviso_widget is not None:
            self._aviso_widget.deleteLater()
            self._aviso_widget = None

        if total_achados == 0:
            self._aviso_widget = InlineMessage(
                MessageLevel.WARNING,
                "Nenhum achado registrado para este cliente. "
                "Rode o diagnóstico em T3 antes de gerar o parecer.",
            )
            self._aviso_layout.addWidget(self._aviso_widget)

    def _on_tese_changed(self, _idx: int) -> None:
        codigo = self._combo_tese.currentData()
        if not codigo:
            return
        teses = dict(self._controller.listar_teses())
        spec = teses.get(codigo, {})
        descricao = spec.get("descricao_curta") or spec.get("descricao", "") or ""
        if isinstance(descricao, str):
            descricao = descricao.strip()
        # Trunca em 320 chars
        if len(descricao) > 320:
            descricao = descricao[:320] + "..."
        self._lbl_descricao.setText(descricao or "(sem descrição)")

    # ------------------------------------------------------------
    # Internos — geração
    # ------------------------------------------------------------

    def _on_gerar_clicado(self) -> None:
        if self._em_execucao or self._cliente is None:
            return
        codigo_tese = self._combo_tese.currentData()
        if not codigo_tese:
            return

        # Caminho destino — convenção: data/output/{cnpj}/{ano}/parecer_{tese}.docx
        destino = (
            Path("data/output") / self._cliente.cnpj
            / str(self._cliente.ano_calendario)
            / f"parecer_{codigo_tese.replace('-', '_')}.docx"
        )
        destino.parent.mkdir(parents=True, exist_ok=True)

        consultor = self._input_consultor.text().strip()

        self._em_execucao = True
        self._btn_gerar.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.expand_log(True)
        self._progress.set_state(ProgressState.RUNNING)
        self._progress.set_label(
            f"Gerando parecer ({codigo_tese})..."
        )

        self._controller.gerar(
            self._cliente.cnpj, self._cliente.ano_calendario,
            codigo_tese, destino, consultor,
        )

    def _on_iniciado(self, cnpj: str, ano: int, tese: str) -> None:
        # Apenas log via _on_log_event (já vinculado).
        pass

    def _on_concluido(self, resultado: ResultadoParecer) -> None:
        self._em_execucao = False
        self._btn_gerar.setEnabled(True)

        if resultado.sucesso and resultado.destino is not None:
            self._progress.set_state(ProgressState.SUCCESS)
            self._ultimo_destino = resultado.destino
            self._btn_abrir_anterior.setVisible(True)
            self.parecer_gerado.emit(resultado.destino)

            destino_path = resultado.destino
            Toast.show_success(
                self.window(),
                f"Parecer gerado: {destino_path.name}",
                action=ToastAction(
                    label="Abrir documento",
                    callback=lambda p=destino_path: self._abrir_arquivo(p),
                ),
            )
        else:
            self._progress.set_state(ProgressState.ERROR)
            Toast.show_error(
                self.window(),
                f"Falha ao gerar parecer: {resultado.mensagem}",
            )

    def _abrir_ultimo(self) -> None:
        if self._ultimo_destino is None:
            return
        self._abrir_arquivo(self._ultimo_destino)

    def _abrir_arquivo(self, path: Path) -> None:
        if not path.exists():
            Toast.show_warning(self.window(), "Arquivo não encontrado.")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    # ------------------------------------------------------------
    # Persistência de QSettings
    # ------------------------------------------------------------

    def _salvar_consultor(self) -> None:
        self._settings.setValue("Parecer/consultor", self._input_consultor.text().strip())

    def _salvar_crc(self) -> None:
        self._settings.setValue("Parecer/crc", self._input_crc.text().strip())

    # ------------------------------------------------------------
    # Estilos
    # ------------------------------------------------------------

    @staticmethod
    def _qss_input() -> str:
        return f"""
        QLineEdit, QComboBox {{
            padding: 6px 10px;
            border: 1px solid #D1D3D6;
            border-radius: 2px;
            background: #FFFFFF;
            color: #53565A;
            font-size: 10pt;
            min-height: 24px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {_PRIMARY_COLOR};
        }}
        QComboBox::drop-down {{ border: none; }}
        """

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
        QPushButton:disabled {{ background: #B3D7DA; color: #FFFFFF; }}
        """

    @staticmethod
    def _qss_btn_secundario() -> str:
        return f"""
        QPushButton {{
            background: #FFFFFF; color: {_PRIMARY_COLOR};
            border: 1px solid {_PRIMARY_COLOR};
            border-radius: 2px; padding: 8px 14px;
            font-size: 10pt; font-weight: 500;
        }}
        QPushButton:hover {{ background: #E6F3F4; }}
        """
