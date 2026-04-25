"""
ParecerWorker — QObject que executa word_parecer.gerar() em thread.

Geração de parecer Word leva poucos segundos para parecer típico, mas
pode passar de 30s em clientes com muitos achados. Worker isolado
mantém UI responsiva.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from src.db.repo import Repositorio
from src.reports import word_parecer

logger = logging.getLogger(__name__)


@dataclass
class ResultadoParecer:
    cnpj: str
    ano_calendario: int
    tese: str
    sucesso: bool
    destino: Path | None = None
    mensagem: str = ""


class ParecerWorker(QObject):
    """Worker que invoca word_parecer.gerar(). Signals:

      iniciado(cnpj, ano, tese)
      log_event(level, mensagem)
      concluido(ResultadoParecer)
    """

    iniciado = Signal(str, int, str)
    log_event = Signal(str, str)
    concluido = Signal(object)

    @Slot(str, int, str, str, str)
    def gerar(
        self,
        cnpj: str,
        ano_calendario: int,
        tese: str,
        destino: str,
        consultor: str,
    ) -> None:
        self.iniciado.emit(cnpj, ano_calendario, tese)
        self.log_event.emit(
            "INFO",
            f"Iniciando parecer — CNPJ {cnpj} / AC {ano_calendario} / tese {tese}",
        )

        destino_path = Path(destino)
        try:
            repo = Repositorio(cnpj, ano_calendario)
            if not repo.caminho.exists():
                raise FileNotFoundError(
                    f"Banco SQLite não encontrado: {repo.caminho}. "
                    "Importe SPED e rode diagnóstico antes do parecer."
                )
            word_parecer.gerar(
                repo, ano_calendario,
                tese=tese,
                destino=destino_path,
            )
        except ValueError as exc:
            self.log_event.emit("ERROR", f"Tese inválida: {exc}")
            self.concluido.emit(ResultadoParecer(
                cnpj=cnpj, ano_calendario=ano_calendario, tese=tese,
                sucesso=False, mensagem=str(exc),
            ))
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception("erro ao gerar parecer")
            self.log_event.emit("ERROR", f"Falha: {exc}")
            self.log_event.emit("DEBUG", traceback.format_exc(limit=3))
            self.concluido.emit(ResultadoParecer(
                cnpj=cnpj, ano_calendario=ano_calendario, tese=tese,
                sucesso=False, mensagem=str(exc),
            ))
            return

        # Consultor é apenas metadado para QSettings — não é gravado no
        # documento por enquanto (word_parecer.gerar usa nome fixo).
        # Se no futuro o gerador aceitar parâmetro, basta passar.
        _ = consultor

        self.log_event.emit(
            "SUCCESS",
            f"Parecer gerado: {destino_path.name} ({destino_path.stat().st_size} bytes)",
        )
        self.concluido.emit(ResultadoParecer(
            cnpj=cnpj, ano_calendario=ano_calendario, tese=tese,
            sucesso=True, destino=destino_path,
        ))
