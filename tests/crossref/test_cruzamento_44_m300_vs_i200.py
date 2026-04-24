"""
Testes do cruzamento CR-44 — M300/M312 (ECF e-Lalur) × I200 (ECD): rastreabilidade.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia de ECF e ECD.

Fixture positivo:
  ECF M300 IND_RELACAO='2' + M312 NUM_LCTO='LC001'
  ECD I200 sem LC001 (tem LC999 apenas)
  → LC001 ausente na ECD → CR-44 dispara.

Fixture negativo:
  ECF M300 IND_RELACAO='2' + M312 NUM_LCTO='LC001'
  ECD I200 com LC001
  → LC001 encontrado na ECD → CR-44 não dispara.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_44_m300_vs_i200
from src.db.repo import Repositorio
from src.parsers import ecd, ecf

_CNPJ = "00000000000144"
_ANO = 2025


def _importar_ecf_ecd(ecf_path: Path, ecd_path: Path, tmp_path: Path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    ecd.importar(ecd_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento44M300VsI200:
    def test_num_lcto_ausente_ecd_dispara(
        self,
        fixture_sprint8_ecf_cr44,
        fixture_sprint8_ecd_cr44_positivo,
        tmp_path,
    ):
        """M312 NUM_LCTO='LC001' mas ECD I200 só tem 'LC999' → CR-44 dispara."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr44, fixture_sprint8_ecd_cr44_positivo, tmp_path
        )
        try:
            ops, divs = cruzamento_44_m300_vs_i200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) >= 1
        op = ops[0]
        assert op.codigo_regra == "CR-44"
        ck = op.evidencia[0]["campos_chave"]
        assert "LC001" in ck["num_lctos_ausentes"]

    def test_num_lcto_presente_ecd_nao_dispara(
        self,
        fixture_sprint8_ecf_cr44,
        fixture_sprint8_ecd_cr44_negativo,
        tmp_path,
    ):
        """M312 NUM_LCTO='LC001' e ECD I200 tem 'LC001' → CR-44 não dispara."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr44, fixture_sprint8_ecd_cr44_negativo, tmp_path
        )
        try:
            ops, divs = cruzamento_44_m300_vs_i200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint8_ecf_cr44, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-44 retorna []."""
        db_dir = tmp_path / "db"
        ecf.importar(
            fixture_sprint8_ecf_cr44,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_44_m300_vs_i200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
