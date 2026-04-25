"""
Testes da view T8 (Auditoria & Logs forense) — usa controller stub.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from src.gui.controllers.auditoria_controller import ImportacaoRow
from src.gui.controllers.clientes_controller import ClienteRow
from src.gui.views.t8_auditoria import T8Auditoria


class _StubController:
    """Stub do AuditoriaController — controla diretamente o que listar_importacoes
    devolve sem mexer em SQLite."""

    def __init__(self, linhas: list[ImportacaoRow] | None = None):
        self._linhas = list(linhas or [])
        self.export_calls: list[Path] = []

    def listar_importacoes(self) -> list[ImportacaoRow]:
        return list(self._linhas)

    def exportar_csv(self, destino: Path) -> Path:
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text("id,sped_tipo\n", encoding="utf-8")
        sha = destino.with_suffix(destino.suffix + ".sha256")
        sha.write_text("0" * 64 + f"  {destino.name}\n", encoding="utf-8")
        self.export_calls.append(destino)
        return destino


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


def _row(
    rid: int = 1,
    sped_tipo: str = "efd_contribuicoes",
    dt_ini: str = "2025-01-01",
    dt_fin: str = "2025-01-31",
    arquivo: str = "/tmp/efd.txt",
    arquivo_hash: str = "a" * 64,
    importado_em: datetime | None = None,
    is_reimport: bool = False,
    hash_anterior: str | None = None,
    status: str = "ok",
) -> ImportacaoRow:
    return ImportacaoRow(
        id=rid,
        sped_tipo=sped_tipo,
        sped_label={
            "efd_contribuicoes": "EFD-Contribuições",
            "efd_icms": "EFD ICMS/IPI",
            "ecd": "ECD",
            "ecf": "ECF",
        }.get(sped_tipo, sped_tipo),
        dt_ini=dt_ini, dt_fin=dt_fin, ano_mes=202501,
        arquivo_origem=arquivo,
        arquivo_nome=Path(arquivo).name,
        arquivo_hash=arquivo_hash,
        importado_em=importado_em or datetime(2025, 4, 20, 10, 30),
        cod_ver="1.0",
        encoding_origem="utf8",
        encoding_confianca="alto",
        status=status,
        is_reimport=is_reimport,
        hash_anterior=hash_anterior,
    )


class TestT8SemCliente:
    def test_inicial_mostra_empty(self, qtbot):
        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        assert t8._stack.currentWidget() is t8._empty


class TestT8ComCliente:
    def test_carregar_cliente_ativa_conteudo(self, qtbot, monkeypatch):
        # Substitui o controller por stub
        stub = _StubController([_row(rid=1)])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        assert t8._stack.currentWidget() is t8._conteudo
        assert "ACME SA" in t8._titulo.text()
        assert "2025" in t8._titulo.text()

    def test_lista_uma_importacao(self, qtbot, monkeypatch):
        stub = _StubController([_row(rid=1)])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        assert t8._tabela.total_rows() == 1

    def test_filtro_chip_sped_filtra(self, qtbot, monkeypatch):
        stub = _StubController([
            _row(rid=1, sped_tipo="efd_contribuicoes"),
            _row(rid=2, sped_tipo="ecd"),
        ])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        assert t8._tabela.total_rows() == 2

        # Liga chip ECD — só ECD deve aparecer
        t8._chips_sped["ecd"].setChecked(True)
        assert t8._tabela.total_rows() == 1

    def test_filtro_chip_status_filtra(self, qtbot, monkeypatch):
        stub = _StubController([
            _row(rid=1, status="ok"),
            _row(rid=2, status="rejeitado"),
        ])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        t8._chips_status["rejeitado"].setChecked(True)
        assert t8._tabela.total_rows() == 1

    def test_chip_reimport_filtra_apenas_reimport(self, qtbot, monkeypatch):
        stub = _StubController([
            _row(rid=1, is_reimport=False),
            _row(
                rid=2, is_reimport=True,
                hash_anterior="b" * 64,
                arquivo_hash="c" * 64,
            ),
        ])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        t8._chip_reimport.setChecked(True)
        assert t8._tabela.total_rows() == 1

    def test_selecao_de_linha_popula_painel(self, qtbot, monkeypatch):
        stub = _StubController([_row(rid=1, arquivo_hash="abc" + "0" * 61)])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())

        # Simula seleção pegando o dict da primeira linha visível
        rows = t8._tabela.visible_rows()
        assert len(rows) == 1
        t8._on_linha_selecionada(rows[0])
        assert t8._linha_selecionada is not None
        assert t8._linha_selecionada.id == 1
        assert "abc" in t8._painel_corpo.text()
        assert t8._btn_abrir_arquivo.isEnabled()

    def test_painel_mostra_reimport_quando_aplicavel(self, qtbot, monkeypatch):
        stub = _StubController([_row(
            rid=2, is_reimport=True,
            arquivo_hash="novo" + "0" * 60,
            hash_anterior="velho" + "0" * 59,
        )])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.carregar_cliente(_cliente())
        rows = t8._tabela.visible_rows()
        t8._on_linha_selecionada(rows[0])
        assert "REIMPORT" in t8._painel_corpo.text()
        assert "velho" in t8._painel_corpo.text()

    def test_export_csv_chama_controller(self, qtbot, monkeypatch, tmp_path):
        monkeypatch.chdir(tmp_path)
        stub = _StubController([_row(rid=1)])
        from src.gui.views import t8_auditoria as t8mod
        monkeypatch.setattr(t8mod, "AuditoriaController", lambda **kw: stub)

        t8 = T8Auditoria()
        qtbot.addWidget(t8)
        t8.show()  # window() necessária para Toast
        t8.carregar_cliente(_cliente())

        with qtbot.waitSignal(t8.csv_exportado, timeout=500) as blocker:
            t8._exportar_csv()

        assert len(stub.export_calls) == 1
        # Caminho default: data/output/{cnpj}/{ano}/auditoria.csv
        destino = stub.export_calls[0]
        assert destino.name == "auditoria.csv"
        assert "00000000000100" in str(destino)
        assert "2025" in str(destino)
        # Sinal trouxe o caminho correto
        assert blocker.args[0] == destino
        # SHA companheiro existe
        assert destino.with_suffix(destino.suffix + ".sha256").exists()
