"""
ParecerController — fachada do ParecerWorker + utilitários de leitura.

Expõe ao T7:
  - Lista das teses disponíveis (via word_parecer._TESES)
  - Contagem de achados por tese (lê banco síncrono — barato)
  - gerar() / shutdown() para integrar com QThread
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import (
    Q_ARG,
    QMetaObject,
    QObject,
    Qt,
    QThread,
    Signal,
)

from src.db.repo import Repositorio
from src.gui.threading.parecer_worker import ParecerWorker, ResultadoParecer
from src.reports.word_parecer import _TESES

logger = logging.getLogger(__name__)


class ParecerController(QObject):
    """Fachada para a tela T7."""

    iniciado = Signal(str, int, str)
    log_event = Signal(str, str)
    concluido = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread = QThread()
        self._thread.setObjectName("ParecerWorkerThread")
        self._worker = ParecerWorker()
        self._worker.moveToThread(self._thread)

        self._worker.iniciado.connect(self.iniciado)
        self._worker.log_event.connect(self.log_event)
        self._worker.concluido.connect(self.concluido)

        self._thread.start()

    # ------------------------------------------------------------
    # Leitura síncrona — para T7 popular dropdown e preview
    # ------------------------------------------------------------

    @staticmethod
    def listar_teses() -> list[tuple[str, dict]]:
        """Retorna [(codigo, spec)] na ordem em que estão registradas."""
        return list(_TESES.items())

    @staticmethod
    def achados_por_tese(cnpj: str, ano_calendario: int) -> dict[str, int]:
        """Conta achados por código de tese (consulta síncrona barata).

        Retorna mapa {tese_codigo: total_achados}, contando oportunidades
        cujas codigo_regra estão nas codigos_regras da tese.
        """
        repo = Repositorio(cnpj, ano_calendario)
        if not repo.caminho.exists():
            return {tese: 0 for tese in _TESES}

        conn = repo.conexao()
        try:
            ops = repo.consultar_oportunidades(conn, cnpj, ano_calendario)
        finally:
            conn.close()

        codigos_op = [o.get("codigo_regra", "") for o in ops]
        contagens: dict[str, int] = {}
        for tese, spec in _TESES.items():
            regras_da_tese = set(spec.get("codigos_regras", []))
            contagens[tese] = sum(
                1 for c in codigos_op if c in regras_da_tese
            )
        return contagens

    # ------------------------------------------------------------
    # Disparo assíncrono
    # ------------------------------------------------------------

    def gerar(
        self,
        cnpj: str,
        ano_calendario: int,
        tese: str,
        destino: Path,
        consultor: str = "",
    ) -> None:
        QMetaObject.invokeMethod(
            self._worker,
            "gerar",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, cnpj),
            Q_ARG(int, ano_calendario),
            Q_ARG(str, tese),
            Q_ARG(str, str(destino)),
            Q_ARG(str, consultor),
        )

    def shutdown(self) -> None:
        self._thread.quit()
        self._thread.wait(3000)
