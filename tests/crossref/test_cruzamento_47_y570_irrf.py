"""
Testes do cruzamento CR-47 — Y570 (ECF): IRRF/CSRF retidos não compensados.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência: ECF apenas.

Fixture positivo:
  Y570 VL_IR_RET=10.000 VL_CSLL_RET=5.000 → total=15.000 > 1.000
  → CR-47 dispara.

Fixture negativo:
  Y570 VL_IR_RET=100 VL_CSLL_RET=0 → total=100 < 1.000
  → CR-47 não dispara.
"""

from src.crossref.camada_2_oportunidades import cruzamento_47_y570_irrf
from src.db.repo import Repositorio
from src.parsers import ecf

_CNPJ = "00000000000147"
_ANO = 2025


def _importar_ecf(ecf_path, tmp_path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento47Y570Irrf:
    def test_total_retencao_dispara(
        self, fixture_sprint8_ecf_cr47_positivo, tmp_path
    ):
        """Y570 IR=10K + CSLL=5K → total=15K > threshold → CR-47 dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr47_positivo, tmp_path)
        try:
            ops, divs = cruzamento_47_y570_irrf.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) >= 1
        op = ops[0]
        assert op.codigo_regra == "CR-47"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["total_retencoes"] == 15000.0
        assert float(op.valor_impacto_conservador) == 15000.0

    def test_total_abaixo_threshold_nao_dispara(
        self, fixture_sprint8_ecf_cr47_negativo, tmp_path
    ):
        """Y570 IR=100 CSLL=0 → total=100 < threshold → CR-47 não dispara."""
        repo, conn = _importar_ecf(fixture_sprint8_ecf_cr47_negativo, tmp_path)
        try:
            ops, divs = cruzamento_47_y570_irrf.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecf_retorna_vazio(self, tmp_path):
        """Sem ECF importada → disponibilidade_ecf != importada → CR-47 retorna []."""
        db_dir = tmp_path / "db"
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_47_y570_irrf.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
