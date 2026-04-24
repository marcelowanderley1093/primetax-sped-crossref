"""
Testes do parser EFD-Contribuições.

Princípio 3 (CLAUDE.md §4): todo componente tem teste positivo e negativo.
Fixtures em tests/fixtures/ são SPEDs mínimos sintéticos com CNPJ fictício.
CNPJ de teste: 00000000000100 (visivelmente fictício — CLAUDE.md §10).
"""

from pathlib import Path

import pytest

from src.parsers import efd_contribuicoes


def _importar(caminho: Path, tmp_path: Path):
    return efd_contribuicoes.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=tmp_path / "db",
    )


class TestParser:
    def test_importacao_minimo_sucesso(self, fixture_minimo, tmp_path):
        res = _importar(fixture_minimo, tmp_path)
        assert res.sucesso
        assert res.cnpj == "00000000000100"
        assert res.ano_mes == 202502
        assert res.ano_calendario == 2025
        assert res.dt_ini == "2025-02-01"
        assert res.dt_fin == "2025-02-28"
        assert res.encoding_origem == "utf8"

    def test_importacao_tese69_positivo(self, fixture_tese69_positivo, tmp_path):
        res = _importar(fixture_tese69_positivo, tmp_path)
        assert res.cnpj == "00000000000100"
        assert res.contagens_reais.get("C100", 0) == 1
        assert res.contagens_reais.get("C170", 0) == 1

    def test_importacao_tese69_negativo(self, fixture_tese69_negativo, tmp_path):
        res = _importar(fixture_tese69_negativo, tmp_path)
        assert res.contagens_reais.get("C100", 0) == 1
        assert res.contagens_reais.get("C170", 0) == 1

    def test_bloco9_divergencia_detectada(self, fixture_bloco9_divergencia, tmp_path):
        """Fixture declara M600=99 mas arquivo tem apenas 1 → deve gerar divergência."""
        res = _importar(fixture_bloco9_divergencia, tmp_path)
        assert not res.sucesso
        assert any("M600" in d for d in res.divergencias_bloco9)

    def test_contagens_declaradas_vs_reais(self, fixture_minimo, tmp_path):
        res = _importar(fixture_minimo, tmp_path)
        assert res.contagens_declaradas.get("0000") == 1
        assert res.contagens_declaradas.get("0110") == 1
        assert res.contagens_declaradas.get("M200") == 1
        assert res.contagens_declaradas.get("M600") == 1

    def test_encoding_utf8_detectado(self, fixture_minimo, tmp_path):
        res = _importar(fixture_minimo, tmp_path)
        assert res.encoding_origem == "utf8"
        assert res.encoding_confianca == "validado"

    def test_arquivo_invalido_retorna_erro(self, tmp_path):
        """Arquivo sem 0000 deve retornar ResultadoImportacao com sucesso=False."""
        arq = tmp_path / "invalido.txt"
        arq.write_text("|9999|3|\n|C100|1|0||||||||\n", encoding="utf-8")
        res = efd_contribuicoes.importar(
            arq,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=tmp_path / "db",
        )
        assert not res.sucesso
        assert "0000" in res.mensagem

    def test_banco_criado_apos_importacao(self, fixture_minimo, tmp_path):
        db_dir = tmp_path / "db"
        _importar(fixture_minimo, tmp_path)
        banco = db_dir / "00000000000100" / "2025.sqlite"
        assert banco.exists()

    def test_apro_rateio_com_0111(self, fixture_apro_rateio, tmp_path):
        """Arquivo com IND_APRO_CRED=2 e 0111 presente deve importar com sucesso."""
        res = _importar(fixture_apro_rateio, tmp_path)
        assert res.contagens_reais.get("0111", 0) == 1
