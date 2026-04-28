"""
Testes da view T9 (Análise Contábil) — usa controller stub.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.controllers.contabil_controller import (
    ContabilDisponibilidade,
    DespesaVsCredito,
    EvidenciaCredito,
    ImobilizadoVsCredito,
    LancamentoRazao,
    LinhaBalanco,
    RazaoConta,
)
from src.gui.views.t9_contabil import T9Contabil


class _StubController:
    def __init__(
        self,
        bp: list[LinhaBalanco] | None = None,
        dre: list[LinhaBalanco] | None = None,
        razao: dict[str, list[LancamentoRazao]] | None = None,
        despesas: list[DespesaVsCredito] | None = None,
        imobilizado: list[ImobilizadoVsCredito] | None = None,
        evidencias: dict[str, list[EvidenciaCredito]] | None = None,
        contas: list[tuple[str, str]] | None = None,
        disp: ContabilDisponibilidade | None = None,
    ):
        self._bp = bp or []
        self._dre = dre or []
        self._razao = razao or {}
        self._despesas = despesas or []
        self._imobilizado = imobilizado or []
        self._evidencias = evidencias or {}
        self._contas = contas or []
        self._marcadas: set[str] = set()
        self._disp = disp or ContabilDisponibilidade(
            tem_ecd=True, tem_j100=True, tem_j150=True,
            tem_i250=True, tem_efd_contribuicoes=True,
        )

    def disponibilidade(self): return self._disp
    def listar_balanco_patrimonial(self): return list(self._bp)
    def listar_dre(self): return list(self._dre)
    def listar_razao(self, cod_cta, ano_mes_ini=None, ano_mes_fin=None):
        return list(self._razao.get(cod_cta, []))
    def consultar_razao_completo(self, cod_cta, ano_mes_ini=None, ano_mes_fin=None):
        lancs = list(self._razao.get(cod_cta, []))
        if not lancs:
            return None
        total_d = sum((l.debito for l in lancs), Decimal("0"))
        total_c = sum((l.credito for l in lancs), Decimal("0"))
        saldo = total_d - total_c
        for l in lancs:
            l.saldo_corrente = saldo
        return RazaoConta(
            cod_cta=cod_cta, descricao="STUB",
            saldo_inicial=Decimal("0"), ind_dc_inicial="D",
            lancamentos=lancs,
            total_debito=total_d, total_credito=total_c,
            saldo_final=abs(saldo), ind_dc_final="D" if saldo >= 0 else "C",
        )
    def listar_contas_movimentadas(self): return list(self._contas)
    def listar_despesas_vs_credito(self): return list(self._despesas)
    def listar_imobilizado_vs_credito(self): return list(self._imobilizado)
    def listar_evidencias_credito(self, cod_cta):
        return list(self._evidencias.get(cod_cta, []))
    def marcar_oportunidade(self, cod_cta, *, marcado_por="", nota=""):
        self._marcadas.add(cod_cta)
        return True
    def desmarcar_oportunidade(self, cod_cta):
        self._marcadas.discard(cod_cta)
        return True


def _cliente() -> ClienteRow:
    return ClienteRow(
        cnpj="00000000000100",
        razao_social="ACME SA",
        ano_calendario=2025,
        speds_importados=["EFD-Contrib", "ECD"],
        impacto_total=Decimal("0"),
        ultima_atividade=datetime(2025, 4, 24),
        banco_path=Path("/tmp/x.sqlite"),
    )


def _injetar_stub(monkeypatch, stub):
    from src.gui.views import t9_contabil as t9mod
    monkeypatch.setattr(t9mod, "ContabilController", lambda **kw: stub)


def _bp_linha(cod_agl, descr, nivel, sup, sintetica, vl_fin, dc_fin="D"):
    return LinhaBalanco(
        nu_ordem=cod_agl, cod_agl=cod_agl, descricao=descr, nivel=nivel,
        cod_agl_sup=sup, grupo="A",
        vl_inicial=Decimal("0"), ind_dc_ini=dc_fin,
        vl_final=Decimal(str(vl_fin)), ind_dc_fin=dc_fin,
        ind_cod_agl="T" if sintetica else "D",
    )


# --------------------------------------------------------------------
# Empty state
# --------------------------------------------------------------------

class TestT9SemCliente:
    def test_inicial_mostra_empty(self, qtbot):
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        assert t9._stack.currentWidget() is t9._empty


class TestT9ComCliente:
    def test_carregar_cliente_ativa_conteudo(self, qtbot, monkeypatch):
        stub = _StubController()
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        assert t9._stack.currentWidget() is t9._conteudo
        assert "ACME SA" in t9._titulo.text()

    def test_quatro_abas_presentes(self, qtbot, monkeypatch):
        stub = _StubController()
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        # 4 abas: BP, DRE, Despesas, Imobilizado (Razão é drill-down inline)
        assert t9._tabs.count() == 4
        assert t9._tabs.tabText(0) == "Balanço Patrimonial"
        assert t9._tabs.tabText(1) == "DRE"
        assert "Despesas" in t9._tabs.tabText(2)
        assert "Imobilizado" in t9._tabs.tabText(3)

    def test_bp_popula_arvore(self, qtbot, monkeypatch):
        bp = [
            _bp_linha("1", "ATIVO", 1, "", True, 100000),
            _bp_linha("2", "ATIVO CIRCULANTE", 2, "1", True, 80000),
            _bp_linha("3", "CAIXA", 3, "2", False, 5000),
        ]
        stub = _StubController(bp=bp)
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        model = t9._tree_bp.model()
        assert model is not None
        assert model.rowCount() == 1  # raiz "ATIVO"
        item_ativo = model.item(0, 0)
        assert item_ativo.text() == "ATIVO"
        assert item_ativo.rowCount() == 1  # filho "ATIVO CIRCULANTE"

    def test_dre_popula_arvore(self, qtbot, monkeypatch):
        dre = [
            LinhaBalanco(
                nu_ordem="1", cod_agl="1", descricao="RECEITA OPERACIONAL",
                nivel=1, cod_agl_sup="", grupo="R",
                vl_inicial=Decimal("500000"), ind_dc_ini="C",
                vl_final=Decimal("500000"), ind_dc_fin="C",
                ind_cod_agl="T",
            ),
        ]
        stub = _StubController(dre=dre)
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        model = t9._tree_dre.model()
        assert model.rowCount() == 1

    def test_despesas_popula(self, qtbot, monkeypatch):
        despesas = [
            DespesaVsCredito(
                cod_cta="3.1.01", descricao="ALUGUEL",
                saldo_periodo=Decimal("12000"),
                credito_pis_cofins=Decimal("12000"),
                tem_credito=True,
            ),
            DespesaVsCredito(
                cod_cta="3.1.02", descricao="FRETE",
                saldo_periodo=Decimal("8000"),
                credito_pis_cofins=Decimal("0"),
                tem_credito=False,
            ),
        ]
        stub = _StubController(despesas=despesas)
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        assert t9._tabela_despesas.total_rows() == 2

    def test_selecao_despesa_popula_evidencias(self, qtbot, monkeypatch):
        despesas = [DespesaVsCredito(
            cod_cta="3.1.01", descricao="ALUGUEL",
            saldo_periodo=Decimal("12000"),
            credito_pis_cofins=Decimal("12000"),
            tem_credito=True,
        )]
        evidencias = {"3.1.01": [
            EvidenciaCredito(
                arquivo="/tmp/efd.txt", linha_arquivo=4567,
                registro="F100", ano_mes=202503,
                valor_base=Decimal("4000"), nat_bc_cred="01",
                descricao="Aluguel março",
            ),
        ]}
        stub = _StubController(despesas=despesas, evidencias=evidencias)
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        # Simula seleção
        t9._on_despesa_selecionada({"cod_cta": "3.1.01", "descricao": "ALUGUEL"})
        assert t9._tabela_evidencias.total_rows() == 1
        assert "1 linha" in t9._evidencias_header.text()

    def test_sem_ecd_mostra_warning(self, qtbot, monkeypatch):
        stub = _StubController(disp=ContabilDisponibilidade(
            tem_ecd=False, tem_j100=False, tem_j150=False,
            tem_i250=False, tem_efd_contribuicoes=False,
        ))
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.carregar_cliente(_cliente())
        assert t9._inline_aviso is not None


class TestT9Export:
    def test_exportar_bp_gera_arquivo(self, qtbot, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        stub = _StubController(bp=[
            _bp_linha("1", "ATIVO", 1, "", True, 100000),
        ])
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.show()
        t9.carregar_cliente(_cliente())

        with qtbot.waitSignal(t9.csv_exportado, timeout=2000) as blocker:
            t9._exportar_bp()
        assert blocker.args[0].exists()
        assert "balanco_patrimonial" in blocker.args[0].name

    def test_exportar_despesas_gera_arquivo(self, qtbot, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        stub = _StubController(despesas=[DespesaVsCredito(
            cod_cta="3.1.01", descricao="ALUGUEL",
            saldo_periodo=Decimal("1000"),
            credito_pis_cofins=Decimal("0"),
            tem_credito=False,
        )])
        _injetar_stub(monkeypatch, stub)
        t9 = T9Contabil()
        qtbot.addWidget(t9)
        t9.show()
        t9.carregar_cliente(_cliente())

        with qtbot.waitSignal(t9.csv_exportado, timeout=2000) as blocker:
            t9._exportar_despesas()
        assert blocker.args[0].exists()
        assert "despesas_vs_credito" in blocker.args[0].name
