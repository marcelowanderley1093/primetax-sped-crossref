"""
Testes do cruzamento CR-20 — Créditos presumidos setoriais não aproveitados (CST 60-67).

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.

Fixture positivo (202601):
  C170 CST_PIS=60, VL_BC_PIS>0, ALIQ_PIS>0, VL_PIS=0 →
  crédito presumido monofásico não aproveitado → CR-20 dispara.

Fixture negativo (202602):
  C170 CST_PIS=60, VL_PIS preenchido → CR-20 não dispara.
"""

from pathlib import Path

import pytest

from src.crossref.camada_2_oportunidades import cruzamento_20_credito_presumido_setorial
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


class TestCruzamento20CreditoPresumidoSetorial:
    def test_cst60_sem_vl_pis_gera_oportunidade(
        self, fixture_sprint5_cr20_positivo, tmp_path
    ):
        """CST_PIS=60 monofásico com BC e alíquota mas VL_PIS=0 → CR-20 dispara."""
        repo, conn = _importar(fixture_sprint5_cr20_positivo, tmp_path)
        try:
            ops, divs = cruzamento_20_credito_presumido_setorial.executar(
                repo, conn, _CNPJ, 202601, _ANO
            )
        finally:
            conn.close()

        assert len(ops) >= 1
        assert divs == []
        op = ops[0]
        assert op.codigo_regra == "CR-20"
        assert op.severidade == "alto"
        ck = op.evidencia[0]["campos_chave"]
        assert ck["cst_pis"] == "60"
        assert ck["vl_pis_declarado"] == pytest.approx(0.0)
        assert ck["impacto_pis"] > 0.0

    def test_cst60_com_vl_pis_nao_dispara(
        self, fixture_sprint5_cr20_negativo, tmp_path
    ):
        """CST_PIS=60 com VL_PIS corretamente preenchido → CR-20 não dispara."""
        repo, conn = _importar(fixture_sprint5_cr20_negativo, tmp_path)
        try:
            ops, divs = cruzamento_20_credito_presumido_setorial.executar(
                repo, conn, _CNPJ, 202602, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
