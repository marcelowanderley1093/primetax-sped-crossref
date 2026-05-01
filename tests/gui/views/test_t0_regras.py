"""
Testes da view T0 (Regras) — usa controller stub.
"""

from __future__ import annotations

import pytest

from src.gui.controllers.regras_controller import RegraInfo
from src.gui.views.t0_regras import T0Regras


class _StubController:
    def __init__(self, regras=None):
        self._regras = regras if regras is not None else [
            RegraInfo(
                codigo="CI-01",
                camada=1,
                descricao="Integridade do Bloco 9",
                base_legal="IN RFB 1.252/2012, art. 4º",
                dependencias_sped=["efd_contribuicoes"],
                sprint="Sprint 1",
                severidade="alto",
                modulo_path="src.crossref.camada_1_integridade.cruzamento_01_bloco9",
            ),
            RegraInfo(
                codigo="CR-07",
                camada=2,
                descricao="Tese 69 — ICMS na base de PIS/COFINS",
                base_legal="RE 574.706/PR (Tema 69 STF)",
                dependencias_sped=["efd_contribuicoes"],
                sprint="Sprint 1",
                severidade="alto",
                modulo_path="src.crossref.camada_2_oportunidades.cruzamento_07_tese69_c170",
            ),
            RegraInfo(
                codigo="CR-29",
                camada=3,
                descricao="Consistência M210 ↔ M100 ↔ M200",
                base_legal="IN RFB 1.252/2012",
                dependencias_sped=["efd_contribuicoes"],
                sprint="Sprint 4",
                severidade="medio",
                modulo_path="src.crossref.camada_3_consistencia.cruzamento_29_m100_m200_fluxo_pis",
            ),
        ]

    def listar_regras(self):
        return list(self._regras)


class TestT0Regras:
    def test_renderiza_sem_erros(self, qtbot):
        ctrl = _StubController()
        t0 = T0Regras(controller=ctrl)
        qtbot.addWidget(t0)

    def test_popula_tabela_com_regras(self, qtbot):
        ctrl = _StubController()
        t0 = T0Regras(controller=ctrl)
        qtbot.addWidget(t0)
        assert t0._tabela.total_rows() == 3

    def test_cards_mostram_contagens_por_camada(self, qtbot):
        ctrl = _StubController()
        t0 = T0Regras(controller=ctrl)
        qtbot.addWidget(t0)
        assert "3" in t0._card_total._primary.text()
        assert "1" in t0._card_camada1._primary.text()
        assert "1" in t0._card_camada2._primary.text()
        assert "1" in t0._card_camada3._primary.text()

    def test_selecao_de_linha_popula_painel(self, qtbot):
        ctrl = _StubController()
        t0 = T0Regras(controller=ctrl)
        qtbot.addWidget(t0)

        rows = t0._tabela.visible_rows()
        assert len(rows) == 3
        # Simula seleção da linha do CR-07
        row_cr07 = next(r for r in rows if r["_codigo"] == "CR-07")
        t0._on_regra_selecionada(row_cr07)

        assert t0._regra_selecionada is not None
        assert t0._regra_selecionada.codigo == "CR-07"
        # QTextBrowser usa toPlainText() em vez de text()
        plain = t0._painel_corpo.toPlainText()
        assert "Tese 69" in plain
        assert "RE 574.706" in plain

    def test_lista_vazia_nao_quebra(self, qtbot):
        ctrl = _StubController(regras=[])
        t0 = T0Regras(controller=ctrl)
        qtbot.addWidget(t0)
        assert t0._tabela.total_rows() == 0
        assert "0" in t0._card_total._primary.text()
