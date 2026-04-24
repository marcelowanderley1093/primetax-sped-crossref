"""
Testes do cruzamento CR-31 — Consistência base PIS (C170) vs M210.VL_BC_CONT.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture consistente (negativo):
  C170 CST=01, VL_BC_PIS=10.000 → M210 VL_BC_CONT=10.000 → diferença=0 → sem CR-31.

Fixture divergente (positivo):
  C170 CST=01, VL_BC_PIS=10.000 → M210 VL_BC_CONT=12.000 → diferença=2.000 > 1 → CR-31 dispara.
"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.crossref.camada_3_consistencia import cruzamento_31_bc_pis_vs_m210
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2024


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento31BcPisVsM210:
    def test_bases_aderentes_sem_divergencia(
        self, fixture_sprint3_m210_consistente, tmp_path
    ):
        """Σ VL_BC_PIS (C170) = Σ VL_BC_CONT (M210) → CR-31 não dispara."""
        repo, conn = _importar(fixture_sprint3_m210_consistente, tmp_path)
        try:
            ops, divs = cruzamento_31_bc_pis_vs_m210.executar(
                repo, conn, _CNPJ, 202409, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_bases_divergentes_gera_divergencia(
        self, fixture_sprint3_m210_divergente, tmp_path
    ):
        """C170 soma 10.000, M210 declara 12.000 → divergência de R$ 2.000 → CR-31 dispara."""
        repo, conn = _importar(fixture_sprint3_m210_divergente, tmp_path)
        try:
            ops, divs = cruzamento_31_bc_pis_vs_m210.executar(
                repo, conn, _CNPJ, 202410, _ANO
            )
        finally:
            conn.close()

        assert len(divs) == 1
        assert ops == []
        div = divs[0]
        assert div.codigo_regra == "CR-31"
        assert div.severidade == "medio"
        ev = div.evidencia[0]
        ck = ev["campos_chave"]
        assert ck["soma_vl_bc_pis_c170"] == pytest.approx(10000.0)
        assert ck["soma_vl_bc_cont_m210"] == pytest.approx(12000.0)
        assert ck["divergencia_absoluta"] == pytest.approx(2000.0)
        assert ck["sentido"] == "superdeclarada"

    def test_periodo_sem_m210_retorna_vazio(self, tmp_path):
        """Período sem registros M210 → CR-31 retorna listas vazias (impossível validar)."""
        arq = tmp_path / "sem_m210.txt"
        cnpj = _CNPJ
        arq.write_text(
            f"|0000|006|0||0|01122024|31122024|EMPRESA TESTE SA|{cnpj}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|9900|4|\n|9900|9999|1|\n|9999|6|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(cnpj, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_31_bc_pis_vs_m210.executar(
                repo, conn, cnpj, 202412, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_entrada_excluida_das_saidas(self, tmp_path):
        """C170 de entrada (C100 IND_OPER=0) não entra na soma → base correta."""
        arq = tmp_path / "entrada.txt"
        cnpj = _CNPJ
        arq.write_text(
            f"|0000|006|0||0|01112024|30112024|EMPRESA TESTE SA|{cnpj}||SP||||||||A|0|\n"
            "|0110|1|1|0|0|\n"
            # C100 IND_OPER=0 (entrada)
            "|C100|0|0|PART001|55|00|001|000001299|43250000000001000000000000000000000001000099|01112024|10000,00|\n"
            "|C170|01|PROD001|Produto entrada|1|UN|10000,00|0,00||00|1102||0,00|0,00|0,00||0,00|0,00||00|||0,00|0,00|01|10000,00|1,65|0,00|0,00|165,00|01|10000,00|7,60|0,00|0,00|760,00|3001|\n"
            # M210 declara base 10.000 (não importa — C170 de entrada é excluído, soma=0)
            "|M210|01|10000,00|10000,00|1,65|0,00|0,00|165,00|0,00|0,00|0,00|0,00|165,00|\n"
            "|9900|0000|1|\n|9900|0110|1|\n|9900|C100|1|\n|9900|C170|1|\n|9900|M210|1|\n"
            "|9900|9900|7|\n|9900|9999|1|\n|9999|13|\n",
            encoding="utf-8",
        )
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(arq, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
        repo = Repositorio(cnpj, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_31_bc_pis_vs_m210.executar(
                repo, conn, cnpj, 202411, _ANO
            )
        finally:
            conn.close()

        # soma_c170 = 0 (entrada excluída), soma_m210 = 10000 → diferença 10000 → divergência
        # Isso sinaliza que M210 tem base que não vem dos C170 de saída analisados
        # (pode vir de outros registros: D100, F100 etc. — CR-31 nota que a análise é parcial)
        assert len(divs) == 1
        assert divs[0].evidencia[0]["campos_chave"]["soma_vl_bc_pis_c170"] == pytest.approx(0.0)
