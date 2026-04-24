"""
Testes do cruzamento CR-40 — COD_CTA em C170 × I050 (ECD).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia da ECD.

Fixture positivo:
  EFD-Contrib C170 COD_CTA='3001' + ECD I050 sem conta '3001'
  → conta fantasma → CR-40 dispara divergência.

Fixture negativo:
  EFD-Contrib C170 COD_CTA='3001' + ECD I050 com conta '3001' (COD_NAT='01', IND_CTA='A')
  → conta presente → CR-40 não dispara.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_40_cod_cta_vs_i050
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


class TestCruzamento40CodCtaVsI050:
    def test_conta_ausente_ecd_dispara(
        self,
        fixture_sprint7_contrib_c170_cta3001,
        fixture_sprint7_ecd_cr40_positivo,
        tmp_path,
    ):
        """C170 COD_CTA='3001' mas I050 sem '3001' → divergência."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_c170_cta3001,
            fixture_sprint7_ecd_cr40_positivo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_40_cod_cta_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 1
        div = divs[0]
        assert div.codigo_regra == "CR-40"
        ck = div.evidencia[0]["campos_chave"]
        assert "3001" in ck["ctas_ausentes_ecd"]
        assert ck["qtd_ctas_ausentes"] >= 1

    def test_conta_presente_ecd_nao_dispara(
        self,
        fixture_sprint7_contrib_c170_cta3001,
        fixture_sprint7_ecd_cr40_negativo,
        tmp_path,
    ):
        """C170 COD_CTA='3001' e I050 tem '3001' (IND_CTA='A') → sem divergência."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_c170_cta3001,
            fixture_sprint7_ecd_cr40_negativo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_40_cod_cta_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint7_contrib_c170_cta3001, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-40 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint7_contrib_c170_cta3001,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_40_cod_cta_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
