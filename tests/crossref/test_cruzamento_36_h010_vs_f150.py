"""
Testes do cruzamento CR-36 — H010.VL_ITEM_IR × F150.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia do EFD ICMS/IPI.

Fixture positivo (202601):
  EFD ICMS H010 VL_ITEM_IR=9000 + EFD-Contrib sem F150
  → inventário com ICMS excluído mas sem crédito sobre estoque → CR-36 dispara.

Fixture negativo (202602):
  EFD ICMS H010 VL_ITEM_IR=9000 + EFD-Contrib com F150
  → crédito sobre estoque já aproveitado → CR-36 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_36_h010_vs_f150
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


class TestCruzamento36H010VsF150:
    def test_h010_sem_f150_dispara(
        self,
        fixture_sprint6_contrib_minimal_202601,
        fixture_sprint6_icms_cr36_202601,
        tmp_path,
    ):
        """H010 VL_ITEM_IR>0 sem F150 na EFD-Contrib → CR-36 dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_minimal_202601,
            fixture_sprint6_icms_cr36_202601,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_36_h010_vs_f150.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert divs == []
        assert len(ops) == 1
        op = ops[0]
        assert op.codigo_regra == "CR-36"
        assert op.severidade == "medio"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["qtd_itens_com_vl_item_ir"] >= 1
        assert ck["soma_vl_item_ir"] == pytest.approx(9000.0)
        assert ck["tem_f150"] is False

    def test_h010_com_f150_nao_dispara(
        self,
        fixture_sprint6_contrib_com_f150_202602,
        fixture_sprint6_icms_cr36_202602,
        tmp_path,
    ):
        """H010 VL_ITEM_IR>0 mas EFD-Contrib já tem F150 → CR-36 não dispara."""
        repo, conn = _importar_cross(
            fixture_sprint6_contrib_com_f150_202602,
            fixture_sprint6_icms_cr36_202602,
            tmp_path,
        )
        try:
            ops, divs = cruzamento_36_h010_vs_f150.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_efd_icms_retorna_vazio(self, fixture_sprint6_contrib_minimal_202601, tmp_path):
        """Sem EFD ICMS importado → disponibilidade_efd_icms != importada → CR-36 retorna []."""
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
            ops, divs = cruzamento_36_h010_vs_f150.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
