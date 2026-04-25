"""
Testes do AuditoriaController — leitura de _importacoes + detecção de
REIMPORT + export CSV + .sha256 companheiro (decisão #21).
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from src.gui.controllers.auditoria_controller import (
    AuditoriaController,
    ImportacaoRow,
)


def _criar_banco_com_importacoes(
    base_dir: Path,
    cnpj: str,
    ano: int,
    importacoes: list[dict],
) -> Path:
    """Cria banco SQLite com _importacoes mínima e insere linhas."""
    caminho = base_dir / cnpj / f"{ano}.sqlite"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(caminho)
    try:
        conn.execute(
            """
            CREATE TABLE _importacoes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                sped_tipo        TEXT NOT NULL,
                dt_ini           TEXT NOT NULL,
                dt_fin           TEXT NOT NULL,
                ano_mes          INTEGER NOT NULL,
                arquivo_hash     TEXT NOT NULL,
                arquivo_origem   TEXT NOT NULL,
                importado_em     TEXT NOT NULL,
                cod_ver          TEXT NOT NULL,
                encoding_origem  TEXT NOT NULL,
                encoding_confianca TEXT NOT NULL,
                status           TEXT NOT NULL
            )
            """
        )
        for imp in importacoes:
            conn.execute(
                """
                INSERT INTO _importacoes
                  (sped_tipo, dt_ini, dt_fin, ano_mes, arquivo_hash,
                   arquivo_origem, importado_em, cod_ver,
                   encoding_origem, encoding_confianca, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    imp["sped_tipo"], imp["dt_ini"], imp["dt_fin"],
                    imp["ano_mes"], imp["arquivo_hash"], imp["arquivo_origem"],
                    imp["importado_em"], imp.get("cod_ver", "1.0"),
                    imp.get("encoding_origem", "utf8"),
                    imp.get("encoding_confianca", "alto"),
                    imp.get("status", "ok"),
                ),
            )
        conn.commit()
    finally:
        conn.close()
    return caminho


class TestAuditoriaControllerLeitura:
    def test_banco_inexistente_retorna_lista_vazia(self, tmp_path):
        ctrl = AuditoriaController(
            cnpj="00000000000100",
            ano_calendario=2025,
            base_dir=tmp_path / "nao-existe",
        )
        assert ctrl.listar_importacoes() == []

    def test_banco_sem_tabela_importacoes_retorna_vazio(self, tmp_path):
        # Cria banco vazio sem tabela _importacoes
        db_dir = tmp_path / "db"
        caminho = db_dir / "00000000000100" / "2025.sqlite"
        caminho.parent.mkdir(parents=True, exist_ok=True)
        sqlite3.connect(caminho).close()

        ctrl = AuditoriaController(
            cnpj="00000000000100",
            ano_calendario=2025,
            base_dir=db_dir,
        )
        assert ctrl.listar_importacoes() == []

    def test_le_uma_importacao_simples(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [{
                "sped_tipo": "efd_contribuicoes",
                "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                "ano_mes": 202501,
                "arquivo_hash": "abc123" * 10,
                "arquivo_origem": "/tmp/efd_contrib.txt",
                "importado_em": "2025-04-20T10:30:00",
            }],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100",
            ano_calendario=2025,
            base_dir=db_dir,
        )
        linhas = ctrl.listar_importacoes()
        assert len(linhas) == 1
        l = linhas[0]
        assert isinstance(l, ImportacaoRow)
        assert l.sped_tipo == "efd_contribuicoes"
        assert l.sped_label == "EFD-Contribuições"
        assert l.is_reimport is False
        assert l.hash_anterior is None
        assert l.arquivo_nome == "efd_contrib.txt"

    def test_ordena_por_importado_em_desc(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "a" * 64,
                    "arquivo_origem": "/tmp/jan.txt",
                    "importado_em": "2025-04-01T08:00:00",
                },
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-02-01", "dt_fin": "2025-02-28",
                    "ano_mes": 202502, "arquivo_hash": "b" * 64,
                    "arquivo_origem": "/tmp/fev.txt",
                    "importado_em": "2025-04-15T10:00:00",
                },
            ],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        linhas = ctrl.listar_importacoes()
        assert len(linhas) == 2
        # Mais recente primeiro
        assert linhas[0].dt_ini == "2025-02-01"
        assert linhas[1].dt_ini == "2025-01-01"

    def test_detecta_reimport_quando_mesmo_periodo_hash_diferente(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501,
                    "arquivo_hash": "primeiro" + "0" * 56,
                    "arquivo_origem": "/tmp/v1.txt",
                    "importado_em": "2025-04-01T08:00:00",
                },
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501,
                    "arquivo_hash": "segundo" + "0" * 57,
                    "arquivo_origem": "/tmp/v2.txt",
                    "importado_em": "2025-04-15T10:00:00",
                },
            ],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        linhas = ctrl.listar_importacoes()
        # Mais recente é REIMPORT
        recente = linhas[0]
        antiga = linhas[1]
        assert recente.is_reimport is True
        assert recente.hash_anterior == "primeiro" + "0" * 56
        # A antiga não é reimport (não há entrada anterior diferente)
        assert antiga.is_reimport is False

    def test_nao_marca_reimport_quando_mesmo_hash(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "x" * 64,
                    "arquivo_origem": "/tmp/v1.txt",
                    "importado_em": "2025-04-01T08:00:00",
                },
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "x" * 64,
                    "arquivo_origem": "/tmp/v1_again.txt",
                    "importado_em": "2025-04-15T10:00:00",
                },
            ],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        linhas = ctrl.listar_importacoes()
        for l in linhas:
            assert l.is_reimport is False

    def test_periodos_diferentes_nao_sao_reimport(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "a" * 64,
                    "arquivo_origem": "/tmp/jan.txt",
                    "importado_em": "2025-04-01T08:00:00",
                },
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-02-01", "dt_fin": "2025-02-28",
                    "ano_mes": 202502, "arquivo_hash": "b" * 64,
                    "arquivo_origem": "/tmp/fev.txt",
                    "importado_em": "2025-04-15T10:00:00",
                },
            ],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        linhas = ctrl.listar_importacoes()
        for l in linhas:
            assert l.is_reimport is False


