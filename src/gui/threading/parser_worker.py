"""
ParserWorker — QObject que processa fila de SPEDs em thread separada.

Padrão Qt idiomático: QObject + moveToThread + signals/slots. UI nunca
trava durante parsing (pode levar segundos para SPEDs grandes).

Despacho por tipo de SPED via cli.detectar_tipo_sped + chamada do parser
correspondente. Cancelamento via flag atômica verificada entre arquivos.
Encoding `auto` por padrão (parser detecta UTF-8 → fallback Latin1) com
prompt_operador=False — confirmação interativa fica no controller via
modal antes de enfileirar.

Por que `_thread_local_log` no signal `log_event`: permite controllers
filtrarem logs por arquivo (a thread emite vários logs durante um único
parse de arquivo grande).
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

from src.cli import detectar_tipo_sped
from src.parsers import ecd, ecf, efd_contribuicoes, efd_icms_ipi

logger = logging.getLogger(__name__)


_PARSERS: dict[str, Any] = {
    "efd_contribuicoes": efd_contribuicoes.importar,
    "efd_icms_ipi": efd_icms_ipi.importar,
    "ecd": ecd.importar,
    "ecf": ecf.importar,
}

_LABELS_TIPO: dict[str, str] = {
    "efd_contribuicoes": "EFD-Contribuições",
    "efd_icms_ipi": "EFD ICMS/IPI",
    "ecd": "ECD",
    "ecf": "ECF",
}


@dataclass
class ResultadoArquivo:
    """Resumo de uma importação para a UI."""
    arquivo: Path
    tipo_sped: str
    sucesso: bool
    mensagem: str = ""
    cnpj: str = ""
    encoding: str = ""
    encoding_confianca: str = ""


class ParserWorker(QObject):
    """Worker que processa lote de SPEDs em thread separada.

    Signals (todos thread-safe via Qt):
      arquivo_iniciado(arquivo, tipo_sped)
      log_event(arquivo, level, message)
      arquivo_concluido(ResultadoArquivo)
      lote_concluido(int total, int sucessos, int falhas)
    """

    arquivo_iniciado = Signal(str, str)        # path, tipo_sped legível
    log_event = Signal(str, str, str)          # path, level, message
    arquivo_concluido = Signal(object)         # ResultadoArquivo
    lote_concluido = Signal(int, int, int)     # total, sucessos, falhas

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._cancelado = False
        self._encoding_override = "auto"

    # ------------------------------------------------------------
    # Configuração antes de iniciar
    # ------------------------------------------------------------

    @Slot(str)
    def set_encoding_override(self, encoding: str) -> None:
        """Aceita 'auto', 'utf8' ou 'latin1'. Aplicado a todos os arquivos do lote."""
        if encoding in ("auto", "utf8", "latin1"):
            self._encoding_override = encoding

    @Slot()
    def cancelar(self) -> None:
        """Sinaliza cancelamento — efeito apenas entre arquivos do lote."""
        self._cancelado = True

    # ------------------------------------------------------------
    # Slot principal — chamado via QMetaObject.invokeMethod do main thread
    # ------------------------------------------------------------

    @Slot(list)
    def importar_lote(self, arquivos: list[str]) -> None:
        """Processa lista de paths sequencialmente. Roda no thread do worker."""
        self._cancelado = False
        sucessos = 0
        falhas = 0

        for arq_str in arquivos:
            if self._cancelado:
                self.log_event.emit("", "WARNING", "Lote cancelado pelo operador.")
                break

            arq = Path(arq_str)
            try:
                tipo = detectar_tipo_sped(arq)
            except Exception as exc:  # noqa: BLE001
                self.log_event.emit(
                    arq_str, "ERROR",
                    f"Falha ao detectar tipo: {exc}",
                )
                self.arquivo_concluido.emit(
                    ResultadoArquivo(
                        arquivo=arq, tipo_sped="desconhecido",
                        sucesso=False, mensagem=str(exc),
                    )
                )
                falhas += 1
                continue

            if tipo == "desconhecido":
                self.log_event.emit(
                    arq_str, "ERROR",
                    "Tipo de SPED não reconhecido — verifique o registro 0000.",
                )
                self.arquivo_concluido.emit(
                    ResultadoArquivo(
                        arquivo=arq, tipo_sped="desconhecido",
                        sucesso=False, mensagem="tipo desconhecido",
                    )
                )
                falhas += 1
                continue

            label_tipo = _LABELS_TIPO.get(tipo, tipo)
            self.arquivo_iniciado.emit(arq_str, label_tipo)
            self.log_event.emit(
                arq_str, "INFO", f"Iniciando importação ({label_tipo})...",
            )

            try:
                resultado = _PARSERS[tipo](
                    arq,
                    encoding_override=self._encoding_override,
                    prompt_operador=False,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("erro no parser %s", tipo)
                self.log_event.emit(
                    arq_str, "ERROR",
                    f"Falha durante parse: {exc}",
                )
                self.log_event.emit(
                    arq_str, "DEBUG",
                    traceback.format_exc(limit=3),
                )
                self.arquivo_concluido.emit(
                    ResultadoArquivo(
                        arquivo=arq, tipo_sped=tipo,
                        sucesso=False, mensagem=str(exc),
                    )
                )
                falhas += 1
                continue

            sucesso = bool(getattr(resultado, "sucesso", True))
            cnpj = getattr(resultado, "cnpj", "") or ""
            encoding = getattr(resultado, "encoding_origem", "")
            confianca = getattr(resultado, "encoding_confianca", "")
            mensagem = getattr(resultado, "mensagem", "")

            if sucesso:
                self.log_event.emit(
                    arq_str, "SUCCESS",
                    f"Importação concluída — CNPJ {cnpj} "
                    f"(encoding={encoding}/{confianca}).",
                )
                sucessos += 1
            else:
                self.log_event.emit(
                    arq_str, "WARNING",
                    f"Importação parcial: {mensagem}",
                )
                falhas += 1

            self.arquivo_concluido.emit(
                ResultadoArquivo(
                    arquivo=arq,
                    tipo_sped=tipo,
                    sucesso=sucesso,
                    mensagem=mensagem,
                    cnpj=cnpj,
                    encoding=str(encoding) if encoding else "",
                    encoding_confianca=str(confianca) if confianca else "",
                )
            )

        self.lote_concluido.emit(len(arquivos), sucessos, falhas)
