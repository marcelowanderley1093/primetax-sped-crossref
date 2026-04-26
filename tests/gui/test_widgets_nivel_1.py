"""
Testes dos componentes de Nível 1 da GUI (Bloco 5 §C8, §C4, §C11).

Cobertura:
  - SearchField: debounce, min-length, clear, contador.
  - TraceabilityBreadcrumb: push/pop, último não-clicável, pop-até no clique.
  - StatCard: render estático, clickable, valor secundário com estilo.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from src.gui.widgets import (
    BreadcrumbSegment,
    SearchField,
    StatCard,
    TraceabilityBreadcrumb,
)


# --------------------------------------------------------------------
# SearchField
# --------------------------------------------------------------------

class TestSearchField:
    def test_instancia_com_placeholder(self, qtbot):
        sf = SearchField(placeholder="Filtrar 127 linhas...")
        qtbot.addWidget(sf)
        assert sf._edit.placeholderText() == "Filtrar 127 linhas..."

    def test_debounce_emite_uma_vez_apos_ultima_tecla(self, qtbot):
        sf = SearchField()
        qtbot.addWidget(sf)
        sf.set_debounce_ms(50)

        with qtbot.waitSignal(sf.query_changed, timeout=500) as blocker:
            qtbot.keyClicks(sf._edit, "acme")
        assert blocker.args[0] == "acme"

    def test_query_muito_curta_nao_emite(self, qtbot):
        sf = SearchField()
        qtbot.addWidget(sf)
        sf.set_debounce_ms(30)

        with qtbot.assertNotEmitted(sf.query_changed, wait=120):
            qtbot.keyClicks(sf._edit, "a")

    def test_limpar_emite_cleared(self, qtbot):
        sf = SearchField()
        qtbot.addWidget(sf)
        sf.set_debounce_ms(30)

        # primeiro digita para ter query, depois limpa
        qtbot.keyClicks(sf._edit, "acme")
        qtbot.wait(80)

        with qtbot.waitSignal(sf.cleared, timeout=300):
            sf.clear()

    def test_set_match_count_exibe_badge(self, qtbot):
        sf = SearchField()
        qtbot.addWidget(sf)
        sf.set_text("acme")
        sf.set_match_count(12, 127)
        assert not sf._count_label.isHidden()
        assert "12 de 127" in sf._count_label.text()

    def test_set_match_count_sem_query_oculta_badge(self, qtbot):
        sf = SearchField()
        qtbot.addWidget(sf)
        sf.set_match_count(0, 127)
        assert sf._count_label.isHidden()


# --------------------------------------------------------------------
# TraceabilityBreadcrumb
# --------------------------------------------------------------------

class TestTraceabilityBreadcrumb:
    def _seg(self, label: str) -> BreadcrumbSegment:
        return BreadcrumbSegment(label=label)

    def test_vazio_sem_segmentos(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        assert bc.segments() == []

    def test_push_adiciona_segmentos(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        bc.push(self._seg("ACME × 2025"))
        bc.push(self._seg("CR-07"))
        assert len(bc.segments()) == 2

    def test_pop_remove_ultimo(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        bc.set_segments([self._seg("A"), self._seg("B"), self._seg("C")])
        removed = bc.pop()
        assert removed is not None
        assert removed.label == "C"
        assert len(bc.segments()) == 2

    def test_pop_vazio_retorna_none(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        assert bc.pop() is None

    def test_clique_em_segmento_emite_indice(self, qtbot):
        bc = TraceabilityBreadcrumb()
        # Desliga o botão Voltar para o teste focar nos segmentos.
        bc.set_voltar_visivel(False)
        qtbot.addWidget(bc)
        bc.set_segments([
            self._seg("Home"),
            self._seg("ACME × 2025"),
            self._seg("CR-07"),
            self._seg("L1847"),  # atual — não clicável
        ])

        # Encontra o botão do segmento "ACME × 2025" (índice 1)
        from PySide6.QtWidgets import QPushButton
        botoes = [w for w in bc.findChildren(QPushButton)]
        assert len(botoes) == 3  # 4 segmentos, último é QLabel (atual)

        with qtbot.waitSignal(bc.segment_clicked, timeout=500) as blocker:
            qtbot.mouseClick(botoes[1], Qt.MouseButton.LeftButton)
        assert blocker.args[0] == 1

    def test_clique_faz_pop_ate_segmento(self, qtbot):
        bc = TraceabilityBreadcrumb()
        bc.set_voltar_visivel(False)
        qtbot.addWidget(bc)
        bc.set_segments([
            self._seg("Home"),
            self._seg("ACME"),
            self._seg("CR-07"),
            self._seg("L1847"),
        ])

        from PySide6.QtWidgets import QPushButton
        botoes = bc.findChildren(QPushButton)
        # Clica no segmento "ACME" (índice 1 na lógica)
        qtbot.mouseClick(botoes[1], Qt.MouseButton.LeftButton)

        assert len(bc.segments()) == 2
        assert bc.segments()[-1].label == "ACME"

    def test_voltar_solicitado_emite_signal(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        bc.set_segments([self._seg("Home"), self._seg("Atual")])

        from PySide6.QtWidgets import QPushButton
        botoes = bc.findChildren(QPushButton)
        # Primeiro botão é "← Voltar"
        assert "Voltar" in botoes[0].text()
        with qtbot.waitSignal(bc.voltar_solicitado, timeout=500):
            qtbot.mouseClick(botoes[0], Qt.MouseButton.LeftButton)

    def test_set_voltar_visivel_oculta_botao(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        bc.set_segments([self._seg("Home"), self._seg("Atual")])
        from PySide6.QtWidgets import QPushButton
        assert any("Voltar" in b.text() for b in bc.findChildren(QPushButton))
        bc.set_voltar_visivel(False)
        # Qt deleteLater é assíncrono; espera o event loop processar.
        qtbot.wait(50)
        assert not any("Voltar" in b.text() for b in bc.findChildren(QPushButton))

    def test_clear_remove_tudo(self, qtbot):
        bc = TraceabilityBreadcrumb()
        qtbot.addWidget(bc)
        bc.set_segments([self._seg("A"), self._seg("B")])
        bc.clear()
        assert bc.segments() == []


# --------------------------------------------------------------------
# StatCard
# --------------------------------------------------------------------

class TestStatCard:
    def test_instancia_com_titulo(self, qtbot):
        c = StatCard(title="Oportunidades")
        qtbot.addWidget(c)
        # Título é convertido para uppercase
        assert c._title.text() == "OPORTUNIDADES"

    def test_set_primary_value(self, qtbot):
        c = StatCard(title="Oportunidades")
        qtbot.addWidget(c)
        c.set_primary_value("12")
        assert c._primary.text() == "12"

    def test_set_secondary_value_com_estilo(self, qtbot):
        c = StatCard(title="Divergências")
        qtbot.addWidget(c)
        c.set_secondary_value("Alto: 1", style="error")
        assert not c._secondary.isHidden()
        assert "B23A3A" in c._secondary.styleSheet().upper()

    def test_set_hint(self, qtbot):
        c = StatCard(title="Pendências")
        qtbot.addWidget(c)
        c.set_hint("aguardando ECF")
        assert not c._hint.isHidden()
        assert c._hint.text() == "aguardando ECF"

    def test_clickable_emite_signal(self, qtbot):
        c = StatCard(title="Oportunidades", clickable=True)
        qtbot.addWidget(c)
        with qtbot.waitSignal(c.clicked, timeout=500):
            qtbot.mouseClick(c, Qt.MouseButton.LeftButton)

    def test_nao_clickable_nao_emite(self, qtbot):
        c = StatCard(title="Limitações", clickable=False)
        qtbot.addWidget(c)
        with qtbot.assertNotEmitted(c.clicked, wait=100):
            qtbot.mouseClick(c, Qt.MouseButton.LeftButton)

    def test_set_secondary_vazio_oculta(self, qtbot):
        c = StatCard(title="OK")
        qtbot.addWidget(c)
        c.set_secondary_value("algo")
        assert not c._secondary.isHidden()
        c.set_secondary_value("")
        assert c._secondary.isHidden()
