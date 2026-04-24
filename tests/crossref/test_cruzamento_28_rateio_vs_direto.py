"""
Testes do cruzamento CR-28 — Método de rateio proporcional vs. apropriação direta.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo:
  0110.IND_APRO_CRED=2 (rateio) + 0111 com pct_tributada=80% → CR-28 dispara como Oportunidade analítica.

Fixture negativo:
  0110.IND_APRO_CRED=1 (direto) → CR-28 não dispara.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_28_rateio_vs_direto
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2025


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento28RateioVsDireto:
    def test_rateio_proporcional_gera_oportunidade(
        self, fixture_sprint4_rateio_proporcional, tmp_path
    ):
        """0110.IND_APRO_CRED=2 → CR-28 dispara como Oportunidade analítica de valor zero."""
        repo, conn = _importar(fixture_sprint4_rateio_proporcional, tmp_path)
        try:
            ops, divs = cruzamento_28_rateio_vs_direto.executar(
                repo, conn, _CNPJ, 202508, _ANO
            )
        finally:
            conn.close()

        assert len(ops) == 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-28"
        assert op.severidade == "baixo"
        assert op.valor_impacto_conservador == Decimal("0")
        ev = op.evidencia[0]
        assert ev["campos_chave"]["ind_apro_cred"] == "2"
        assert ev["campos_chave"]["tem_0111"] is True
        assert ev["campos_chave"]["percentual_receita_tributada"] == pytest.approx(80.0)

    def test_apropriacao_direta_sem_oportunidade(self, tmp_path):
        """0110.IND_APRO_CRED=1 → CR-28 não dispara."""
        arq = tmp_path / "direto.txt"
        arq.write_text(
            f"|0000|006|0||0|01092025|30092025|EMPRESA TESTE SA|{_CNPJ}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_28_rateio_vs_direto.executar(
                repo, conn, _CNPJ, 202509, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
