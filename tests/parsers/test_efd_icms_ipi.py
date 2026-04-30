"""Testes do parser EFD ICMS/IPI — foco em Bloco 9 (Bug-001)."""

from __future__ import annotations

from pathlib import Path

from src.parsers import efd_icms_ipi


def _importar(caminho: Path, tmp_path: Path):
    return efd_icms_ipi.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=tmp_path / "db",
    )


class TestParserEfdIcmsIpi:
    def test_bloco9_divergencia_detectada(
        self, fixture_efd_icms_bloco9_divergencia, tmp_path,
    ):
        """Fixture declara 9900.0000=99 mas real=1 → divergência detectada."""
        res = _importar(fixture_efd_icms_bloco9_divergencia, tmp_path)
        assert not res.sucesso
        assert any("0000" in d for d in res.divergencias_bloco9)

    def test_contagens_reais_cumulativo(
        self, fixture_efd_icms_bloco9_divergencia, tmp_path,
    ):
        """contagens_reais cumulativo por reg_tipo (Bug-001 mudança observável)."""
        res = _importar(fixture_efd_icms_bloco9_divergencia, tmp_path)
        assert res.contagens_reais.get("0000") == 1
        assert res.contagens_reais.get("9999") == 1

    def test_contagens_declaradas_populadas(
        self, fixture_efd_icms_bloco9_divergencia, tmp_path,
    ):
        """contagens_declaradas derivado dos 9900."""
        res = _importar(fixture_efd_icms_bloco9_divergencia, tmp_path)
        assert res.contagens_declaradas.get("0000") == 99
