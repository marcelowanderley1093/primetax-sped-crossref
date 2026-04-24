"""
Testes do cruzamento CR-48 — 9100 ECF (avisos do PGE).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência: ECF apenas.

Fixture positivo:
  ECF com 2 registros 9100 (REGRA_LINHA_DESPREZADA + REGRA_COMPATIBILIDADE_K155_E155)
  → CR-48 emite 2 Divergencias informativas.

Fixture negativo:
  ECF sem registros 9100 → CR-48 silencioso.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_48_avisos_ecf_9100
from src.db.repo import Repositorio
from src.parsers import ecf

_CNPJ = "00000000000148"
_ANO = 2025


def _importar_ecf(ecf_path, tmp_path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento48AvisosEcf9100:
    def test_avisos_presentes_dispara_uma_div_por_aviso(
        self, fixture_ecf_cr48_avisos_positivo, tmp_path
    ):
        """2 avisos 9100 → 2 Divergencias informativas."""
        repo, conn = _importar_ecf(fixture_ecf_cr48_avisos_positivo, tmp_path)
        try:
            ops, divs = cruzamento_48_avisos_ecf_9100.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 2
        codigos = {d.evidencia[0]["campos_chave"]["cod_aviso"] for d in divs}
        assert "REGRA_LINHA_DESPREZADA" in codigos
        assert "REGRA_COMPATIBILIDADE_K155_E155" in codigos
        assert all(d.codigo_regra == "CR-48" for d in divs)
        assert all(d.severidade == "medio" for d in divs)

    def test_sem_avisos_nao_dispara(
        self, fixture_ecf_cr48_avisos_negativo, tmp_path
    ):
        """ECF sem 9100 → CR-48 silencioso."""
        repo, conn = _importar_ecf(fixture_ecf_cr48_avisos_negativo, tmp_path)
        try:
            ops, divs = cruzamento_48_avisos_ecf_9100.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []

    def test_sem_ecf_retorna_vazio(self, tmp_path):
        """Sem ECF importada → disponibilidade_ecf != importada → CR-48 retorna []."""
        db_dir = tmp_path / "db"
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_48_avisos_ecf_9100.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []
