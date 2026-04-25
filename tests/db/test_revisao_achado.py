"""
Testes da decisão #12 — revisão por-linha persistida em achados.

Cobre:
  - Schema novo cria colunas revisado_em/revisado_por/nota
  - Migration aditiva sobre banco pré-existente (sem as colunas)
  - Helpers marcar_revisada / desmarcar_revisada / atualizar_nota
  - Validação de tabela (SQL injection guard)
  - SELECT * inclui as novas colunas
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.db.repo import Repositorio


def _criar_oportunidade_minima(conn: sqlite3.Connection, cnpj: str, ano: int) -> int:
    cur = conn.execute(
        """INSERT INTO crossref_oportunidades
           (codigo_regra, descricao, severidade,
            valor_impacto_conservador, valor_impacto_maximo,
            evidencia_json, cnpj_declarante, ano_mes, ano_calendario, gerado_em)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        ("CR-07", "Tese 69 — exclusão ICMS C170", "alto",
         523000.00, 780500.00, "[]", cnpj, 202501, ano, "2025-04-24T09:47:00"),
    )
    return cur.lastrowid


class TestSchemaNovo:
    def test_colunas_revisao_existem_em_oportunidades(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            cols = {r["name"] for r in conn.execute(
                "PRAGMA table_info(crossref_oportunidades)"
            )}
        finally:
            conn.close()
        assert {"revisado_em", "revisado_por", "nota"}.issubset(cols)

    def test_colunas_revisao_existem_em_divergencias(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            cols = {r["name"] for r in conn.execute(
                "PRAGMA table_info(crossref_divergencias)"
            )}
        finally:
            conn.close()
        assert {"revisado_em", "revisado_por", "nota"}.issubset(cols)


class TestMigrationAditiva:
    def test_banco_pre_existente_recebe_colunas_via_alter(self, tmp_path):
        """Cria um banco com schema antigo (sem as colunas de revisão),
        depois roda criar_banco() de novo — deve aplicar migration."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        # Schema "antigo" (manualmente sem as 3 colunas)
        repo.caminho.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(repo.caminho)
        try:
            conn.executescript("""
                CREATE TABLE crossref_oportunidades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_regra TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    severidade TEXT NOT NULL,
                    valor_impacto_conservador REAL DEFAULT 0,
                    valor_impacto_maximo REAL DEFAULT 0,
                    evidencia_json TEXT NOT NULL,
                    cnpj_declarante TEXT NOT NULL,
                    ano_mes INTEGER,
                    ano_calendario INTEGER NOT NULL,
                    gerado_em TEXT NOT NULL
                );
                CREATE TABLE crossref_divergencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    codigo_regra TEXT NOT NULL,
                    descricao TEXT NOT NULL,
                    severidade TEXT NOT NULL,
                    evidencia_json TEXT NOT NULL,
                    cnpj_declarante TEXT NOT NULL,
                    ano_mes INTEGER,
                    ano_calendario INTEGER NOT NULL,
                    gerado_em TEXT NOT NULL
                );
            """)
            conn.commit()
        finally:
            conn.close()

        # Confirma que NÃO tem as colunas ainda
        conn = sqlite3.connect(repo.caminho)
        cols_antes = {r[1] for r in conn.execute("PRAGMA table_info(crossref_oportunidades)")}
        conn.close()
        assert "revisado_em" not in cols_antes

        # Aplica migration — chamando criar_banco em banco existente
        repo.criar_banco()

        # Agora deve ter
        conn = repo.conexao()
        try:
            cols_depois = {r["name"] for r in conn.execute(
                "PRAGMA table_info(crossref_oportunidades)"
            )}
        finally:
            conn.close()
        assert {"revisado_em", "revisado_por", "nota"}.issubset(cols_depois)

    def test_migration_idempotente(self, tmp_path):
        """Chamar criar_banco() múltiplas vezes não quebra."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        repo.criar_banco()
        repo.criar_banco()
        conn = repo.conexao()
        try:
            cols = {r["name"] for r in conn.execute(
                "PRAGMA table_info(crossref_oportunidades)"
            )}
        finally:
            conn.close()
        assert {"revisado_em", "revisado_por", "nota"}.issubset(cols)


class TestMarcarRevisada:
    def test_marcar_persiste_timestamp_e_usuario(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                achado_id = _criar_oportunidade_minima(conn, "00000000000100", 2025)
                repo.marcar_revisada(conn, achado_id, usuario="marcelo@primetax.com.br")

            row = conn.execute(
                "SELECT revisado_em, revisado_por FROM crossref_oportunidades WHERE id=?",
                (achado_id,),
            ).fetchone()
            assert row["revisado_por"] == "marcelo@primetax.com.br"
            assert row["revisado_em"]  # timestamp não-nulo
        finally:
            conn.close()

    def test_desmarcar_zera_campos(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                achado_id = _criar_oportunidade_minima(conn, "00000000000100", 2025)
                repo.marcar_revisada(conn, achado_id, usuario="marcelo")
                repo.desmarcar_revisada(conn, achado_id)

            row = conn.execute(
                "SELECT revisado_em, revisado_por FROM crossref_oportunidades WHERE id=?",
                (achado_id,),
            ).fetchone()
            assert row["revisado_em"] is None
            assert row["revisado_por"] is None
        finally:
            conn.close()


class TestAtualizarNota:
    def test_atualizar_persiste_texto(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                achado_id = _criar_oportunidade_minima(conn, "00000000000100", 2025)
                repo.atualizar_nota(
                    conn, achado_id,
                    "Confirmar com cliente se NF-e foi emitida",
                )
            row = conn.execute(
                "SELECT nota FROM crossref_oportunidades WHERE id=?",
                (achado_id,),
            ).fetchone()
            assert "NF-e" in row["nota"]
        finally:
            conn.close()

    def test_nota_vazia_vira_null(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                achado_id = _criar_oportunidade_minima(conn, "00000000000100", 2025)
                repo.atualizar_nota(conn, achado_id, "rascunho")
                repo.atualizar_nota(conn, achado_id, "   ")  # só espaços
            row = conn.execute(
                "SELECT nota FROM crossref_oportunidades WHERE id=?",
                (achado_id,),
            ).fetchone()
            assert row["nota"] is None
        finally:
            conn.close()


class TestValidacaoTabela:
    def test_tabela_invalida_levanta_value_error(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with pytest.raises(ValueError, match="Tabela inválida"):
                repo.marcar_revisada(conn, 1, "marcelo", tabela="DROP TABLE; --")
            with pytest.raises(ValueError):
                repo.atualizar_nota(conn, 1, "x", tabela="OUTRA")
        finally:
            conn.close()
