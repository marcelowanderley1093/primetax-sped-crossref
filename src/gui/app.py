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
from pathlib import Path  # noqa: F401  (usado em _on_abrir_sped)

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence, QShortcut
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
from src.gui.controllers.parecer_controller import ParecerController
from src.gui.views.t0_regras import T0Regras
from src.gui.views.t1_clientes import T1Clientes
from src.gui.views.t2_importacao import T2Importacao
from src.gui.views.t3_diagnostico import T3Diagnostico
from src.gui.views.t4_oportunidade import T4Oportunidade
from src.gui.views.t5_sped_viewer import T5SpedViewer
from src.gui.views.t7_parecer import T7Parecer
from src.gui.views.t8_auditoria import T8Auditoria
from src.gui.widgets import SideRailItem, Toast
from src.gui.widgets.icons import IconName


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

        # Histórico de navegação para o atalho "Voltar".
        # Append em _navegar_para; pop em _voltar.
        self._nav_history: list[str] = []

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
        self._act_voltar = QAction("← &Voltar", self)
        self._act_voltar.setShortcut(QKeySequence("Alt+Left"))
        self._act_voltar.triggered.connect(self._voltar)
        m_arq.addAction(self._act_voltar)

        m_arq.addSeparator()
        sair = QAction("&Sair", self)
        sair.setShortcut(QKeySequence("Ctrl+Q"))
        sair.triggered.connect(self.close)
        m_arq.addAction(sair)

        # Menus Editar/Cliente/Ferramentas/Ajuda — adicionar quando tiverem
        # actions reais. Vazios atrapalham a primeira impressão.

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
        rail.setFixedWidth(96)
        rail.setStyleSheet(
            "#SideRail { background: #F7F7F8; border-right: 1px solid #D1D3D6; }"
        )
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(0, 8, 0, 8)
        rail_layout.setSpacing(0)
        rail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._side_items: dict[str, SideRailItem] = {}

        for icon, tela_id, label, shortcut in [
            (IconName.HOME,         "T1", "Clientes",      "Ctrl+1"),
            (IconName.LIST_CHECK,   "T0", "Regras",        "Ctrl+R"),
            (IconName.DOWNLOAD,     "T2", "Importação",    "Ctrl+2"),
            (IconName.BAR_CHART,    "T3", "Diagnóstico",   "Ctrl+3"),
            (IconName.FLAG,         "T4", "Oportunidade",  "Ctrl+4"),
            (IconName.FILE_TEXT,    "T5", "Visualizador",  None),
            (IconName.GIT_MERGE,    "T6", "Reconciliação", "Ctrl+6"),
            (IconName.PEN,          "T7", "Parecer",       "Ctrl+P"),
            (IconName.SHIELD_CHECK, "T8", "Auditoria",     "Ctrl+H"),
        ]:
            item = SideRailItem(icon, tela_id, label, shortcut, parent=rail)
            if tela_id == "T1":
                item.set_active(True)
            elif tela_id == "T2":
                pass  # ativo nesta iteração
            elif tela_id == "T3":
                item.setEnabled(False)  # habilitado quando há cliente aberto
                item.setToolTip(f"{label} — selecione um cliente em T1 primeiro")
            elif tela_id == "T4":
                item.setEnabled(False)  # habilitado quando há cruzamento aberto
                item.setToolTip(f"{label} — abra um cruzamento em T3 primeiro")
            elif tela_id == "T5":
                item.setEnabled(False)  # habilitado quando há linha SPED aberta
                item.setToolTip(f"{label} — acessível via evidência em T4")
            elif tela_id == "T7":
                item.setEnabled(False)  # habilitado quando há cliente aberto
                item.setToolTip(f"{label} — selecione um cliente em T1 primeiro")
            elif tela_id == "T8":
                item.setEnabled(False)  # habilitado quando há cliente aberto
                item.setToolTip(f"{label} — selecione um cliente em T1 primeiro")
            elif tela_id == "T0":
                # Regras é read-only, sempre acessível.
                pass
            else:
                item.setEnabled(False)
                item.setToolTip(f"{label} — disponível em iteração futura")
            item.activated_with_tela.connect(self._navegar_para)
            rail_layout.addWidget(item)
            self._side_items[tela_id] = item

        rail_layout.addStretch()

        # T9 (config) na base do rail
        cfg = SideRailItem(IconName.SETTINGS, "T9", "Configurações", "Ctrl+,", parent=rail)
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
        self._t3.cruzamento_aberto.connect(self._on_cruzamento_aberto)
        self._t3.abrir_cliente_sugerido.connect(self._on_abrir_cliente_sugerido)
        self._central_stack.addWidget(self._t3)

        # T4 — Oportunidade detalhada
        self._t4 = T4Oportunidade()
        self._t4.abrir_sped.connect(self._on_abrir_sped)
        self._central_stack.addWidget(self._t4)

        # T5 — Visualizador SPED (rastreabilidade §1)
        self._t5 = T5SpedViewer()
        self._t5.voltar_solicitado.connect(self._on_voltar_de_t5)
        self._central_stack.addWidget(self._t5)

        # T7 — Geração de parecer Word
        self._parecer_controller = ParecerController(parent=self)
        self._t7 = T7Parecer(controller=self._parecer_controller)
        self._central_stack.addWidget(self._t7)

        # T8 — Auditoria & Logs forense
        self._t8 = T8Auditoria()
        self._central_stack.addWidget(self._t8)

        # T0 — Visualizador de regras (read-only, sempre acessível)
        self._t0 = T0Regras()
        self._central_stack.addWidget(self._t0)

        h.addWidget(self._central_stack, 1)
        self.setCentralWidget(central)

        # Atalhos globais — navegação rápida entre telas habilitadas
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self._atalho_t7)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self._atalho_t8)
        QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self._navegar_para("T0"))
        QShortcut(QKeySequence("Ctrl+1"), self, activated=lambda: self._navegar_para("T1"))
        QShortcut(QKeySequence("Ctrl+2"), self, activated=lambda: self._navegar_para("T2"))
        QShortcut(QKeySequence("Ctrl+3"), self, activated=self._atalho_t3)
        QShortcut(QKeySequence("Ctrl+4"), self, activated=self._atalho_t4)
        # Atalho "Voltar" (Alt+←) já registrado via QAction no menu Arquivo.

        # Carregamento inicial dos clientes
        self._t1.recarregar()

        # Mapa tela_id → widget no stack
        self._tela_widgets: dict[str, QWidget] = {
            "T0": self._t0,
            "T1": self._t1,
            "T2": self._t2,
            "T3": self._t3,
            "T4": self._t4,
            "T5": self._t5,
            "T7": self._t7,
            "T8": self._t8,
        }

        # Conecta o botão "← Voltar" do breadcrumb de cada view ao
        # _voltar() global (mesma ação do Alt+← e do menu Arquivo).
        # Conecta também target_tela_clicked → navegação direta quando
        # auditor clica em "Home", "Diagnóstico", etc. dentro do breadcrumb.
        for view in self._tela_widgets.values():
            bc = getattr(view, "_breadcrumb", None)
            if bc is not None and hasattr(bc, "voltar_solicitado"):
                bc.voltar_solicitado.connect(self._voltar)
            if bc is not None and hasattr(bc, "target_tela_clicked"):
                bc.target_tela_clicked.connect(self._on_breadcrumb_target)

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
        """Carrega o cliente em T3 (e T7) e navega para o diagnóstico."""
        self._sb_cliente.setText(
            f"Cliente: {cliente.razao_social}  ·  AC {cliente.ano_calendario}  "
            f"·  CNPJ {cliente.cnpj_formatado()}"
        )
        self._side_items["T3"].setEnabled(True)
        self._side_items["T3"].setToolTip("Diagnóstico · Ctrl+3")
        self._side_items["T7"].setEnabled(True)
        self._side_items["T7"].setToolTip("Parecer · Ctrl+P")
        self._side_items["T8"].setEnabled(True)
        self._side_items["T8"].setToolTip("Auditoria · Ctrl+H")
        self._t3.carregar_cliente(cliente)
        self._t7.carregar_cliente(cliente)
        self._t8.carregar_cliente(cliente)
        self._navegar_para("T3")

    def _on_importar_solicitado(self) -> None:
        self._navegar_para("T2")

    def _on_importacao_concluida(self, sucessos: int) -> None:
        if sucessos > 0:
            self._t1.recarregar()

    def _on_cruzamento_aberto(self, codigo_regra: str) -> None:
        """Duplo-clique em CR-XX em T3 → carrega T4 e navega."""
        cliente = self._t3.cliente_atual()
        if cliente is None:
            return
        self._side_items["T4"].setEnabled(True)
        self._side_items["T4"].setToolTip("Oportunidade · Ctrl+4")
        self._t4.carregar(cliente, codigo_regra)
        self._navegar_para("T4")

    def _on_abrir_sped(self, payload: dict) -> None:
        """T4 emitiu pedido para abrir T5 com a linha do SPED original."""
        cliente = self._t4.cliente_atual()
        codigo = self._t4.codigo_atual()
        if cliente is None:
            return
        self._side_items["T5"].setEnabled(True)
        self._side_items["T5"].setToolTip("Visualizador SPED")
        try:
            self._t5.carregar(cliente, codigo, payload)
        except Exception as exc:  # noqa: BLE001
            Toast.show_error(self, f"Falha ao abrir SPED: {exc}")
            return
        self._navegar_para("T5")

    def _on_breadcrumb_target(self, target_tela: str, _payload: dict) -> None:
        """Clique em segmento de breadcrumb com target_tela definido —
        navega pra essa tela se estiver habilitada. Caso contrário,
        cai pra T1 (home)."""
        item = self._side_items.get(target_tela)
        if item is not None and item.isEnabled():
            self._navegar_para(target_tela)
        else:
            self._navegar_para("T1")

    def _on_voltar_de_t5(self) -> None:
        """Backspace ou clique 'Voltar' em T5 → tela anterior (T4 se houver)."""
        if self._side_items["T4"].isEnabled():
            self._navegar_para("T4")
        else:
            self._navegar_para("T1")

    def _on_abrir_cliente_sugerido(
        self, cnpj_sugerido: str, ano_calendario: int,
    ) -> None:
        """Quando T3 sugere abrir matriz (filial sem EFD-Contrib),
        carrega o CNPJ sugerido como cliente ativo. Procura por
        CNPJ × AC; se não achar pelo AC, fallback pelo CNPJ apenas."""
        cliente = self._t1.localizar_cliente_por_cnpj(
            cnpj_sugerido, ano_calendario,
        )
        if cliente is None:
            cliente = self._t1.localizar_cliente_por_cnpj(cnpj_sugerido)
        if cliente is None:
            Toast.show_warning(
                self,
                f"CNPJ {cnpj_sugerido} não está disponível na lista de clientes.",
            )
            return
        self._on_cliente_aberto(cliente)

    # ------------------------------------------------------------
    # Navegação entre telas
    # ------------------------------------------------------------

    def _navegar_para(self, tela_id: str, *, registrar: bool = True) -> None:
        widget = self._tela_widgets.get(tela_id)
        if widget is None:
            return
        # Empilha no histórico se for nova tela (evita duplicatas consecutivas).
        # `registrar=False` é usado pelo próprio _voltar para não re-empilhar.
        if registrar:
            if not self._nav_history or self._nav_history[-1] != tela_id:
                self._nav_history.append(tela_id)
        self._central_stack.setCurrentWidget(widget)
        for tid, item in self._side_items.items():
            item.set_active(tid == tela_id)

    def _voltar(self) -> None:
        """Volta para a tela anterior do histórico. No-op se não há histórico."""
        if len(self._nav_history) < 2:
            return
        # Remove a tela atual; navega para a anterior sem re-empilhar.
        self._nav_history.pop()
        anterior = self._nav_history[-1]
        # Só volta se a tela anterior continua acessível (cliente aberto etc.)
        item = self._side_items.get(anterior)
        if item is not None and not item.isEnabled() and anterior != "T1":
            # Tela anterior não está mais habilitada — limpa histórico até T1.
            while self._nav_history and self._nav_history[-1] not in ("T1", "T2"):
                self._nav_history.pop()
            anterior = self._nav_history[-1] if self._nav_history else "T1"
        self._navegar_para(anterior, registrar=False)

    def _atalho_t3(self) -> None:
        if self._side_items["T3"].isEnabled():
            self._navegar_para("T3")

    def _atalho_t4(self) -> None:
        if self._side_items["T4"].isEnabled():
            self._navegar_para("T4")

    def _atalho_t7(self) -> None:
        if self._side_items["T7"].isEnabled():
            self._navegar_para("T7")

    def _atalho_t8(self) -> None:
        if self._side_items["T8"].isEnabled():
            self._navegar_para("T8")

    def closeEvent(self, ev) -> None:  # noqa: N802 (Qt API)
        # Encerra worker threads (importação, diagnóstico, parecer) limpamente
        for view_attr in ("_t2", "_t3", "_t7"):
            try:
                getattr(self, view_attr).shutdown()
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
