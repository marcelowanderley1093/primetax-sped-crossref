"""
Testes dos cruzamentos da Camada 1 — integridade estrutural.

Princípio 3 (CLAUDE.md §4): par positivo (deve disparar) + negativo (não deve).
"""

import pytest

from src.crossref.camada_1_integridade import (
    cruzamento_02_unicidade_m,
    cruzamento_03_presenca_0110,
    cruzamento_04_0110_0111,
    cruzamento_05_hierarquia,
)
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes


def _importar_e_abrir(caminho, tmp_path):
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho,
        encoding_override="utf8",
        prompt_operador=False,
        base_dir_db=db_dir,
    )
    repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
    conn = repo.conexao()
    return repo, conn


class TestCruzamento02UnicoM:
    def test_positivo_m200_m600_presentes(self, fixture_minimo, tmp_path):
        """Arquivo mínimo com exatamente 1 M200 e 1 M600 — sem divergência."""
        repo, conn = _importar_e_abrir(fixture_minimo, tmp_path)
        try:
            divs = cruzamento_02_unicidade_m.executar(repo, conn, "00000000000100", 202502, 2025)
        finally:
            conn.close()
        assert divs == []

    def test_negativo_m200_ausente(self, tmp_path):
        """Arquivo sem M200 deve gerar divergência CI-02."""
        arq = tmp_path / "sem_m200.txt"
        arq.write_text(
            "|0000|006|0||0|01012025|31012025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|M600|0,00|0,00|0,00|0,00|0,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|M600|1|\n"
            "|9900|9900|4|\n|9900|9999|1|\n|9999|9|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            divs = cruzamento_02_unicidade_m.executar(repo, conn, "00000000000100", 202501, 2025)
        finally:
            conn.close()
        assert any("M200" in d.descricao for d in divs)
        assert any(d.codigo_regra == "CI-02" for d in divs)


class TestCruzamento03Presenca0110:
    def test_positivo_0110_valido(self, fixture_minimo, tmp_path):
        """0110 presente e válido — sem divergência."""
        repo, conn = _importar_e_abrir(fixture_minimo, tmp_path)
        try:
            divs = cruzamento_03_presenca_0110.executar(
                repo, conn, "00000000000100", 202502, 2025
            )
        finally:
            conn.close()
        assert divs == []

    def test_negativo_0110_ausente(self, tmp_path):
        """Arquivo sem 0110 deve disparar CI-03."""
        arq = tmp_path / "sem_0110.txt"
        arq.write_text(
            "|0000|006|0||0|01012025|31012025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|M200|0,00|0,00|0,00|0,00|0,00|\n"
            "|M600|0,00|0,00|0,00|0,00|0,00|\n"
            "|9900|0000|1|\n|9900|M200|1|\n|9900|M600|1|\n"
            "|9900|9900|4|\n|9900|9999|1|\n|9999|9|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            divs = cruzamento_03_presenca_0110.executar(
                repo, conn, "00000000000100", 202501, 2025
            )
        finally:
            conn.close()
        assert any(d.codigo_regra == "CI-03" for d in divs)


class TestCruzamento04Consistencia0110_0111:
    def test_positivo_rateio_com_0111(self, fixture_apro_rateio, tmp_path):
        """IND_APRO_CRED=2 com 0111 presente — sem divergência."""
        repo, conn = _importar_e_abrir(fixture_apro_rateio, tmp_path)
        try:
            divs = cruzamento_04_0110_0111.executar(
                repo, conn, "00000000000100", 202504, 2025
            )
        finally:
            conn.close()
        assert divs == []

    def test_negativo_rateio_sem_0111(self, tmp_path):
        """IND_APRO_CRED=2 sem 0111 deve disparar CI-04."""
        arq = tmp_path / "rateio_sem_0111.txt"
        arq.write_text(
            "|0000|006|0||0|01052025|31052025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|3|2|0|0|\n"
            "|M200|0,00|0,00|0,00|0,00|0,00|\n"
            "|M600|0,00|0,00|0,00|0,00|0,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|M200|1|\n|9900|M600|1|\n"
            "|9900|9900|5|\n|9900|9999|1|\n|9999|11|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            divs = cruzamento_04_0110_0111.executar(
                repo, conn, "00000000000100", 202505, 2025
            )
        finally:
            conn.close()
        assert any(d.codigo_regra == "CI-04" for d in divs)


class TestCruzamento05Hierarquia:
    def test_positivo_c170_com_c100(self, fixture_tese69_positivo, tmp_path):
        """C170 com C100 pai presente — sem divergência."""
        repo, conn = _importar_e_abrir(fixture_tese69_positivo, tmp_path)
        try:
            divs = cruzamento_05_hierarquia.executar(
                repo, conn, "00000000000100", 202501, 2025
            )
        finally:
            conn.close()
        assert divs == []

    def test_negativo_c170_orfao_detectado_no_parse(self, tmp_path):
        """Parser deve rejeitar C170 órfão — não persiste no banco."""
        arq = tmp_path / "c170_orfao.txt"
        arq.write_text(
            "|0000|006|0||0|01062025|30062025|EMPRESA TESTE SA|00000000000100||SP||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|C170|01|PROD001||1|UN|1000,00|0,00||00|5102|||0,00|0,00||0,00|0,00||00|||0,00|0,00|01|1000,00|1,65|0,00|0,00|16,50|01|1000,00|7,60|0,00|0,00|76,00||\n"
            "|M200|0,00|0,00|0,00|0,00|0,00|\n"
            "|M600|0,00|0,00|0,00|0,00|0,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|C170|1|\n"
            "|9900|M200|1|\n|9900|M600|1|\n"
            "|9900|9900|6|\n|9900|9999|1|\n|9999|13|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        res = efd_contribuicoes.importar(
            arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
        )
        # Parser deve ter logado e não persistido o C170 órfão
        assert not res.sucesso or res.contagens_reais.get("C170", 0) == 1
        # C170 não deve estar no banco (foi rejeitado como órfão)
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        conn = repo.conexao()
        try:
            c170s = repo.consultar_c170_por_periodo(conn, "00000000000100", 202506)
        finally:
            conn.close()
        assert len(c170s) == 0
