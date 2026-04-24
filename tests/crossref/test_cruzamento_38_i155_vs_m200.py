"""
Testes do cruzamento CR-38 — I155 (ECD) × M200 (EFD-Contribuições).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia da ECD.

Fixture positivo:
  EFD-Contrib M200 VL_REC_BRT_TOTAL=125.000 + ECD I155 VL_CRED=100.000 (COD_NAT='04')
  → diferença 25% > 5% → CR-38 dispara.

Fixture negativo:
  EFD-Contrib M200 VL_REC_BRT_TOTAL=120.000 + ECD I155 VL_CRED=120.000 (COD_NAT='04')
  → diferença 0% → CR-38 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_38_i155_vs_m200
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


class TestCruzamento38I155VsM200:
    def test_m200_maior_i155_dispara(
        self,
        fixture_sprint7_contrib_m200_alto,
        fixture_sprint7_ecd_cr38_positivo,
        tmp_path,
    ):
        """M200=125K e I155=100K (diferença 25% > 5%) → CR-38 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m200_alto,
            fixture_sprint7_ecd_cr38_positivo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_38_i155_vs_m200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-38"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["receita_efd_m200"] == pytest.approx(125000.0)
        assert ck["receita_ecd_i155"] == pytest.approx(100000.0)
        assert ck["proporcao_pct"] == pytest.approx(25.0)

    def test_m200_igual_i155_nao_dispara(
        self,
        fixture_sprint7_contrib_m200_match,
        fixture_sprint7_ecd_cr38_negativo,
        tmp_path,
    ):
        """M200=120K e I155=120K (diferença 0%) → CR-38 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m200_match,
            fixture_sprint7_ecd_cr38_negativo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_38_i155_vs_m200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint7_contrib_m200_alto, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-38 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint7_contrib_m200_alto,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_38_i155_vs_m200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    # §16.7 — testes de modo degradado (reconciliação != 'integra')

    def test_modo_degradado_positivo_dispara_marcando_execucao(
        self,
        fixture_sprint7_contrib_m200_alto,
        fixture_ecd_cr38_degradado_positivo,
        tmp_path,
    ):
        """ECD IND_MUDANC_PC=1 sem Bloco C + M200=125K e I155=100K → dispara em modo degradado."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m200_alto,
            fixture_ecd_cr38_degradado_positivo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_38_i155_vs_m200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        ck = ops[0].evidencia[0]["campos_chave"]
        assert ck["modo_execucao"] == "degradado"
        assert ck["reconciliacao_plano_contas"] == "ausente"
        assert ck["receita_efd_m200"] == pytest.approx(125000.0)
        assert ck["receita_ecd_i155"] == pytest.approx(100000.0)

    def test_modo_degradado_negativo_nao_dispara(
        self,
        fixture_sprint7_contrib_m200_match,
        fixture_ecd_cr38_degradado_negativo,
        tmp_path,
    ):
        """ECD degradada com receita batendo M200 → não dispara mesmo em modo degradado."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_m200_match,
            fixture_ecd_cr38_degradado_negativo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_38_i155_vs_m200.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
