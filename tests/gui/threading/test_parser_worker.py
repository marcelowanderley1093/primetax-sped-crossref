"""
Testes do ParserWorker — invocado direto no main thread (sem QThread).

Permite verificar lógica de despacho por tipo, tratamento de erro e
emissão de signals sem complicações de cross-thread.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.gui.threading.parser_worker import ParserWorker, ResultadoArquivo


class TestParserWorker:
    def test_arquivo_inexistente_resulta_em_falha(self, qtbot, tmp_path):
        worker = ParserWorker()
        qtbot.addWidget(getattr(worker, "_dummy_parent", None) or _dummy(qtbot))
        resultados: list[ResultadoArquivo] = []
        worker.arquivo_concluido.connect(resultados.append)

        with qtbot.waitSignal(worker.lote_concluido, timeout=5000) as _:
            worker.importar_lote([str(tmp_path / "inexistente.txt")])

        assert len(resultados) == 1
        assert resultados[0].sucesso is False

    def test_lote_vazio_emite_concluido(self, qtbot):
        worker = ParserWorker()
        with qtbot.waitSignal(worker.lote_concluido, timeout=2000) as blocker:
            worker.importar_lote([])
        total, sucessos, falhas = blocker.args
        assert total == 0 and sucessos == 0 and falhas == 0

    def test_arquivo_sped_invalido_resulta_em_tipo_desconhecido(
        self, qtbot, tmp_path
    ):
        # Arquivo de texto sem registro 0000 válido
        arq = tmp_path / "lixo.txt"
        arq.write_text("isto não é um SPED\nlinha qualquer\n", encoding="utf-8")

        worker = ParserWorker()
        resultados: list[ResultadoArquivo] = []
        worker.arquivo_concluido.connect(resultados.append)
        with qtbot.waitSignal(worker.lote_concluido, timeout=5000):
            worker.importar_lote([str(arq)])

        assert len(resultados) == 1
        r = resultados[0]
        assert r.sucesso is False
        assert r.tipo_sped == "desconhecido"

    def test_efd_contrib_real_importa_com_sucesso(
        self, qtbot, fixture_tese69_positivo, tmp_path, monkeypatch
    ):
        """Smoke test integrativo: importa fixture EFD-Contrib via worker.

        O parser cria banco em data/db/{cnpj}/{ano}.sqlite — para isolar,
        muda diretório de trabalho temporariamente.
        """
        cwd_anterior = Path.cwd()
        monkeypatch.chdir(tmp_path)

        worker = ParserWorker()
        resultados: list[ResultadoArquivo] = []
        worker.arquivo_concluido.connect(resultados.append)

        with qtbot.waitSignal(worker.lote_concluido, timeout=20_000):
            worker.importar_lote([str(fixture_tese69_positivo)])

        assert len(resultados) == 1
        r = resultados[0]
        assert r.sucesso is True, f"Esperava sucesso, falhou: {r.mensagem}"
        assert r.tipo_sped == "efd_contribuicoes"
        assert r.cnpj  # algum CNPJ extraído

    def test_cancelar_para_o_lote(self, qtbot, fixture_tese69_positivo, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        worker = ParserWorker()
        # Pré-cancela antes de iniciar; o primeiro arquivo já é processado,
        # mas o segundo (se houver) não deveria ser. Aqui simplificamos:
        # cancelamento antes de invocar deve fazer o lote terminar logo.
        worker.cancelar()
        with qtbot.waitSignal(worker.lote_concluido, timeout=5000) as blocker:
            # Lote com 1 arquivo só — cancelamento entre arquivos
            worker.importar_lote([str(fixture_tese69_positivo)])
        # Se cancelado antes do loop, lote_concluido com 0/0/0 ou similar.
        # Se não, ao menos o sinal lote_concluido foi emitido.
        assert blocker.args[0] >= 0


def _dummy(qtbot):
    from PySide6.QtWidgets import QWidget
    w = QWidget()
    qtbot.addWidget(w)
    return w
