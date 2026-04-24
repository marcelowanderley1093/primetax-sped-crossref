"""
Testes dos componentes de Nível 0 da GUI (Bloco 5 §C3, §C6, §C10).

Usa pytest-qt (fixture `qtbot`) — roda sem janela visível via offscreen
platform se variável QT_QPA_PLATFORM for setada. Cada teste limita escopo
a contrato API + propriedades básicas; a inspeção visual fina é feita
via `python -m src.gui.demo`.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QKeyEvent

from src.gui.widgets import (
    BadgeStatus,
    CodigoLinkButton,
    SpedType,
    StatusBadge,
    VersionLabel,
)


# --------------------------------------------------------------------
# StatusBadge
# --------------------------------------------------------------------

class TestStatusBadge:
    def test_instancia_com_rotulo_padrao(self, qtbot):
        badge = StatusBadge(BadgeStatus.ALTO)
        qtbot.addWidget(badge)
        assert badge.status() == BadgeStatus.ALTO
        assert badge.text() == "ALTO"
        assert badge.height() == 22

    def test_texto_customizado_sobrescreve_rotulo_padrao(self, qtbot):
        badge = StatusBadge(BadgeStatus.MEDIO, text="Revisar até 30/04")
        qtbot.addWidget(badge)
        assert badge.text() == "Revisar até 30/04"

    def test_troca_status_atualiza_rotulo_se_padrao(self, qtbot):
        badge = StatusBadge(BadgeStatus.OK)
        qtbot.addWidget(badge)
        badge.set_status(BadgeStatus.ALTO)
        assert badge.text() == "ALTO"

    def test_troca_status_nao_sobrescreve_texto_customizado(self, qtbot):
        badge = StatusBadge(BadgeStatus.OK, text="Tudo certo!")
        qtbot.addWidget(badge)
        badge.set_status(BadgeStatus.ALTO)
        assert badge.text() == "Tudo certo!"

    def test_pulse_cria_animacao(self, qtbot):
        badge = StatusBadge(BadgeStatus.EM_PROCESSO)
        qtbot.addWidget(badge)
        assert badge._pulse_anim is None
        badge.set_pulse(True)
        assert badge._pulse_anim is not None
        badge.set_pulse(False)
        assert badge._pulse_anim is None

    def test_todos_os_9_estados_renderizam_sem_erro(self, qtbot):
        for status in BadgeStatus:
            badge = StatusBadge(status)
            qtbot.addWidget(badge)
            badge.show()
            # Força paint ciclo — deve terminar sem exceção
            badge.repaint()
            assert badge.isVisible()

    def test_largura_cresce_com_texto_maior(self, qtbot):
        curto = StatusBadge(BadgeStatus.OK, text="OK")
        longo = StatusBadge(BadgeStatus.OK, text="Verificação em andamento")
        qtbot.addWidget(curto)
        qtbot.addWidget(longo)
        assert longo.sizeHint().width() > curto.sizeHint().width()


# --------------------------------------------------------------------
# VersionLabel
# --------------------------------------------------------------------

class TestVersionLabel:
    def test_instancia_mostra_rotulo_e_versao(self, qtbot):
        lbl = VersionLabel(SpedType.EFD_CONTRIB, "3.1.0")
        qtbot.addWidget(lbl)
        assert "EFD-Contrib" in lbl.text()
        assert "3.1.0" in lbl.text()

    def test_versao_atual_nao_sinaliza_desatualizada(self, qtbot):
        lbl = VersionLabel(SpedType.ECD, "9.00")
        qtbot.addWidget(lbl)
        assert not lbl.is_desatualizada()

    def test_versao_antiga_sinaliza_desatualizada(self, qtbot):
        lbl = VersionLabel(SpedType.ECD, "8.00")
        qtbot.addWidget(lbl)
        assert lbl.is_desatualizada()

    def test_tooltip_contem_referencia_legal(self, qtbot):
        lbl = VersionLabel(SpedType.ECF, "0012")
        qtbot.addWidget(lbl)
        assert "ADE Cofis" in lbl.toolTip() or "Leiaute" in lbl.toolTip()

    def test_set_version_atualiza_exibicao(self, qtbot):
        lbl = VersionLabel(SpedType.EFD_CONTRIB, "3.1.0")
        qtbot.addWidget(lbl)
        lbl.set_version("2.9.0")
        assert "2.9.0" in lbl.text()
        assert lbl.is_desatualizada()

    def test_quatro_tipos_de_sped_renderizam(self, qtbot):
        for tipo in SpedType:
            lbl = VersionLabel(tipo, "0.0.0")
            qtbot.addWidget(lbl)
            assert lbl.text()  # não-vazio


# --------------------------------------------------------------------
# CodigoLinkButton
# --------------------------------------------------------------------

class TestCodigoLinkButton:
    @pytest.fixture(autouse=True)
    def _limpar_qsettings(self, qtbot):
        """Limpa cache de visitados antes de cada teste para isolamento."""
        s = QSettings("Primetax Solutions", "SpedCrossref")
        s.setValue("visited_sped_links", [])
        yield
        s.setValue("visited_sped_links", [])

    def test_exibe_numero_da_linha(self, qtbot):
        btn = CodigoLinkButton("efd_c.txt", 1847, "C", "C170")
        qtbot.addWidget(btn)
        assert "L1847" in btn.text()

    def test_payload_carrega_dados_completos(self, qtbot):
        btn = CodigoLinkButton("/path/efd_c.txt", 1847, "C", "C170")
        qtbot.addWidget(btn)
        p = btn.payload()
        assert p == {
            "arquivo": "/path/efd_c.txt",
            "linha": 1847,
            "bloco": "C",
            "registro": "C170",
        }

    def test_clique_emite_open_sped_com_payload(self, qtbot):
        btn = CodigoLinkButton("efd_c.txt", 100, "C", "C170")
        qtbot.addWidget(btn)
        with qtbot.waitSignal(btn.open_sped, timeout=500) as blocker:
            qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
        assert blocker.args[0]["linha"] == 100

    def test_enter_emite_open_sped(self, qtbot):
        btn = CodigoLinkButton("efd_c.txt", 42, "M", "M300")
        qtbot.addWidget(btn)
        btn.setFocus()
        with qtbot.waitSignal(btn.open_sped, timeout=500):
            qtbot.keyClick(btn, Qt.Key.Key_Return)

    def test_clique_marca_como_visitado(self, qtbot):
        btn = CodigoLinkButton("efd_c.txt", 100, "C", "C170")
        qtbot.addWidget(btn)
        assert not btn.is_visited()
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
        assert btn.is_visited()

    def test_visitado_persiste_entre_instancias(self, qtbot):
        btn1 = CodigoLinkButton("efd_c.txt", 100, "C", "C170")
        qtbot.addWidget(btn1)
        btn1.mark_visited(True)

        btn2 = CodigoLinkButton("efd_c.txt", 100, "C", "C170")
        qtbot.addWidget(btn2)
        assert btn2.is_visited()

    def test_tooltip_mostra_arquivo_e_registro(self, qtbot):
        btn = CodigoLinkButton("/caminho/longo/efd_c.txt", 1847, "C", "C170")
        qtbot.addWidget(btn)
        tip = btn.toolTip()
        assert "efd_c.txt" in tip
        assert "C170" in tip
        assert "1847" in tip
