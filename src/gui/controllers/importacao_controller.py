"""
ImportacaoController — orquestra o ParserWorker em QThread.

Lifecycle:
  - controller mantém UMA QThread + UM worker. Reutilizada entre lotes.
  - importar_lote() invoca slot do worker via QMetaObject.invokeMethod
    (necessário para chamada cross-thread thread-safe).
  - signals do worker são repassados para a view via signals próprios.
  - cancelar() emite o slot cancelar do worker via DirectConnection.

Não conhece nada da view (T2). View conecta nos signals e expõe ao usuário.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import (
    QObject,
    Qt,
    QThread,
    Signal,
)

from src.gui.threading.parser_worker import ParserWorker, ResultadoArquivo

logger = logging.getLogger(__name__)


class ImportacaoController(QObject):
    """Fachada para a view sobre a fila de importação."""

    arquivo_iniciado = Signal(str, str)
    log_event = Signal(str, str, str)
    arquivo_concluido = Signal(object)
    lote_concluido = Signal(int, int, int)

    # Signals internos para invocação cross-thread.
    # Por que via signal e não QMetaObject.invokeMethod com Q_ARG: o
    # QMetaType do Qt6 não registra `list` por padrão e Q_ARG(list, ...)
    # falha em runtime ("Unable to find a QMetaType for 'list'") no
    # bundle PyInstaller. Signals fazem marshalling de tipos Python
    # automaticamente via QueuedConnection — robusto para qualquer tipo.
    _disparar_encoding = Signal(str)
    _disparar_lote = Signal(list)
    _disparar_cancelar = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread = QThread()
        self._thread.setObjectName("ParserWorkerThread")
        self._worker = ParserWorker()
        self._worker.moveToThread(self._thread)

        # Re-emite os signals do worker
        self._worker.arquivo_iniciado.connect(self.arquivo_iniciado)
        self._worker.log_event.connect(self.log_event)
        self._worker.arquivo_concluido.connect(self.arquivo_concluido)
        self._worker.lote_concluido.connect(self.lote_concluido)

        # Conexões cross-thread (QueuedConnection por padrão entre threads)
        self._disparar_encoding.connect(
            self._worker.set_encoding_override,
            Qt.ConnectionType.QueuedConnection,
        )
        self._disparar_lote.connect(
            self._worker.importar_lote,
            Qt.ConnectionType.QueuedConnection,
        )
        # cancelar é DirectConnection — flag precisa ser tocada mesmo
        # com o slot importar_lote em execução.
        self._disparar_cancelar.connect(
            self._worker.cancelar,
            Qt.ConnectionType.DirectConnection,
        )

        self._thread.start()

    # ------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------

    def importar_lote(
        self,
        arquivos: list[Path],
        *,
        encoding_override: str = "auto",
    ) -> None:
        """Inicia importação em thread separada. Não bloqueia."""
        if not arquivos:
            return
        self._disparar_encoding.emit(encoding_override)
        self._disparar_lote.emit([str(a) for a in arquivos])

    def cancelar(self) -> None:
        self._disparar_cancelar.emit()

    def shutdown(self) -> None:
        """Encerra a thread limpamente. Chamar em closeEvent da MainWindow."""
        self.cancelar()
        self._thread.quit()
        self._thread.wait(3000)
