"""
Testes da view T5 (Visualizador SPED) — usa fixture sintética em disco.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.views.t5_sped_viewer import T5SpedViewer


def _cliente() -> ClienteRow:
    return ClienteRow(
        cnpj="00000000000100",
        razao_social="ACME SA",
        ano_calendario=2025,
        speds_importados=["EFD-Contrib"],
        impacto_total=Decimal("0"),
        ultima_atividade=datetime(2025, 4, 24),
        banco_path=Path("/tmp/x.sqlite"),
    )


def _criar_sped(tmp_path: Path) -> Path:
    arq = tmp_path / "test_sped.txt"
    linhas = [
        "|0000|006|0||0|01012025|31012025|EMPRESA|00000000000100|",
        "|0001|0|",
        "|C100|0|0|FORN001|55|00|001|000001||",
        "|C170|001|PROD-A|Item A|10,00|UN|100,00|",
        "|C170|002|PROD-B|Item B|20,00|UN|200,00|",
        "|C170|003|PROD-C|Item C|30,00|UN|300,00|",
        "|9999|6|",
    ]
    arq.write_text("\n".join(linhas), encoding="latin-1")
    return arq


class TestT5SemContexto:
    def test_estado_inicial_mostra_empty(self, qtbot):
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)
        assert t5._stack.currentWidget() is t5._empty


class TestT5Carregar:
    def test_carrega_linha_alvo_e_decompoe_campos(self, qtbot, tmp_path):
        arq = _criar_sped(tmp_path)
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)

        payload = {
            "arquivo": str(arq),
            "linha": 4,  # |C170|001|PROD-A|...
            "bloco": "C",
            "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)

        assert t5._stack.currentWidget() is t5._conteudo
        assert "C170" in t5._titulo.text()
        # Campos decompostos
        rows = t5._tabela_campos.visible_rows()
        valores = [r["valor"] for r in rows]
        assert "C170" in valores
        assert "PROD-A" in valores

    def test_botao_pai_habilita_para_C170(self, qtbot, tmp_path):
        arq = _criar_sped(tmp_path)
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)

        payload = {
            "arquivo": str(arq),
            "linha": 5,  # |C170|002|...
            "bloco": "C",
            "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)
        assert t5._btn_pai.isEnabled()
        assert "C100" in t5._btn_pai.text()

    def test_arquivo_inexistente_volta_para_empty(self, qtbot, tmp_path):
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)
        t5.show()  # Toast precisa de window()
        payload = {
            "arquivo": str(tmp_path / "naoexiste.txt"),
            "linha": 1,
            "bloco": "C",
            "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)
        assert t5._stack.currentWidget() is t5._empty


class TestT5Navegacao:
    def test_proxima_ocorrencia_navega(self, qtbot, tmp_path):
        arq = _criar_sped(tmp_path)
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)
        t5.show()

        payload = {
            "arquivo": str(arq),
            "linha": 4,  # primeiro C170
            "bloco": "C",
            "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)
        assert t5._contexto.linha_alvo == 4

        t5._ocorrencia_proxima()
        assert t5._contexto.linha_alvo == 5

    def test_pai_C100_navega(self, qtbot, tmp_path):
        arq = _criar_sped(tmp_path)
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)
        t5.show()

        payload = {
            "arquivo": str(arq),
            "linha": 5,  # C170 #2
            "bloco": "C",
            "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)
        t5._ir_para_pai()
        assert t5._contexto.linha_alvo == 3
        assert t5._contexto.reg_alvo == "C100"

    def test_voltar_emite_signal(self, qtbot, tmp_path):
        arq = _criar_sped(tmp_path)
        t5 = T5SpedViewer()
        qtbot.addWidget(t5)
        payload = {
            "arquivo": str(arq), "linha": 4, "bloco": "C", "registro": "C170",
        }
        t5.carregar(_cliente(), "CR-07", payload)
        with qtbot.waitSignal(t5.voltar_solicitado, timeout=500):
            t5._btn_voltar.click()
