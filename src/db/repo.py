"""
Repositório SQLite — acesso abstrato por CNPJ × ano-calendário.
Caminho canônico: data/db/{cnpj}/{ano_calendario}.sqlite
"""

import json
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from src.models.registros import (
    Divergencia,
    Oportunidade,
    Reg0000,
    Reg0110,
    Reg0111,
    Reg0200,
    Reg9900,
    Reg1100,
    Reg1500,
    RegC100,
    RegC170,
    RegC181,
    RegC185,
    RegD201,
    RegD205,
    RegF100,
    RegF120,
    RegF130,
    RegF150,
    RegF600,
    RegF700,
    RegF800,
    RegM100,
    RegM105,
    RegM200,
    RegM210,
    RegM215,
    RegM500,
    RegM505,
    RegM600,
    RegM610,
    RegM615,
    RegIcms0000,
    RegIcmsC100,
    RegIcmsC170,
    RegIcmsG110,
    RegIcmsG125,
    RegIcmsH005,
    RegIcmsH010,
    RegEcd0000,
    RegEcdC050,
    RegEcdC155,
    RegEcdI010,
    RegEcdI050,
    RegEcdI150,
    RegEcdI155,
    RegEcdI200,
    RegEcdI250,
    RegEcdJ005,
    RegEcdJ100,
    RegEcdJ150,
    RegEcf0000,
    RegEcf0010,
    RegEcfK155,
    RegEcfK355,
    RegEcfM300,
    RegEcfM312,
    RegEcfM350,
    RegEcfM362,
    RegEcfM500,
    RegEcfX460,
    RegEcfX480,
    RegEcfY570,
    RegEcf9100,
)

_SCHEMA = Path(__file__).parent / "schema.sql"
_BASE_DATA = Path("data/db")

# Migrações aditivas idempotentes — aplicadas após o schema base.
# Usadas para bancos criados em versões anteriores do projeto.
# Cada SQL é tentado isoladamente; "duplicate column name" é ignorado.
_MIGRATIONS_ADITIVAS: list[str] = [
    # Decisão #12 — revisão por-linha persistida (GUI Sprint).
    "ALTER TABLE crossref_oportunidades ADD COLUMN revisado_em TEXT",
    "ALTER TABLE crossref_oportunidades ADD COLUMN revisado_por TEXT",
    "ALTER TABLE crossref_oportunidades ADD COLUMN nota TEXT",
    "ALTER TABLE crossref_divergencias ADD COLUMN revisado_em TEXT",
    "ALTER TABLE crossref_divergencias ADD COLUMN revisado_por TEXT",
    "ALTER TABLE crossref_divergencias ADD COLUMN nota TEXT",
]


def _caminho_banco(cnpj: str, ano_calendario: int, base_dir: Path | None = None) -> Path:
    base = base_dir if base_dir is not None else _BASE_DATA
    return base / cnpj / f"{ano_calendario}.sqlite"


def _agora() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


# Mapa: sped_tipo → (chave_periodo, lista de tabelas filhas).
# Usado por Repositorio.deletar_dados_anteriores (Bug-002 fix) para
# garantir dedup ao reimportar SPED. Tabelas de controle e anotação
# (_importacoes, _sped_contexto, reconciliacao_override,
# contabil_oportunidades_essencialidade, crossref_*) NÃO entram aqui —
# são preservadas por design.
_TABELAS_POR_SPED_TIPO: dict[str, tuple[str, list[str]]] = {
    "efd_contribuicoes": ("ano_mes", [
        "efd_contrib_0000", "efd_contrib_0110", "efd_contrib_0111",
        "efd_contrib_0200", "efd_contrib_c100", "efd_contrib_c170",
        "efd_contrib_c181", "efd_contrib_c185", "efd_contrib_d201",
        "efd_contrib_d205", "efd_contrib_f100", "efd_contrib_f120",
        "efd_contrib_f130", "efd_contrib_f150", "efd_contrib_f600",
        "efd_contrib_f700", "efd_contrib_f800", "efd_contrib_m100",
        "efd_contrib_m105", "efd_contrib_m200", "efd_contrib_m210",
        "efd_contrib_m215", "efd_contrib_m500", "efd_contrib_m505",
        "efd_contrib_m600", "efd_contrib_m610", "efd_contrib_m615",
        "efd_contrib_1100", "efd_contrib_1500", "efd_contrib_9900",
    ]),
    "efd_icms": ("ano_mes", [
        "efd_icms_0000", "efd_icms_c100", "efd_icms_c170",
        "efd_icms_g110", "efd_icms_g125", "efd_icms_h005", "efd_icms_h010",
    ]),
    "ecd": ("ano_calendario", [
        "ecd_0000", "ecd_i010", "ecd_c050", "ecd_c155",
        "ecd_i050", "ecd_i150", "ecd_i155", "ecd_i200", "ecd_i250",
        "ecd_j005", "ecd_j100", "ecd_j150",
    ]),
    "ecf": ("ano_calendario", [
        "ecf_0000", "ecf_0010", "ecf_k155", "ecf_k355",
        "ecf_m300", "ecf_m312", "ecf_m350", "ecf_m362", "ecf_m500",
        "ecf_x460", "ecf_x480", "ecf_9100", "ecf_y570",
    ]),
}


