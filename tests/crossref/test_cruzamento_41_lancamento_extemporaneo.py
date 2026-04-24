"""
Testes do cruzamento CR-41 — I200 extemporâneos (ECD) × 1100/1500 (EFD-Contribuições).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia da ECD.

Fixture positivo:
  EFD-Contrib sem 1100 de ano anterior + ECD I200 IND_LCTO='X'
  → lançamento extemporâneo sem crédito correspondente → CR-41 dispara.

Fixture negativo:
  EFD-Contrib com 1100 PER_APU_CRED='122024' (ano anterior) + mesma ECD I200 extemporânea
  → crédito extemporâneo já declarado → CR-41 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_41_lancamento_extemporaneo
from src.db.repo import Repositorio
from src.parsers import ecd, efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2025


def _importar_cross(contrib: Path, ecd_path: Path, tmp_path: Path):
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        contrib, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    ecd.importar(
        ecd_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento41LancamentoExtemporaneo:
    def test_i200_ext_sem_1100_ant_dispara(
        self,
        fixture_sprint7_contrib_minimal,
        fixture_sprint7_ecd_cr41,
        tmp_path,
    ):
        """I200 IND_LCTO='X' sem 1100 de ano anterior → CR-41 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_minimal,
            fixture_sprint7_ecd_cr41,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_41_lancamento_extemporaneo.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-41"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["qtd_lancamentos_extemporaneos"] >= 1
        assert ck["tem_credito_extemporaneo_efd"] is False

    def test_i200_ext_com_1100_ant_nao_dispara(
        self,
        fixture_sprint7_contrib_com_1100_ant,
        fixture_sprint7_ecd_cr41,
        tmp_path,
    ):
        """I200 IND_LCTO='X' + 1100 PER_APU_CRED='122024' → crédito já declarado → CR-41 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_com_1100_ant,
            fixture_sprint7_ecd_cr41,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_41_lancamento_extemporaneo.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint7_contrib_minimal, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-41 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint7_contrib_minimal,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_41_lancamento_extemporaneo.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
