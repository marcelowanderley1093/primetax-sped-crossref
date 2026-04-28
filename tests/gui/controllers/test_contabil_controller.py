"""
Testes do ContabilController — BP/DRE/Razão/Despesas×Crédito.
"""

from __future__ import annotations

import sqlite3
from decimal import Decimal
from pathlib import Path

import pytest

from src.db.repo import Repositorio
from src.gui.controllers.contabil_controller import (
    ContabilController,
    DespesaVsCredito,
    LinhaBalanco,
)


def _criar_banco(tmp_path: Path, cnpj: str = "00000000000100", ano: int = 2025) -> Path:
    """Cria banco com schema completo (inclui ecd_*) e devolve diretório base."""
    base = tmp_path / "db"
    repo = Repositorio(cnpj, ano, base_dir=base)
    repo.criar_banco()
    return base


def _inserir_j005(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    linha_arquivo: int = 100,
    dt_fin: str | None = None,
) -> int:
    """Insere um J005 (cabeçalho de demonstração). Retorna a linha_arquivo
    para uso como FK no J100/J150. Se já existe um, retorna o existente."""
    dt_fin = dt_fin or f"{ano}-12-31"
    conn.execute(
        """INSERT INTO ecd_j005
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
            dt_ini_dem, dt_fin_dem, id_dem)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", linha_arquivo, cnpj,
            f"{ano}-01-01", dt_fin, ano * 100 + 1, ano, "9.00",
            f"{ano}-01-01", dt_fin, "2",
        ),
    )
    return linha_arquivo


def _inserir_j100(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    nu_ordem: str, cod_agl: str, descr: str, nivel: str,
    cod_agl_sup: str, ind_grp_bal: str,
    vl_ini: float, ind_dc_ini: str, vl_fin: float, ind_dc_fin: str,
    j005_linha: int = 100,
) -> None:
    conn.execute(
        """INSERT INTO ecd_j100
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
            j005_linha_arquivo, nu_ordem, cod_agl, ind_cod_agl, nivel_agl,
            cod_agl_sup, ind_grp_bal, descr_cod_agl,
            vl_cta_ini, ind_dc_ini, vl_cta_fin, ind_dc_fin)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", 1, cnpj,
            f"{ano}-01-01", f"{ano}-12-31", ano * 100 + 1, ano, "9.00",
            j005_linha, nu_ordem, cod_agl, "S", nivel,
            cod_agl_sup, ind_grp_bal, descr,
            vl_ini, ind_dc_ini, vl_fin, ind_dc_fin,
        ),
    )


def _inserir_i050(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    cod_cta: str, cta: str, cod_nat: str = "04", ind_cta: str = "A",
) -> None:
    conn.execute(
        """INSERT INTO ecd_i050
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario,
            cod_ver, cod_nat, ind_cta, nivel, cod_cta, cta)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", 1, cnpj,
            f"{ano}-01-01", f"{ano}-12-31", ano * 100 + 1, ano,
            "9.00", cod_nat, ind_cta, "5", cod_cta, cta,
        ),
    )


def _inserir_i200(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    linha: int, num_lcto: str, dt_lcto: str, vl: float,
) -> None:
    conn.execute(
        """INSERT INTO ecd_i200
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario,
            cod_ver, num_lcto, dt_lcto, vl_lcto, ind_lcto, dt_lcto_ext)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", linha, cnpj,
            f"{ano}-01-01", f"{ano}-12-31", ano * 100 + 1, ano,
            "9.00", num_lcto, dt_lcto, vl, "N", "",
        ),
    )


def _inserir_i250(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    i200_linha: int, cod_cta: str, vl: float, ind_dc: str,
    historico: str = "Hist",
) -> None:
    conn.execute(
        """INSERT INTO ecd_i250
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario,
            cod_ver, i200_linha_arquivo, cod_cta, cod_ccus,
            vl_deb_cred, ind_dc, hist_lcto_ccus, cod_hist_pad)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", i200_linha + 100, cnpj,
            f"{ano}-01-01", f"{ano}-12-31", ano * 100 + 1, ano,
            "9.00", i200_linha, cod_cta, "",
            vl, ind_dc, historico, "",
        ),
    )


def _inserir_i155(
    conn: sqlite3.Connection, cnpj: str, ano: int,
    cod_cta: str, vl_deb: float, vl_cred: float,
) -> None:
    conn.execute(
        """INSERT INTO ecd_i155
           (arquivo_origem, linha_arquivo, cnpj_declarante,
            dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario,
            cod_ver, i150_linha_arquivo, cod_cta, cod_ccus,
            vl_sld_ini, ind_dc_ini, vl_deb, vl_cred, vl_sld_fin, ind_dc_fin)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            "/tmp/x.txt", 999, cnpj,
            f"{ano}-01-01", f"{ano}-12-31", ano * 100 + 1, ano,
            "9.00", 0, cod_cta, "",
            0, "D", vl_deb, vl_cred, vl_deb - vl_cred, "D",
        ),
    )


