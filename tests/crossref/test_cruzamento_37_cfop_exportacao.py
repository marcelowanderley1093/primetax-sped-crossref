"""
Testes do cruzamento CR-37 — CFOP exportação (EFD ICMS/IPI) × CST_PIS/COFINS.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia do EFD ICMS/IPI.

Fixture positivo (202601):
  EFD ICMS C170 CFOP=7101 + EFD-Contrib C170 CFOP=7101 CST_PIS=01 VL_BC_PIS=5000
  → exportação tributada incorretamente por PIS/COFINS → CR-37 dispara.

Fixture negativo (202602):
  EFD ICMS C170 CFOP=7101 + EFD-Contrib C170 CFOP=7101 CST_PIS=07 VL_BC_PIS=0
  → exportação com CST correto (alíquota zero) → CR-37 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_37_cfop_exportacao
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes, efd_icms_ipi

_CNPJ = "00000000000109"
_ANO = 2026


def _importar_cross(
    contrib: Path, icms: Path, tmp_path: Path
) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        contrib, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    efd_icms_ipi.importar(
        icms, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento37CfopExportacao:
    def test_exportacao_cst_errado_dispara(
        self,
        fixture_sprint6_contrib_cr37_positivo,
        fixture_sprint6_icms_cr37_202601,
        tmp_path,
    ):
        """CFOP=7101 na EFD ICMS e CST_PIS=01 na EFD-Contrib (errado) → CR-37 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_cr37_positivo,
            fixture_sprint6_icms_cr37_202601,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_37_cfop_exportacao.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-37"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert "7101" in ck["cfops_exportacao_icms"]
        assert ck["qtd_itens_cst_errado"] >= 1
        assert ck["soma_vl_bc_pis_afetado"] == pytest.approx(5000.0)

    def test_exportacao_cst_correto_nao_dispara(
        self,
        fixture_sprint6_contrib_cr37_negativo,
        fixture_sprint6_icms_cr37_202602,
        tmp_path,
    ):
        """CFOP=7101 na EFD ICMS e CST_PIS=07 na EFD-Contrib (correto) → CR-37 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_cr37_negativo,
            fixture_sprint6_icms_cr37_202602,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_37_cfop_exportacao.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_efd_icms_retorna_vazio(self, fixture_sprint6_contrib_cr37_positivo, tmp_path):
        """Sem EFD ICMS importado → disponibilidade_efd_icms != importada → CR-37 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint6_contrib_cr37_positivo,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_37_cfop_exportacao.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
