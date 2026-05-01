"""Testes dos 3 métodos de dedup adicionados ao Repositorio (Bug-002 + Bug-005).

  - existe_import_com_hash: protege contra reimport idêntico (UX, Opção 3)
  - deletar_dados_anteriores: DELETE prévio em tabelas SPED filhas (Opção 2)
  - deletar_diagnostico_anterior: DELETE em crossref_* antes de re-diagnóstico

Tabelas de controle/anotação NÃO devem ser tocadas por nenhum dos métodos.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from src.db.repo import Repositorio


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _inserir_import(
    conn: sqlite3.Connection, *, sped_tipo: str, ano_mes: int,
    arquivo_hash: str, dt_ini: str = "2025-01-01", dt_fin: str = "2025-01-31",
) -> int:
    cur = conn.execute(
        """INSERT INTO _importacoes
           (sped_tipo, dt_ini, dt_fin, ano_mes, arquivo_hash, arquivo_origem,
            importado_em, cod_ver, encoding_origem, encoding_confianca, status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (sped_tipo, dt_ini, dt_fin, ano_mes, arquivo_hash, "/tmp/x.txt",
         "2025-04-29T10:00:00+00:00", "006", "utf8", "validado", "ok"),
    )
    return cur.lastrowid

def _inserir_efd_contrib_0000(
    conn: sqlite3.Connection, cnpj: str, ano_mes: int,
) -> None:
    conn.execute(
        """INSERT INTO efd_contrib_0000
           (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
            nome)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        ("/tmp/x.txt", 1, "0", "0000", cnpj,
         "2025-01-01", "2025-01-31", ano_mes, ano_mes // 100,
         "006", "EMPRESA TESTE"),
    )

def _inserir_ecd_0000(
    conn: sqlite3.Connection, cnpj: str, ano_calendario: int,
) -> None:
    conn.execute(
        """INSERT INTO ecd_0000
           (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
            nome, uf, cod_mun, ind_fin_esc, ind_grande_porte, tip_ecd,
            ident_mf, ind_mudanc_pc, cod_plan_ref)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("/tmp/x.txt", 1, "0", "0000", cnpj,
         f"{ano_calendario}-01-01", f"{ano_calendario}-12-31",
         ano_calendario * 100 + 1, ano_calendario, "9.00",
         "EMPRESA TESTE", "SP", "3550308",
         "0", "N", "0", "S", "0", "1"),
    )


# ----------------------------------------------------------------------
# existe_import_com_hash
# ----------------------------------------------------------------------

