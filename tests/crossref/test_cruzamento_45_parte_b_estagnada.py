"""
Testes do cruzamento CR-45 — M500 Parte B estagnada (ECF).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência: ECF apenas.

Fixture positivo:
  M500 COD_CTA_B='PRVCONT' SD_FIM=50.000 IND='D' VL_LCTO_A=0 VL_LCTO_B=0
  → exclusão futura estagnada → CR-45 dispara.

Fixture negativo:
  M500 COD_CTA_B='PRVCONT' SD_FIM=50.000 IND='D' VL_LCTO_A=10.000 (com movimento)
  → conta em movimento → CR-45 não dispara.
"""

from src.crossref.camada_2_oportunidades import cruzamento_45_parte_b_estagnada
from src.db.repo import Repositorio
from src.parsers import ecf

_CNPJ = "00000000000145"
_ANO = 2025


def _importar_ecf(ecf_path, tmp_path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento45ParteBEstagnada:
    def test_m500_estagnada_dispara(
        self, fixture_sprint8_ecf_cr45_positivo, tmp_path
    ):
        """M500 SD_FIM=50K IND='D' sem movimento → CR-45 dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr45_positivo, tmp_path)
        try:
            ops, divs = cruzamento_45_parte_b_estagnada.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-45"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cod_cta_b"] == "PRVCONT"
        assert ck["sd_fim_lal"] == 50000.0
        assert ck["ind_sd_fim_lal"] == "D"
        assert ck["vl_lcto_parte_a"] == 0.0
        assert float(op.valor_impacto_conservador) == 50000.0

    def test_m500_com_movimento_nao_dispara(
        self, fixture_sprint8_ecf_cr45_negativo, tmp_path
    ):
        """M500 SD_FIM=40K com VL_LCTO_A=10K (em movimento) → CR-45 não dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr45_negativo, tmp_path)
        try:
            ops, divs = cruzamento_45_parte_b_estagnada.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecf_retorna_vazio(self, tmp_path):
        """Sem ECF importada → disponibilidade_ecf != importada → CR-45 retorna []."""
        db_dir = tmp_path / "db"
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_45_parte_b_estagnada.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
