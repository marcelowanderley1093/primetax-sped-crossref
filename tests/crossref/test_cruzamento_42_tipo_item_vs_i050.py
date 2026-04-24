"""
Testes do cruzamento CR-42 — TIPO_ITEM em 0200 × COD_NAT em I050 (ECD).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia da ECD.

Fixture positivo:
  EFD-Contrib 0200 TIPO_ITEM='01' + C170 COD_CTA='3001' + ECD I050 '3001' COD_NAT='02' (Passivo)
  → insumo mapeado para conta de Passivo → CR-42 dispara divergência.

Fixture negativo:
  EFD-Contrib igual + ECD I050 '3001' COD_NAT='01' (Ativo — correto)
  → classificação correta → CR-42 não dispara.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_42_tipo_item_vs_i050
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


class TestCruzamento42TipoItemVsI050:
    def test_insumo_conta_passivo_dispara(
        self,
        fixture_sprint7_contrib_0200_c170,
        fixture_sprint7_ecd_cr42_positivo,
        tmp_path,
    ):
        """0200 TIPO_ITEM='01' + C170 COD_CTA='3001' + I050 '3001' COD_NAT='02' → divergência."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_0200_c170,
            fixture_sprint7_ecd_cr42_positivo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_42_tipo_item_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 1
        div = divs[0]
        assert div.codigo_regra == "CR-42"
        ck = div.evidencia[0]["campos_chave"]
        assert ck["qtd_problemas"] >= 1
        problemas = ck["contas_classificacao_suspeita"]
        assert any(p["cod_cta"] == "3001" for p in problemas)
        problema_3001 = next(p for p in problemas if p["cod_cta"] == "3001")
        assert problema_3001["cod_nat"] == "02"

    def test_insumo_conta_ativo_nao_dispara(
        self,
        fixture_sprint7_contrib_0200_c170,
        fixture_sprint7_ecd_cr42_negativo,
        tmp_path,
    ):
        """0200 TIPO_ITEM='01' + C170 COD_CTA='3001' + I050 '3001' COD_NAT='01' → sem divergência."""
        repo, conn = _importar_cross(
            fixture_sprint7_contrib_0200_c170,
            fixture_sprint7_ecd_cr42_negativo,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_42_tipo_item_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint7_contrib_0200_c170, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-42 retorna []."""
        db_dir = tmp_path / "db"
        efd_contribuicoes.importar(
            fixture_sprint7_contrib_0200_c170,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_42_tipo_item_vs_i050.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