class TestAuditoriaControllerExportCsv:
    def test_exporta_csv_e_sha_companheiro(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [{
                "sped_tipo": "efd_contribuicoes",
                "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                "ano_mes": 202501,
                "arquivo_hash": "a" * 64,
                "arquivo_origem": "/tmp/jan.txt",
                "importado_em": "2025-04-01T08:00:00",
            }],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        destino = tmp_path / "out" / "auditoria.csv"
        retorno = ctrl.exportar_csv(destino)

        assert retorno == destino
        assert destino.exists()
        sha_file = destino.with_suffix(destino.suffix + ".sha256")
        assert sha_file.exists()

        # Conferir SHA-256
        sha_esperado = hashlib.sha256(destino.read_bytes()).hexdigest()
        sha_arquivo = sha_file.read_text(encoding="utf-8").split()[0]
        assert sha_arquivo == sha_esperado

    def test_csv_contem_header_e_linha(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [{
                "sped_tipo": "efd_contribuicoes",
                "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                "ano_mes": 202501,
                "arquivo_hash": "abc123" + "0" * 58,
                "arquivo_origem": "/tmp/jan.txt",
                "importado_em": "2025-04-01T08:00:00",
            }],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        destino = tmp_path / "out" / "auditoria.csv"
        ctrl.exportar_csv(destino)

        conteudo = destino.read_text(encoding="utf-8")
        # Header
        assert "id,sped_tipo,dt_ini" in conteudo
        # Linha
        assert "efd_contribuicoes" in conteudo
        assert "abc123" in conteudo

    def test_csv_marca_is_reimport_corretamente(self, tmp_path):
        db_dir = tmp_path / "db"
        _criar_banco_com_importacoes(
            db_dir, "00000000000100", 2025,
            [
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "a" * 64,
                    "arquivo_origem": "/tmp/v1.txt",
                    "importado_em": "2025-04-01T08:00:00",
                },
                {
                    "sped_tipo": "efd_contribuicoes",
                    "dt_ini": "2025-01-01", "dt_fin": "2025-01-31",
                    "ano_mes": 202501, "arquivo_hash": "b" * 64,
                    "arquivo_origem": "/tmp/v2.txt",
                    "importado_em": "2025-04-15T10:00:00",
                },
            ],
        )
        ctrl = AuditoriaController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=db_dir,
        )
        destino = tmp_path / "out" / "auditoria.csv"
        ctrl.exportar_csv(destino)

        conteudo = destino.read_text(encoding="utf-8")
        # Pelo menos um "true" e um "false" para is_reimport
        linhas = [l for l in conteudo.splitlines() if l.startswith("2,") or l.startswith("1,")]
        assert any(",true," in l for l in linhas)
        assert any(",false," in l for l in linhas)
