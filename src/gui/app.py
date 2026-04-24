"""
AppShell — janela principal do Primetax SPED Cross-Reference.

Estrutura (Bloco 3 §3.0):
  ┌─ Menubar (Arquivo / Editar / Cliente / Ferramentas / Ajuda) ──┐
  │  Side Rail (72px) │ Área Central (T1-T9 conforme navegação)   │
  │  T1..T9 ícones    │                                           │
  ├───────────────────┴───────────────────────────────────────────┤
  │ Status: cliente ativo · banco · última importação · sistema   │
  └────────────────────────────────────────────────────────────────┘

Sprint 1 da GUI: apenas T1 (Clientes) ativa; demais SideRailItems
ficam disabled. Persistência de geometria via QSettings (decisão #16
fechada — sim).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStatusBar,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.controllers.clientes_controller import ClienteRow, ClientesController
from src.gui.controllers.diagnostico_controller import DiagnosticoController
from src.gui.controllers.importacao_controller import ImportacaoController
from src.gui.views.t1_clientes import T1Clientes
from src.gui.views.t2_importacao import T2Importacao
from src.gui.views.t3_diagnostico import T3Diagnostico
from src.gui.widgets import SideRailItem, Toast


APP_NAME = "Primetax SPED Cross-Reference"
APP_VERSION = "0.2.0"
ORG_NAME = "Primetax Solutions"

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Janela principal — esqueleto pronto para hospedar T1-T9."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self._settings = QSettings(ORG_NAME, "SpedCrossref")

        self._restaurar_geometria()

        self._montar_menubar()
        self._montar_central()
        self._montar_statusbar()

    # ------------------------------------------------------------
    # Persistência de geometria (decisão #16)
    # ------------------------------------------------------------

    def _restaurar_geometria(self) -> None:
        geom = self._settings.value("MainWindow/geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(1280, 800)

        state = self._settings.value("MainWindow/state")
        if state:
            self.restoreState(state)

    # closeEvent unificado fica no fim do arquivo (gerencia worker + geometria).

    # ------------------------------------------------------------
    # Menubar
    # ------------------------------------------------------------

    def _montar_menubar(self) -> None:
        mb = self.menuBar()

        # Arquivo
        m_arq = mb.addMenu("&Arquivo")
        self._act_importar = QAction("Importar &SPED...", self)
        self._act_importar.setShortcut(QKeySequence("Ctrl+I"))
        self._act_importar.triggered.connect(self._on_importar_solicitado)
        m_arq.addAction(self._act_importar)
        m_arq.addSeparator()
        sair = QAction("&Sair", self)
        sair.setShortcut(QKeySequence("Ctrl+Q"))
        sair.triggered.connect(self.close)
        m_arq.addAction(sair)

        mb.addMenu("&Editar")
        mb.addMenu("&Cliente")
        mb.addMenu("&Ferramentas")
        mb.addMenu("&Ajuda")

    # ------------------------------------------------------------
    # Área central — side rail + view stack
    # ------------------------------------------------------------

    def _montar_central(self) -> None:
        central = QWidget()
        central.setStyleSheet("background: #FFFFFF;")
        h = QHBoxLayout(central)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # --- Side Rail ----------------------------------------
        rail = QWidget()
        rail.setObjectName("SideRail")
        rail.setFixedWidth(72)
        rail.setStyleSheet(
            "#SideRail { background: #F7F7F8; border-right: 1px solid #D1D3D6; }"
        )
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(0, 8, 0, 8)
        rail_layout.setSpacing(2)
        rail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._side_items: dict[str, SideRailItem] = {}

        for icon, tela_id, label, shortcut in [
            ("⌂", "T1", "Clientes",       "Ctrl+1"),
            ("⇩", "T2", "Importação",     "Ctrl+2"),
            ("▦", "T3", "Diagnóstico",    "Ctrl+3"),
            ("⚑", "T4", "Oportunidade",   "Ctrl+4"),
            ("≣", "T5", "Visualizador",   None),
            ("⊕", "T6", "Reconciliação",  "Ctrl+6"),
            ("✎", "T7", "Parecer",        "Ctrl+P"),
            ("⊙", "T8", "Auditoria",      "Ctrl+H"),
        ]:
            item = SideRailItem(icon, tela_id, label, shortcut, parent=rail)
            if tela_id == "T1":
                item.set_active(True)
            elif tela_id == "T2":
                pass  # ativo nesta iteração
            elif tela_id == "T3":
                item.setEnabled(False)  # habilitado quando há cliente aberto
                item.setToolTip(f"{label} — selecione um cliente em T1 primeiro")
            else:
                item.setEnabled(False)
                item.setToolTip(f"{label} — disponível em iteração futura")
            item.activated_with_tela.connect(self._navegar_para)
            rail_layout.addWidget(item)
            self._side_items[tela_id] = item

        rail_layout.addStretch()

        # T9 (config) na base do rail
        cfg = SideRailItem("⚙", "T9", "Configurações", "Ctrl+,", parent=rail)
        cfg.setEnabled(False)
        rail_layout.addWidget(cfg)
        self._side_items["T9"] = cfg

        h.addWidget(rail)

        # --- Área central (stack das views) -----------------
        self._central_stack = QStackedWidget()
        self._central_stack.setStyleSheet("background: #FFFFFF;")

        # T1 — Clientes
        self._t1 = T1Clientes(controller=ClientesController())
        self._t1.cliente_aberto.connect(self._on_cliente_aberto)
        self._t1.importacao_solicitada.connect(self._on_importar_solicitado)
        self._central_stack.addWidget(self._t1)

        # T2 — Importação (controller persistente — uma única QThread por sessão)
        self._import_controller = ImportacaoController(parent=self)
        self._t2 = T2Importacao(controller=self._import_controller)
        self._t2.importacao_concluida.connect(self._on_importacao_concluida)
        self._central_stack.addWidget(self._t2)

        # T3 — Diagnóstico (controller persistente)
        self._diag_controller = DiagnosticoController(parent=self)
        self._t3 = T3Diagnostico(controller=self._diag_controller)
        self._central_stack.addWidget(self._t3)

        h.addWidget(self._central_stack, 1)
        self.setCentralWidget(central)

        # Carregamento inicial dos clientes
        self._t1.recarregar()

        # Mapa tela_id → widget no stack
        self._tela_widgets: dict[str, QWidget] = {
            "T1": self._t1,
            "T2": self._t2,
            "T3": self._t3,
        }

    # ------------------------------------------------------------
    # Statusbar
    # ------------------------------------------------------------

    def _montar_statusbar(self) -> None:
        sb = QStatusBar(self)
        sb.setStyleSheet(
            "QStatusBar { background: #F7F7F8; color: #787A80; "
            "border-top: 1px solid #D1D3D6; font-size: 9pt; }"
        )

        self._sb_cliente = QLabel("Nenhum cliente ativo")
        sb.addWidget(self._sb_cliente)

        sb.addPermanentWidget(QLabel(f"Primetax SPED v{APP_VERSION}"))
        self.setStatusBar(sb)

    # ------------------------------------------------------------
    # Slots — eventos das views
    # ------------------------------------------------------------

    def _on_cliente_aberto(self, cliente: ClienteRow) -> None:
        """Carrega o cliente em T3 e navega para a tela."""
        self._sb_cliente.setText(
            f"Cliente: {cliente.razao_social}  ·  AC {cliente.ano_calendario}  "
            f"·  CNPJ {cliente.cnpj_formatado()}"
        )
        self._side_items["T3"].setEnabled(True)
        self._side_items["T3"].setToolTip("Diagnóstico · Ctrl+3")
        self._t3.carregar_cliente(cliente)
        self._navegar_para("T3")

    def _on_importar_solicitado(self) -> None:
        self._navegar_para("T2")

    def _on_importacao_concluida(self, sucessos: int) -> None:
        if sucessos > 0:
            self._t1.recarregar()

    # ------------------------------------------------------------
    # Navegação entre telas
    # ------------------------------------------------------------

    def _navegar_para(self, tela_id: str) -> None:
        widget = self._tela_widgets.get(tela_id)
        if widget is None:
            return
        self._central_stack.setCurrentWidget(widget)
        for tid, item in self._side_items.items():
            item.set_active(tid == tela_id)

    def closeEvent(self, ev) -> None:  # noqa: N802 (Qt API)
        # Encerra worker threads (importação e diagnóstico) limpamente
        try:
            self._t2.shutdown()
        except Exception:
            pass
        try:
            self._t3.shutdown()
        except Exception:
            pass
        self._settings.setValue("MainWindow/geometry", self.saveGeometry())
        self._settings.setValue("MainWindow/state", self.saveState())
        super().closeEvent(ev)


def run() -> int:
    logging.basicConfig(level=logging.INFO)
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORG_NAME)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