class Repositorio:
    def __init__(self, cnpj: str, ano_calendario: int, base_dir: Path | None = None):
        self.cnpj = cnpj
        self.ano_calendario = ano_calendario
        self.caminho = _caminho_banco(cnpj, ano_calendario, base_dir)

    def criar_banco(self) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        schema = _SCHEMA.read_text(encoding="utf-8")
        conn = sqlite3.connect(self.caminho)
        try:
            conn.executescript(schema)
            self._aplicar_migrations(conn)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _aplicar_migrations(conn: sqlite3.Connection) -> None:
        """Aplica migrações aditivas idempotentes para bancos pré-existentes.

        SQLite aceita ALTER TABLE ADD COLUMN sem afetar dados. Erros de
        coluna duplicada são silenciados — significa que a migration já
        foi aplicada. Outros erros propagam.
        """
        for sql in _MIGRATIONS_ADITIVAS:
            try:
                conn.execute(sql)
            except sqlite3.OperationalError as exc:
                if "duplicate column name" in str(exc).lower():
                    continue  # já aplicada
                raise

    def conexao(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.caminho)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------
    # Controle de importações e contexto
    # ------------------------------------------------------------------

    def registrar_importacao(
        self,
        conn: sqlite3.Connection,
        sped_tipo: str,
        dt_ini: str,
        dt_fin: str,
        ano_mes: int,
        arquivo_hash: str,
        arquivo_origem: str,
        cod_ver: str,
        encoding_origem: str,
        encoding_confianca: str,
        status: str,
    ) -> int:
        cur = conn.execute(
            """INSERT INTO _importacoes
               (sped_tipo, dt_ini, dt_fin, ano_mes, arquivo_hash, arquivo_origem,
                importado_em, cod_ver, encoding_origem, encoding_confianca, status)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                sped_tipo, dt_ini, dt_fin, ano_mes, arquivo_hash, arquivo_origem,
                _agora(), cod_ver, encoding_origem, encoding_confianca, status,
            ),
        )
        return cur.lastrowid  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Dedup de reimport (Bug-002) e re-diagnóstico (Bug-005)
    # ------------------------------------------------------------------

    def existe_import_com_hash(
        self, conn: sqlite3.Connection, sped_tipo: str, cnpj: str,
        periodo: int, arquivo_hash: str,
    ) -> dict | None:
        """Verifica se já existe import em `_importacoes` com mesmo
        `arquivo_hash` para o mesmo (sped_tipo × cnpj × período).

        `periodo` semântica:
        - SPED mensal (efd_contribuicoes, efd_icms): ano_mes (AAAAMM).
        - SPED anual (ecd, ecf): ano_calendario (AAAA). Internamente
          mapeado para ano_mes=AAAA01 conforme convenção observada nos
          bancos NG (registrar_importacao grava jan do ano-calendário
          para SPED anual).

        Retorna `{"id": int, "importado_em": str}` se existe, ou None.

        Bug-002 — Opção 3 (camada UX): protege contra reimport acidental.
        Caller decide se aborta (sem flag `--force-reimport`) ou prossegue.
        Reimport com hash diferente (retificadora real) não é detectado
        por este método — é tratado pela camada Opção 2 (DELETE prévio
        em `deletar_dados_anteriores`).
        """
        if sped_tipo not in _TABELAS_POR_SPED_TIPO:
            raise ValueError(f"sped_tipo invalido: {sped_tipo!r}")
        # SPED anual: _importacoes.ano_mes é gravado como AAAA01
        if sped_tipo in ("ecd", "ecf"):
            ano_mes_filtro = periodo * 100 + 1
        else:
            ano_mes_filtro = periodo
        row = conn.execute(
            "SELECT id, importado_em FROM _importacoes "
            "WHERE sped_tipo=? AND arquivo_hash=? AND ano_mes=? "
            "ORDER BY id DESC LIMIT 1",
            (sped_tipo, arquivo_hash, ano_mes_filtro),
        ).fetchone()
        return dict(row) if row else None

    def deletar_dados_anteriores(
        self, conn: sqlite3.Connection, sped_tipo: str, cnpj: str,
        *, ano_mes: int | None = None, ano_calendario: int | None = None,
    ) -> int:
        """Apaga rows anteriores em todas as tabelas SPED do tipo dado
        para (cnpj × período). Retorna total de rows deletadas (soma
        entre tabelas).

        Tabelas de controle e anotação NÃO são tocadas:
        `_importacoes` (mantém histórico de versões para T8 Auditoria),
        `_sped_contexto`, `reconciliacao_override`,
        `contabil_oportunidades_essencialidade`.

        Bug-002 — Opção 2 (núcleo do fix): garante zero duplicação em
        reimport (idêntico OU retificadora). Caller deve invocar dentro
        de `with conn:` (transação atômica com os INSERTs subsequentes).

        Para SPED mensal, passar `ano_mes=AAAAMM`. Para SPED anual,
        passar `ano_calendario=AAAA`. ValueError se ambos None.
        """
        if sped_tipo not in _TABELAS_POR_SPED_TIPO:
            raise ValueError(f"sped_tipo invalido: {sped_tipo!r}")
        chave_periodo, tabelas = _TABELAS_POR_SPED_TIPO[sped_tipo]
        valor = ano_mes if chave_periodo == "ano_mes" else ano_calendario
        if valor is None:
            raise ValueError(
                f"sped_tipo={sped_tipo!r} requer {chave_periodo}, recebido None"
            )
        total = 0
        for tab in tabelas:
            try:
                cur = conn.execute(
                    f"DELETE FROM {tab} WHERE cnpj_declarante = ? AND {chave_periodo} = ?",
                    (cnpj, valor),
                )
                total += cur.rowcount
            except sqlite3.OperationalError:
                # Tabela ainda não existe (banco antigo sem migração) — OK
                continue
        return total

    def deletar_diagnostico_anterior(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int,
    ) -> tuple[int, int]:
        """Apaga rows anteriores em `crossref_oportunidades` +
        `crossref_divergencias` para (cnpj × ano_calendario). Retorna
        tupla `(qtd_op_apagadas, qtd_div_apagadas)`.

        Bug-005 — Opção 2: garante zero duplicação em re-diagnóstico.

        LIMITAÇÃO DOCUMENTADA: anotações do auditor (`revisado_em`,
        `revisado_por`, `nota`) em rows previamente diagnosticadas SÃO
        PERDIDAS. Decisão consciente baseada em verificação empírica
        (zero anotações em qualquer banco do projeto na data da
        resolução — feature implementada mas não usada em produção).
        Re-debate previsto em sprint UX se aparecer banco com anotação
        real (gatilho documentado em `docs/debitos-conhecidos.md`
        entrada Bug-005).
        """
        cur_op = conn.execute(
            "DELETE FROM crossref_oportunidades "
            "WHERE cnpj_declarante = ? AND ano_calendario = ?",
            (cnpj, ano_calendario),
        )
        cur_div = conn.execute(
            "DELETE FROM crossref_divergencias "
            "WHERE cnpj_declarante = ? AND ano_calendario = ?",
            (cnpj, ano_calendario),
        )
        return cur_op.rowcount, cur_div.rowcount

    def atualizar_sped_contexto(self, conn: sqlite3.Connection, **campos) -> None:
        campos.setdefault("cnpj", self.cnpj)
        campos.setdefault("ano_calendario", self.ano_calendario)
        campos["atualizado_em"] = _agora()
        col_names = list(campos.keys())
        placeholders = ",".join("?" * len(col_names))
        col_str = ",".join(col_names)
        update_cols = [c for c in col_names if c not in ("cnpj", "ano_calendario")]
        update_str = ",".join(f"{c}=excluded.{c}" for c in update_cols)
        conn.execute(
            f"""INSERT INTO _sped_contexto ({col_str}) VALUES ({placeholders})
                ON CONFLICT(cnpj, ano_calendario) DO UPDATE SET {update_str}""",
            list(campos.values()),
        )

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _ctx(self, ctx: dict) -> tuple:
        return (
            ctx["cnpj_declarante"],
            ctx["dt_ini_periodo"],
            ctx["dt_fin_periodo"],
            ctx["ano_mes"],
            ctx["ano_calendario"],
            ctx["cod_ver"],
        )

    @staticmethod
    def _f(v) -> float:
        return float(v) if v is not None else 0.0

    # ------------------------------------------------------------------
    # Inserters
    # ------------------------------------------------------------------

    def inserir_0000(self, conn: sqlite3.Connection, reg: Reg0000, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_0000
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nome, cpf, uf, ie, cod_mun, im, suframa, ind_perfil, ind_ativ)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0000",
                *self._ctx(ctx),
                reg.nome, reg.cpf, reg.uf, reg.ie, reg.cod_mun,
                reg.im, reg.suframa, reg.ind_perfil, reg.ind_ativ,
            ),
        )

    def inserir_0110(self, conn: sqlite3.Connection, reg: Reg0110, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_0110
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_inc_trib, ind_apro_cred, cod_tipo_cont, ind_reg_cum)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0110",
                *self._ctx(ctx),
                reg.cod_inc_trib, reg.ind_apro_cred, reg.cod_tipo_cont, reg.ind_reg_cum,
            ),
        )

    def inserir_0111(self, conn: sqlite3.Connection, reg: Reg0111, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_0111
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                rec_brt_ncum_trib_mi, rec_brt_ncum_nt_mi, rec_brt_ncum_exp,
                rec_brt_cum, rec_brt_total)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0111",
                *self._ctx(ctx),
                self._f(reg.rec_brt_ncum_trib_mi), self._f(reg.rec_brt_ncum_nt_mi),
                self._f(reg.rec_brt_ncum_exp), self._f(reg.rec_brt_cum),
                self._f(reg.rec_brt_total),
            ),
        )

    def inserir_c100(self, conn: sqlite3.Connection, reg: RegC100, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_c100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_oper, ind_emit, cod_part, cod_mod, cod_sit, ser, num_doc,
                chave_nfe, dt_doc, vl_doc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C100",
                *self._ctx(ctx),
                reg.ind_oper, reg.ind_emit, reg.cod_part, reg.cod_mod, reg.cod_sit,
                reg.ser, reg.num_doc, reg.chave_nfe, reg.dt_doc, self._f(reg.vl_doc),
            ),
        )

    def inserir_c170(self, conn: sqlite3.Connection, reg: RegC170, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_c170
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                c100_linha_arquivo, num_item, cod_item, vl_item, vl_desc, cfop,
                vl_icms, vl_icms_st, cst_pis, vl_bc_pis, aliq_pis, quant_bc_pis,
                aliq_pis_quant, vl_pis, cst_cofins, vl_bc_cofins, aliq_cofins,
                quant_bc_cofins, aliq_cofins_quant, vl_cofins, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C170",
                *self._ctx(ctx),
                reg.c100_linha_arquivo, reg.num_item, reg.cod_item,
                self._f(reg.vl_item), self._f(reg.vl_desc), reg.cfop,
                self._f(reg.vl_icms), self._f(reg.vl_icms_st),
                reg.cst_pis, self._f(reg.vl_bc_pis), self._f(reg.aliq_pis),
                self._f(reg.quant_bc_pis), self._f(reg.aliq_pis_quant), self._f(reg.vl_pis),
                reg.cst_cofins, self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins),
                self._f(reg.quant_bc_cofins), self._f(reg.aliq_cofins_quant),
                self._f(reg.vl_cofins), reg.cod_cta,
            ),
        )

    def inserir_c181(self, conn: sqlite3.Connection, reg: RegC181, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_c181
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                c180_linha_arquivo, ind_oper, cst_pis, cfop, vl_item, vl_desc,
                vl_bc_pis, aliq_pis, quant_bc_pis, aliq_pis_quant, vl_pis, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C181",
                *self._ctx(ctx),
                reg.c180_linha_arquivo, reg.ind_oper,
                reg.cst_pis, reg.cfop,
                self._f(reg.vl_item), self._f(reg.vl_desc),
                self._f(reg.vl_bc_pis), self._f(reg.aliq_pis),
                self._f(reg.quant_bc_pis), self._f(reg.aliq_pis_quant),
                self._f(reg.vl_pis), reg.cod_cta,
            ),
        )

    def inserir_c185(self, conn: sqlite3.Connection, reg: RegC185, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_c185
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                c180_linha_arquivo, ind_oper, cst_cofins, cfop, vl_item, vl_desc,
                vl_bc_cofins, aliq_cofins, quant_bc_cofins, aliq_cofins_quant,
                vl_cofins, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C185",
                *self._ctx(ctx),
                reg.c180_linha_arquivo, reg.ind_oper,
                reg.cst_cofins, reg.cfop,
                self._f(reg.vl_item), self._f(reg.vl_desc),
                self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins),
                self._f(reg.quant_bc_cofins), self._f(reg.aliq_cofins_quant),
                self._f(reg.vl_cofins), reg.cod_cta,
            ),
        )

    def inserir_d201(self, conn: sqlite3.Connection, reg: RegD201, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_d201
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                d200_linha_arquivo, ind_oper, cst_pis, vl_item, vl_bc_pis,
                aliq_pis, quant_bc_pis, aliq_pis_quant, vl_pis, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "D", "D201",
                *self._ctx(ctx),
                reg.d200_linha_arquivo, reg.ind_oper,
                reg.cst_pis,
                self._f(reg.vl_item), self._f(reg.vl_bc_pis),
                self._f(reg.aliq_pis), self._f(reg.quant_bc_pis),
                self._f(reg.aliq_pis_quant), self._f(reg.vl_pis), reg.cod_cta,
            ),
        )

    def inserir_d205(self, conn: sqlite3.Connection, reg: RegD205, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_d205
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                d200_linha_arquivo, ind_oper, cst_cofins, vl_item, vl_bc_cofins,
                aliq_cofins, quant_bc_cofins, aliq_cofins_quant, vl_cofins, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "D", "D205",
                *self._ctx(ctx),
                reg.d200_linha_arquivo, reg.ind_oper,
                reg.cst_cofins,
                self._f(reg.vl_item), self._f(reg.vl_bc_cofins),
                self._f(reg.aliq_cofins), self._f(reg.quant_bc_cofins),
                self._f(reg.aliq_cofins_quant), self._f(reg.vl_cofins), reg.cod_cta,
            ),
        )

    def inserir_m215(self, conn: sqlite3.Connection, reg: RegM215, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m215
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                m210_linha_arquivo, ind_aj_bc, vl_aj_bc, cod_aj_bc, num_doc,
                descr_aj_bc, dt_ref, cod_cta, cnpj_ref)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M215",
                *self._ctx(ctx),
                reg.m210_linha_arquivo, reg.ind_aj_bc,
                self._f(reg.vl_aj_bc), reg.cod_aj_bc, reg.num_doc,
                reg.descr_aj_bc, reg.dt_ref, reg.cod_cta, reg.cnpj_ref,
            ),
        )

    def inserir_m615(self, conn: sqlite3.Connection, reg: RegM615, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m615
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                m610_linha_arquivo, ind_aj_bc, vl_aj_bc, cod_aj_bc, num_doc,
                descr_aj_bc, dt_ref, cod_cta, cnpj_ref)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M615",
                *self._ctx(ctx),
                reg.m610_linha_arquivo, reg.ind_aj_bc,
                self._f(reg.vl_aj_bc), reg.cod_aj_bc, reg.num_doc,
                reg.descr_aj_bc, reg.dt_ref, reg.cod_cta, reg.cnpj_ref,
            ),
        )

    def inserir_f600(self, conn: sqlite3.Connection, reg: RegF600, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f600
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_nat_ret, dt_ret, vl_bc_ret, aliq_ret, vl_ret_apu, cod_rec,
                ind_nat_rec, pr_rec_ret, cnpj_fonte_pag, vl_ret_per, vl_ret_dcomp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F600",
                *self._ctx(ctx),
                reg.ind_nat_ret, reg.dt_ret,
                self._f(reg.vl_bc_ret), self._f(reg.aliq_ret), self._f(reg.vl_ret_apu),
                reg.cod_rec, reg.ind_nat_rec, reg.pr_rec_ret, reg.cnpj_fonte_pag,
                self._f(reg.vl_ret_per), self._f(reg.vl_ret_dcomp),
            ),
        )

    def inserir_f700(self, conn: sqlite3.Connection, reg: RegF700, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f700
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_nat_ret, dt_ret, vl_bc_ret, aliq_ret, vl_ret_apu, cod_rec,
                ind_nat_rec, pr_rec_ret, cnpj_fonte_pag, vl_ret_per, vl_ret_dcomp)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F700",
                *self._ctx(ctx),
                reg.ind_nat_ret, reg.dt_ret,
                self._f(reg.vl_bc_ret), self._f(reg.aliq_ret), self._f(reg.vl_ret_apu),
                reg.cod_rec, reg.ind_nat_rec, reg.pr_rec_ret, reg.cnpj_fonte_pag,
                self._f(reg.vl_ret_per), self._f(reg.vl_ret_dcomp),
            ),
        )

    def inserir_m210(self, conn: sqlite3.Connection, reg: RegM210, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m210
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cont, vl_rec_brt, vl_bc_cont, aliq_pis, vl_cont_apu,
                vl_ajus_reduc, vl_cont_per)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M210",
                *self._ctx(ctx),
                reg.cod_cont, self._f(reg.vl_rec_brt), self._f(reg.vl_bc_cont),
                self._f(reg.aliq_pis), self._f(reg.vl_cont_apu),
                self._f(reg.vl_ajus_reduc), self._f(reg.vl_cont_per),
            ),
        )

    def inserir_m610(self, conn: sqlite3.Connection, reg: RegM610, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m610
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cont, vl_rec_brt, vl_bc_cont, aliq_cofins, vl_cont_apu,
                vl_ajus_reduc, vl_cont_per)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M610",
                *self._ctx(ctx),
                reg.cod_cont, self._f(reg.vl_rec_brt), self._f(reg.vl_bc_cont),
                self._f(reg.aliq_cofins), self._f(reg.vl_cont_apu),
                self._f(reg.vl_ajus_reduc), self._f(reg.vl_cont_per),
            ),
        )

    def inserir_f120(self, conn: sqlite3.Connection, reg: RegF120, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f120
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nat_bc_cred, ident_bem_imob, ind_orig_cred, ind_util_bem_imob,
                vl_oper_dep, parc_oper_nao_bc_cred, cst_pis, vl_bc_pis, aliq_pis, vl_pis,
                cst_cofins, vl_bc_cofins, aliq_cofins, vl_cofins, cod_cta, cod_ccus, desc_bem_imob)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F120",
                *self._ctx(ctx),
                reg.nat_bc_cred, reg.ident_bem_imob, reg.ind_orig_cred, reg.ind_util_bem_imob,
                self._f(reg.vl_oper_dep), self._f(reg.parc_oper_nao_bc_cred),
                reg.cst_pis, self._f(reg.vl_bc_pis), self._f(reg.aliq_pis), self._f(reg.vl_pis),
                reg.cst_cofins, self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins), self._f(reg.vl_cofins),
                reg.cod_cta, reg.cod_ccus, reg.desc_bem_imob,
            ),
        )

    def inserir_f130(self, conn: sqlite3.Connection, reg: RegF130, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f130
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nat_bc_cred, ident_bem_imob, ind_orig_cred, ind_util_bem_imob,
                mes_oper_aquis, vl_oper_aquis, parc_oper_nao_bc_cred, vl_bc_cred, ind_nr_parc,
                cst_pis, vl_bc_pis, aliq_pis, vl_pis,
                cst_cofins, vl_bc_cofins, aliq_cofins, vl_cofins,
                cod_cta, cod_ccus, desc_bem_imob)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F130",
                *self._ctx(ctx),
                reg.nat_bc_cred, reg.ident_bem_imob, reg.ind_orig_cred, reg.ind_util_bem_imob,
                reg.mes_oper_aquis, self._f(reg.vl_oper_aquis), self._f(reg.parc_oper_nao_bc_cred),
                self._f(reg.vl_bc_cred), reg.ind_nr_parc,
                reg.cst_pis, self._f(reg.vl_bc_pis), self._f(reg.aliq_pis), self._f(reg.vl_pis),
                reg.cst_cofins, self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins), self._f(reg.vl_cofins),
                reg.cod_cta, reg.cod_ccus, reg.desc_bem_imob,
            ),
        )

    def inserir_f150(self, conn: sqlite3.Connection, reg: RegF150, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f150
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nat_bc_cred, vl_tot_est, est_imp, vl_bc_est, vl_bc_men_est,
                cst_pis, aliq_pis, vl_cred_pis, cst_cofins, aliq_cofins, vl_cred_cofins,
                desc_est, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F150",
                *self._ctx(ctx),
                reg.nat_bc_cred, self._f(reg.vl_tot_est), self._f(reg.est_imp),
                self._f(reg.vl_bc_est), self._f(reg.vl_bc_men_est),
                reg.cst_pis, self._f(reg.aliq_pis), self._f(reg.vl_cred_pis),
                reg.cst_cofins, self._f(reg.aliq_cofins), self._f(reg.vl_cred_cofins),
                reg.desc_est, reg.cod_cta,
            ),
        )

    def inserir_m100(self, conn: sqlite3.Connection, reg: RegM100, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cred, ind_cred_ori, vl_bc_pis, aliq_pis, quant_bc_pis, aliq_pis_quant,
                vl_cred_disp, vl_ajus_acres, vl_ajus_reduc, vl_cred_difer, vl_cred_difer_ant,
                ind_apro, vl_cred_desc, sld_cred)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M100",
                *self._ctx(ctx),
                reg.cod_cred, reg.ind_cred_ori,
                self._f(reg.vl_bc_pis), self._f(reg.aliq_pis),
                self._f(reg.quant_bc_pis), self._f(reg.aliq_pis_quant),
                self._f(reg.vl_cred_disp), self._f(reg.vl_ajus_acres), self._f(reg.vl_ajus_reduc),
                self._f(reg.vl_cred_difer), self._f(reg.vl_cred_difer_ant),
                reg.ind_apro, self._f(reg.vl_cred_desc), self._f(reg.sld_cred),
            ),
        )

    def inserir_m500(self, conn: sqlite3.Connection, reg: RegM500, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m500
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cred, ind_cred_ori, vl_bc_cofins, aliq_cofins, quant_bc_cofins, aliq_cofins_quant,
                vl_cred_disp, vl_ajus_acres, vl_ajus_reduc, vl_cred_difer, vl_cred_difer_ant,
                ind_apro, vl_cred_desc, sld_cred)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M500",
                *self._ctx(ctx),
                reg.cod_cred, reg.ind_cred_ori,
                self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins),
                self._f(reg.quant_bc_cofins), self._f(reg.aliq_cofins_quant),
                self._f(reg.vl_cred_disp), self._f(reg.vl_ajus_acres), self._f(reg.vl_ajus_reduc),
                self._f(reg.vl_cred_difer), self._f(reg.vl_cred_difer_ant),
                reg.ind_apro, self._f(reg.vl_cred_desc), self._f(reg.sld_cred),
            ),
        )

    def inserir_m200(self, conn: sqlite3.Connection, reg: RegM200, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m200
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                vl_tot_cont_nc_per, vl_tot_cred_desc, vl_rec_brt_total)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M200",
                *self._ctx(ctx),
                self._f(reg.vl_tot_cont_nc_per), self._f(reg.vl_tot_cred_desc),
                self._f(reg.vl_rec_brt_total),
            ),
        )

    def inserir_m600(self, conn: sqlite3.Connection, reg: RegM600, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m600
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                vl_tot_cont_nc_per, vl_tot_cred_desc, vl_rec_brt_total)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M600",
                *self._ctx(ctx),
                self._f(reg.vl_tot_cont_nc_per), self._f(reg.vl_tot_cred_desc),
                self._f(reg.vl_rec_brt_total),
            ),
        )

    def inserir_9900(self, conn: sqlite3.Connection, reg: Reg9900, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_9900
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                reg_blc, qtd_reg_blc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "9", "9900",
                *self._ctx(ctx),
                reg.reg_blc, reg.qtd_reg_blc,
            ),
        )

    def inserir_oportunidade(
        self,
        conn: sqlite3.Connection,
        op: Oportunidade,
        cnpj: str,
        ano_mes: int,
        ano_calendario: int,
    ) -> None:
        conn.execute(
            """INSERT INTO crossref_oportunidades
               (codigo_regra, descricao, severidade, valor_impacto_conservador,
                valor_impacto_maximo, evidencia_json, cnpj_declarante, ano_mes,
                ano_calendario, gerado_em)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                op.codigo_regra, op.descricao, op.severidade,
                self._f(op.valor_impacto_conservador),
                self._f(op.valor_impacto_maximo),
                json.dumps(op.evidencia, ensure_ascii=False, default=str),
                cnpj, ano_mes, ano_calendario, _agora(),
            ),
        )

    def inserir_divergencia(
        self,
        conn: sqlite3.Connection,
        div: Divergencia,
        cnpj: str,
        ano_mes: int,
        ano_calendario: int,
    ) -> None:
        conn.execute(
            """INSERT INTO crossref_divergencias
               (codigo_regra, descricao, severidade, evidencia_json,
                cnpj_declarante, ano_mes, ano_calendario, gerado_em)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                div.codigo_regra, div.descricao, div.severidade,
                json.dumps(div.evidencia, ensure_ascii=False, default=str),
                cnpj, ano_mes, ano_calendario, _agora(),
            ),
        )

    # ------------------------------------------------------------------
    # Queries para o motor de cruzamentos
    # ------------------------------------------------------------------

    def consultar_c170_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_c170 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_c100_ind_oper(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> dict[int, str]:
        cur = conn.execute(
            "SELECT linha_arquivo, ind_oper FROM efd_contrib_c100"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return {row["linha_arquivo"]: row["ind_oper"] for row in cur}

    def consultar_0110(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> dict | None:
        row = conn.execute(
            "SELECT * FROM efd_contrib_0110 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return dict(row) if row else None

    def consultar_0111(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> dict | None:
        row = conn.execute(
            "SELECT * FROM efd_contrib_0111 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return dict(row) if row else None

    def contar_m200(self, conn: sqlite3.Connection, cnpj: str, ano_mes: int) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM efd_contrib_m200 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()[0]

    def contar_m600(self, conn: sqlite3.Connection, cnpj: str, ano_mes: int) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM efd_contrib_m600 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()[0]

    def consultar_9900(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_9900 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_c100_linhas(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> set[int]:
        cur = conn.execute(
            "SELECT linha_arquivo FROM efd_contrib_c100"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return {row[0] for row in cur}

    def consultar_c170_c100_refs(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> set[int]:
        cur = conn.execute(
            "SELECT DISTINCT c100_linha_arquivo FROM efd_contrib_c170"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return {row[0] for row in cur}

    def consultar_oportunidades(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM crossref_oportunidades"
            " WHERE cnpj_declarante=? AND ano_calendario=?"
            " ORDER BY valor_impacto_conservador DESC",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_divergencias(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM crossref_divergencias"
            " WHERE cnpj_declarante=? AND ano_calendario=?"
            " ORDER BY severidade, codigo_regra",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    # ------------------------------------------------------------------
    # Revisão de achado (decisão #12 do planejamento GUI)
    # ------------------------------------------------------------------

    def marcar_revisada(
        self,
        conn: sqlite3.Connection,
        achado_id: int,
        usuario: str,
        *,
        tabela: str = "crossref_oportunidades",
    ) -> None:
        """Marca um achado como revisado por usuário em timestamp atual.

        `tabela` deve ser 'crossref_oportunidades' ou 'crossref_divergencias';
        outros valores rejeitados para prevenir SQL injection.
        """
        if tabela not in ("crossref_oportunidades", "crossref_divergencias"):
            raise ValueError(f"Tabela inválida: {tabela!r}")
        conn.execute(
            f"UPDATE {tabela} SET revisado_em=?, revisado_por=? WHERE id=?",
            (_agora(), usuario, achado_id),
        )

    def desmarcar_revisada(
        self,
        conn: sqlite3.Connection,
        achado_id: int,
        *,
        tabela: str = "crossref_oportunidades",
    ) -> None:
        if tabela not in ("crossref_oportunidades", "crossref_divergencias"):
            raise ValueError(f"Tabela inválida: {tabela!r}")
        conn.execute(
            f"UPDATE {tabela} SET revisado_em=NULL, revisado_por=NULL WHERE id=?",
            (achado_id,),
        )

    def atualizar_nota(
        self,
        conn: sqlite3.Connection,
        achado_id: int,
        nota: str,
        *,
        tabela: str = "crossref_oportunidades",
    ) -> None:
        if tabela not in ("crossref_oportunidades", "crossref_divergencias"):
            raise ValueError(f"Tabela inválida: {tabela!r}")
        # nota=None → vira NULL; string vazia também vira NULL para consistência
        valor = nota.strip() if isinstance(nota, str) and nota.strip() else None
        conn.execute(
            f"UPDATE {tabela} SET nota=? WHERE id=?",
            (valor, achado_id),
        )

    def consultar_meses_importados(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[int]:
        cur = conn.execute(
            "SELECT DISTINCT ano_mes FROM efd_contrib_0000"
            " WHERE cnpj_declarante=? AND ano_calendario=? ORDER BY ano_mes",
            (cnpj, ano_calendario),
        )
        return [row[0] for row in cur]

    def consultar_sped_contexto(
        self, conn: sqlite3.Connection
    ) -> dict | None:
        row = conn.execute(
            "SELECT * FROM _sped_contexto WHERE cnpj=? AND ano_calendario=?",
            (self.cnpj, self.ano_calendario),
        ).fetchone()
        return dict(row) if row else None

    # Sprint 2 — queries para cruzamentos 08, 09, 26

    def consultar_c181_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_c181 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_d201_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_d201 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m215_reducoes(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """Retorna M215 com IND_AJ_BC='0' (reduções de base) para o período."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m215"
            " WHERE cnpj_declarante=? AND ano_mes=? AND ind_aj_bc='0'",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m615_reducoes(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """Retorna M615 com IND_AJ_BC='0' (reduções de base) para o período."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m615"
            " WHERE cnpj_declarante=? AND ano_mes=? AND ind_aj_bc='0'",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    # Sprint 3 — queries para cruzamentos 16, 17, 19, 31

    def consultar_f600_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f600 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_f700_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f700 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_f600_historico(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """Todos os F600 do ano-calendário — para CR-19 (prescrição)."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f600 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_f700_historico(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f700 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_m210_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m210 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m610_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m610 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def contar_m215(self, conn: sqlite3.Connection, cnpj: str, ano_mes: int) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM efd_contrib_m215 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()[0]

    # Sprint 4 — queries para cruzamentos 14, 15, 22, 27, 28, 29, 30

    def consultar_f120_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f120 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_f130_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f130 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_f150_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f150 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m100_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m100 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m500_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m500 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m200_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> dict | None:
        """Retorna o único M200 do período (para CR-29)."""
        row = conn.execute(
            "SELECT * FROM efd_contrib_m200 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return dict(row) if row else None

    def consultar_m600_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> dict | None:
        """Retorna o único M600 do período (para CR-30)."""
        row = conn.execute(
            "SELECT * FROM efd_contrib_m600 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return dict(row) if row else None

    # Sprint 5 — inserters

    def inserir_0200(self, conn: sqlite3.Connection, reg: Reg0200, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_0200
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_item, descr_item, cod_barra, cod_ant_item, unid_inv, tipo_item,
                cod_ncm, ex_ipi, cod_gen, cod_lst, aliq_icms)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0200",
                *self._ctx(ctx),
                reg.cod_item, reg.descr_item, reg.cod_barra, reg.cod_ant_item,
                reg.unid_inv, reg.tipo_item, reg.cod_ncm, reg.ex_ipi,
                reg.cod_gen, reg.cod_lst, self._f(reg.aliq_icms),
            ),
        )

    def inserir_f100(self, conn: sqlite3.Connection, reg: RegF100, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_oper, cod_part, cod_item, dt_oper, vl_oper,
                cst_pis, vl_bc_pis, aliq_pis, vl_pis,
                cst_cofins, vl_bc_cofins, aliq_cofins, vl_cofins,
                nat_bc_cred, ind_orig_cred, cod_cta, cod_ccus, desc_doc_oper)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F100",
                *self._ctx(ctx),
                reg.ind_oper, reg.cod_part, reg.cod_item, reg.dt_oper,
                self._f(reg.vl_oper),
                reg.cst_pis, self._f(reg.vl_bc_pis), self._f(reg.aliq_pis), self._f(reg.vl_pis),
                reg.cst_cofins, self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins), self._f(reg.vl_cofins),
                reg.nat_bc_cred, reg.ind_orig_cred, reg.cod_cta, reg.cod_ccus, reg.desc_doc_oper,
            ),
        )

    def inserir_f800(self, conn: sqlite3.Connection, reg: RegF800, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_f800
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_transf, ind_nat_transf, cnpj_transf, dt_transf,
                vl_transf_pis, vl_transf_cofins, vl_cred_pis_trans, vl_cred_cofins_trans)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "F", "F800",
                *self._ctx(ctx),
                reg.ind_transf, reg.ind_nat_transf, reg.cnpj_transf, reg.dt_transf,
                self._f(reg.vl_transf_pis), self._f(reg.vl_transf_cofins),
                self._f(reg.vl_cred_pis_trans), self._f(reg.vl_cred_cofins_trans),
            ),
        )

    def inserir_m105(self, conn: sqlite3.Connection, reg: RegM105, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m105
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nat_bc_cred, vl_bc_pis_tot, vl_bc_minut, vl_bc_mindt, vl_bc_mexp,
                vl_amt_parc_forn, vl_bc_isenta, vl_bc_outras, desc_compl)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M105",
                *self._ctx(ctx),
                reg.nat_bc_cred, self._f(reg.vl_bc_pis_tot),
                self._f(reg.vl_bc_minut), self._f(reg.vl_bc_mindt), self._f(reg.vl_bc_mexp),
                self._f(reg.vl_amt_parc_forn), self._f(reg.vl_bc_isenta),
                self._f(reg.vl_bc_outras), reg.desc_compl,
            ),
        )

    def inserir_m505(self, conn: sqlite3.Connection, reg: RegM505, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_m505
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nat_bc_cred, vl_bc_cofins_tot, vl_bc_minut, vl_bc_mindt, vl_bc_mexp,
                vl_amt_parc_forn, vl_bc_isenta, vl_bc_outras, desc_compl)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M505",
                *self._ctx(ctx),
                reg.nat_bc_cred, self._f(reg.vl_bc_cofins_tot),
                self._f(reg.vl_bc_minut), self._f(reg.vl_bc_mindt), self._f(reg.vl_bc_mexp),
                self._f(reg.vl_amt_parc_forn), self._f(reg.vl_bc_isenta),
                self._f(reg.vl_bc_outras), reg.desc_compl,
            ),
        )

    def inserir_1100(self, conn: sqlite3.Connection, reg: Reg1100, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_1100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                per_apu_cred, orig_cred, cnpj_suc, cod_cred,
                vl_cred_apu, vl_cred_ext_apu, vl_tot_cred_apu,
                vl_cred_desc_pa_ant, vl_cred_per_pa_ant, vl_cred_dcomp_pa_ant,
                sd_cred_disp_efd, vl_cred_desc_efd, vl_cred_per_efd, vl_cred_dcomp_efd,
                vl_cred_trans, vl_cred_out, sld_cred_fim)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "1", "1100",
                *self._ctx(ctx),
                reg.per_apu_cred, reg.orig_cred, reg.cnpj_suc, reg.cod_cred,
                self._f(reg.vl_cred_apu), self._f(reg.vl_cred_ext_apu), self._f(reg.vl_tot_cred_apu),
                self._f(reg.vl_cred_desc_pa_ant), self._f(reg.vl_cred_per_pa_ant),
                self._f(reg.vl_cred_dcomp_pa_ant), self._f(reg.sd_cred_disp_efd),
                self._f(reg.vl_cred_desc_efd), self._f(reg.vl_cred_per_efd),
                self._f(reg.vl_cred_dcomp_efd), self._f(reg.vl_cred_trans),
                self._f(reg.vl_cred_out), self._f(reg.sld_cred_fim),
            ),
        )

    def inserir_1500(self, conn: sqlite3.Connection, reg: Reg1500, ctx: dict) -> None:
        conn.execute(
            """INSERT INTO efd_contrib_1500
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                per_apu_cred, orig_cred, cnpj_suc, cod_cred,
                vl_cred_apu, vl_cred_ext_apu, vl_tot_cred_apu,
                vl_cred_desc_pa_ant, vl_cred_per_pa_ant, vl_cred_dcomp_pa_ant,
                sd_cred_disp_efd, vl_cred_desc_efd, vl_cred_per_efd, vl_cred_dcomp_efd,
                vl_cred_trans, vl_cred_out, sld_cred_fim)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "1", "1500",
                *self._ctx(ctx),
                reg.per_apu_cred, reg.orig_cred, reg.cnpj_suc, reg.cod_cred,
                self._f(reg.vl_cred_apu), self._f(reg.vl_cred_ext_apu), self._f(reg.vl_tot_cred_apu),
                self._f(reg.vl_cred_desc_pa_ant), self._f(reg.vl_cred_per_pa_ant),
                self._f(reg.vl_cred_dcomp_pa_ant), self._f(reg.sd_cred_disp_efd),
                self._f(reg.vl_cred_desc_efd), self._f(reg.vl_cred_per_efd),
                self._f(reg.vl_cred_dcomp_efd), self._f(reg.vl_cred_trans),
                self._f(reg.vl_cred_out), self._f(reg.sld_cred_fim),
            ),
        )

    # Sprint 5 — queries

    def consultar_0200_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_0200 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_c170_com_tipo_item(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """C170 com JOIN em 0200 por cod_item — para CR-11."""
        cur = conn.execute(
            """SELECT c.*, p.tipo_item
               FROM efd_contrib_c170 c
               LEFT JOIN efd_contrib_0200 p
                 ON c.cod_item = p.cod_item
                 AND c.cnpj_declarante = p.cnpj_declarante
                 AND c.ano_mes = p.ano_mes
               WHERE c.cnpj_declarante=? AND c.ano_mes=?""",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def contar_f100_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM efd_contrib_f100 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()[0]

    def consultar_f100_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f100 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_f800_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_f800 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m105_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m105 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_m505_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m505 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_1100_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_1100 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_1500_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        cur = conn.execute(
            "SELECT * FROM efd_contrib_1500 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def soma_vl_bc_pis_credito_c170(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ C170.VL_BC_PIS onde CST_PIS em {50..56,60..67} — para CR-32."""
        row = conn.execute(
            """SELECT COALESCE(SUM(vl_bc_pis), 0)
               FROM efd_contrib_c170
               WHERE cnpj_declarante=? AND ano_mes=?
               AND CAST(cst_pis AS TEXT) IN
                 ('50','51','52','53','54','55','56','60','61','62','63','64','65','66','67')""",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_pis_credito_f100(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ F100.VL_BC_PIS onde CST_PIS em {50..56,60..67} — para CR-32."""
        row = conn.execute(
            """SELECT COALESCE(SUM(vl_bc_pis), 0)
               FROM efd_contrib_f100
               WHERE cnpj_declarante=? AND ano_mes=?
               AND CAST(cst_pis AS TEXT) IN
                 ('50','51','52','53','54','55','56','60','61','62','63','64','65','66','67')""",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_pis_tot_m105(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ M105.VL_BC_PIS_TOT — para CR-32."""
        row = conn.execute(
            "SELECT COALESCE(SUM(vl_bc_pis_tot), 0) FROM efd_contrib_m105"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_cofins_debito_c170(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ C170.VL_BC_COFINS onde CST_COFINS em {01..05} — para CR-33."""
        row = conn.execute(
            """SELECT COALESCE(SUM(vl_bc_cofins), 0)
               FROM efd_contrib_c170
               WHERE cnpj_declarante=? AND ano_mes=?
               AND CAST(cst_cofins AS TEXT) IN ('01','02','03','04','05')""",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_cont_m610(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ M610.VL_BC_CONT — para CR-33."""
        row = conn.execute(
            "SELECT COALESCE(SUM(vl_bc_cont), 0) FROM efd_contrib_m610"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_cofins_credito_c170(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ C170.VL_BC_COFINS onde CST_COFINS em {50..56,60..67} — para CR-34."""
        row = conn.execute(
            """SELECT COALESCE(SUM(vl_bc_cofins), 0)
               FROM efd_contrib_c170
               WHERE cnpj_declarante=? AND ano_mes=?
               AND CAST(cst_cofins AS TEXT) IN
                 ('50','51','52','53','54','55','56','60','61','62','63','64','65','66','67')""",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_cofins_credito_f100(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ F100.VL_BC_COFINS onde CST_COFINS em {50..56,60..67} — para CR-34."""
        row = conn.execute(
            """SELECT COALESCE(SUM(vl_bc_cofins), 0)
               FROM efd_contrib_f100
               WHERE cnpj_declarante=? AND ano_mes=?
               AND CAST(cst_cofins AS TEXT) IN
                 ('50','51','52','53','54','55','56','60','61','62','63','64','65','66','67')""",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def soma_vl_bc_cofins_tot_m505(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> float:
        """Σ M505.VL_BC_COFINS_TOT — para CR-34."""
        row = conn.execute(
            "SELECT COALESCE(SUM(vl_bc_cofins_tot), 0) FROM efd_contrib_m505"
            " WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        ).fetchone()
        return float(row[0]) if row else 0.0

    # Sprint 6 — EFD ICMS/IPI inserters

    def inserir_icms_0000(
        self, conn: sqlite3.Connection, reg: RegIcms0000, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_0000
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nome, uf, ie, ind_perfil, ind_ativ)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0000",
                *self._ctx(ctx),
                reg.nome, reg.uf, reg.ie, reg.ind_perfil, reg.ind_ativ,
            ),
        )

    def inserir_icms_c100(
        self, conn: sqlite3.Connection, reg: RegIcmsC100, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_c100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_oper)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C100",
                *self._ctx(ctx),
                reg.ind_oper,
            ),
        )

    def inserir_icms_c170(
        self, conn: sqlite3.Connection, reg: RegIcmsC170, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_c170
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                c100_linha_arquivo, num_item, cod_item, cfop, cst_icms,
                vl_item, vl_bc_icms, aliq_icms, vl_icms,
                cst_pis, vl_bc_pis, aliq_pis, vl_pis,
                cst_cofins, vl_bc_cofins, aliq_cofins, vl_cofins, cod_cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C170",
                *self._ctx(ctx),
                reg.c100_linha_arquivo, reg.num_item, reg.cod_item, reg.cfop, reg.cst_icms,
                self._f(reg.vl_item), self._f(reg.vl_bc_icms), self._f(reg.aliq_icms),
                self._f(reg.vl_icms),
                reg.cst_pis, self._f(reg.vl_bc_pis), self._f(reg.aliq_pis), self._f(reg.vl_pis),
                reg.cst_cofins, self._f(reg.vl_bc_cofins), self._f(reg.aliq_cofins),
                self._f(reg.vl_cofins), reg.cod_cta,
            ),
        )

    def inserir_icms_g110(
        self, conn: sqlite3.Connection, reg: RegIcmsG110, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_g110
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_ini, dt_fin, saldo_in_icms, som_parc, vl_trib_exp,
                vl_total, ind_per_sai, icms_aprop, som_icms_oc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "G", "G110",
                *self._ctx(ctx),
                reg.dt_ini, reg.dt_fin,
                self._f(reg.saldo_in_icms), self._f(reg.som_parc),
                self._f(reg.vl_trib_exp), self._f(reg.vl_total),
                self._f(reg.ind_per_sai), self._f(reg.icms_aprop),
                self._f(reg.som_icms_oc),
            ),
        )

    def inserir_icms_g125(
        self, conn: sqlite3.Connection, reg: RegIcmsG125, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_g125
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_ind_bem, ident_bem, dt_mov, tipo_mov,
                vl_imob_icms_op, vl_imob_icms_st, vl_imob_icms_frt, vl_imob_icms_dif,
                num_parc, vl_parc_pass)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "G", "G125",
                *self._ctx(ctx),
                reg.cod_ind_bem, reg.ident_bem, reg.dt_mov, reg.tipo_mov,
                self._f(reg.vl_imob_icms_op), self._f(reg.vl_imob_icms_st),
                self._f(reg.vl_imob_icms_frt), self._f(reg.vl_imob_icms_dif),
                reg.num_parc, self._f(reg.vl_parc_pass),
            ),
        )

    def inserir_icms_h005(
        self, conn: sqlite3.Connection, reg: RegIcmsH005, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_h005
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_inv, vl_inv, mot_inv)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "H", "H005",
                *self._ctx(ctx),
                reg.dt_inv, self._f(reg.vl_inv), reg.mot_inv,
            ),
        )

    def inserir_icms_h010(
        self, conn: sqlite3.Connection, reg: RegIcmsH010, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO efd_icms_h010
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                h005_linha_arquivo, cod_item, unid, qtd, vl_unit, vl_item,
                ind_prop, cod_part, txt_compl, cod_cta, vl_item_ir)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "H", "H010",
                *self._ctx(ctx),
                reg.h005_linha_arquivo, reg.cod_item, reg.unid,
                self._f(reg.qtd), self._f(reg.vl_unit), self._f(reg.vl_item),
                reg.ind_prop, reg.cod_part, reg.txt_compl, reg.cod_cta,
                self._f(reg.vl_item_ir),
            ),
        )

    # Sprint 6 — EFD ICMS/IPI queries

    def consultar_icms_g125_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """G125 com VL_PARC_PASS — para CR-35 (CIAP vs F120/F130)."""
        cur = conn.execute(
            "SELECT * FROM efd_icms_g125 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_icms_h010_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """H010 com VL_ITEM_IR — para CR-36 (inventário vs F150)."""
        cur = conn.execute(
            "SELECT * FROM efd_icms_h010 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_icms_c170_exportacao(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """C170 do ICMS com CFOP início '7' (exportação) — para CR-37."""
        cur = conn.execute(
            "SELECT * FROM efd_icms_c170"
            " WHERE cnpj_declarante=? AND ano_mes=? AND cfop LIKE '7%'",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_c170_contrib_cfop(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int, cfop: str
    ) -> list[dict]:
        """C170 da EFD-Contrib para um CFOP específico — para CR-37."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_c170"
            " WHERE cnpj_declarante=? AND ano_mes=? AND cfop=?",
            (cnpj, ano_mes, cfop),
        )
        return [dict(row) for row in cur]

    # Sprint 7 — ECD inserters

    def inserir_ecd_0000(
        self, conn: sqlite3.Connection, reg: RegEcd0000, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_0000
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nome, uf, cod_mun, ind_fin_esc, ind_grande_porte, tip_ecd,
                ident_mf, ind_mudanc_pc, cod_plan_ref)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0000",
                *self._ctx(ctx),
                reg.nome, reg.uf, reg.cod_mun, reg.ind_fin_esc,
                reg.ind_grande_porte, reg.tip_ecd, reg.ident_mf,
                reg.ind_mudanc_pc, reg.cod_plan_ref,
            ),
        )

    def inserir_ecd_i010(
        self, conn: sqlite3.Connection, reg: RegEcdI010, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i010
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                ind_esc, cod_ver_lc)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I010",
                *self._ctx(ctx),
                reg.ind_esc, reg.cod_ver_lc,
            ),
        )

    def inserir_ecd_c050(
        self, conn: sqlite3.Connection, reg: RegEcdC050, ctx: dict
    ) -> None:
        """C050 — plano de contas recuperado do ano anterior (Bloco C, §16)."""
        conn.execute(
            """INSERT INTO ecd_c050
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_alt, cod_nat, ind_cta, nivel, cod_cta, cod_cta_sup, cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C050",
                *self._ctx(ctx),
                reg.dt_alt, reg.cod_nat, reg.ind_cta, reg.nivel,
                reg.cod_cta, reg.cod_cta_sup, reg.cta,
            ),
        )

    def inserir_ecd_c155(
        self, conn: sqlite3.Connection, reg: RegEcdC155, ctx: dict
    ) -> None:
        """C155 — saldos finais do exercício anterior (Bloco C, §16)."""
        conn.execute(
            """INSERT INTO ecd_c155
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cta, cod_ccus, vl_sld_ini, ind_dc_ini, vl_sld_fin, ind_dc_fin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "C", "C155",
                *self._ctx(ctx),
                reg.cod_cta, reg.cod_ccus,
                self._f(reg.vl_sld_ini), reg.ind_dc_ini,
                self._f(reg.vl_sld_fin), reg.ind_dc_fin,
            ),
        )

    def inserir_ecd_i050(
        self, conn: sqlite3.Connection, reg: RegEcdI050, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i050
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_alt, cod_nat, ind_cta, nivel, cod_cta, cod_cta_sup, cta)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I050",
                *self._ctx(ctx),
                reg.dt_alt, reg.cod_nat, reg.ind_cta, reg.nivel,
                reg.cod_cta, reg.cod_cta_sup, reg.cta,
            ),
        )

    def inserir_ecd_i150(
        self, conn: sqlite3.Connection, reg: RegEcdI150, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i150
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_ini_per, dt_fin_per)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I150",
                *self._ctx(ctx),
                reg.dt_ini, reg.dt_fin,
            ),
        )

    def inserir_ecd_i155(
        self, conn: sqlite3.Connection, reg: RegEcdI155, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i155
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                i150_linha_arquivo, cod_cta, cod_ccus,
                vl_sld_ini, ind_dc_ini, vl_deb, vl_cred, vl_sld_fin, ind_dc_fin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I155",
                *self._ctx(ctx),
                reg.i150_linha_arquivo, reg.cod_cta, reg.cod_ccus,
                self._f(reg.vl_sld_ini), reg.ind_dc_ini,
                self._f(reg.vl_deb), self._f(reg.vl_cred),
                self._f(reg.vl_sld_fin), reg.ind_dc_fin,
            ),
        )

    def inserir_ecd_i200(
        self, conn: sqlite3.Connection, reg: RegEcdI200, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i200
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                num_lcto, dt_lcto, vl_lcto, ind_lcto, dt_lcto_ext)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I200",
                *self._ctx(ctx),
                reg.num_lcto, reg.dt_lcto, self._f(reg.vl_lcto),
                reg.ind_lcto, reg.dt_lcto_ext,
            ),
        )

    def inserir_ecd_i250(
        self, conn: sqlite3.Connection, reg: RegEcdI250, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_i250
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                i200_linha_arquivo, cod_cta, cod_ccus, vl_deb_cred, ind_dc,
                hist_lcto_ccus, cod_hist_pad)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "I", "I250",
                *self._ctx(ctx),
                reg.i200_linha_arquivo, reg.cod_cta, reg.cod_ccus,
                self._f(reg.vl_deb_cred), reg.ind_dc,
                reg.hist_lcto_ccus, reg.cod_hist_pad,
            ),
        )

    def inserir_ecd_j005(
        self, conn: sqlite3.Connection, reg: RegEcdJ005, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_j005
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                dt_ini_dem, dt_fin_dem, id_dem)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "J", "J005",
                *self._ctx(ctx),
                reg.dt_ini, reg.dt_fin, reg.id_dem,
            ),
        )

    def inserir_ecd_j150(
        self, conn: sqlite3.Connection, reg: RegEcdJ150, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_j150
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                j005_linha_arquivo, nu_ordem, cod_agl, ind_cod_agl, nivel_agl,
                cod_agl_sup, descr_cod_agl, vl_cta_ini, ind_dc_ini,
                vl_cta_fin, ind_dc_fin, ind_grp_dre)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "J", "J150",
                *self._ctx(ctx),
                reg.j005_linha_arquivo, reg.nu_ordem, reg.cod_agl,
                reg.ind_cod_agl, reg.nivel_agl, reg.cod_agl_sup,
                reg.descr_cod_agl, self._f(reg.vl_cta_ini), reg.ind_dc_ini,
                self._f(reg.vl_cta_fin), reg.ind_dc_fin, reg.ind_grp_dre,
            ),
        )

    def inserir_ecd_j100(
        self, conn: sqlite3.Connection, reg: RegEcdJ100, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecd_j100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                j005_linha_arquivo, nu_ordem, cod_agl, ind_cod_agl, nivel_agl,
                cod_agl_sup, ind_grp_bal, descr_cod_agl,
                vl_cta_ini, ind_dc_ini, vl_cta_fin, ind_dc_fin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "J", "J100",
                *self._ctx(ctx),
                reg.j005_linha_arquivo, reg.nu_ordem, reg.cod_agl,
                reg.ind_cod_agl, reg.nivel_agl, reg.cod_agl_sup,
                reg.ind_grp_bal, reg.descr_cod_agl,
                self._f(reg.vl_cta_ini), reg.ind_dc_ini,
                self._f(reg.vl_cta_fin), reg.ind_dc_fin,
            ),
        )

    # Sprint 7 — ECD queries

    def consultar_ecd_ind_mudanc_pc(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> str | None:
        """
        Retorna IND_MUDANC_PC do ECD 0000 para o CNPJ × ano-calendário.

        None quando a ECD não foi importada.
        Usado pela classificação de reconciliação de plano de contas (§16.2).
        """
        row = conn.execute(
            "SELECT ind_mudanc_pc FROM ecd_0000"
            " WHERE cnpj_declarante=? AND ano_calendario=?"
            " ORDER BY linha_arquivo LIMIT 1",
            (cnpj, ano_calendario),
        ).fetchone()
        return row["ind_mudanc_pc"] if row else None

    def consultar_ecd_i050(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """Plano de contas analítico — para CR-40, CR-42."""
        cur = conn.execute(
            "SELECT * FROM ecd_i050 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecd_c050(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """Plano de contas recuperado (Bloco C) — para template de reconciliação §16.6."""
        cur = conn.execute(
            "SELECT * FROM ecd_c050 WHERE cnpj_declarante=? AND ano_calendario=?"
            " ORDER BY cod_cta",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def contar_ecd_i050_analitico(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> int:
        """Número de contas analíticas no plano atual (I050 com IND_CTA='A')."""
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM ecd_i050"
            " WHERE cnpj_declarante=? AND ano_calendario=? AND ind_cta='A'",
            (cnpj, ano_calendario),
        ).fetchone()
        return row["n"] if row else 0

    def contar_ecd_c050(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> int:
        """Número de contas no plano recuperado (C050) — §16.2."""
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM ecd_c050"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        ).fetchone()
        return row["n"] if row else 0

    def contar_ecd_c155(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> int:
        """Número de saldos recuperados (C155) — §16.2."""
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM ecd_c155"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        ).fetchone()
        return row["n"] if row else 0

    # Reconciliação manual de plano de contas (§16.6)

    def inserir_reconciliacao_override(
        self,
        conn: sqlite3.Connection,
        cnpj: str,
        ano_calendario: int,
        cod_cta_atual: str,
        cod_cta_antigo: str,
        nome_antigo: str = "",
        observacoes: str = "",
        arquivo_origem: str = "",
    ) -> None:
        """Insere ou substitui um mapeamento manual COD_CTA atual → antigo."""
        conn.execute(
            """INSERT INTO reconciliacao_override
               (cnpj, ano_calendario, cod_cta_atual, cod_cta_antigo,
                nome_antigo, observacoes, importado_em, arquivo_origem)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(cnpj, ano_calendario, cod_cta_atual) DO UPDATE SET
                  cod_cta_antigo=excluded.cod_cta_antigo,
                  nome_antigo=excluded.nome_antigo,
                  observacoes=excluded.observacoes,
                  importado_em=excluded.importado_em,
                  arquivo_origem=excluded.arquivo_origem""",
            (
                cnpj, ano_calendario, cod_cta_atual, cod_cta_antigo,
                nome_antigo or "", observacoes or "",
                _agora(), arquivo_origem or "",
            ),
        )

    def consultar_reconciliacao_overrides(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """Lista todos os overrides manuais para o CNPJ × ano-calendário."""
        cur = conn.execute(
            "SELECT * FROM reconciliacao_override"
            " WHERE cnpj=? AND ano_calendario=?"
            " ORDER BY cod_cta_atual",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def contar_reconciliacao_overrides(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> int:
        """Número de linhas de override — insumo para classificação §16.2."""
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM reconciliacao_override"
            " WHERE cnpj=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        ).fetchone()
        return row["n"] if row else 0

    def limpar_reconciliacao_overrides(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> int:
        """Remove todos os overrides do CNPJ × ano. Retorna quantidade removida."""
        cur = conn.execute(
            "DELETE FROM reconciliacao_override"
            " WHERE cnpj=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return cur.rowcount

    def consultar_ecd_i155_por_periodo(
        self, conn: sqlite3.Connection, cnpj: str, ano_mes: int
    ) -> list[dict]:
        """I155 para um mês específico — para CR-38."""
        cur = conn.execute(
            "SELECT * FROM ecd_i155 WHERE cnpj_declarante=? AND ano_mes=?",
            (cnpj, ano_mes),
        )
        return [dict(row) for row in cur]

    def consultar_ecd_i155_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """I155 de todo o ano — para CR-38 anual."""
        cur = conn.execute(
            "SELECT * FROM ecd_i155"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecd_i200_extemporaneos(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """I200 com IND_LCTO='X' (extemporâneos) — para CR-41."""
        cur = conn.execute(
            "SELECT * FROM ecd_i200"
            " WHERE cnpj_declarante=? AND ano_calendario=? AND ind_lcto='X'",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecd_j150_dre(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """J150 da DRE (id_dem='02') — para CR-39."""
        cur = conn.execute(
            """SELECT j150.* FROM ecd_j150 j150
               JOIN ecd_j005 j005 ON j005.linha_arquivo = j150.j005_linha_arquivo
                    AND j005.cnpj_declarante = j150.cnpj_declarante
               WHERE j150.cnpj_declarante=? AND j150.ano_calendario=?
                 AND j005.id_dem='02'""",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_m200_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """M200 de todos os meses do ano — para CR-38."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m200"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_m210_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """M210 de todos os meses do ano — para CR-39."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_m210"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_c170_cod_cta(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """COD_CTA distintos usados em C170 — para CR-40."""
        cur = conn.execute(
            "SELECT DISTINCT cod_cta FROM efd_contrib_c170"
            " WHERE cnpj_declarante=? AND ano_calendario=? AND cod_cta IS NOT NULL AND cod_cta != ''",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_1100_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """1100 de todos os meses do ano — para CR-41."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_1100"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_1500_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """1500 de todos os meses do ano — para CR-41."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_1500"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_0200_anual(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """0200 de todos os meses do ano — para CR-42."""
        cur = conn.execute(
            "SELECT * FROM efd_contrib_0200"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    # Sprint 8 — ECF inserters

    def inserir_ecf_0000(
        self, conn: sqlite3.Connection, reg: RegEcf0000, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_0000
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                nome, ind_sit_ini_per, sit_especial, dt_ini, dt_fin,
                retificadora, tip_ecf)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0000",
                *self._ctx(ctx),
                reg.nome, reg.ind_sit_ini_per, reg.sit_especial,
                reg.dt_ini, reg.dt_fin, reg.retificadora, reg.tip_ecf,
            ),
        )

    def inserir_ecf_0010(
        self, conn: sqlite3.Connection, reg: RegEcf0010, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_0010
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                forma_trib, forma_apur, cod_qualif_pj, tip_esc_pre)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "0", "0010",
                *self._ctx(ctx),
                reg.forma_trib, reg.forma_apur, reg.cod_qualif_pj, reg.tip_esc_pre,
            ),
        )

    def inserir_ecf_k155(
        self, conn: sqlite3.Connection, reg: RegEcfK155, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_k155
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cta, cod_ccus, vl_sld_ini, ind_vl_sld_ini,
                vl_deb, vl_cred, vl_sld_fin, ind_vl_sld_fin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "K", "K155",
                *self._ctx(ctx),
                reg.cod_cta, reg.cod_ccus,
                self._f(reg.vl_sld_ini), reg.ind_vl_sld_ini,
                self._f(reg.vl_deb), self._f(reg.vl_cred),
                self._f(reg.vl_sld_fin), reg.ind_vl_sld_fin,
            ),
        )

    def inserir_ecf_k355(
        self, conn: sqlite3.Connection, reg: RegEcfK355, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_k355
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cta, cod_ccus, vl_sld_ini, ind_vl_sld_ini,
                vl_deb, vl_cred, vl_sld_fin, ind_vl_sld_fin)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "K", "K355",
                *self._ctx(ctx),
                reg.cod_cta, reg.cod_ccus,
                self._f(reg.vl_sld_ini), reg.ind_vl_sld_ini,
                self._f(reg.vl_deb), self._f(reg.vl_cred),
                self._f(reg.vl_sld_fin), reg.ind_vl_sld_fin,
            ),
        )

    def inserir_ecf_m300(
        self, conn: sqlite3.Connection, reg: RegEcfM300, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_m300
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                codigo, descricao, tipo_lancamento, ind_relacao, valor, hist_lan_lal)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M300",
                *self._ctx(ctx),
                reg.codigo, reg.descricao, reg.tipo_lancamento,
                reg.ind_relacao, self._f(reg.valor), reg.hist_lan_lal,
            ),
        )

    def inserir_ecf_m312(
        self, conn: sqlite3.Connection, reg: RegEcfM312, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_m312
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                m300_linha_arquivo, num_lcto)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M312",
                *self._ctx(ctx),
                reg.m300_linha_arquivo, reg.num_lcto,
            ),
        )

    def inserir_ecf_m350(
        self, conn: sqlite3.Connection, reg: RegEcfM350, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_m350
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                codigo, descricao, tipo_lancamento, ind_relacao, valor, hist_lan_lal)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M350",
                *self._ctx(ctx),
                reg.codigo, reg.descricao, reg.tipo_lancamento,
                reg.ind_relacao, self._f(reg.valor), reg.hist_lan_lal,
            ),
        )

    def inserir_ecf_m362(
        self, conn: sqlite3.Connection, reg: RegEcfM362, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_m362
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                m350_linha_arquivo, num_lcto)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M362",
                *self._ctx(ctx),
                reg.m350_linha_arquivo, reg.num_lcto,
            ),
        )

    def inserir_ecf_m500(
        self, conn: sqlite3.Connection, reg: RegEcfM500, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_m500
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_cta_b, cod_tributo,
                sd_ini_lal, ind_sd_ini_lal,
                vl_lcto_parte_a, ind_vl_lcto_parte_a,
                vl_lcto_parte_b, ind_vl_lcto_parte_b,
                sd_fim_lal, ind_sd_fim_lal)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "M", "M500",
                *self._ctx(ctx),
                reg.cod_cta_b, reg.cod_tributo,
                self._f(reg.sd_ini_lal), reg.ind_sd_ini_lal,
                self._f(reg.vl_lcto_parte_a), reg.ind_vl_lcto_parte_a,
                self._f(reg.vl_lcto_parte_b), reg.ind_vl_lcto_parte_b,
                self._f(reg.sd_fim_lal), reg.ind_sd_fim_lal,
            ),
        )

    def inserir_ecf_x460(
        self, conn: sqlite3.Connection, reg: RegEcfX460, ctx: dict
    ) -> None:
        """X460 — dispêndios com inovação tecnológica (Lei do Bem, §8.6)."""
        conn.execute(
            """INSERT INTO ecf_x460
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                codigo, descricao, valor)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "X", "X460",
                *self._ctx(ctx),
                reg.codigo, reg.descricao, self._f(reg.valor),
            ),
        )

    def inserir_ecf_9100(
        self, conn: sqlite3.Connection, reg: RegEcf9100, ctx: dict
    ) -> None:
        """9100 — avisos emitidos pelo PGE na validação (ECF layout §22.1)."""
        conn.execute(
            """INSERT INTO ecf_9100
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                cod_aviso, descr_aviso, reg_ref, campo_ref)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "9", "9100",
                *self._ctx(ctx),
                reg.cod_aviso, reg.descr_aviso, reg.reg_ref, reg.campo_ref,
            ),
        )

    def inserir_ecf_x480(
        self, conn: sqlite3.Connection, reg: RegEcfX480, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_x480
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                codigo, descricao, valor, ind_valor)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "X", "X480",
                *self._ctx(ctx),
                reg.codigo, reg.descricao, self._f(reg.valor), reg.ind_valor,
            ),
        )

    def inserir_ecf_y570(
        self, conn: sqlite3.Connection, reg: RegEcfY570, ctx: dict
    ) -> None:
        conn.execute(
            """INSERT INTO ecf_y570
               (arquivo_origem, linha_arquivo, bloco, registro, cnpj_declarante,
                dt_ini_periodo, dt_fin_periodo, ano_mes, ano_calendario, cod_ver,
                per_apu, nat_rend, vl_ir_ret, vl_csll_ret)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                reg.arquivo_origem, reg.linha_arquivo, "Y", "Y570",
                *self._ctx(ctx),
                reg.per_apu, reg.nat_rend,
                self._f(reg.vl_ir_ret), self._f(reg.vl_csll_ret),
            ),
        )

    # Sprint 8 — ECF queries

    def consultar_ecf_k155(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """K155 (patrimonial) — para CR-43."""
        cur = conn.execute(
            "SELECT * FROM ecf_k155 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_k355(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """K355 (resultado) — para CR-43."""
        cur = conn.execute(
            "SELECT * FROM ecf_k355 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_m300(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """M300 (e-Lalur Parte A) — para CR-44, CR-46."""
        cur = conn.execute(
            "SELECT * FROM ecf_m300 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_m312(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """M312 (NUM_LCTO → link ECD) — para CR-44."""
        cur = conn.execute(
            "SELECT * FROM ecf_m312 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_m500(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """M500 (Parte B) — para CR-45."""
        cur = conn.execute(
            "SELECT * FROM ecf_m500 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_x460(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """X460 (inovação tecnológica — Lei do Bem) — para CR-49."""
        cur = conn.execute(
            "SELECT * FROM ecf_x460 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_x480(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """X480 (benefícios fiscais) — para CR-46."""
        cur = conn.execute(
            "SELECT * FROM ecf_x480 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_9100(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """9100 (avisos do PGE) — para CR-48."""
        cur = conn.execute(
            "SELECT * FROM ecf_9100"
            " WHERE cnpj_declarante=? AND ano_calendario=?"
            " ORDER BY linha_arquivo",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecf_y570(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> list[dict]:
        """Y570 (IRRF/CSRF retidos) — para CR-47."""
        cur = conn.execute(
            "SELECT * FROM ecf_y570 WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return [dict(row) for row in cur]

    def consultar_ecd_i155_fin_por_conta(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> dict[str, float]:
        """I155 VL_SLD_FIN por COD_CTA — saldo final do último mês do ano. Para CR-43."""
        cur = conn.execute(
            """SELECT cod_cta,
                      SUM(CASE WHEN ind_dc_fin='D' THEN -vl_sld_fin ELSE vl_sld_fin END) AS saldo
               FROM ecd_i155
               WHERE cnpj_declarante=? AND ano_calendario=?
               GROUP BY cod_cta""",
            (cnpj, ano_calendario),
        )
        return {row["cod_cta"]: float(row["saldo"]) for row in cur}

    def consultar_ecd_num_lcto_set(
        self, conn: sqlite3.Connection, cnpj: str, ano_calendario: int
    ) -> set[str]:
        """Set de NUM_LCTO existentes na ECD — para CR-44."""
        cur = conn.execute(
            "SELECT DISTINCT num_lcto FROM ecd_i200"
            " WHERE cnpj_declarante=? AND ano_calendario=?",
            (cnpj, ano_calendario),
        )
        return {row[0] for row in cur}
