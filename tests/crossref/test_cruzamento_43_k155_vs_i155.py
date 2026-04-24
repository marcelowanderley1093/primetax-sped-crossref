"""
Testes do cruzamento CR-43 — K155/K355 (ECF) × I155 (ECD): saldos contábeis.

Princípio 3 (CLAUDE.md §4): par positivo + negativo obrigatório.
Dependência inter-SPED: requer importação prévia de ECF e ECD.

Fixture positivo:
  ECF K155 VL_SLD_FIN=150.000 (C) + ECD I155 VL_SLD_FIN=100.000 (C) para conta 1.01.001
  → divergência 33% > 1% → CR-43 dispara.

Fixture negativo:
  ECF K155 VL_SLD_FIN=150.000 (C) + ECD I155 VL_SLD_FIN=150.000 (C) para conta 1.01.001
  → divergência 0% → CR-43 não dispara.
"""

from pathlib import Path

from src.crossref.camada_2_oportunidades import cruzamento_43_k155_vs_i155
from src.db.repo import Repositorio
from src.parsers import ecd, ecf

_CNPJ = "00000000000143"
_ANO = 2025


def _importar_ecf_ecd(ecf_path: Path, ecd_path: Path, tmp_path: Path):
    db_dir = tmp_path / "db"
    ecf.importar(ecf_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    ecd.importar(ecd_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir)
    repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
    return repo, repo.conexao()


class TestCruzamento43K155VsI155:
    def test_divergencia_saldo_dispara(
        self,
        fixture_sprint8_ecf_cr43,
        fixture_sprint8_ecd_cr43_positivo,
        tmp_path,
    ):
        """ECF K155=150K e ECD I155=100K (divergência 33% > 1%) → CR-43 dispara."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr43, fixture_sprint8_ecd_cr43_positivo, tmp_path
        )
        try:
            ops, divs = cruzamento_43_k155_vs_i155.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 1
        div = divs[0]
        assert div.codigo_regra == "CR-43"
        assert div.severidade == "alto"
        ck = div.evidencia[0]["campos_chave"]
        assert ck["cod_cta"] == "1.01.001"
        assert ck["saldo_ecf"] == 150000.0
        assert ck["saldo_ecd"] == 100000.0

    def test_saldo_igual_nao_dispara(
        self,
        fixture_sprint8_ecf_cr43,
        fixture_sprint8_ecd_cr43_negativo,
        tmp_path,
    ):
        """ECF K155=150K e ECD I155=150K (divergência 0%) → CR-43 não dispara."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr43, fixture_sprint8_ecd_cr43_negativo, tmp_path
        )
        try:
            ops, divs = cruzamento_43_k155_vs_i155.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    def test_sem_ecd_retorna_vazio(self, fixture_sprint8_ecf_cr43, tmp_path):
        """Sem ECD importada → disponibilidade_ecd != importada → CR-43 retorna []."""
        db_dir = tmp_path / "db"
        ecf.importar(
            fixture_sprint8_ecf_cr43,
            encoding_override="utf8",
            prompt_operador=False,
            base_dir_db=db_dir,
        )
        repo = Repositorio(_CNPJ, _ANO, base_dir=db_dir)
        conn = repo.conexao()
        try:
            ops, divs = cruzamento_43_k155_vs_i155.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []

    # §16.7 — testes de modo degradado (agregação por COD_NAT)

    def test_modo_degradado_positivo_agrega_natureza_dispara(
        self,
        fixture_sprint8_ecf_cr43,
        fixture_ecd_cr43_degradado_positivo,
        tmp_path,
    ):
        """ECF K155 Ativo=150K + ECD IND_MUDANC_PC=1 I155 Ativo=100K → Divergência agregada por natureza."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr43, fixture_ecd_cr43_degradado_positivo, tmp_path
        )
        try:
            ops, divs = cruzamento_43_k155_vs_i155.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert len(divs) == 1
        ck = divs[0].evidencia[0]["campos_chave"]
        assert ck["modo_execucao"] == "degradado"
        assert ck["reconciliacao_plano_contas"] == "ausente"
        assert ck["cod_nat"] == "01"
        assert ck["saldo_ecf_agregado"] == 150000.0
        assert ck["saldo_ecd_agregado"] == 100000.0

    def test_modo_degradado_negativo_nao_dispara(
        self,
        fixture_sprint8_ecf_cr43,
        fixture_ecd_cr43_degradado_negativo,
        tmp_path,
    ):
        """ECF Ativo=150K + ECD degradada Ativo=150K → agregados iguais → não dispara."""
        repo, conn = _importar_ecf_ecd(
            fixture_sprint8_ecf_cr43, fixture_ecd_cr43_degradado_negativo, tmp_path
        )
        try:
            ops, divs = cruzamento_43_k155_vs_i155.executar(
                repo, conn, _CNPJ, 202501, _ANO
            )
        finally:
            conn.close()

        assert ops == []
        assert divs == []
