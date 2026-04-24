"""
Testes do anonimizador de SPEDs.

Cobertura:
  - CNPJ sintético gerado é válido (dígitos verificadores corretos).
  - CPF sintético gerado é válido.
  - Determinismo: mesma entrada + mesma seed → mesma saída.
  - Detecta os 4 tipos de SPED corretamente.
  - Preserva estrutura, valores e datas.
  - Modo --preservar-cnpj mantém o CNPJ do declarante intacto.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import anonimizar_sped


class TestCnpjSintetico:
    def test_cnpj_gerado_tem_14_digitos(self):
        cnpj = anonimizar_sped._cnpj_sintetico("12345678000100", seed=42)
        assert cnpj.isdigit()
        assert len(cnpj) == 14

    def test_cnpj_gerado_tem_dv_valido(self):
        """Valida que os dois últimos dígitos batem com o cálculo oficial."""
        cnpj = anonimizar_sped._cnpj_sintetico("12345678000100", seed=42)
        base = cnpj[:12]
        dv = anonimizar_sped._digitos_cnpj(base)
        assert cnpj[12:] == dv

    def test_determinismo(self):
        a = anonimizar_sped._cnpj_sintetico("12345678000100", seed=42)
        b = anonimizar_sped._cnpj_sintetico("12345678000100", seed=42)
        assert a == b

    def test_seed_diferente_gera_cnpj_diferente(self):
        a = anonimizar_sped._cnpj_sintetico("12345678000100", seed=1)
        b = anonimizar_sped._cnpj_sintetico("12345678000100", seed=2)
        assert a != b


class TestCpfSintetico:
    def test_cpf_gerado_tem_11_digitos(self):
        cpf = anonimizar_sped._cpf_sintetico("12345678901", seed=42)
        assert cpf.isdigit()
        assert len(cpf) == 11

    def test_cpf_gerado_tem_dv_valido(self):
        cpf = anonimizar_sped._cpf_sintetico("12345678901", seed=42)
        base = cpf[:9]
        dv = anonimizar_sped._digitos_cpf(base)
        assert cpf[9:] == dv


class TestDetectarTipo:
    def test_detecta_ecf(self):
        campos = "|0000|LECF|0012|12345678000100|EMPRESA SA|".split("|")
        assert anonimizar_sped._detectar_tipo(campos) == "ecf"

    def test_detecta_ecd(self):
        campos = "|0000|LECD|01012025|31122025|EMPRESA|12345678000100|".split("|")
        assert anonimizar_sped._detectar_tipo(campos) == "ecd"

    def test_detecta_efd_icms(self):
        # CNPJ (14 dígitos) em campos[7]
        campos = "|0000|003|0|01012026|31012026|EMPRESA|12345678000100||".split("|")
        assert anonimizar_sped._detectar_tipo(campos) == "efd_icms"

    def test_detecta_efd_contrib(self):
        # CNPJ (14 dígitos) em campos[9]
        campos = "|0000|006|0||0|01022025|28022025|EMPRESA|12345678000100|".split("|")
        assert anonimizar_sped._detectar_tipo(campos) == "efd_contrib"


class TestAnonimizacaoIntegracao:
    def test_anonimiza_fixture_ecd_preservando_estrutura(self, tmp_path):
        entrada = Path("tests/fixtures/ecd_sprint8_cr43_positivo_2025.txt")
        saida = tmp_path / "anon.txt"

        sumario = anonimizar_sped.anonimizar(entrada, saida, seed=42, encoding="utf-8")

        assert saida.exists()
        assert sumario["tipo_sped"] == "ecd"
        assert sumario["cnpjs_substituidos"] >= 1

        texto_original = entrada.read_text(encoding="utf-8")
        texto_anon = saida.read_text(encoding="utf-8")

        # CNPJ original (00000000000143) não deve mais aparecer
        assert "00000000000143" not in texto_anon
        # Estrutura preservada: mesmo número de registros
        assert texto_original.count("|0000|") == texto_anon.count("|0000|")
        assert texto_original.count("|I155|") == texto_anon.count("|I155|")
        # Datas preservadas
        assert "01012025" in texto_anon
        assert "31122025" in texto_anon
        # Valores preservados (saldo I155)
        assert "100000,00" in texto_anon

    def test_determinismo_end_to_end(self, tmp_path):
        entrada = Path("tests/fixtures/ecd_sprint8_cr43_positivo_2025.txt")
        saida_a = tmp_path / "a.txt"
        saida_b = tmp_path / "b.txt"

        anonimizar_sped.anonimizar(entrada, saida_a, seed=42, encoding="utf-8")
        anonimizar_sped.anonimizar(entrada, saida_b, seed=42, encoding="utf-8")

        assert saida_a.read_text(encoding="utf-8") == saida_b.read_text(encoding="utf-8")

    def test_preservar_cnpj_declarante(self, tmp_path):
        entrada = Path("tests/fixtures/ecd_sprint8_cr43_positivo_2025.txt")
        saida = tmp_path / "preserva.txt"

        anonimizar_sped.anonimizar(
            entrada, saida, seed=42, encoding="utf-8",
            preservar_cnpj_declarante=True,
        )
        texto = saida.read_text(encoding="utf-8")
        # CNPJ do declarante mantido na linha do 0000
        linha_0000 = next(
            l for l in texto.splitlines() if l.startswith("|0000|")
        )
        assert "00000000000143" in linha_0000

    def test_arquivo_anonimizado_e_importavel(self, tmp_path):
        """Fixture anonimizada deve ser processável pelo parser original."""
        from src.db.repo import Repositorio
        from src.parsers import ecd as parser_ecd

        entrada = Path("tests/fixtures/ecd_sprint8_cr43_positivo_2025.txt")
        saida = tmp_path / "anonimizado.txt"
        sumario = anonimizar_sped.anonimizar(
            entrada, saida, seed=42, encoding="utf-8"
        )

        # Recupera o CNPJ sintético gerado
        texto = saida.read_text(encoding="utf-8")
        linha_0000 = next(
            l for l in texto.splitlines() if l.startswith("|0000|")
        )
        cnpj_anon = linha_0000.split("|")[6]  # posição do CNPJ em ECD 0000

        # Tenta importar — exercitando o parser completo
        db_dir = tmp_path / "db"
        parser_ecd.importar(
            saida, encoding_override="utf8",
            prompt_operador=False, base_dir_db=db_dir,
        )
        repo = Repositorio(cnpj_anon, 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ctx = repo.consultar_sped_contexto(conn)
        finally:
            conn.close()
        assert ctx is not None
        assert ctx.get("disponibilidade_ecd") == "importada"
