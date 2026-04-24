"""
Entry point da aplicação GUI.

Smoke test inicial: abre uma MainWindow vazia com identificação Primetax.
Componentes e telas são plugados em iterações seguintes.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)


APP_NAME = "Primetax SPED Cross-Reference"
APP_VERSION = "0.1.0"


class MainWindow(QMainWindow):
    """Janela principal — casca inicial, sem telas T1-T9 ainda."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 800)

        self._montar_menubar()
        self._montar_central_placeholder()
        self._montar_statusbar()

    def _montar_menubar(self) -> None:
        mb = self.menuBar()

        menu_arquivo = mb.addMenu("&Arquivo")
        act_sair = QAction("&Sair", self)
        act_sair.setShortcut(QKeySequence("Ctrl+Q"))
        act_sair.triggered.connect(self.close)
        menu_arquivo.addAction(act_sair)

        mb.addMenu("&Editar")
        mb.addMenu("&Cliente")
        mb.addMenu("&Ferramentas")
        mb.addMenu("&Ajuda")

    def _montar_central_placeholder(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel("Primetax SPED Cross-Reference")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("font-size: 24pt; color: #008C95; font-weight: 600;")

        sub = QLabel(
            f"GUI em construção · versão {APP_VERSION} · "
            "Sprint 1 (Nível 0 dos componentes)"
        )
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 11pt; color: #53565A; margin-top: 8px;")

        layout.addWidget(titulo)
        layout.addWidget(sub)
        self.setCentralWidget(central)

    def _montar_statusbar(self) -> None:
        sb = QStatusBar(self)
        sb.showMessage("Pronto")
        self.setStatusBar(sb)


def run() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Primetax Solutions")

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
