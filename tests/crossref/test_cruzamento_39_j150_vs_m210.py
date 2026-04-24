"""
Testes do cruzamento CR-39 — J150 (DRE-ECD) × M210 (EFD-Contribuições).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia da ECD.

Fixture positivo:
  EFD-Contrib sem M210 com CST não-operacional + ECD J150 IND_GRP_DRE='07' VL=20.000
  → receita financeira sem CST adequado no M210 → CR-39 dispara.

Fixture negativo:
  EFD-Contrib com M210 CST='73' (alíquota reduzida) + mesma ECD J150
  → CST adequado presente → CR-39 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_39_j150_vs_m210
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


class TestCruzamento39J150VsM210:
    def test_receita_fin_sem_cst_adequado_dispara(
        self,
        fixture_sprint7_contrib_minimal,
        fixture_sprint7_ecd_cr39,
        tmp_path,
    ):
        """J150 IND_GRP_DRE='07' VL=20K sem M210 com CST 70/73/75 → CR-39 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_minimal,
            fixture_sprint7_ecd_cr39,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_39_j150_vs_m210.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-39"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["soma_receita_nao_operacional"] == pytest.approx(20000.0)
        assert "07" in ck["grupos_dre"]

    def test_m210_com_cst73_nao_dispara(
        self,
        fixture_sprint7_contrib_m210_cst73,
        fixture_sprint7_ecd_cr39,
        tmp_path,
    ):
        """M210 com COD_CONT='7300' (CST 73) → CST adequado presente → CR-39 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m210_cst73,
            fixture_sprint7_ecd_cr39,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_39_j150_vs_m210.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint7_contrib_minimal, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-39 retorna []."""
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
            ops, divs = cruzamento_39_j150_vs_m210.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    # §16.7 — testes de modo degradado

    def test_modo_degradado_positivo_dispara_marcando_execucao(
        self,
        fixture_sprint7_contrib_minimal,
        fixture_ecd_cr39_degradado,
        tmp_path,
    ):
        """ECD IND_MUDANC_PC=1 + J150 não-op 20K + EFD sem CST adequado → dispara em degradado."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_minimal,
            fixture_ecd_cr39_degradado,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_39_j150_vs_m210.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        ck = ops[0].evidencia[0]["campos_chave"]
        assert ck["modo_execucao"] == "degradado"
        assert ck["reconciliacao_plano_contas"] == "ausente"

    def test_modo_degradado_negativo_nao_dispara(
        self,
        fixture_sprint7_contrib_m210_cst73,
        fixture_ecd_cr39_degradado,
        tmp_path,
    ):
        """EFD com CST='73' + ECD degradada → CST adequado protege → não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m210_cst73,
            fixture_ecd_cr39_degradado,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_39_j150_vs_m210.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