# --------------------------------------------------------------------
# Disponibilidade
# --------------------------------------------------------------------

class TestDisponibilidade:
    def test_banco_inexistente(self, tmp_path):
        ctrl = ContabilController(
            cnpj="11111111111111", ano_calendario=2025,
            base_dir=tmp_path / "nada",
        )
        d = ctrl.disponibilidade()
        assert d.tem_ecd is False
        assert d.tem_j100 is False

    def test_banco_vazio(self, tmp_path):
        base = _criar_banco(tmp_path)
        ctrl = ContabilController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=base,
        )
        d = ctrl.disponibilidade()
        # Tabelas existem mas vazias
        assert d.tem_ecd is False

    def test_com_dados_ecd(self, tmp_path):
        base = _criar_banco(tmp_path)
        # Insere ECD 0000 mínimo
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            conn.execute(
                "INSERT INTO ecd_0000 (arquivo_origem, linha_arquivo,"
                " cnpj_declarante, dt_ini_periodo, dt_fin_periodo,"
                " ano_mes, ano_calendario, cod_ver, nome,"
                " uf, cod_mun, ind_fin_esc, ind_grande_porte,"
                " tip_ecd, ident_mf, ind_mudanc_pc, cod_plan_ref)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("/tmp/x", 1, "00000000000100", "2025-01-01", "2025-12-31",
                 202501, 2025, "9.00", "ACME",
                 "SP", "3550308", "0", "N",
                 "0", "S", "0", "1"),
            )
            conn.commit()
        finally:
            conn.close()
        ctrl = ContabilController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=base,
        )
        assert ctrl.disponibilidade().tem_ecd is True


# --------------------------------------------------------------------
# Balanço Patrimonial
# --------------------------------------------------------------------

class TestBalancoPatrimonial:
    def test_lista_linhas_estruturadas(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            _inserir_j005(conn, "00000000000100", 2025)
            _inserir_j100(conn, "00000000000100", 2025,
                "1", "1", "ATIVO", "1", "", "A",
                100000, "D", 150000, "D")
            _inserir_j100(conn, "00000000000100", 2025,
                "2", "1.1", "ATIVO CIRCULANTE", "2", "1", "A",
                50000, "D", 80000, "D")
            _inserir_j100(conn, "00000000000100", 2025,
                "10", "2", "PASSIVO + PL", "1", "", "P",
                100000, "C", 150000, "C")
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=base,
        )
        linhas = ctrl.listar_balanco_patrimonial()
        assert len(linhas) == 3
        assert linhas[0].cod_agl == "1"
        assert linhas[0].grupo == "A"
        # Ativo D = positivo
        assert linhas[0].vl_inicial_signed == Decimal("100000")
        # Passivo C = positivo
        assert linhas[2].grupo == "P"
        assert linhas[2].vl_final_signed == Decimal("150000")

    def test_banco_sem_j100_retorna_vazio(self, tmp_path):
        base = _criar_banco(tmp_path)
        ctrl = ContabilController(
            cnpj="00000000000100", ano_calendario=2025, base_dir=base,
        )
        assert ctrl.listar_balanco_patrimonial() == []


# --------------------------------------------------------------------
# Razão da conta
# --------------------------------------------------------------------

