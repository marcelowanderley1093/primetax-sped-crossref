"""Testes regressivos do Bug-005 (Opção 2 — DELETE prévio no engine).

Cenários cobertos:
  - Re-execução de Motor.diagnosticar_ano não duplica rows em
    crossref_oportunidades / crossref_divergencias
  - LIMITAÇÃO DOCUMENTADA: anotações (revisado_em, nota) em rows
    previamente diagnosticadas SÃO PERDIDAS no re-diagnóstico
  - Apaga apenas o ano-calendário corrente; outros anos preservados
"""

from __future__ import annotations

import sqlite3

import pytest

from src.crossref.engine import Motor
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes


def _importar_e_motor(caminho, tmp_path):
    """Importa fixture e devolve (repo, motor) para o ano 2025."""
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=db_dir,
    )
    repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
    motor = Motor(repo)
    return repo, motor


class TestDedupDiagnostico:
    def test_re_execucao_nao_duplica_oportunidades(
        self, fixture_tese69_positivo, tmp_path,
    ):
        """diagnosticar_ano(2025) 2x: contagem final == contagem 1x."""
        repo, motor = _importar_e_motor(fixture_tese69_positivo, tmp_path)
        # 1ª execução
        motor.diagnosticar_ano(2025)
        conn = repo.conexao()
        try:
            n_op_1 = conn.execute(
                "SELECT COUNT(*) FROM crossref_oportunidades"
            ).fetchone()[0]
        finally:
            conn.close()

        # 2ª execução — sem fix, duplicaria; com fix, mantém
        motor.diagnosticar_ano(2025)
        conn = repo.conexao()
        try:
            n_op_2 = conn.execute(
                "SELECT COUNT(*) FROM crossref_oportunidades"
            ).fetchone()[0]
        finally:
            conn.close()

        assert n_op_2 == n_op_1, (
            f"crossref_oportunidades duplicou: {n_op_1} → {n_op_2}"
        )

    def test_re_execucao_nao_duplica_divergencias(
        self, fixture_tese69_positivo, tmp_path,
    ):
        repo, motor = _importar_e_motor(fixture_tese69_positivo, tmp_path)
        motor.diagnosticar_ano(2025)
        conn = repo.conexao()
        try:
            n_div_1 = conn.execute(
                "SELECT COUNT(*) FROM crossref_divergencias"
            ).fetchone()[0]
        finally:
            conn.close()

        motor.diagnosticar_ano(2025)
        conn = repo.conexao()
        try:
            n_div_2 = conn.execute(
                "SELECT COUNT(*) FROM crossref_divergencias"
            ).fetchone()[0]
        finally:
            conn.close()

        assert n_div_2 == n_div_1

    def test_re_execucao_apaga_anotacoes_LIMITACAO(
        self, fixture_tese69_positivo, tmp_path,
    ):
        """LIMITAÇÃO DOCUMENTADA: re-diagnóstico apaga anotação prévia.

        Comportamento documentado em docs/debitos-conhecidos.md (Bug-005):
        decisão consciente baseada em verificação empírica de zero
        anotações em uso real. Quando a feature de anotação começar a
        ser usada em produção, este débito reabre como Bug-005-bis.

        Este teste documenta o trade-off explicitamente — sua existência
        é o gatilho de revisão se a UX da T4 Oportunidades for ampliada.
        """
        repo, motor = _importar_e_motor(fixture_tese69_positivo, tmp_path)
        motor.diagnosticar_ano(2025)

        # Anota a primeira oportunidade
        conn = repo.conexao()
        try:
            row = conn.execute(
                "SELECT id FROM crossref_oportunidades LIMIT 1"
            ).fetchone()
            if row is None:
                pytest.skip("Fixture não gerou oportunidade")
            achado_id = row[0]
            with conn:
                conn.execute(
                    "UPDATE crossref_oportunidades "
                    "SET revisado_em=?, revisado_por=?, nota=? WHERE id=?",
                    ("2026-05-01T10:00:00+00:00", "auditor",
                     "candidata Tema 779", achado_id),
                )
        finally:
            conn.close()

        # Re-execução apaga
        motor.diagnosticar_ano(2025)

        conn = repo.conexao()
        try:
            n_anotadas = conn.execute(
                "SELECT COUNT(*) FROM crossref_oportunidades "
                "WHERE revisado_em IS NOT NULL OR (nota IS NOT NULL AND nota != '')"
            ).fetchone()[0]
        finally:
            conn.close()

        # Documentação explícita do comportamento atual
        assert n_anotadas == 0, (
            "LIMITAÇÃO Bug-005 confirmada: re-diagnóstico apagou anotação "
            "prévia. Se este assert quebrar (n_anotadas > 0), é porque o "
            "fix foi reformulado para preservar anotações — atualizar "
            "docs/debitos-conhecidos.md entrada Bug-005."
        )

    def test_preserva_outro_ano(
        self, fixture_tese69_positivo, tmp_path,
    ):
        """diagnosticar_ano(2025) não toca dados de 2024 em crossref_*."""
        repo, motor = _importar_e_motor(fixture_tese69_positivo, tmp_path)
        # Insere artificialmente uma oportunidade em 2024
        conn = repo.conexao()
        try:
            with conn:
                conn.execute(
                    "INSERT INTO crossref_oportunidades "
                    "(codigo_regra, descricao, severidade, evidencia_json, "
                    "cnpj_declarante, ano_calendario, gerado_em) "
                    "VALUES (?,?,?,?,?,?,?)",
                    ("CR-99", "fake 2024", "alto", "[]",
                     "00000000000100", 2024, "2024-12-31T10:00:00"),
                )
        finally:
            conn.close()

        # Diagnóstico para 2025 — não deve apagar 2024
        motor.diagnosticar_ano(2025)

        conn = repo.conexao()
        try:
            n_2024 = conn.execute(
                "SELECT COUNT(*) FROM crossref_oportunidades "
                "WHERE ano_calendario = 2024"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n_2024 == 1, "diagnóstico de 2025 apagou rows de 2024"
