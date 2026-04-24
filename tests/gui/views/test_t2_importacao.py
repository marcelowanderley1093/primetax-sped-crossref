"""
Testes da view T2 (Importação) — usa controller stub para isolar do core.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from src.gui.threading.parser_worker import ResultadoArquivo
from src.gui.views.t2_importacao import T2Importacao


class _StubController(QObject):
    """Controller fake — expõe os mesmos signals do real, sem QThread."""
    arquivo_iniciado = Signal(str, str)
    log_event = Signal(str, str, str)
    arquivo_concluido = Signal(object)
    lote_concluido = Signal(int, int, int)

    def __init__(self):
        super().__init__()
        self.lote_recebido = []

    def importar_lote(self, arquivos, *, encoding_override="auto"):
        self.lote_recebido = list(arquivos)

    def cancelar(self):
        pass

    def shutdown(self):
        pass


class TestT2Importacao:
    def test_inicial_sem_arquivos(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        assert view._fila == []
        assert not view._btn_iniciar.isEnabled()

    def test_add_arquivos_popula_fila(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        view.add_arquivos([Path("/tmp/efd_c.txt"), Path("/tmp/ecd.txt")])
        assert len(view._fila) == 2
        assert view._tabela.total_rows() == 2
        assert view._btn_iniciar.isEnabled()

    def test_add_arquivos_ignora_duplicados(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        view.add_arquivos([Path("/tmp/efd.txt")])
        view.add_arquivos([Path("/tmp/efd.txt")])
        assert len(view._fila) == 1

    def test_iniciar_chama_controller_com_lote(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        view.add_arquivos([Path("/tmp/efd.txt")])
        view._iniciar()
        assert ctrl.lote_recebido == [Path("/tmp/efd.txt")]
        assert view._em_execucao is True
        assert not view._btn_iniciar.isEnabled()

    def test_arquivo_iniciado_atualiza_status(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        path = Path("/tmp/efd.txt")
        view.add_arquivos([path])
        view._iniciar()
        ctrl.arquivo_iniciado.emit(str(path), "EFD-Contribuições")
        # Garante que a linha não está mais como pendente
        rows = view._tabela._model.rows()
        assert rows[0]["status"] == "processando"

    def test_arquivo_concluido_sucesso_atualiza_status(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        path = Path("/tmp/efd.txt")
        view.add_arquivos([path])
        view._iniciar()

        ctrl.arquivo_concluido.emit(
            ResultadoArquivo(
                arquivo=path,
                tipo_sped="efd_contribuicoes",
                sucesso=True,
                cnpj="00000000000100",
            )
        )
        rows = view._tabela._model.rows()
        assert rows[0]["status"] == "ok"
        assert "EFD-Contribuições" in rows[0]["tipo_sped"]
        assert "00.000.000" in rows[0]["cnpj"]

    def test_arquivo_concluido_falha_marca_alto(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        path = Path("/tmp/efd.txt")
        view.add_arquivos([path])
        view._iniciar()

        ctrl.arquivo_concluido.emit(
            ResultadoArquivo(
                arquivo=path,
                tipo_sped="desconhecido",
                sucesso=False,
                mensagem="erro qualquer",
            )
        )
        rows = view._tabela._model.rows()
        assert rows[0]["status"] == "falhou"

    def test_lote_concluido_emite_signal_view(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        view.show()  # window() precisa existir para Toast.show_*
        view.add_arquivos([Path("/tmp/efd.txt")])
        view._iniciar()

        with qtbot.waitSignal(view.importacao_concluida, timeout=500) as blocker:
            ctrl.lote_concluido.emit(1, 1, 0)
        assert blocker.args == [1]
        assert view._em_execucao is False
        assert view._btn_limpar.isEnabled()

    def test_limpar_fila_quando_nao_em_execucao(self, qtbot):
        ctrl = _StubController()
        view = T2Importacao(controller=ctrl)
        qtbot.addWidget(view)
        view.add_arquivos([Path("/tmp/a.txt"), Path("/tmp/b.txt")])
        assert len(view._fila) == 2
        view._limpar_fila()
        assert view._fila == []
        assert view._tabela.total_rows() == 0
