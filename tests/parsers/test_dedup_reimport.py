"""Testes regressivos do Bug-002 (Opção 2 — DELETE prévio nos parsers).

Cenários cobertos:
  - Reimport idêntico (mesmo arquivo) não duplica dados
  - Retificadora (mesmo período, conteúdo diferente) substitui
  - _importacoes preserva histórico (cada import gera nova row)
  - Tabelas de anotação (contabil_oportunidades_essencialidade)
    não são tocadas em re-import

Aplicados aos 4 parsers (EFD-Contribuições, ECD, EFD ICMS/IPI, ECF).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.parsers import ecd, ecf, efd_contribuicoes, efd_icms_ipi


# ----------------------------------------------------------------------
# EFD-Contribuições (parser de referência: tem fixtures completas)
# ----------------------------------------------------------------------

class TestDedupReimportEfdContribuicoes:
    def _importar(self, caminho: Path, tmp_path: Path, *, force: bool = False):
        return efd_contribuicoes.importar(
            caminho,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=tmp_path / "db",
            force_reimport=force,
        )

    def test_reimport_identico_com_force_nao_duplica(self, fixture_minimo, tmp_path):
        """Importar 2x o mesmo arquivo (segundo com force_reimport=True):
        contagens nas tabelas SPED filhas idênticas a 1 import."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"
        conn = sqlite3.connect(banco)
        try:
            n_0000_1 = conn.execute("SELECT COUNT(*) FROM efd_contrib_0000").fetchone()[0]
            n_m200_1 = conn.execute("SELECT COUNT(*) FROM efd_contrib_m200").fetchone()[0]
        finally:
            conn.close()

        # Reimport com flag (Opção 3 sem flag aborta — testado em
        # TestForceReimport abaixo)
        self._importar(fixture_minimo, tmp_path, force=True)

        conn = sqlite3.connect(banco)
        try:
            n_0000_2 = conn.execute("SELECT COUNT(*) FROM efd_contrib_0000").fetchone()[0]
            n_m200_2 = conn.execute("SELECT COUNT(*) FROM efd_contrib_m200").fetchone()[0]
            n_imp = conn.execute("SELECT COUNT(*) FROM _importacoes").fetchone()[0]
        finally:
            conn.close()

        assert n_0000_2 == n_0000_1, f"efd_contrib_0000 duplicou: {n_0000_1} → {n_0000_2}"
        assert n_m200_2 == n_m200_1
        # _importacoes preserva histórico — 2 rows após 2 imports autorizados
        assert n_imp == 2

    def test_importacoes_preserva_historico(self, fixture_minimo, tmp_path):
        """Após 2 imports autorizados, _importacoes tem 2 rows com mesmo hash."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        self._importar(fixture_minimo, tmp_path, force=True)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"
        conn = sqlite3.connect(banco)
        try:
            rows = list(conn.execute(
                "SELECT id, arquivo_hash FROM _importacoes ORDER BY id"
            ))
        finally:
            conn.close()
        assert len(rows) == 2
        # Mesmo hash (mesmo arquivo)
        assert rows[0][1] == rows[1][1]

    def test_anotacao_contabil_preservada_em_reimport(
        self, fixture_minimo, tmp_path,
    ):
        """contabil_oportunidades_essencialidade é por (cnpj, ano, cod_cta)
        — não deve ser tocada por DELETE prévio em tabelas SPED filhas."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"
        # Insere anotação (simulando uso futuro da T9)
        conn = sqlite3.connect(banco)
        try:
            conn.execute(
                "INSERT INTO contabil_oportunidades_essencialidade "
                "(cnpj_declarante, ano_calendario, cod_cta, marcado_em, "
                " marcado_por, nota) VALUES (?,?,?,?,?,?)",
                ("00000000000100", 2025, "3.1.01",
                 "2025-04-29T10:00:00+00:00", "auditor", "candidata"),
            )
            conn.commit()
        finally:
            conn.close()
        # Reimport autorizado
        self._importar(fixture_minimo, tmp_path, force=True)
        conn = sqlite3.connect(banco)
        try:
            n = conn.execute(
                "SELECT COUNT(*) FROM contabil_oportunidades_essencialidade"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n == 1, "anotação contábil foi destruída por DELETE prévio"


# ----------------------------------------------------------------------
# TestForceReimport — Bug-002 Opção 3 (camada UX)
# ----------------------------------------------------------------------

class TestForceReimport:
    """Testes da camada Opção 3: hash check em _importacoes.

    Sem flag, reimport idêntico aborta. Com flag, prossegue (e Opção 2
    DELETE prévio garante que não duplique).
    """

    def _importar(self, caminho, tmp_path, *, force=False):
        return efd_contribuicoes.importar(
            caminho, encoding_override="utf8", prompt_operador=False,
            base_dir_db=tmp_path / "db", force_reimport=force,
        )

    def test_reimport_identico_aborta_sem_flag(self, fixture_minimo, tmp_path):
        """Sem --force-reimport, segundo import com mesmo hash retorna
        sucesso=False com mensagem clara. Tabelas filhas não recebem
        novos dados (não houve DELETE prévio nem INSERT)."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"
        conn = sqlite3.connect(banco)
        try:
            n_0000_1 = conn.execute("SELECT COUNT(*) FROM efd_contrib_0000").fetchone()[0]
        finally:
            conn.close()

        # Reimport SEM flag — deve abortar
        res = self._importar(fixture_minimo, tmp_path, force=False)
        assert res.sucesso is False
        assert "ja importado" in res.mensagem.lower() or "ja importado" in res.mensagem
        assert "force-reimport" in res.mensagem

        # Tabelas filhas e _importacoes inalteradas
        conn = sqlite3.connect(banco)
        try:
            n_0000_2 = conn.execute("SELECT COUNT(*) FROM efd_contrib_0000").fetchone()[0]
            n_imp = conn.execute("SELECT COUNT(*) FROM _importacoes").fetchone()[0]
        finally:
            conn.close()
        assert n_0000_2 == n_0000_1
        assert n_imp == 1, "Reimport abortado não deveria registrar nova row"

    def test_reimport_identico_prossegue_com_flag(self, fixture_minimo, tmp_path):
        """Com force_reimport=True, segundo import substitui dados
        (Opção 2 DELETE) e registra nova row em _importacoes."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"

        res = self._importar(fixture_minimo, tmp_path, force=True)
        assert res.sucesso is True

        conn = sqlite3.connect(banco)
        try:
            n_imp = conn.execute("SELECT COUNT(*) FROM _importacoes").fetchone()[0]
        finally:
            conn.close()
        assert n_imp == 2

    def test_arquivo_diferente_passa_sem_flag(self, fixture_minimo, fixture_apro_rateio, tmp_path):
        """Arquivos com hash diferente (cenário retificadora) não disparam
        Opção 3. Mesmo período × cnpj — apenas hash distinto. Comportamento:
        passa sem precisar de --force-reimport (Opção 2 DELETE atua)."""
        import sqlite3
        self._importar(fixture_minimo, tmp_path)
        banco = tmp_path / "db" / "00000000000100" / "2025.sqlite"
        # fixture_apro_rateio: outro arquivo, outro hash, mas cnpj/ano
        # iguais. Cenário "retificadora real".
        # Como pode estar em ano_mes diferente, o teste valida apenas
        # que importação de outro hash não é bloqueada pela Opção 3.
        res = self._importar(fixture_apro_rateio, tmp_path, force=False)
        assert res.sucesso is True
        # _importacoes acumula 2 rows com hashes distintos
        conn = sqlite3.connect(banco)
        try:
            hashes = [r[0] for r in conn.execute(
                "SELECT arquivo_hash FROM _importacoes ORDER BY id"
            )]
        finally:
            conn.close()
        assert len(hashes) == 2
        assert hashes[0] != hashes[1]


# ----------------------------------------------------------------------
# ECD — testa que o DELETE prévio é aplicado ao parser anual
# ----------------------------------------------------------------------

class TestDedupReimportEcd:
    def test_reimport_identico_nao_duplica(self, tmp_path):
        """ECD usa ano_calendario; reimport idêntico não duplica I050/J150."""
        import sqlite3
        from pathlib import Path
        fixture = Path("tests/fixtures/ecd_sprint7_cr39_2025.txt")
        ecd.importar(fixture, encoding_override="utf8",
                     prompt_operador=False, base_dir_db=tmp_path / "db")
        banco = tmp_path / "db" / "00000000000109" / "2025.sqlite"
        conn = sqlite3.connect(banco)
        try:
            n_i050_1 = conn.execute("SELECT COUNT(*) FROM ecd_i050").fetchone()[0]
            n_j150_1 = conn.execute("SELECT COUNT(*) FROM ecd_j150").fetchone()[0]
        finally:
            conn.close()
        ecd.importar(fixture, encoding_override="utf8",
                     prompt_operador=False, base_dir_db=tmp_path / "db",
                     force_reimport=True)
        conn = sqlite3.connect(banco)
        try:
            n_i050_2 = conn.execute("SELECT COUNT(*) FROM ecd_i050").fetchone()[0]
            n_j150_2 = conn.execute("SELECT COUNT(*) FROM ecd_j150").fetchone()[0]
            n_imp = conn.execute(
                "SELECT COUNT(*) FROM _importacoes WHERE sped_tipo='ecd'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n_i050_2 == n_i050_1
        assert n_j150_2 == n_j150_1
        assert n_imp == 2  # _importacoes preserva histórico


# ----------------------------------------------------------------------
# EFD ICMS/IPI — mensal
# ----------------------------------------------------------------------

class TestDedupReimportEfdIcms:
    def test_reimport_identico_nao_duplica(self, tmp_path):
        """EFD ICMS/IPI usa ano_mes; reimport idêntico não duplica G125."""
        import sqlite3
        from pathlib import Path
        fixture = Path("tests/fixtures/efd_icms_sprint6_cr35_202601.txt")
        efd_icms_ipi.importar(fixture, encoding_override="utf8",
                              prompt_operador=False, base_dir_db=tmp_path / "db")
        banco = tmp_path / "db" / "00000000000109" / "2026.sqlite"
        conn = sqlite3.connect(banco)
        try:
            n_g125_1 = conn.execute("SELECT COUNT(*) FROM efd_icms_g125").fetchone()[0]
        finally:
            conn.close()
        efd_icms_ipi.importar(fixture, encoding_override="utf8",
                              prompt_operador=False, base_dir_db=tmp_path / "db",
                              force_reimport=True)
        conn = sqlite3.connect(banco)
        try:
            n_g125_2 = conn.execute("SELECT COUNT(*) FROM efd_icms_g125").fetchone()[0]
            n_imp = conn.execute(
                "SELECT COUNT(*) FROM _importacoes WHERE sped_tipo='efd_icms'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n_g125_2 == n_g125_1
        assert n_imp == 2


# ----------------------------------------------------------------------
# ECF — anual
# ----------------------------------------------------------------------

class TestDedupReimportEcf:
    def test_reimport_identico_nao_duplica(self, tmp_path):
        """ECF usa ano_calendario; reimport idêntico não duplica K155."""
        import sqlite3
        from pathlib import Path
        fixture = Path("tests/fixtures/ecf_sprint8_cr43_2025.txt")
        ecf.importar(fixture, encoding_override="utf8",
                     prompt_operador=False, base_dir_db=tmp_path / "db")
        banco = tmp_path / "db" / "00000000000143" / "2025.sqlite"
        conn = sqlite3.connect(banco)
        try:
            n_k155_1 = conn.execute("SELECT COUNT(*) FROM ecf_k155").fetchone()[0]
        finally:
            conn.close()
        ecf.importar(fixture, encoding_override="utf8",
                     prompt_operador=False, base_dir_db=tmp_path / "db",
                     force_reimport=True)
        conn = sqlite3.connect(banco)
        try:
            n_k155_2 = conn.execute("SELECT COUNT(*) FROM ecf_k155").fetchone()[0]
            n_imp = conn.execute(
                "SELECT COUNT(*) FROM _importacoes WHERE sped_tipo='ecf'"
            ).fetchone()[0]
        finally:
            conn.close()
        assert n_k155_2 == n_k155_1
        assert n_imp == 2
