"""
Testes do SpedViewerController — leitura de arquivo SPED + navegação.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.gui.controllers.sped_viewer_controller import (
    ContextoLinha,
    SpedViewerController,
)


def _criar_sped_sintetico(tmp_path: Path) -> Path:
    """Cria um arquivo SPED-like minimal para testes."""
    arq = tmp_path / "exemplo.txt"
    linhas = [
        "|0000|006|0||0|01012025|31012025|EMPRESA|00000000000100|",
        "|0001|0|",
        "|C001|0|",
        "|C100|0|0|FORN001|55|00|001|000001||",
        "|C170|001|PROD-A|Item A|10,00|UN|100,00|",
        "|C170|002|PROD-B|Item B|20,00|UN|200,00|",
        "|C170|003|PROD-C|Item C|30,00|UN|300,00|",
        "|C100|0|0|FORN002|55|00|001|000002||",
        "|C170|001|PROD-D|Item D|40,00|UN|400,00|",
        "|C170|002|PROD-E|Item E|50,00|UN|500,00|",
        "|C990|10|",
        "|9999|11|",
    ]
    arq.write_text("\n".join(linhas), encoding="latin-1")
    return arq


class TestCarregarArquivo:
    def test_arquivo_inexistente_levanta(self, tmp_path):
        ctrl = SpedViewerController()
        with pytest.raises(FileNotFoundError):
            ctrl.carregar_arquivo(tmp_path / "naoexiste.txt", 1)

    def test_linha_alvo_invalida_levanta(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        with pytest.raises(IndexError):
            ctrl.carregar_arquivo(arq, 9999)

    def test_carrega_linha_alvo_centralizada(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        ctx = ctrl.carregar_arquivo(arq, linha_alvo=5, janela=2)
        assert ctx.linha_alvo == 5
        assert ctx.linha_offset == 3
        assert ctx.linhas[ctx.linha_alvo_idx].startswith("|C170|001|PROD-A")
        assert ctx.reg_alvo == "C170"

    def test_decompoe_campos_da_linha_alvo(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        ctx = ctrl.carregar_arquivo(arq, linha_alvo=5)
        # |C170|001|PROD-A|Item A|10,00|UN|100,00|
        valores = [c.valor for c in ctx.campos]
        assert "C170" in valores
        assert "001" in valores
        assert "PROD-A" in valores

    def test_acha_pai_C100_de_C170(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # linha 6 = |C170|002|PROD-B; pai = C100 da linha 4
        ctx = ctrl.carregar_arquivo(arq, linha_alvo=6)
        assert ctx.parent_reg == "C100"
        assert ctx.parent_linha == 4

    def test_pai_inexistente_para_C100(self, tmp_path):
        """C100 não tem pai conhecido no _PARENT_HINTS."""
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        ctx = ctrl.carregar_arquivo(arq, linha_alvo=4)  # C100
        assert ctx.parent_reg is None
        assert ctx.parent_linha is None

    def test_total_linhas_correto(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        ctx = ctrl.carregar_arquivo(arq, linha_alvo=1)
        assert ctx.total_linhas == 12


class TestNavegacao:
    def test_proxima_ocorrencia_de_C170(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # Estou em linha 5 (C170 #1), próxima é linha 6
        prox = ctrl.proxima_ocorrencia(arq, partir_de=5, reg_tipo="C170")
        assert prox == 6

    def test_proxima_ocorrencia_pula_pai(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # Estou em linha 7 (último C170 do primeiro C100); próximo C170 é linha 9
        prox = ctrl.proxima_ocorrencia(arq, partir_de=7, reg_tipo="C170")
        assert prox == 9

    def test_proxima_ocorrencia_sem_proximo_retorna_none(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # Estou em linha 10 (último C170); não há próximo
        prox = ctrl.proxima_ocorrencia(arq, partir_de=10, reg_tipo="C170")
        assert prox is None

    def test_anterior_ocorrencia(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # Estou em linha 9 (C170); anterior é linha 7
        ant = ctrl.anterior_ocorrencia(arq, ate=9, reg_tipo="C170")
        assert ant == 7

    def test_anterior_sem_anterior_retorna_none(self, tmp_path):
        arq = _criar_sped_sintetico(tmp_path)
        ctrl = SpedViewerController()
        # Estou em linha 5 (primeiro C170); não há anterior
        ant = ctrl.anterior_ocorrencia(arq, ate=5, reg_tipo="C170")
        assert ant is None
