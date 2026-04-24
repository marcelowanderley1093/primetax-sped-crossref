"""
Testes do cruzamento CR-49 — X460 ECF (Lei do Bem — Lei 11.196/2005).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência: ECF apenas.

Fixture positivo:
  X460 total 80K + M300 com adição 10K (sem exclusão Lei do Bem) →
  benefício estimado 60% × 80K = 48K não aproveitado → CR-49 dispara.

Fixture negativo:
  X460 total 80K + M300 com exclusão 50K (>= 48K estimado) →
  exclusão presumidamente aproveitada → CR-49 silencioso.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_49_x460_lei_do_bem
from src.db.repo import Repositorio
from src.parsers import ecf

_CNPJ = "00000000000149"
_ANO = 2025


def _importar_ecf(ecf_path, tmp_path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento49X460LeiDoBem:
    def test_x460_sem_exclusao_dispara(
        self, fixture_ecf_cr49_x460_positivo, tmp_path
    ):
        """X460 80K + M300 adição 10K → exclusão estimada 48K não aproveitada → dispara."""
        repo, conn = _importar_ecf(fixture_ecf_cr49_x460_positivo, tmp_path)
        try:
            ops, divs = cruzamento_49_x460_lei_do_bem.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-49"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["total_x460_declarado"] == 80000.0
        assert ck["total_exclusoes_m300"] == 0.0
        assert ck["beneficio_estimado_60pct"] == 48000.0
        assert ck["qtd_linhas_x460"] == 2

    def test_x460_com_exclusao_suficiente_nao_dispara(
        self, fixture_ecf_cr49_x460_negativo, tmp_path
    ):
        """X460 80K + M300 exclusão 50K (>= 48K estimado) → não dispara."""
        repo, conn = _importar_ecf(fixture_ecf_cr49_x460_negativo, tmp_path)
        try:
            ops, divs = cruzamento_49_x460_lei_do_bem.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []

    def test_sem_ecf_retorna_vazio(self, tmp_path):
        """Sem ECF → disponibilidade != importada → []."""
        db_dir = tmp_path / "db"
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_49_x460_lei_do_bem.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()
        assert ops == []
        assert divs == []
