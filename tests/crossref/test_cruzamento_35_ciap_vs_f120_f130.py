"""
Testes do cruzamento CR-35 — CIAP (G125) × F120/F130.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia do EFD ICMS/IPI.

Fixture positivo (202601):
  EFD ICMS G125 VL_PARC_PASS=500 + EFD-Contrib sem F120/F130
  → CIAP sem contrapartida PIS/COFINS → CR-35 dispara.

Fixture negativo (202602):
  EFD ICMS G125 VL_PARC_PASS=500 + EFD-Contrib com F120
  → CIAP já tem contrapartida → CR-35 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_35_ciap_vs_f120_f130
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


class TestCruzamento35CiapVsF120F130:
    def test_ciap_sem_f120_f130_dispara(
        self,
        fixture_sprint6_contrib_minimal_202601,
        fixture_sprint6_icms_cr35_202601,
        tmp_path,
    ):
        """G125 VL_PARC_PASS>0 sem F120/F130 na EFD-Contrib → CR-35 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_minimal_202601,
            fixture_sprint6_icms_cr35_202601,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_35_ciap_vs_f120_f130.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-35"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["qtd_bens_ciap"] >= 1
        assert ck["soma_vl_parc_pass"] == pytest.approx(500.0)
        assert ck["tem_f120"] is False
        assert ck["tem_f130"] is False

    def test_ciap_com_f120_nao_dispara(
        self,
        fixture_sprint6_contrib_com_f120_202602,
        fixture_sprint6_icms_cr35_202602,
        tmp_path,
    ):
        """G125 VL_PARC_PASS>0 mas EFD-Contrib já tem F120 → CR-35 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_com_f120_202602,
            fixture_sprint6_icms_cr35_202602,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_35_ciap_vs_f120_f130.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_efd_icms_retorna_vazio(self, fixture_sprint6_contrib_minimal_202601, tmp_path):
        """Sem EFD ICMS importado → disponibilidade_efd_icms != importada → CR-35 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint6_contrib_minimal_202601,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_35_ciap_vs_f120_f130.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
