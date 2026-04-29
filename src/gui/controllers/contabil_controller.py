"""
ContabilController — análise contábil de um cliente × ano-calendário.

Quatro fluxos de leitura síncrona sobre o banco SQLite (sem QThread —
queries são rápidas, dados raramente passam de algumas centenas de
linhas; razão da conta pode ter milhares mas QTableView aguenta):

  1. listar_balanco_patrimonial(): hierarquia do J100 da ECD
     (Ativo / Passivo+PL com agrupadores via cod_agl/nivel_agl)
  2. listar_dre(): hierarquia do J150 da ECD
     (Receita Bruta → Lucro Líquido com ind_grp_dre)
  3. listar_razao(cod_cta, ano_mes_ini, ano_mes_fin): partidas do
     I250 filtradas por COD_CTA + janela temporal, joineadas com I200
     pra trazer data e número do lançamento. Contrapartida derivada
     das outras partidas do mesmo I200.
  4. listar_despesas_vs_credito(): contas de despesa do plano (I050
     com cod_nat='04') com saldo do I155 lado a lado com créditos
     PIS/COFINS tomados em F100/F120/F130/M105 (mesmo cod_cta).
     Diferencial pro Tema 779 — auditor identifica visualmente
     contas com despesa relevante e zero crédito.

Read-only — não muda nada no banco.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class LinhaBalanco:
    """Uma linha do Balanço Patrimonial (J100) ou DRE (J150)."""
    nu_ordem: str
    cod_agl: str             # código de aglutinação
    descricao: str
    nivel: int               # nivel_agl convertido para int
    cod_agl_sup: str
    grupo: str               # 'A'/'P' (BP) ou ind_grp_dre (DRE)
    vl_inicial: Decimal
    ind_dc_ini: str          # 'D' ou 'C'
    vl_final: Decimal
    ind_dc_fin: str
    ind_cod_agl: str = ""    # 'T' (sintética/total) ou 'D' (analítica) ou ''

    @property
    def vl_inicial_signed(self) -> Decimal:
        """Sinal contábil aplicado (Ativo + débito; Passivo+PL + crédito)."""
        return self._signed(self.vl_inicial, self.ind_dc_ini, self.grupo)

    @property
    def vl_final_signed(self) -> Decimal:
        return self._signed(self.vl_final, self.ind_dc_fin, self.grupo)

    @staticmethod
    def _signed(valor: Decimal, ind_dc: str, grupo: str) -> Decimal:
        """Aplica sinal contábil. Para Ativo (A): D=positivo, C=negativo.
        Para Passivo+PL (P): C=positivo, D=negativo. DRE segue mesma
        convenção do crédito-positivo (receita)."""
        if grupo == "A":
            return valor if ind_dc == "D" else -valor
        return valor if ind_dc == "C" else -valor


@dataclass
class LancamentoRazao:
    """Uma partida de I250 do razão da conta, com contexto do I200."""
    data: str                # YYYY-MM-DD
    num_lcto: str
    historico: str
    sub_conta: str           # cod_ccus — centro de custo / sub-conta
    debito: Decimal
    credito: Decimal
    contrapartida_cta: str   # cod_cta da outra perna do lançamento
    contrapartida_descr: str
    vl_lcto_total: Decimal   # valor total do I200 pai (rastreabilidade)
    arquivo: str
    linha_arquivo: int
    saldo_corrente: Decimal = Decimal("0")  # saldo após esta partida (D positivo)


@dataclass
class RazaoConta:
    """Razão completo de uma conta — header + lançamentos + totais."""
    cod_cta: str
    descricao: str
    saldo_inicial: Decimal           # vl_sld_ini do I155 mais antigo do AC
    ind_dc_inicial: str              # D ou C
    lancamentos: list[LancamentoRazao]
    total_debito: Decimal
    total_credito: Decimal
    saldo_final: Decimal
    ind_dc_final: str


@dataclass
class DespesaVsCredito:
    """Conta de despesa (cod_nat='04') × créditos PIS/COFINS no período."""
    cod_cta: str
    descricao: str
    saldo_periodo: Decimal           # SUM(vl_deb) do I155 no AC = despesa bruta incorrida
    credito_pis_cofins: Decimal      # F100+F120+F130 no mesmo cod_cta
    tem_credito: bool
    # Marcação subjetiva do auditor (Tema 779 essencialidade).
    # Persistida em contabil_oportunidades_essencialidade.
    marcada_oportunidade: bool = False
    nota_oportunidade: str = ""


@dataclass
class ImobilizadoVsCredito:
    """Conta de imobilizado (cod_nat='01' analítica relacionada a bens
    do ativo imobilizado) × créditos PIS/COFINS de F120 (depreciação)
    e F130 (aquisição) no período. Complementar à CR-23 (que pega
    apenas CST 98/99 em C170)."""
    cod_cta: str
    descricao: str
    saldo_periodo: Decimal           # SUM(vl_deb) do I155 no AC = aquisições/aumentos do ano
    credito_f120: Decimal            # base PIS de F120 (encargos depreciação)
    credito_f130: Decimal            # base PIS de F130 (aquisição imobilizado)
    tem_credito: bool                # F120 ou F130 com cod_cta match
    marcada_oportunidade: bool = False
    nota_oportunidade: str = ""


@dataclass
class EvidenciaCredito:
    """Linha individual de F100/F120/F130 que contribui para o crédito
    PIS/COFINS de uma conta — visa rastreabilidade absoluta (CLAUDE.md §1)."""
    arquivo: str            # caminho do SPED de origem
    linha_arquivo: int      # linha física no SPED
    registro: str           # 'F100', 'F120' ou 'F130'
    ano_mes: int            # YYYYMM da escrituração
    valor_base: Decimal     # vl_bc_pis ou vl_bc_cred
    nat_bc_cred: str        # natureza da base de crédito (NAT_BC_CRED)
    descricao: str          # descrição livre adicional


@dataclass
class ContabilDisponibilidade:
    """Indica o que está disponível para o cliente × AC."""
    tem_ecd: bool
    tem_j100: bool
    tem_j150: bool
    tem_i250: bool
    tem_efd_contribuicoes: bool


class ContabilController:
    """Read-only sobre o banco SQLite; um por cliente × AC."""

    def __init__(
        self,
        cnpj: str,
        ano_calendario: int,
        base_dir: Path = Path("data/db"),
    ) -> None:
        self._cnpj = cnpj
        self._ano = ano_calendario
        self._caminho = base_dir / cnpj / f"{ano_calendario}.sqlite"

    # ------------------------------------------------------------
    # Disponibilidade (informa T9 se há o que mostrar)
    # ------------------------------------------------------------

    def disponibilidade(self) -> ContabilDisponibilidade:
        if not self._caminho.exists():
            return ContabilDisponibilidade(False, False, False, False, False)
        conn = sqlite3.connect(self._caminho)
        try:
            return ContabilDisponibilidade(
                tem_ecd=self._tem_dados(conn, "ecd_0000"),
                tem_j100=self._tem_dados(conn, "ecd_j100"),
                tem_j150=self._tem_dados(conn, "ecd_j150"),
                tem_i250=self._tem_dados(conn, "ecd_i250"),
                tem_efd_contribuicoes=self._tem_dados(conn, "efd_contrib_0000"),
            )
        finally:
            conn.close()

    @staticmethod
    def _tem_dados(conn: sqlite3.Connection, tabela: str) -> bool:
        try:
            n = conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
            return n > 0
        except sqlite3.OperationalError:
            return False  # tabela inexistente = sem dado

    # ------------------------------------------------------------
    # Balanço Patrimonial (J100)
    # ------------------------------------------------------------

    def listar_balanco_patrimonial(self) -> list[LinhaBalanco]:
        """BP do exercício: J100 do ÚLTIMO período de demonstração (J005
        com maior dt_fin). ECDs trimestrais têm 4 J100 (1Q, 2Q, 3Q, 4Q);
        o que importa para o BP anual é o saldo de fechamento do exercício,
        que está no J100 do trimestre final."""
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            try:
                # Identifica o J005 com dt_fin mais tardia (= período final)
                row = conn.execute(
                    "SELECT linha_arquivo FROM ecd_j005"
                    " WHERE cnpj_declarante=? AND ano_calendario=?"
                    " ORDER BY dt_fin_dem DESC, linha_arquivo DESC LIMIT 1",
                    (self._cnpj, self._ano),
                ).fetchone()
                if row is None:
                    return []
                j005_alvo = row[0]
                cur = conn.execute(
                    "SELECT nu_ordem, cod_agl, descr_cod_agl, nivel_agl,"
                    " cod_agl_sup, ind_grp_bal,"
                    " vl_cta_ini, ind_dc_ini, vl_cta_fin, ind_dc_fin,"
                    " ind_cod_agl"
                    " FROM ecd_j100"
                    " WHERE cnpj_declarante=? AND ano_calendario=?"
                    "   AND j005_linha_arquivo=?"
                    " ORDER BY linha_arquivo",
                    (self._cnpj, self._ano, j005_alvo),
                )
            except sqlite3.OperationalError:
                return []
            return [self._linha_balanco(r, modo="bp") for r in cur]
        finally:
            conn.close()

    # ------------------------------------------------------------
    # DRE (J150)
    # ------------------------------------------------------------

    def listar_dre(self) -> list[LinhaBalanco]:
        """DRE do exercício: soma de vl_cta_ini de J150 dos N períodos
        de demonstração (trimestres) por cod_agl. Necessário porque
        ECDs trimestrais emitem 4 J150 não-cumulativos — o anual é a soma."""
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            try:
                # Quantos J005 existem? Se for 1, retorna direto. Se >1, agrega.
                n_j005 = conn.execute(
                    "SELECT COUNT(*) FROM ecd_j005"
                    " WHERE cnpj_declarante=? AND ano_calendario=?",
                    (self._cnpj, self._ano),
                ).fetchone()[0]
                if n_j005 <= 1:
                    cur = conn.execute(
                        "SELECT nu_ordem, cod_agl, descr_cod_agl, nivel_agl,"
                        " cod_agl_sup, ind_grp_dre,"
                        " vl_cta_ini, ind_dc_ini, vl_cta_fin, ind_dc_fin,"
                        " ind_cod_agl"
                        " FROM ecd_j150"
                        " WHERE cnpj_declarante=? AND ano_calendario=?"
                        " ORDER BY linha_arquivo",
                        (self._cnpj, self._ano),
                    )
                    return [self._linha_balanco(r, modo="dre") for r in cur]

                # Agrega múltiplos J150 por cod_agl somando o valor (vl_cta_ini)
                # com sinal contábil correto (C positivo, D negativo).
                # Mantém a primeira ocorrência da estrutura (descr, nível, etc.).
                cur = conn.execute(
                    "SELECT nu_ordem, cod_agl, descr_cod_agl, nivel_agl,"
                    " cod_agl_sup, ind_grp_dre,"
                    " vl_cta_ini, ind_dc_ini, ind_cod_agl, j005_linha_arquivo"
                    " FROM ecd_j150"
                    " WHERE cnpj_declarante=? AND ano_calendario=?"
                    " ORDER BY j005_linha_arquivo, linha_arquivo",
                    (self._cnpj, self._ano),
                )
                acumulado: dict[str, dict] = {}
                ordem: list[str] = []
                for r in cur:
                    cod_agl = r[1] or ""
                    valor = Decimal(str(r[6] or 0))
                    sinal = 1 if (r[7] or "C") == "C" else -1
                    val_signed = valor * sinal
                    if cod_agl not in acumulado:
                        acumulado[cod_agl] = {
                            "nu_ordem": r[0] or "",
                            "cod_agl": cod_agl,
                            "descr": r[2] or "",
                            "nivel": r[3] or "",
                            "cod_agl_sup": r[4] or "",
                            "grupo": r[5] or "",
                            "soma": Decimal("0"),
                            "ind_cod_agl": r[8] or "",
                        }
                        ordem.append(cod_agl)
                    acumulado[cod_agl]["soma"] += val_signed

                resultado: list[LinhaBalanco] = []
                for cod in ordem:
                    a = acumulado[cod]
                    soma = a["soma"]
                    ind_dc = "C" if soma >= 0 else "D"
                    valor_abs = abs(soma)
                    nivel = 0
                    try:
                        nivel = int(a["nivel"] or 0)
                    except (TypeError, ValueError):
                        pass
                    resultado.append(LinhaBalanco(
                        nu_ordem=a["nu_ordem"],
                        cod_agl=a["cod_agl"],
                        descricao=a["descr"],
                        nivel=nivel,
                        cod_agl_sup=a["cod_agl_sup"],
                        grupo=a["grupo"],
                        vl_inicial=valor_abs,
                        ind_dc_ini=ind_dc,
                        vl_final=valor_abs,
                        ind_dc_fin=ind_dc,
                        ind_cod_agl=a["ind_cod_agl"],
                    ))
                return resultado
            except sqlite3.OperationalError:
                return []
        finally:
            conn.close()

    @staticmethod
    def _linha_balanco(row: tuple, *, modo: str) -> LinhaBalanco:
        """row = (nu_ordem, cod_agl, descr_cod_agl, nivel_agl, cod_agl_sup,
                  grupo, vl_cta_ini, ind_dc_ini, vl_cta_fin, ind_dc_fin,
                  ind_cod_agl)"""
        nivel = 0
        try:
            nivel = int(row[3] or 0)
        except (TypeError, ValueError):
            nivel = 0
        return LinhaBalanco(
            nu_ordem=row[0] or "",
            cod_agl=row[1] or "",
            descricao=row[2] or "",
            nivel=nivel,
            cod_agl_sup=row[4] or "",
            grupo=row[5] or "",
            vl_inicial=Decimal(str(row[6] or 0)),
            ind_dc_ini=row[7] or "",
            vl_final=Decimal(str(row[8] or 0)),
            ind_dc_fin=row[9] or "",
            ind_cod_agl=(row[10] if len(row) > 10 else "") or "",
        )

    # ------------------------------------------------------------
    # Razão da conta (I250 + I200)
    # ------------------------------------------------------------

    def listar_contas_movimentadas(self) -> list[tuple[str, str]]:
        """Lista [(cod_cta, descrição)] das contas com lançamentos no AC.
        Usado pra alimentar combo da aba Razão.
        """
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            try:
                cur = conn.execute(
                    "SELECT DISTINCT i250.cod_cta, COALESCE(i050.cta, '')"
                    " FROM ecd_i250 AS i250"
                    " LEFT JOIN ecd_i050 AS i050"
                    "   ON i050.cnpj_declarante = i250.cnpj_declarante"
                    "   AND i050.cod_cta = i250.cod_cta"
                    " WHERE i250.cnpj_declarante=? AND i250.ano_calendario=?"
                    " ORDER BY i250.cod_cta",
                    (self._cnpj, self._ano),
                )
                return [(r[0], r[1]) for r in cur]
            except sqlite3.OperationalError:
                return []
        finally:
            conn.close()

    def listar_razao(
        self,
        cod_cta: str,
        ano_mes_ini: int | None = None,
        ano_mes_fin: int | None = None,
    ) -> list[LancamentoRazao]:
        """Partidas do I250 da conta dada, joineadas com I200 pai.
        Período opcional via ano_mes_ini/fin (formato YYYYMM).
        Saldo corrente NÃO é preenchido aqui — use consultar_razao_completo."""
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            return self._listar_razao_interno(
                conn, cod_cta, ano_mes_ini, ano_mes_fin,
            )
        finally:
            conn.close()

    def consultar_razao_completo(
        self,
        cod_cta: str,
        ano_mes_ini: int | None = None,
        ano_mes_fin: int | None = None,
    ) -> RazaoConta | None:
        """Razão completo da conta com saldo inicial, lançamentos com saldo
        corrente, e totais de débito/crédito + saldo final.
        Retorna None se a conta não existe ou não tem movimentação."""
        if not self._caminho.exists():
            return None
        conn = sqlite3.connect(self._caminho)
        try:
            descricao = self._descricao_conta(conn, cod_cta)
            saldo_ini, dc_ini = self._saldo_inicial(conn, cod_cta)
            lancamentos = self._listar_razao_interno(
                conn, cod_cta, ano_mes_ini, ano_mes_fin,
            )
        finally:
            conn.close()

        # Computa saldo corrente cronológico (D positivo, C negativo).
        # Convenção: saldo positivo = devedor (D), negativo = credor (C).
        saldo = saldo_ini if dc_ini == "D" else -saldo_ini
        total_d = Decimal("0")
        total_c = Decimal("0")
        for l in lancamentos:
            saldo += l.debito - l.credito
            total_d += l.debito
            total_c += l.credito
            l.saldo_corrente = saldo

        saldo_final_abs = abs(saldo)
        ind_final = "D" if saldo >= 0 else "C"

        return RazaoConta(
            cod_cta=cod_cta,
            descricao=descricao,
            saldo_inicial=saldo_ini,
            ind_dc_inicial=dc_ini,
            lancamentos=lancamentos,
            total_debito=total_d,
            total_credito=total_c,
            saldo_final=saldo_final_abs,
            ind_dc_final=ind_final,
        )

    def _listar_razao_interno(
        self,
        conn: sqlite3.Connection,
        cod_cta: str,
        ano_mes_ini: int | None,
        ano_mes_fin: int | None,
    ) -> list[LancamentoRazao]:
        params: list = [self._cnpj, self._ano, cod_cta]
        sql = (
            "SELECT i200.dt_lcto, i200.num_lcto, i200.vl_lcto,"
            " i250.vl_deb_cred, i250.ind_dc, i250.hist_lcto_ccus,"
            " i250.cod_ccus,"
            " i250.linha_arquivo, i250.arquivo_origem,"
            " i250.i200_linha_arquivo, i250.cod_cta"
            " FROM ecd_i250 AS i250"
            " LEFT JOIN ecd_i200 AS i200"
            "   ON i200.cnpj_declarante = i250.cnpj_declarante"
            "   AND i200.linha_arquivo = i250.i200_linha_arquivo"
            " WHERE i250.cnpj_declarante=? AND i250.ano_calendario=?"
            "   AND i250.cod_cta=?"
        )
        if ano_mes_ini is not None:
            sql += " AND i250.ano_mes >= ?"
            params.append(ano_mes_ini)
        if ano_mes_fin is not None:
            sql += " AND i250.ano_mes <= ?"
            params.append(ano_mes_fin)
        sql += " ORDER BY i200.dt_lcto, i200.num_lcto, i250.linha_arquivo"

        try:
            rows = list(conn.execute(sql, params))
        except sqlite3.OperationalError:
            return []

        resultado: list[LancamentoRazao] = []
        for r in rows:
            contrapartida_cta, contrapartida_descr = (
                self._buscar_contrapartida(conn, r[9], cod_cta)
            )
            debito = Decimal(str(r[3] or 0)) if (r[4] or "") == "D" else Decimal("0")
            credito = Decimal(str(r[3] or 0)) if (r[4] or "") == "C" else Decimal("0")
            resultado.append(LancamentoRazao(
                data=r[0] or "",
                num_lcto=r[1] or "",
                historico=r[5] or "",
                sub_conta=r[6] or "",
                debito=debito,
                credito=credito,
                contrapartida_cta=contrapartida_cta,
                contrapartida_descr=contrapartida_descr,
                vl_lcto_total=Decimal(str(r[2] or 0)),
                arquivo=r[8] or "",
                linha_arquivo=int(r[7] or 0),
            ))
        return resultado

    def _descricao_conta(
        self, conn: sqlite3.Connection, cod_cta: str,
    ) -> str:
        try:
            row = conn.execute(
                "SELECT cta FROM ecd_i050"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?"
                " ORDER BY linha_arquivo LIMIT 1",
                (self._cnpj, self._ano, cod_cta),
            ).fetchone()
            return (row[0] if row else "") or ""
        except sqlite3.OperationalError:
            return ""

    def _saldo_inicial(
        self, conn: sqlite3.Connection, cod_cta: str,
    ) -> tuple[Decimal, str]:
        """Saldo inicial da conta no AC — pega vl_sld_ini do I155 do
        primeiro mês com movimento."""
        try:
            row = conn.execute(
                "SELECT vl_sld_ini, ind_dc_ini FROM ecd_i155"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?"
                " ORDER BY ano_mes, linha_arquivo LIMIT 1",
                (self._cnpj, self._ano, cod_cta),
            ).fetchone()
        except sqlite3.OperationalError:
            return Decimal("0"), "D"
        if not row:
            return Decimal("0"), "D"
        return Decimal(str(row[0] or 0)), (row[1] or "D")

    def _buscar_contrapartida(
        self, conn: sqlite3.Connection,
        i200_linha_arquivo: int, cod_cta_atual: str,
    ) -> tuple[str, str]:
        """Retorna (cod_cta, descrição) da primeira contrapartida do I200.
        Se houver múltiplas, indica '+ N outras'."""
        try:
            cur = conn.execute(
                "SELECT i250.cod_cta, COALESCE(i050.cta, '')"
                " FROM ecd_i250 AS i250"
                " LEFT JOIN ecd_i050 AS i050"
                "   ON i050.cnpj_declarante = i250.cnpj_declarante"
                "   AND i050.cod_cta = i250.cod_cta"
                " WHERE i250.cnpj_declarante=?"
                "   AND i250.i200_linha_arquivo=?"
                "   AND i250.cod_cta != ?"
                " ORDER BY i250.linha_arquivo",
                (self._cnpj, i200_linha_arquivo, cod_cta_atual),
            )
            outras = list(cur)
        except sqlite3.OperationalError:
            return "", ""
        if not outras:
            return "", ""
        cod, desc = outras[0]
        if len(outras) > 1:
            sufixo = f"  (+{len(outras) - 1} outra{'s' if len(outras) > 2 else ''})"
            desc = (desc or "") + sufixo
        return cod or "", desc or ""

    # ------------------------------------------------------------
    # Despesas × Crédito PIS/COFINS — diferencial Tema 779
    # ------------------------------------------------------------

    def listar_despesas_vs_credito(self) -> list[DespesaVsCredito]:
        """Para cada conta de despesa (cod_nat='04') do plano:
          - saldo no AC = soma de vl_deb - vl_cred do I155
          - crédito PIS/COFINS = soma de F100/F120/F130/M105 com mesmo cod_cta
          - marcada_oportunidade = se está em contabil_oportunidades_essencialidade
        Auditor filtra por "sem crédito" pra identificar candidatas Tema 779.
        """
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            # Contas de despesa do plano
            try:
                cur = conn.execute(
                    "SELECT cod_cta, cta FROM ecd_i050"
                    " WHERE cnpj_declarante=? AND ano_calendario=?"
                    "   AND cod_nat='04' AND ind_cta='A'"
                    " ORDER BY cod_cta",
                    (self._cnpj, self._ano),
                )
                contas = [(r[0], r[1] or "") for r in cur]
            except sqlite3.OperationalError:
                return []

            marcadas = self._marcadas_set(conn)

            resultado: list[DespesaVsCredito] = []
            for cod_cta, descricao in contas:
                saldo = self._total_debito_anual(conn, cod_cta)
                credito = self._credito_pis_cofins_por_cta(conn, cod_cta)
                marcada, nota = marcadas.get(cod_cta, (False, ""))
                resultado.append(DespesaVsCredito(
                    cod_cta=cod_cta,
                    descricao=descricao,
                    saldo_periodo=saldo,
                    credito_pis_cofins=credito,
                    tem_credito=credito > 0,
                    marcada_oportunidade=marcada,
                    nota_oportunidade=nota,
                ))
            return resultado
        finally:
            conn.close()

    # ------------------------------------------------------------
    # Imobilizado × Crédito PIS/COFINS — complementar à CR-23
    # ------------------------------------------------------------

    def listar_imobilizado_vs_credito(self) -> list[ImobilizadoVsCredito]:
        """Lista contas analíticas do plano que aparentam ser imobilizado
        e cruza com F120/F130 da EFD-Contribuições. Heurística: cod_nat='01'
        (Ativo) + descrição contém palavras-chave de imobilizado, OU é
        descendente de conta com 'IMOBILIZ' no nome.

        Base legal: Art. 3º, VI da Lei 10.637/2002 (PIS) e 10.833/2003
        (COFINS) — créditos de PIS/COFINS sobre bens do ativo imobilizado
        adquiridos para uso na produção / locação a terceiros, via:
          - F120: encargos de depreciação
          - F130: valor de aquisição (apropriação direta — opção)
        """
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        try:
            try:
                # Contas analíticas de Ativo cuja descrição (própria ou
                # ascendente direto) contenha palavra-chave de imobilizado.
                cur = conn.execute(
                    "SELECT DISTINCT i.cod_cta, i.cta"
                    " FROM ecd_i050 i"
                    " LEFT JOIN ecd_i050 sup"
                    "   ON sup.cnpj_declarante = i.cnpj_declarante"
                    "   AND sup.ano_calendario = i.ano_calendario"
                    "   AND sup.cod_cta = i.cod_cta_sup"
                    " WHERE i.cnpj_declarante=? AND i.ano_calendario=?"
                    "   AND i.cod_nat='01' AND i.ind_cta='A'"
                    "   AND ("
                    "        LOWER(i.cta) LIKE '%imobiliz%'"
                    "     OR LOWER(i.cta) LIKE '%maquin%'"
                    "     OR LOWER(i.cta) LIKE '%equipament%'"
                    "     OR LOWER(i.cta) LIKE '%veicul%'"
                    "     OR LOWER(i.cta) LIKE '%movel%'"
                    "     OR LOWER(i.cta) LIKE '%utensil%'"
                    "     OR LOWER(i.cta) LIKE '%instalac%'"
                    "     OR LOWER(i.cta) LIKE '%computad%'"
                    "     OR LOWER(i.cta) LIKE '%edifica%'"
                    "     OR LOWER(i.cta) LIKE '%predio%'"
                    "     OR LOWER(i.cta) LIKE '%terreno%'"
                    "     OR LOWER(i.cta) LIKE '%benfeitor%'"
                    "     OR LOWER(COALESCE(sup.cta,'')) LIKE '%imobiliz%'"
                    "   )"
                    " ORDER BY i.cod_cta",
                    (self._cnpj, self._ano),
                )
                contas = [(r[0], r[1] or "") for r in cur]
            except sqlite3.OperationalError:
                return []

            marcadas = self._marcadas_set(conn)

            resultado: list[ImobilizadoVsCredito] = []
            for cod_cta, descricao in contas:
                saldo = self._total_debito_anual(conn, cod_cta)
                f120 = self._credito_de_tabela(conn, cod_cta, "efd_contrib_f120", "vl_bc_cred")
                f130 = self._credito_de_tabela(conn, cod_cta, "efd_contrib_f130", "vl_bc_cred")
                marcada, nota = marcadas.get(cod_cta, (False, ""))
                resultado.append(ImobilizadoVsCredito(
                    cod_cta=cod_cta,
                    descricao=descricao,
                    saldo_periodo=saldo,
                    credito_f120=f120,
                    credito_f130=f130,
                    tem_credito=(f120 + f130) > 0,
                    marcada_oportunidade=marcada,
                    nota_oportunidade=nota,
                ))
            return resultado
        finally:
            conn.close()

    def _credito_de_tabela(
        self, conn: sqlite3.Connection, cod_cta: str,
        tabela: str, coluna: str,
    ) -> Decimal:
        try:
            row = conn.execute(
                f"SELECT COALESCE(SUM({coluna}), 0) FROM {tabela}"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?",
                (self._cnpj, self._ano, cod_cta),
            ).fetchone()
            return Decimal(str(row[0] or 0))
        except sqlite3.OperationalError:
            return Decimal("0")

    # ------------------------------------------------------------
    # Oportunidades de essencialidade (Tema 779)
    # ------------------------------------------------------------

    def marcar_oportunidade(
        self, cod_cta: str, *, marcado_por: str = "", nota: str = "",
    ) -> bool:
        """Persiste a marcação dessa conta como candidata a crédito sob
        essencialidade. UPSERT — se já existe, atualiza nota."""
        from datetime import datetime, timezone
        if not self._caminho.exists():
            return False
        conn = sqlite3.connect(self._caminho)
        try:
            self._garantir_tabela(conn)
            now = datetime.now(tz=timezone.utc).isoformat()
            try:
                conn.execute(
                    """INSERT INTO contabil_oportunidades_essencialidade
                       (cnpj_declarante, ano_calendario, cod_cta,
                        marcado_em, marcado_por, nota)
                       VALUES (?,?,?,?,?,?)
                       ON CONFLICT(cnpj_declarante, ano_calendario, cod_cta)
                       DO UPDATE SET nota=excluded.nota,
                                     marcado_em=excluded.marcado_em,
                                     marcado_por=excluded.marcado_por""",
                    (self._cnpj, self._ano, cod_cta, now, marcado_por, nota),
                )
                conn.commit()
                return True
            except sqlite3.OperationalError:
                return False
        finally:
            conn.close()

    def desmarcar_oportunidade(self, cod_cta: str) -> bool:
        if not self._caminho.exists():
            return False
        conn = sqlite3.connect(self._caminho)
        try:
            try:
                conn.execute(
                    "DELETE FROM contabil_oportunidades_essencialidade"
                    " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?",
                    (self._cnpj, self._ano, cod_cta),
                )
                conn.commit()
                return True
            except sqlite3.OperationalError:
                return False
        finally:
            conn.close()

    def _marcadas_set(self, conn: sqlite3.Connection) -> dict:
        """Retorna {cod_cta: (True, nota)} pra contas já marcadas."""
        try:
            cur = conn.execute(
                "SELECT cod_cta, COALESCE(nota, '') FROM"
                " contabil_oportunidades_essencialidade"
                " WHERE cnpj_declarante=? AND ano_calendario=?",
                (self._cnpj, self._ano),
            )
            return {r[0]: (True, r[1]) for r in cur}
        except sqlite3.OperationalError:
            return {}

    def _garantir_tabela(self, conn: sqlite3.Connection) -> None:
        """Cria a tabela se não existe (banco antigo sem migração)."""
        conn.execute(
            """CREATE TABLE IF NOT EXISTS contabil_oportunidades_essencialidade (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cnpj_declarante TEXT NOT NULL,
                ano_calendario INTEGER NOT NULL,
                cod_cta TEXT NOT NULL,
                marcado_em TEXT NOT NULL,
                marcado_por TEXT,
                nota TEXT,
                UNIQUE(cnpj_declarante, ano_calendario, cod_cta)
            )"""
        )

    def _total_debito_anual(
        self, conn: sqlite3.Connection, cod_cta: str,
    ) -> Decimal:
        """Total debitado em uma conta de resultado/imobilizado no AC.

        Para conta de despesa (cod_nat='04'): representa a despesa bruta
        incorrida no ano. Em escrituração com apuração trimestral, a
        conta é zerada via crédito ao final de cada trimestre (transferência
        ao resultado), então SUM(vl_deb)-SUM(vl_cred)=0 — fórmula errada.
        SUM(vl_deb) isolado dá a despesa real, base correta para
        diagnóstico Tema 779 (REsp 1.221.170/PR — essencialidade).

        Para conta de imobilizado (cod_nat='01'): representa as aquisições
        e aumentos do ano. Coerente com cruzamento contra F130 (base de
        crédito sobre aquisição de imobilizado).

        Bug-003 — solução conservadora (Opção i). Refinamentos pendentes:
        (ii) distinguir transferência de apuração vs estorno legítimo;
        (iii) computar via I250 excluindo contrapartidas de apuração.
        Ver docs/debitos-conhecidos.md.
        """
        try:
            row = conn.execute(
                "SELECT COALESCE(SUM(vl_deb), 0)"
                " FROM ecd_i155"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?",
                (self._cnpj, self._ano, cod_cta),
            ).fetchone()
        except sqlite3.OperationalError:
            return Decimal("0")
        if row is None or row[0] is None:
            return Decimal("0")
        return Decimal(str(row[0]))

    def _credito_pis_cofins_por_cta(
        self, conn: sqlite3.Connection, cod_cta: str,
    ) -> Decimal:
        """Soma de bases de crédito PIS/COFINS associadas a um cod_cta
        em F100, F120, F130. Zero se a tabela não existir ou cod_cta
        não houver match."""
        total = Decimal("0")
        for tabela, coluna in (
            ("efd_contrib_f100", "vl_bc_pis"),
            ("efd_contrib_f120", "vl_bc_cred"),
            ("efd_contrib_f130", "vl_bc_cred"),
        ):
            try:
                row = conn.execute(
                    f"SELECT COALESCE(SUM({coluna}), 0) FROM {tabela}"
                    " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?",
                    (self._cnpj, self._ano, cod_cta),
                ).fetchone()
                total += Decimal(str(row[0] or 0))
            except sqlite3.OperationalError:
                continue
        return total

    # ------------------------------------------------------------
    # Rastreabilidade — evidências por trás do crédito PIS/COFINS
    # ------------------------------------------------------------

    def listar_evidencias_credito(self, cod_cta: str) -> list[EvidenciaCredito]:
        """Lista as linhas individuais de F100/F120/F130 que contribuíram
        para o crédito PIS/COFINS dessa conta no AC. Cada evidência traz
        arquivo, linha física, registro, valor — rastreabilidade fiscal
        absoluta (CLAUDE.md §1, princípio 1)."""
        if not self._caminho.exists():
            return []
        conn = sqlite3.connect(self._caminho)
        evidencias: list[EvidenciaCredito] = []
        try:
            self._coletar_evidencias_f100(conn, cod_cta, evidencias)
            self._coletar_evidencias_f120(conn, cod_cta, evidencias)
            self._coletar_evidencias_f130(conn, cod_cta, evidencias)
        finally:
            conn.close()
        evidencias.sort(key=lambda e: (e.ano_mes, e.registro, e.linha_arquivo))
        return evidencias

    def _coletar_evidencias_f100(
        self, conn: sqlite3.Connection, cod_cta: str,
        out: list[EvidenciaCredito],
    ) -> None:
        try:
            cur = conn.execute(
                "SELECT arquivo_origem, linha_arquivo, ano_mes,"
                " vl_bc_pis, nat_bc_cred, COALESCE(desc_doc_oper, '')"
                " FROM efd_contrib_f100"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?"
                " ORDER BY ano_mes, linha_arquivo",
                (self._cnpj, self._ano, cod_cta),
            )
            for r in cur:
                out.append(EvidenciaCredito(
                    arquivo=r[0] or "", linha_arquivo=int(r[1] or 0),
                    registro="F100", ano_mes=int(r[2] or 0),
                    valor_base=Decimal(str(r[3] or 0)),
                    nat_bc_cred=r[4] or "",
                    descricao=r[5] or "",
                ))
        except sqlite3.OperationalError:
            return

    def _coletar_evidencias_f120(
        self, conn: sqlite3.Connection, cod_cta: str,
        out: list[EvidenciaCredito],
    ) -> None:
        try:
            cur = conn.execute(
                "SELECT arquivo_origem, linha_arquivo, ano_mes,"
                " vl_bc_cred, nat_bc_cred"
                " FROM efd_contrib_f120"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?"
                " ORDER BY ano_mes, linha_arquivo",
                (self._cnpj, self._ano, cod_cta),
            )
            for r in cur:
                out.append(EvidenciaCredito(
                    arquivo=r[0] or "", linha_arquivo=int(r[1] or 0),
                    registro="F120", ano_mes=int(r[2] or 0),
                    valor_base=Decimal(str(r[3] or 0)),
                    nat_bc_cred=r[4] or "",
                    descricao="Crédito sobre encargos de depreciação",
                ))
        except sqlite3.OperationalError:
            return

    def _coletar_evidencias_f130(
        self, conn: sqlite3.Connection, cod_cta: str,
        out: list[EvidenciaCredito],
    ) -> None:
        try:
            cur = conn.execute(
                "SELECT arquivo_origem, linha_arquivo, ano_mes,"
                " vl_bc_cred, nat_bc_cred"
                " FROM efd_contrib_f130"
                " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta=?"
                " ORDER BY ano_mes, linha_arquivo",
                (self._cnpj, self._ano, cod_cta),
            )
            for r in cur:
                out.append(EvidenciaCredito(
                    arquivo=r[0] or "", linha_arquivo=int(r[1] or 0),
                    registro="F130", ano_mes=int(r[2] or 0),
                    valor_base=Decimal(str(r[3] or 0)),
                    nat_bc_cred=r[4] or "",
                    descricao="Crédito sobre aquisição de imobilizado",
                ))
        except sqlite3.OperationalError:
            return
