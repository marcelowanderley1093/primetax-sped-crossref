"""
Testes do módulo de reconciliação de plano de contas (CLAUDE.md §16).

Cobertura:
  - classificar_reconciliacao: integra / ausente / None
  - resolver_cod_cta: passthrough quando integra, None quando comprometido
  - consultar_plano_contas_natureza: mapa cod_cta → cod_nat
  - agregar_por_natureza: agrega saldos por COD_NAT
  - Persistência em _sped_contexto após importação da ECD
"""

from decimal import Decimal
from pathlib import Path

from src.crossref.common import reconciliacao_plano_contas
from src.db.repo import Repositorio
from src.parsers import ecd


def _importar_ecd(ecd_path: Path, tmp_path: Path, cnpj: str, ano: int):
    db_dir = tmp_path / "db"
    ecd.importar(
        ecd_path, encoding_override="utf8", prompt_operador=False, base_dir_db=db_dir
    )
    repo = Repositorio(cnpj, ano, base_dir=db_dir)
    return repo, repo.conexao()


class TestClassificarReconciliacao:
    def test_ecd_sem_mudanca_classifica_integra(
        self, fixture_sprint8_ecd_cr43_positivo, tmp_path
    ):
        """ECD com IND_MUDANC_PC='0' → integra."""
        repo, conn = _importar_ecd(
            fixture_sprint8_ecd_cr43_positivo, tmp_path, "00000000000143", 2025
        )
        try:
            estado = reconciliacao_plano_contas.classificar_reconciliacao(
                repo, conn, "00000000000143", 2025
            )
        finally:
            conn.close()
        assert estado == "integra"

    def test_ecd_com_mudanca_sem_bloco_c_classifica_ausente(
        self, fixture_ecd_reconciliacao_mudanc_pc, tmp_path
    ):
        """ECD com IND_MUDANC_PC='1' e Bloco C vazio → ausente (§16.2)."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_mudanc_pc, tmp_path, "00000000000148", 2025
        )
        try:
            estado = reconciliacao_plano_contas.classificar_reconciliacao(
                repo, conn, "00000000000148", 2025
            )
        finally:
            conn.close()
        assert estado == "ausente"

    def test_ecd_com_mudanca_bloco_c_completo_classifica_integra(
        self, fixture_ecd_reconciliacao_blococ_completo, tmp_path
    ):
        """IND_MUDANC_PC='1' + C050 cobre 100% do I050 analítico + C155 ≥1 → integra."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_blococ_completo, tmp_path,
            "00000000000149", 2025,
        )
        try:
            estado = reconciliacao_plano_contas.classificar_reconciliacao(
                repo, conn, "00000000000149", 2025
            )
        finally:
            conn.close()
        assert estado == "integra"

    def test_ecd_com_mudanca_bloco_c_parcial_classifica_suspeita(
        self, fixture_ecd_reconciliacao_blococ_parcial, tmp_path
    ):
        """IND_MUDANC_PC='1' + C050 cobre apenas 33% do I050 analítico → suspeita."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_blococ_parcial, tmp_path,
            "00000000000150", 2025,
        )
        try:
            estado = reconciliacao_plano_contas.classificar_reconciliacao(
                repo, conn, "00000000000150", 2025
            )
        finally:
            conn.close()
        assert estado == "suspeita"

    def test_sem_ecd_retorna_none(self, tmp_path):
        """Sem ECD importada → None."""
        db_dir = tmp_path / "db"
        repo = Repositorio("00000000000100", 2025, base_dir=db_dir)
        repo.criar_banco()
        conn = repo.conexao()
        try:
            estado = reconciliacao_plano_contas.classificar_reconciliacao(
                repo, conn, "00000000000100", 2025
            )
        finally:
            conn.close()
        assert estado is None


class TestResolverCodCta:
    def test_integra_retorna_cod_cta_inalterado(
        self, fixture_sprint8_ecd_cr43_positivo, tmp_path
    ):
        repo, conn = _importar_ecd(
            fixture_sprint8_ecd_cr43_positivo, tmp_path, "00000000000143", 2025
        )
        try:
            resultado = reconciliacao_plano_contas.resolver_cod_cta(
                repo, conn, "00000000000143", 2025, "1.01.001"
            )
        finally:
            conn.close()
        assert resultado == "1.01.001"

    def test_ausente_retorna_none(
        self, fixture_ecd_reconciliacao_mudanc_pc, tmp_path
    ):
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_mudanc_pc, tmp_path, "00000000000148", 2025
        )
        try:
            resultado = reconciliacao_plano_contas.resolver_cod_cta(
                repo, conn, "00000000000148", 2025, "1.01.001"
            )
        finally:
            conn.close()
        assert resultado is None


class TestConsultarPlanoContasNatureza:
    def test_mapa_cod_cta_para_cod_nat(
        self, fixture_ecd_reconciliacao_mudanc_pc, tmp_path
    ):
        """Fixture tem 1.01.001 com COD_NAT='01' e 3.01.001 com COD_NAT='04'."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_mudanc_pc, tmp_path, "00000000000148", 2025
        )
        try:
            mapa = reconciliacao_plano_contas.consultar_plano_contas_natureza(
                repo, conn, "00000000000148", 2025
            )
        finally:
            conn.close()
        assert mapa["1.01.001"] == "01"
        assert mapa["3.01.001"] == "04"