class TestRazao:
    def test_razao_traz_partidas_da_conta_com_contrapartida(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            cnpj, ano = "00000000000100", 2025
            _inserir_i050(conn, cnpj, ano, "5.1.01", "FORNECEDORES", "02", "A")
            _inserir_i050(conn, cnpj, ano, "3.1.01", "DESPESAS COMERCIAIS", "04", "A")
            # Lançamento: D Despesa, C Fornecedor (clássico)
            _inserir_i200(conn, cnpj, ano, 100, "0001", "2025-03-15", 5000)
            _inserir_i250(conn, cnpj, ano, 100, "3.1.01", 5000, "D", "Compra material")
            _inserir_i250(conn, cnpj, ano, 100, "5.1.01", 5000, "C", "Compra material")
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(cnpj="00000000000100", ano_calendario=2025, base_dir=base)
        razao = ctrl.listar_razao("3.1.01")
        assert len(razao) == 1
        assert razao[0].debito == Decimal("5000")
        assert razao[0].credito == Decimal("0")
        assert razao[0].contrapartida_cta == "5.1.01"
        assert "FORNECEDORES" in razao[0].contrapartida_descr

    def test_razao_filtra_por_periodo(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            cnpj, ano = "00000000000100", 2025
            _inserir_i200(conn, cnpj, ano, 100, "0001", "2025-03-15", 1000)
            _inserir_i250(conn, cnpj, ano, 100, "3.1.01", 1000, "D")
            # Fora de janela
            conn.execute(
                "UPDATE ecd_i250 SET ano_mes=202503 WHERE cod_cta='3.1.01'"
            )
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(cnpj="00000000000100", ano_calendario=2025, base_dir=base)
        # Filtro só fevereiro — sem resultado
        assert ctrl.listar_razao("3.1.01", ano_mes_ini=202502, ano_mes_fin=202502) == []
        # Filtro inclui março — vem
        assert len(ctrl.listar_razao("3.1.01", ano_mes_ini=202503, ano_mes_fin=202503)) == 1


# --------------------------------------------------------------------
# Despesas × Crédito PIS/COFINS
# --------------------------------------------------------------------

class TestDespesasVsCredito:
    def test_lista_despesas_com_e_sem_credito(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            cnpj, ano = "00000000000100", 2025
            # Despesa COM crédito (F100 com cod_cta correspondente)
            _inserir_i050(conn, cnpj, ano, "3.1.01", "ALUGUEL", "04", "A")
            _inserir_i155(conn, cnpj, ano, "3.1.01", 12000, 0)
            conn.execute(
                "INSERT INTO efd_contrib_f100"
                " (arquivo_origem, linha_arquivo, cnpj_declarante,"
                " dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario,"
                " cod_ver, ind_oper, cod_part, cod_item, dt_oper, vl_oper,"
                " cst_pis, vl_bc_pis, aliq_pis, vl_pis, cst_cofins,"
                " vl_bc_cofins, aliq_cofins, vl_cofins, nat_bc_cred,"
                " ind_orig_cred, cod_cta, cod_ccus, desc_doc_oper)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("/tmp/x", 1, cnpj, "2025-01-01", "2025-01-31",
                 202501, ano, "5.0.0", "1", "", "", "", 0,
                 "01", 12000, 1.65, 198, "01",
                 0, 0, 0, "01", "0", "3.1.01", "", ""),
            )
            # Despesa SEM crédito
            _inserir_i050(conn, cnpj, ano, "3.1.02", "FRETE NA VENDA", "04", "A")
            _inserir_i155(conn, cnpj, ano, "3.1.02", 8000, 0)
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(cnpj="00000000000100", ano_calendario=2025, base_dir=base)
        linhas = ctrl.listar_despesas_vs_credito()
        assert len(linhas) == 2

        aluguel = next(l for l in linhas if l.cod_cta == "3.1.01")
        assert aluguel.tem_credito is True
        assert aluguel.credito_pis_cofins == Decimal("12000")
        assert aluguel.saldo_periodo == Decimal("8000") or aluguel.saldo_periodo == Decimal("12000")

        frete = next(l for l in linhas if l.cod_cta == "3.1.02")
        assert frete.tem_credito is False
        assert frete.credito_pis_cofins == Decimal("0")

    def test_sem_despesas_no_plano_retorna_vazio(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            cnpj, ano = "00000000000100", 2025
            # Só conta de ativo, não de despesa
            _inserir_i050(conn, cnpj, ano, "1.1.01", "CAIXA", "01", "A")
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(cnpj="00000000000100", ano_calendario=2025, base_dir=base)
        assert ctrl.listar_despesas_vs_credito() == []


# --------------------------------------------------------------------
# Contas movimentadas (combo do razão)
# --------------------------------------------------------------------

class TestContasMovimentadas:
    def test_lista_distinct_de_cod_cta_no_i250(self, tmp_path):
        base = _criar_banco(tmp_path)
        conn = sqlite3.connect(base / "00000000000100" / "2025.sqlite")
        try:
            cnpj, ano = "00000000000100", 2025
            _inserir_i050(conn, cnpj, ano, "3.1.01", "DESPESAS")
            _inserir_i050(conn, cnpj, ano, "5.1.01", "FORNECEDORES", "02")
            _inserir_i200(conn, cnpj, ano, 100, "0001", "2025-03-15", 1000)
            _inserir_i250(conn, cnpj, ano, 100, "3.1.01", 1000, "D")
            _inserir_i250(conn, cnpj, ano, 100, "5.1.01", 1000, "C")
            _inserir_i250(conn, cnpj, ano, 100, "3.1.01", 500, "D")  # duplicada
            conn.commit()
        finally:
            conn.close()

        ctrl = ContabilController(cnpj="00000000000100", ano_calendario=2025, base_dir=base)
        contas = ctrl.listar_contas_movimentadas()
        codigos = [c[0] for c in contas]
        assert "3.1.01" in codigos
        assert "5.1.01" in codigos
        assert len(codigos) == len(set(codigos))  # sem duplicatas
