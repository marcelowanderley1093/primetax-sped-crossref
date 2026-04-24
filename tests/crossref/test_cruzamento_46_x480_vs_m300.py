"""
Testes do cruzamento CR-46 — X480 × M300 (ECF): benefício fiscal não aproveitado.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência: ECF apenas.

Fixture positivo:
  X480 CODIGO='101' VALOR=5.000 sem M300 com TIPO_LANCAMENTO='E'
  → benefício declarado sem exclusão correspondente → CR-46 dispara.

Fixture negativo:
  X480 CODIGO='101' VALOR=5.000 + M300 TIPO='E' CODIGO='101' VALOR=5.000
  → exclusão presente → CR-46 não dispara.
"""

from src.crossref.camada_2_oportunidades import cruzamento_46_x480_vs_m300
from src.db.repo import Repositorio
from src.parsers import ecf

_CNPJ = "00000000000146"
_ANO = 2025


def _importar_ecf(ecf_path, tmp_path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento46X480VsM300:
    def test_beneficio_sem_exclusao_dispara(
        self, fixture_sprint8_ecf_cr46_positivo, tmp_path
    ):
        """X480 VALOR=5K sem M300 exclusão → CR-46 dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr46_positivo, tmp_path)
        try:
            ops, divs = cruzamento_46_x480_vs_m300.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) >= 1
        op = ops[0]
        assert op.codigo_regra == "CR-46"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["total_exclusoes_m300"] == 0.0
        assert float(op.valor_impacto_conservador) == 5000.0

    def test_beneficio_com_exclusao_nao_dispara(
        self, fixture_sprint8_ecf_cr46_negativo, tmp_path
    ):
        """X480 VALOR=5K + M300 TIPO='E' CODIGO='101' → CR-46 não dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr46_negativo, tmp_path)
        try:
            ops, divs = cruzamento_46_x480_vs_m300.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecf_retorna_vazio(self, tmp_path):
        """Sem ECF importada → disponibilidade_ecf != importada → CR-46 retorna []."""
        db_dir = tmp_path / "db"
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_46_x480_vs_m300.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