class TestAgregarPorNatureza:
    def test_agregacao_simples(self):
        saldos = {
            "1.01.001": Decimal("100"),
            "1.01.002": Decimal("200"),
            "3.01.001": Decimal("500"),
        }
        plano = {
            "1.01.001": "01",  # Ativo
            "1.01.002": "01",  # Ativo
            "3.01.001": "04",  # Resultado
        }
        agregado = reconciliacao_plano_contas.agregar_por_natureza(saldos, plano)
        assert agregado == {"01": Decimal("300"), "04": Decimal("500")}

    def test_conta_ausente_vai_para_natureza_99(self):
        """Conta em saldos sem correspondência no plano → cod_nat='99'."""
        saldos = {"1.99.999": Decimal("50")}
        plano = {"1.01.001": "01"}
        agregado = reconciliacao_plano_contas.agregar_por_natureza(saldos, plano)
        assert agregado == {"99": Decimal("50")}


class TestPersistenciaEmContexto:
    def test_ecd_integra_persiste_no_contexto(
        self, fixture_sprint8_ecd_cr43_positivo, tmp_path
    ):
        """Importação da ECD atualiza _sped_contexto.reconciliacao_plano_contas='integra'."""
        repo, conn = _importar_ecd(
            fixture_sprint8_ecd_cr43_positivo, tmp_path, "00000000000143", 2025
        )
        try:
            ctx = repo.consultar_sped_contexto(conn)
        finally:
            conn.close()
        assert ctx is not None
        assert ctx["reconciliacao_plano_contas"] == "integra"

    def test_ecd_mudanc_pc_persiste_ausente(
        self, fixture_ecd_reconciliacao_mudanc_pc, tmp_path
    ):
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_mudanc_pc, tmp_path, "00000000000148", 2025
        )
        try:
            ctx = repo.consultar_sped_contexto(conn)
        finally:
            conn.close()
        assert ctx is not None
        assert ctx["reconciliacao_plano_contas"] == "ausente"

    def test_bloco_c_completo_persiste_integra(
        self, fixture_ecd_reconciliacao_blococ_completo, tmp_path
    ):
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_blococ_completo, tmp_path,
            "00000000000149", 2025,
        )
        try:
            ctx = repo.consultar_sped_contexto(conn)
        finally:
            conn.close()
        assert ctx is not None
        assert ctx["reconciliacao_plano_contas"] == "integra"


class TestBlocoCParsing:
    def test_c050_persistido(
        self, fixture_ecd_reconciliacao_blococ_completo, tmp_path
    ):
        """Fixture tem 2 registros C050 — devem estar persistidos."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_blococ_completo, tmp_path,
            "00000000000149", 2025,
        )
        try:
            c050 = repo.consultar_ecd_c050(conn, "00000000000149", 2025)
            qtd = repo.contar_ecd_c050(conn, "00000000000149", 2025)
        finally:
            conn.close()
        assert qtd == 2
        codigos = {r["cod_cta"] for r in c050}
        assert codigos == {"1.01.001", "3.01.001"}

    def test_c155_persistido(
        self, fixture_ecd_reconciliacao_blococ_completo, tmp_path
    ):
        """Fixture tem 1 registro C155 com VL_SLD_FIN=80000."""
        repo, conn = _importar_ecd(
            fixture_ecd_reconciliacao_blococ_completo, tmp_path,
            "00000000000149", 2025,
        )
        try:
            qtd = repo.contar_ecd_c155(conn, "00000000000149", 2025)
        finally:
            conn.close()
        assert qtd == 1