class TestExisteImportComHash:
    def test_retorna_none_quando_nao_existe(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            res = repo.existe_import_com_hash(
                conn, sped_tipo="efd_contribuicoes", cnpj="00000000000100",
                periodo=202501, arquivo_hash="abc123",
            )
            assert res is None
        finally:
            conn.close()

    def test_retorna_dict_quando_existe(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_import(conn, sped_tipo="efd_contribuicoes",
                                ano_mes=202501, arquivo_hash="abc123")
            res = repo.existe_import_com_hash(
                conn, sped_tipo="efd_contribuicoes", cnpj="00000000000100",
                periodo=202501, arquivo_hash="abc123",
            )
            assert res is not None
            assert "id" in res
            assert "importado_em" in res
        finally:
            conn.close()

    def test_distingue_por_sped_tipo(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_import(conn, sped_tipo="efd_contribuicoes",
                                ano_mes=202501, arquivo_hash="abc123")
            # Mesmo hash + ano_mes, mas tipo diferente: NÃO match
            res = repo.existe_import_com_hash(
                conn, sped_tipo="efd_icms", cnpj="00000000000100",
                periodo=202501, arquivo_hash="abc123",
            )
            assert res is None
        finally:
            conn.close()

    def test_sped_anual_usa_aaaa01(self, tmp_path):
        """Para sped_tipo='ecd', _importacoes.ano_mes é AAAA01.
        existe_import_com_hash deve aceitar periodo=ano_calendario."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_import(conn, sped_tipo="ecd",
                                ano_mes=202501,  # AAAA01 = jan/2025
                                arquivo_hash="ecd_hash",
                                dt_ini="2025-01-01", dt_fin="2025-12-31")
            # Caller passa ano_calendario=2025
            res = repo.existe_import_com_hash(
                conn, sped_tipo="ecd", cnpj="00000000000100",
                periodo=2025, arquivo_hash="ecd_hash",
            )
            assert res is not None
        finally:
            conn.close()

    def test_sped_tipo_invalido_levanta_value_error(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with pytest.raises(ValueError, match="sped_tipo"):
                repo.existe_import_com_hash(
                    conn, sped_tipo="invalido", cnpj="x",
                    periodo=1, arquivo_hash="x",
                )
        finally:
            conn.close()


# ----------------------------------------------------------------------
# deletar_dados_anteriores
# ----------------------------------------------------------------------

class TestDeletarDadosAnteriores:
    def test_apaga_apenas_periodo_solicitado_mensal(self, tmp_path):
        """EFD-Contrib jan e fev no banco. DELETE só apaga jan."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_efd_contrib_0000(conn, "00000000000100", 202501)
                _inserir_efd_contrib_0000(conn, "00000000000100", 202502)
                qtd = repo.deletar_dados_anteriores(
                    conn, sped_tipo="efd_contribuicoes",
                    cnpj="00000000000100", ano_mes=202501,
                )
            assert qtd == 1
            restantes = conn.execute(
                "SELECT ano_mes FROM efd_contrib_0000"
            ).fetchall()
            assert len(restantes) == 1
            assert restantes[0]["ano_mes"] == 202502
        finally:
            conn.close()

    def test_apaga_anual_completo_para_ecd(self, tmp_path):
        """ECD usa ano_calendario; DELETE apaga todos os meses do ano."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_ecd_0000(conn, "00000000000100", 2025)
                _inserir_ecd_0000(conn, "00000000000100", 2024)
                qtd = repo.deletar_dados_anteriores(
                    conn, sped_tipo="ecd",
                    cnpj="00000000000100", ano_calendario=2025,
                )
            assert qtd == 1
            restantes = conn.execute(
                "SELECT ano_calendario FROM ecd_0000"
            ).fetchall()
            assert len(restantes) == 1
            assert restantes[0]["ano_calendario"] == 2024
        finally:
            conn.close()

    def test_preserva_outros_cnpj(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_efd_contrib_0000(conn, "00000000000100", 202501)
                _inserir_efd_contrib_0000(conn, "11111111111111", 202501)
                qtd = repo.deletar_dados_anteriores(
                    conn, sped_tipo="efd_contribuicoes",
                    cnpj="00000000000100", ano_mes=202501,
                )
            assert qtd == 1
            restantes = conn.execute(
                "SELECT cnpj_declarante FROM efd_contrib_0000"
            ).fetchall()
            assert len(restantes) == 1
            assert restantes[0]["cnpj_declarante"] == "11111111111111"
        finally:
            conn.close()

    def test_preserva_tabelas_de_controle(self, tmp_path):
        """_importacoes, _sped_contexto e contabil_oportunidades_essencialidade
        NÃO podem ser tocadas pelo DELETE."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                _inserir_import(conn, sped_tipo="efd_contribuicoes",
                                ano_mes=202501, arquivo_hash="abc")
                _inserir_efd_contrib_0000(conn, "00000000000100", 202501)
                conn.execute(
                    "INSERT INTO contabil_oportunidades_essencialidade "
                    "(cnpj_declarante, ano_calendario, cod_cta, marcado_em, marcado_por, nota) "
                    "VALUES (?,?,?,?,?,?)",
                    ("00000000000100", 2025, "3.1.01",
                     "2025-04-29T10:00:00+00:00", "auditor", "candidata"),
                )
                repo.deletar_dados_anteriores(
                    conn, sped_tipo="efd_contribuicoes",
                    cnpj="00000000000100", ano_mes=202501,
                )
            # Tabelas filhas SPED apagadas; controle preservadas
            assert conn.execute("SELECT COUNT(*) FROM efd_contrib_0000").fetchone()[0] == 0
            assert conn.execute("SELECT COUNT(*) FROM _importacoes").fetchone()[0] == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM contabil_oportunidades_essencialidade"
            ).fetchone()[0] == 1
        finally:
            conn.close()

    def test_sped_tipo_invalido_levanta_value_error(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with pytest.raises(ValueError, match="sped_tipo"):
                repo.deletar_dados_anteriores(
                    conn, sped_tipo="x", cnpj="y", ano_mes=202501,
                )
        finally:
            conn.close()

    def test_periodo_obrigatorio(self, tmp_path):
        """Sem ano_mes nem ano_calendario, levanta ValueError."""
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with pytest.raises(ValueError, match="ano_mes"):
                repo.deletar_dados_anteriores(
                    conn, sped_tipo="efd_contribuicoes",
                    cnpj="00000000000100",
                )
        finally:
            conn.close()


# ----------------------------------------------------------------------
# deletar_diagnostico_anterior
# ----------------------------------------------------------------------

class TestDeletarDiagnosticoAnterior:
    def test_apaga_oportunidades_e_divergencias(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO crossref_oportunidades "
                    "(codigo_regra, descricao, severidade, evidencia_json, "
                    "cnpj_declarante, ano_calendario, gerado_em) "
                    "VALUES (?,?,?,?,?,?,?)",
                    ("CR-01", "x", "alto", "[]", "00000000000100", 2025,
                     "2025-04-29T10:00:00"),
                )
                conn.execute(
                    "INSERT INTO crossref_divergencias "
                    "(codigo_regra, descricao, severidade, evidencia_json, "
                    "cnpj_declarante, ano_calendario, gerado_em) "
                    "VALUES (?,?,?,?,?,?,?)",
                    ("CR-02", "y", "med", "[]", "00000000000100", 2025,
                     "2025-04-29T10:00:00"),
                )
                qtd_op, qtd_div = repo.deletar_diagnostico_anterior(
                    conn, "00000000000100", 2025,
                )
            assert qtd_op == 1
            assert qtd_div == 1
            assert conn.execute(
                "SELECT COUNT(*) FROM crossref_oportunidades"
            ).fetchone()[0] == 0
            assert conn.execute(
                "SELECT COUNT(*) FROM crossref_divergencias"
            ).fetchone()[0] == 0
        finally:
            conn.close()

    def test_preserva_outro_ano(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            with conn:
                for ano in (2024, 2025):
                    conn.execute(
                        "INSERT INTO crossref_oportunidades "
                        "(codigo_regra, descricao, severidade, evidencia_json, "
                        "cnpj_declarante, ano_calendario, gerado_em) "
                        "VALUES (?,?,?,?,?,?,?)",
                        ("CR-01", "x", "alto", "[]", "00000000000100", ano,
                         "2025-04-29T10:00:00"),
                    )
                qtd_op, qtd_div = repo.deletar_diagnostico_anterior(
                    conn, "00000000000100", 2025,
                )
            assert qtd_op == 1
            restante = conn.execute(
                "SELECT ano_calendario FROM crossref_oportunidades"
            ).fetchall()
            assert len(restante) == 1
            assert restante[0]["ano_calendario"] == 2024
        finally:
            conn.close()

    def test_retorna_zero_quando_vazio(self, tmp_path):
        repo = Repositorio("00000000000100", 2025, base_dir=tmp_path)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            qtd_op, qtd_div = repo.deletar_diagnostico_anterior(
                conn, "00000000000100", 2025,
            )
            assert (qtd_op, qtd_div) == (0, 0)
        finally:
            conn.close()
