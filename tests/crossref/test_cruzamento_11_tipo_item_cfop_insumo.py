"""
Testes do cruzamento CR-11 — TIPO_ITEM '07' (uso e consumo) com CFOP de insumo.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  0200 TIPO_ITEM=07 + C170 CFOP=1101 + CST_PIS=70 (sem crédito) →
  candidato a reclassificação sob REsp 1.221.170/PR → CR-11 dispara.

Fixture negativo (202602):
  0200 TIPO_ITEM=01 (matéria-prima) + C170 CST_PIS=50 (com crédito) →
  CR-11 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_11_tipo_item_cfop_insumo
from src.db.repo import Repositorio
from src.parsers import efd_contribuicoes

_CNPJ = "00000000000109"
_ANO = 2026


def _importar(caminho: Path, tmp_path: Path) -> tuple[Repositorio, object]:
    db_dir = tmp_path / "db"
    efd_contribuicoes.importar(
        caminho, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento11TipoItemCfopInsumo:
    def test_tipo07_cfop_insumo_cst70_gera_oportunidade(
        self, fixture_sprint5_cr11_positivo, tmp_path
    ):
        """TIPO_ITEM=07 + CFOP=1101 + CST=70 → CR-11 sinaliza reclassificação possível."""
        repo, conn = _importar(fixture_sprint5_cr11_positivo, tmp_path)
        try:
            ops, divs = cruzamento_11_tipo_item_cfop_insumo.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-11"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["tipo_item"] == "07"
        assert ck["cfop"] == "1101"
        assert ck["cst_pis"] == "70"
        assert ck["impacto_pis"] > 0.0
        assert ck["impacto_cofins"] > 0.0

    def test_tipo01_sem_oportunidade(
        self, fixture_sprint5_cr11_negativo, tmp_path
    ):
        """TIPO_ITEM=01 (MP) já com crédito CST=50 → CR-11 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr11_negativo, tmp_path)
        try:
            ops, divs = cruzamento_11_tipo_item_cfop_insumo.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
