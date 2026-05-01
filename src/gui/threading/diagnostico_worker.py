"""
DiagnosticoWorker — QObject que executa Motor.diagnosticar_ano() em thread.

Executar os 47+ cruzamentos de Camada 1+2+3 em SPED real pode levar
alguns segundos. Worker isolado mantém UI responsiva.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot

from src.crossref.engine import Motor
from src.db.repo import Repositorio

logger = logging.getLogger(__name__)


@dataclass
class ResultadoDiagnostico:
    cnpj: str
    ano_calendario: int
    sucesso: bool
    sumario: dict | None = None
    mensagem: str = ""


class DiagnosticoWorker(QObject):
    """Worker que executa o motor de cruzamentos em thread.

    Signals:
      iniciado(cnpj, ano)
      log_event(level, message)
      concluido(ResultadoDiagnostico)
    """

    iniciado = Signal(str, int)
    log_event = Signal(str, str)              # level, message
    concluido = Signal(object)                # ResultadoDiagnostico

    @Slot(str, int)
    def diagnosticar(self, cnpj: str, ano_calendario: int) -> None:
        self.iniciado.emit(cnpj, ano_calendario)
        self.log_event.emit("INFO", f"Iniciando diagnóstico de {cnpj} / AC {ano_calendario}...")

        try:
            repo = Repositorio(cnpj, ano_calendario)
            motor = Motor(repo)
            sumario = motor.diagnosticar_ano(ano_calendario)
        except Exception as exc:  # noqa: BLE001
            logger.exception("erro no diagnóstico de %s/%d", cnpj, ano_calendario)
            self.log_event.emit("ERROR", f"Falha no diagnóstico: {exc}")
            self.log_event.emit("DEBUG", traceback.format_exc(limit=3))
            self.concluido.emit(
                ResultadoDiagnostico(
                    cnpj=cnpj,
                    ano_calendario=ano_calendario,
                    sucesso=False,
                    mensagem=str(exc),
                )
            )
            return

        meses = sumario.get("meses", [])
        total_op = sum(m.get("oportunidades_camada2", 0) for m in meses)
        total_div = sum(m.get("divergencias_camada1", 0) for m in meses)
        self.log_event.emit(
            "SUCCESS",
            f"Diagnóstico concluído — {len(meses)} período(s), "
            f"{total_op} oportunidade(s), {total_div} divergência(s) de integridade.",
        )
        self.concluido.emit(
            ResultadoDiagnostico(
                cnpj=cnpj,
                ano_calendario=ano_calendario,
                sucesso=True,
                sumario=sumario,
            )
        )
