-- Schema Sprint 1 — EFD-Contribuições
-- Banco por CNPJ × ano-calendário: data/db/{cnpj}/{ano_calendario}.sqlite
-- Todas as tabelas derivadas têm colunas de auditoria obrigatórias (CLAUDE.md §7.1).

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- Infraestrutura de controle (criada desde Sprint 1)
-- ============================================================

CREATE TABLE IF NOT EXISTS _importacoes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sped_tipo        TEXT    NOT NULL,  -- "efd_contribuicoes", "ecd", "ecf", "efd_icms"
    dt_ini           TEXT    NOT NULL,  -- YYYY-MM-DD
    dt_fin           TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,  -- YYYYMM (mês de referência da competência)
    arquivo_hash     TEXT    NOT NULL,  -- SHA-256 do arquivo original
    arquivo_origem   TEXT    NOT NULL,  -- caminho absoluto
    importado_em     TEXT    NOT NULL,  -- ISO-8601
    cod_ver          TEXT    NOT NULL,
    encoding_origem  TEXT    NOT NULL,  -- "utf8" ou "latin1"
    encoding_confianca TEXT  NOT NULL,  -- "alto", "validado", "suspeito"
    status           TEXT    NOT NULL   -- "ok", "rejeitado", "parcial"
);

-- Override manual de reconciliação de plano de contas (CLAUDE.md §16.6).
-- Preenchido pelo comando `primetax-sped reconciliacao-import` a partir do
-- template gerado pelo comando `reconciliacao-template`. Cada linha mapeia
-- a COD_CTA atual (pós-mudança) à COD_CTA antiga (pré-mudança) declarada
-- pelo auditor — permite elevar o estado de reconciliação de 'ausente'
-- ou 'suspeita' para 'integra' quando a cobertura for suficiente.
CREATE TABLE IF NOT EXISTS reconciliacao_override (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj              TEXT    NOT NULL,
    ano_calendario    INTEGER NOT NULL,
    cod_cta_atual     TEXT    NOT NULL,
    cod_cta_antigo    TEXT    NOT NULL,
    nome_antigo       TEXT,
    observacoes       TEXT,
    importado_em      TEXT    NOT NULL,  -- ISO-8601
    arquivo_origem    TEXT,
    UNIQUE(cnpj, ano_calendario, cod_cta_atual)
);
CREATE INDEX IF NOT EXISTS idx_reconciliacao_override_cnpj
    ON reconciliacao_override(cnpj, ano_calendario);

-- Controle de disponibilidade por SPED (infraestrutura para Sprint 6+)
-- Semântica ativa apenas a partir do Sprint 6. Sprint 1 só cria a tabela.
CREATE TABLE IF NOT EXISTS _sped_contexto (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj                     TEXT    NOT NULL,
    ano_calendario           INTEGER NOT NULL,
    disponibilidade_efd_contrib  TEXT DEFAULT 'pendente',
    disponibilidade_efd_icms     TEXT DEFAULT 'pendente',
    disponibilidade_ecd          TEXT DEFAULT 'pendente',
    disponibilidade_ecf          TEXT DEFAULT 'pendente',
    disponibilidade_bloco_i      TEXT DEFAULT 'pendente',
    reconciliacao_plano_contas   TEXT DEFAULT NULL,  -- integra/suspeita/ausente (Sprint 7+)
    atualizado_em            TEXT NOT NULL,
    UNIQUE(cnpj, ano_calendario)
);

-- ============================================================
-- Bloco 0
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_0000 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0000',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    nome             TEXT    NOT NULL,
    cpf              TEXT,
    uf               TEXT,
    ie               TEXT,
    cod_mun          TEXT,
    im               TEXT,
    suframa          TEXT,
    ind_perfil       TEXT,
    ind_ativ         TEXT
);
CREATE INDEX IF NOT EXISTS idx_0000_cnpj_ano ON efd_contrib_0000(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_0110 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0110',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_inc_trib     TEXT    NOT NULL,
    ind_apro_cred    TEXT    NOT NULL,
    cod_tipo_cont    TEXT,
    ind_reg_cum      TEXT
);
CREATE INDEX IF NOT EXISTS idx_0110_cnpj_ano ON efd_contrib_0110(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_0111 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0111',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    rec_brt_ncum_trib_mi  REAL NOT NULL DEFAULT 0,
    rec_brt_ncum_nt_mi    REAL NOT NULL DEFAULT 0,
    rec_brt_ncum_exp      REAL NOT NULL DEFAULT 0,
    rec_brt_cum           REAL NOT NULL DEFAULT 0,
    rec_brt_total         REAL NOT NULL DEFAULT 0
);

-- ============================================================
-- Bloco C
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_c100 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'C',
    registro         TEXT    NOT NULL DEFAULT 'C100',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_oper         TEXT,
    ind_emit         TEXT,
    cod_part         TEXT,
    cod_mod          TEXT,
    cod_sit          TEXT,
    ser              TEXT,
    num_doc          TEXT,
    chave_nfe        TEXT,
    dt_doc           TEXT,
    vl_doc           REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_c100_cnpj_ano ON efd_contrib_c100(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_c100_linha ON efd_contrib_c100(linha_arquivo);

CREATE TABLE IF NOT EXISTS efd_contrib_c170 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'C',
    registro             TEXT    NOT NULL DEFAULT 'C170',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    -- Vínculo pai
    c100_linha_arquivo   INTEGER NOT NULL,
    -- Campos do item
    num_item             TEXT,
    cod_item             TEXT,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_desc              REAL    NOT NULL DEFAULT 0,
    cfop                 TEXT,
    vl_icms              REAL    NOT NULL DEFAULT 0,  -- campo 15: ICMS próprio
    vl_icms_st           REAL    NOT NULL DEFAULT 0,  -- campo 18: ICMS-ST
    cst_pis              TEXT    NOT NULL,
    vl_bc_pis            REAL    NOT NULL DEFAULT 0,
    aliq_pis             REAL    NOT NULL DEFAULT 0,
    quant_bc_pis         REAL    NOT NULL DEFAULT 0,
    aliq_pis_quant       REAL    NOT NULL DEFAULT 0,
    vl_pis               REAL    NOT NULL DEFAULT 0,
    cst_cofins           TEXT    NOT NULL,
    vl_bc_cofins         REAL    NOT NULL DEFAULT 0,
    aliq_cofins          REAL    NOT NULL DEFAULT 0,
    quant_bc_cofins      REAL    NOT NULL DEFAULT 0,
    aliq_cofins_quant    REAL    NOT NULL DEFAULT 0,
    vl_cofins            REAL    NOT NULL DEFAULT 0,
    cod_cta              TEXT    -- chave universal de cruzamento EFD↔ECD (Sprint 7+)
);
CREATE INDEX IF NOT EXISTS idx_c170_cnpj_ano ON efd_contrib_c170(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_c170_cst_pis  ON efd_contrib_c170(cst_pis);
CREATE INDEX IF NOT EXISTS idx_c170_linha    ON efd_contrib_c170(linha_arquivo);
CREATE INDEX IF NOT EXISTS idx_c170_c100     ON efd_contrib_c170(c100_linha_arquivo);

-- ============================================================
-- Bloco C — Sprint 2: NFC-e consolidada (C181 / C185)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_c181 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'C',
    registro             TEXT    NOT NULL DEFAULT 'C181',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    c180_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_oper             TEXT    NOT NULL DEFAULT '',
    cst_pis              TEXT    NOT NULL,
    cfop                 TEXT,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_desc              REAL    NOT NULL DEFAULT 0,
    vl_bc_pis            REAL    NOT NULL DEFAULT 0,
    aliq_pis             REAL    NOT NULL DEFAULT 0,
    quant_bc_pis         REAL    NOT NULL DEFAULT 0,
    aliq_pis_quant       REAL    NOT NULL DEFAULT 0,
    vl_pis               REAL    NOT NULL DEFAULT 0,
    cod_cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_c181_cnpj_ano ON efd_contrib_c181(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_c181_cst_pis  ON efd_contrib_c181(cst_pis);

CREATE TABLE IF NOT EXISTS efd_contrib_c185 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'C',
    registro             TEXT    NOT NULL DEFAULT 'C185',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    c180_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_oper             TEXT    NOT NULL DEFAULT '',
    cst_cofins           TEXT    NOT NULL,
    cfop                 TEXT,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_desc              REAL    NOT NULL DEFAULT 0,
    vl_bc_cofins         REAL    NOT NULL DEFAULT 0,
    aliq_cofins          REAL    NOT NULL DEFAULT 0,
    quant_bc_cofins      REAL    NOT NULL DEFAULT 0,
    aliq_cofins_quant    REAL    NOT NULL DEFAULT 0,
    vl_cofins            REAL    NOT NULL DEFAULT 0,
    cod_cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_c185_cnpj_ano ON efd_contrib_c185(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco D — Sprint 2: serviços de transporte (D201 / D205)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_d201 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'D',
    registro             TEXT    NOT NULL DEFAULT 'D201',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    d200_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_oper             TEXT    NOT NULL DEFAULT '',
    cst_pis              TEXT    NOT NULL,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_bc_pis            REAL    NOT NULL DEFAULT 0,
    aliq_pis             REAL    NOT NULL DEFAULT 0,
    quant_bc_pis         REAL    NOT NULL DEFAULT 0,
    aliq_pis_quant       REAL    NOT NULL DEFAULT 0,
    vl_pis               REAL    NOT NULL DEFAULT 0,
    cod_cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_d201_cnpj_ano ON efd_contrib_d201(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_d201_cst_pis  ON efd_contrib_d201(cst_pis);

CREATE TABLE IF NOT EXISTS efd_contrib_d205 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'D',
    registro             TEXT    NOT NULL DEFAULT 'D205',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    d200_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_oper             TEXT    NOT NULL DEFAULT '',
    cst_cofins           TEXT    NOT NULL,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_bc_cofins         REAL    NOT NULL DEFAULT 0,
    aliq_cofins          REAL    NOT NULL DEFAULT 0,
    quant_bc_cofins      REAL    NOT NULL DEFAULT 0,
    aliq_cofins_quant    REAL    NOT NULL DEFAULT 0,
    vl_cofins            REAL    NOT NULL DEFAULT 0,
    cod_cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_d205_cnpj_ano ON efd_contrib_d205(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco M — Sprint 2: ajuste de base (M215 PIS / M615 COFINS)
-- Introduzido no leiaute 3.1.0 (janeiro/2019). CLAUDE.md §5.2.
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_m215 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'M',
    registro             TEXT    NOT NULL DEFAULT 'M215',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    m210_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_aj_bc            TEXT    NOT NULL,
    vl_aj_bc             REAL    NOT NULL DEFAULT 0,
    cod_aj_bc            TEXT,
    num_doc              TEXT,
    descr_aj_bc          TEXT,
    dt_ref               TEXT,
    cod_cta              TEXT,
    cnpj_ref             TEXT
);
CREATE INDEX IF NOT EXISTS idx_m215_cnpj_ano ON efd_contrib_m215(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_m215_ind_aj   ON efd_contrib_m215(ind_aj_bc);

CREATE TABLE IF NOT EXISTS efd_contrib_m615 (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem       TEXT    NOT NULL,
    linha_arquivo        INTEGER NOT NULL,
    bloco                TEXT    NOT NULL DEFAULT 'M',
    registro             TEXT    NOT NULL DEFAULT 'M615',
    cnpj_declarante      TEXT    NOT NULL,
    dt_ini_periodo       TEXT    NOT NULL,
    dt_fin_periodo       TEXT    NOT NULL,
    ano_mes              INTEGER NOT NULL,
    ano_calendario       INTEGER NOT NULL,
    cod_ver              TEXT    NOT NULL,
    m610_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_aj_bc            TEXT    NOT NULL,
    vl_aj_bc             REAL    NOT NULL DEFAULT 0,
    cod_aj_bc            TEXT,
    num_doc              TEXT,
    descr_aj_bc          TEXT,
    dt_ref               TEXT,
    cod_cta              TEXT,
    cnpj_ref             TEXT
);
CREATE INDEX IF NOT EXISTS idx_m615_cnpj_ano ON efd_contrib_m615(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco M (mínimo Sprint 1 — campos expandidos em Sprint 3+)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_m200 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M200',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    vl_tot_cont_nc_per    REAL    DEFAULT 0,
    vl_tot_cred_desc      REAL    DEFAULT 0,  -- campo 3 — Σ M100.VL_CRED_DESC (Sprint 4+)
    vl_rec_brt_total      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m200_cnpj_ano ON efd_contrib_m200(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_m600 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M600',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    vl_tot_cont_nc_per    REAL    DEFAULT 0,
    vl_tot_cred_desc      REAL    DEFAULT 0,  -- campo 3 — Σ M500.VL_CRED_DESC (Sprint 4+)
    vl_rec_brt_total      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m600_cnpj_ano ON efd_contrib_m600(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco F — Sprint 3: retenções na fonte (F600 PIS / F700 COFINS)
-- Base legal: Art. 30, 33 e 34 da Lei 10.833/2003.
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_f600 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'F',
    registro         TEXT    NOT NULL DEFAULT 'F600',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_nat_ret      TEXT,
    dt_ret           TEXT,
    vl_bc_ret        REAL    DEFAULT 0,
    aliq_ret         REAL    DEFAULT 0,
    vl_ret_apu       REAL    DEFAULT 0,
    cod_rec          TEXT,
    ind_nat_rec      TEXT,
    pr_rec_ret       TEXT,
    cnpj_fonte_pag   TEXT,
    vl_ret_per       REAL    DEFAULT 0,
    vl_ret_dcomp     REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_f600_cnpj_ano ON efd_contrib_f600(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_f600_dt_ret   ON efd_contrib_f600(dt_ret);

CREATE TABLE IF NOT EXISTS efd_contrib_f700 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'F',
    registro         TEXT    NOT NULL DEFAULT 'F700',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_nat_ret      TEXT,
    dt_ret           TEXT,
    vl_bc_ret        REAL    DEFAULT 0,
    aliq_ret         REAL    DEFAULT 0,
    vl_ret_apu       REAL    DEFAULT 0,
    cod_rec          TEXT,
    ind_nat_rec      TEXT,
    pr_rec_ret       TEXT,
    cnpj_fonte_pag   TEXT,
    vl_ret_per       REAL    DEFAULT 0,
    vl_ret_dcomp     REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_f700_cnpj_ano ON efd_contrib_f700(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_f700_dt_ret   ON efd_contrib_f700(dt_ret);

-- ============================================================
-- Bloco M — Sprint 3: contribuição por CST/alíquota (M210 / M610)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_m210 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'M',
    registro         TEXT    NOT NULL DEFAULT 'M210',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_cont         TEXT    NOT NULL,
    vl_rec_brt       REAL    DEFAULT 0,
    vl_bc_cont       REAL    DEFAULT 0,
    aliq_pis         REAL    DEFAULT 0,
    vl_cont_apu      REAL    DEFAULT 0,
    vl_ajus_reduc    REAL    DEFAULT 0,
    vl_cont_per      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m210_cnpj_ano ON efd_contrib_m210(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_m610 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'M',
    registro         TEXT    NOT NULL DEFAULT 'M610',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_cont         TEXT    NOT NULL,
    vl_rec_brt       REAL    DEFAULT 0,
    vl_bc_cont       REAL    DEFAULT 0,
    aliq_cofins      REAL    DEFAULT 0,
    vl_cont_apu      REAL    DEFAULT 0,
    vl_ajus_reduc    REAL    DEFAULT 0,
    vl_cont_per      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m610_cnpj_ano ON efd_contrib_m610(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco F — Sprint 4: ativo imobilizado e estoque de abertura
-- Base legal: Art. 3º, VI Lei 10.637/2002 e 10.833/2003.
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_f120 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'F',
    registro              TEXT    NOT NULL DEFAULT 'F120',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    nat_bc_cred           TEXT,             -- fixo "09"
    ident_bem_imob        TEXT,
    ind_orig_cred         TEXT,
    ind_util_bem_imob     TEXT,             -- 1=Prod; 2=Serv; 3=Loc; 9=Vedado
    vl_oper_dep           REAL    DEFAULT 0,
    parc_oper_nao_bc_cred REAL    DEFAULT 0,
    cst_pis               TEXT,
    vl_bc_pis             REAL    DEFAULT 0,
    aliq_pis              REAL    DEFAULT 0,
    vl_pis                REAL    DEFAULT 0,
    cst_cofins            TEXT,
    vl_bc_cofins          REAL    DEFAULT 0,
    aliq_cofins           REAL    DEFAULT 0,
    vl_cofins             REAL    DEFAULT 0,
    cod_cta               TEXT,
    cod_ccus              TEXT,
    desc_bem_imob         TEXT
);
CREATE INDEX IF NOT EXISTS idx_f120_cnpj_ano      ON efd_contrib_f120(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_f120_ind_util       ON efd_contrib_f120(ind_util_bem_imob);

CREATE TABLE IF NOT EXISTS efd_contrib_f130 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'F',
    registro              TEXT    NOT NULL DEFAULT 'F130',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    nat_bc_cred           TEXT,             -- fixo "10"
    ident_bem_imob        TEXT,
    ind_orig_cred         TEXT,
    ind_util_bem_imob     TEXT,             -- 1=Prod; 2=Serv; 3=Loc; 9=Vedado
    mes_oper_aquis        TEXT,             -- mmaaaa
    vl_oper_aquis         REAL    DEFAULT 0,
    parc_oper_nao_bc_cred REAL    DEFAULT 0,
    vl_bc_cred            REAL    DEFAULT 0,
    ind_nr_parc           TEXT,             -- 1=Integral; 2=12m; 3=24m; 4=48m
    cst_pis               TEXT,
    vl_bc_pis             REAL    DEFAULT 0,
    aliq_pis              REAL    DEFAULT 0,
    vl_pis                REAL    DEFAULT 0,
    cst_cofins            TEXT,
    vl_bc_cofins          REAL    DEFAULT 0,
    aliq_cofins           REAL    DEFAULT 0,
    vl_cofins             REAL    DEFAULT 0,
    cod_cta               TEXT,
    cod_ccus              TEXT,
    desc_bem_imob         TEXT
);
CREATE INDEX IF NOT EXISTS idx_f130_cnpj_ano      ON efd_contrib_f130(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_f130_ind_util       ON efd_contrib_f130(ind_util_bem_imob);

CREATE TABLE IF NOT EXISTS efd_contrib_f150 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'F',
    registro              TEXT    NOT NULL DEFAULT 'F150',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    nat_bc_cred           TEXT,             -- fixo "18"
    vl_tot_est            REAL    DEFAULT 0,
    est_imp               REAL    DEFAULT 0,
    vl_bc_est             REAL    DEFAULT 0,
    vl_bc_men_est         REAL    DEFAULT 0, -- base mensal = vl_bc_est / 12
    cst_pis               TEXT,
    aliq_pis              REAL    DEFAULT 0, -- fixo 0,65
    vl_cred_pis           REAL    DEFAULT 0,
    cst_cofins            TEXT,
    aliq_cofins           REAL    DEFAULT 0, -- fixo 3,0
    vl_cred_cofins        REAL    DEFAULT 0,
    desc_est              TEXT,
    cod_cta               TEXT
);
CREATE INDEX IF NOT EXISTS idx_f150_cnpj_ano ON efd_contrib_f150(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco M — Sprint 4: créditos PIS/COFINS por tipo (M100/M500)
-- CR-29: Σ M100.VL_CRED_DESC = M200.VL_TOT_CRED_DESC
-- CR-30: Σ M500.VL_CRED_DESC = M600.VL_TOT_CRED_DESC
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_m100 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M100',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    cod_cred              TEXT,
    ind_cred_ori          TEXT,
    vl_bc_pis             REAL    DEFAULT 0,
    aliq_pis              REAL    DEFAULT 0,
    quant_bc_pis          REAL    DEFAULT 0,
    aliq_pis_quant        REAL    DEFAULT 0,
    vl_cred_disp          REAL    DEFAULT 0,
    vl_ajus_acres         REAL    DEFAULT 0,
    vl_ajus_reduc         REAL    DEFAULT 0,
    vl_cred_difer         REAL    DEFAULT 0,
    vl_cred_difer_ant     REAL    DEFAULT 0,
    ind_apro              TEXT,
    vl_cred_desc          REAL    DEFAULT 0, -- → Σ = M200.VL_TOT_CRED_DESC
    sld_cred              REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m100_cnpj_ano ON efd_contrib_m100(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_m500 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M500',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    cod_cred              TEXT,
    ind_cred_ori          TEXT,
    vl_bc_cofins          REAL    DEFAULT 0,
    aliq_cofins           REAL    DEFAULT 0,
    quant_bc_cofins       REAL    DEFAULT 0,
    aliq_cofins_quant     REAL    DEFAULT 0,
    vl_cred_disp          REAL    DEFAULT 0,
    vl_ajus_acres         REAL    DEFAULT 0,
    vl_ajus_reduc         REAL    DEFAULT 0,
    vl_cred_difer         REAL    DEFAULT 0,
    vl_cred_difer_ant     REAL    DEFAULT 0,
    ind_apro              TEXT,
    vl_cred_desc          REAL    DEFAULT 0, -- → Σ = M600.VL_TOT_CRED_DESC
    sld_cred              REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m500_cnpj_ano ON efd_contrib_m500(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco 0 — Sprint 5: catálogo de itens (0200)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_0200 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0200',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_item         TEXT    NOT NULL,
    descr_item       TEXT,
    cod_barra        TEXT,
    cod_ant_item     TEXT,
    unid_inv         TEXT,
    tipo_item        TEXT,             -- 00=Rev; 01=MP; 02=Emb; 03=PI; 04=Ativo; 05=Consumo; 06=Serv; 07=Outros
    cod_ncm          TEXT,
    ex_ipi           TEXT,
    cod_gen          TEXT,
    cod_lst          TEXT,
    aliq_icms        REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_0200_cnpj_ano  ON efd_contrib_0200(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_0200_cod_item  ON efd_contrib_0200(cod_item);
CREATE INDEX IF NOT EXISTS idx_0200_tipo_item ON efd_contrib_0200(tipo_item);

-- ============================================================
-- Bloco F — Sprint 5: F100 (demais documentos), F800 (eventos corporativos)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_f100 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'F',
    registro         TEXT    NOT NULL DEFAULT 'F100',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_oper         TEXT,
    cod_part         TEXT,
    cod_item         TEXT,
    dt_oper          TEXT,
    vl_oper          REAL    DEFAULT 0,
    cst_pis          TEXT,
    vl_bc_pis        REAL    DEFAULT 0,
    aliq_pis         REAL    DEFAULT 0,
    vl_pis           REAL    DEFAULT 0,
    cst_cofins       TEXT,
    vl_bc_cofins     REAL    DEFAULT 0,
    aliq_cofins      REAL    DEFAULT 0,
    vl_cofins        REAL    DEFAULT 0,
    nat_bc_cred      TEXT,
    ind_orig_cred    TEXT,
    cod_cta          TEXT,
    cod_ccus         TEXT,
    desc_doc_oper    TEXT
);
CREATE INDEX IF NOT EXISTS idx_f100_cnpj_ano ON efd_contrib_f100(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_f100_cst_pis  ON efd_contrib_f100(cst_pis);

CREATE TABLE IF NOT EXISTS efd_contrib_f800 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'F',
    registro              TEXT    NOT NULL DEFAULT 'F800',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    ind_transf            TEXT,
    ind_nat_transf        TEXT,             -- 01=Incorporação; 02=Fusão; 03=Cisão; 04=Extinção
    cnpj_transf           TEXT,
    dt_transf             TEXT,
    vl_transf_pis         REAL    DEFAULT 0,
    vl_transf_cofins      REAL    DEFAULT 0,
    vl_cred_pis_trans     REAL    DEFAULT 0, -- crédito PIS efetivamente transferido → CR-18
    vl_cred_cofins_trans  REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_f800_cnpj_ano ON efd_contrib_f800(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco M — Sprint 5: bases de crédito por NAT_BC_CRED (M105/M505)
-- CR-32: Σ C170/F100 VL_BC_PIS (CST 50-67) vs Σ M105.VL_BC_PIS_TOT
-- CR-34: Σ C170/F100 VL_BC_COFINS (CST 50-67) vs Σ M505.VL_BC_COFINS_TOT
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_m105 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M105',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    nat_bc_cred           TEXT    NOT NULL,
    vl_bc_pis_tot         REAL    DEFAULT 0, -- total da base PIS por nat_bc_cred
    vl_bc_minut           REAL    DEFAULT 0,
    vl_bc_mindt           REAL    DEFAULT 0,
    vl_bc_mexp            REAL    DEFAULT 0,
    vl_amt_parc_forn      REAL    DEFAULT 0,
    vl_bc_isenta          REAL    DEFAULT 0,
    vl_bc_outras          REAL    DEFAULT 0,
    desc_compl            TEXT
);
CREATE INDEX IF NOT EXISTS idx_m105_cnpj_ano    ON efd_contrib_m105(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_m105_nat_bc_cred ON efd_contrib_m105(nat_bc_cred);

CREATE TABLE IF NOT EXISTS efd_contrib_m505 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M505',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    nat_bc_cred           TEXT    NOT NULL,
    vl_bc_cofins_tot      REAL    DEFAULT 0,
    vl_bc_minut           REAL    DEFAULT 0,
    vl_bc_mindt           REAL    DEFAULT 0,
    vl_bc_mexp            REAL    DEFAULT 0,
    vl_amt_parc_forn      REAL    DEFAULT 0,
    vl_bc_isenta          REAL    DEFAULT 0,
    vl_bc_outras          REAL    DEFAULT 0,
    desc_compl            TEXT
);
CREATE INDEX IF NOT EXISTS idx_m505_cnpj_ano    ON efd_contrib_m505(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_m505_nat_bc_cred ON efd_contrib_m505(nat_bc_cred);

-- ============================================================
-- Bloco 1 — Sprint 5: carry-forward de créditos (1100/1500)
-- CR-25: SLD_CRED_FIM > 0 → crédito acumulado disponível para compensação
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_1100 (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem         TEXT    NOT NULL,
    linha_arquivo          INTEGER NOT NULL,
    bloco                  TEXT    NOT NULL DEFAULT '1',
    registro               TEXT    NOT NULL DEFAULT '1100',
    cnpj_declarante        TEXT    NOT NULL,
    dt_ini_periodo         TEXT    NOT NULL,
    dt_fin_periodo         TEXT    NOT NULL,
    ano_mes                INTEGER NOT NULL,
    ano_calendario         INTEGER NOT NULL,
    cod_ver                TEXT    NOT NULL,
    per_apu_cred           TEXT,
    orig_cred              TEXT,
    cnpj_suc               TEXT,
    cod_cred               TEXT,
    vl_cred_apu            REAL    DEFAULT 0,
    vl_cred_ext_apu        REAL    DEFAULT 0,
    vl_tot_cred_apu        REAL    DEFAULT 0,
    vl_cred_desc_pa_ant    REAL    DEFAULT 0,
    vl_cred_per_pa_ant     REAL    DEFAULT 0,
    vl_cred_dcomp_pa_ant   REAL    DEFAULT 0,
    sd_cred_disp_efd       REAL    DEFAULT 0,
    vl_cred_desc_efd       REAL    DEFAULT 0,
    vl_cred_per_efd        REAL    DEFAULT 0,
    vl_cred_dcomp_efd      REAL    DEFAULT 0,
    vl_cred_trans          REAL    DEFAULT 0,
    vl_cred_out            REAL    DEFAULT 0,
    sld_cred_fim           REAL    DEFAULT 0  -- saldo a transportar → CR-25
);
CREATE INDEX IF NOT EXISTS idx_1100_cnpj_ano ON efd_contrib_1100(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_contrib_1500 (
    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem         TEXT    NOT NULL,
    linha_arquivo          INTEGER NOT NULL,
    bloco                  TEXT    NOT NULL DEFAULT '1',
    registro               TEXT    NOT NULL DEFAULT '1500',
    cnpj_declarante        TEXT    NOT NULL,
    dt_ini_periodo         TEXT    NOT NULL,
    dt_fin_periodo         TEXT    NOT NULL,
    ano_mes                INTEGER NOT NULL,
    ano_calendario         INTEGER NOT NULL,
    cod_ver                TEXT    NOT NULL,
    per_apu_cred           TEXT,
    orig_cred              TEXT,
    cnpj_suc               TEXT,
    cod_cred               TEXT,
    vl_cred_apu            REAL    DEFAULT 0,
    vl_cred_ext_apu        REAL    DEFAULT 0,
    vl_tot_cred_apu        REAL    DEFAULT 0,
    vl_cred_desc_pa_ant    REAL    DEFAULT 0,
    vl_cred_per_pa_ant     REAL    DEFAULT 0,
    vl_cred_dcomp_pa_ant   REAL    DEFAULT 0,
    sd_cred_disp_efd       REAL    DEFAULT 0,
    vl_cred_desc_efd       REAL    DEFAULT 0,
    vl_cred_per_efd        REAL    DEFAULT 0,
    vl_cred_dcomp_efd      REAL    DEFAULT 0,
    vl_cred_trans          REAL    DEFAULT 0,
    vl_cred_out            REAL    DEFAULT 0,
    sld_cred_fim           REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_1500_cnpj_ano ON efd_contrib_1500(cnpj_declarante, ano_mes);

-- ============================================================
-- Bloco 9
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_contrib_9900 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '9',
    registro         TEXT    NOT NULL DEFAULT '9900',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    reg_blc          TEXT    NOT NULL,
    qtd_reg_blc      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_9900_cnpj_ano ON efd_contrib_9900(cnpj_declarante, ano_mes);

-- ============================================================
-- EFD ICMS/IPI — Sprint 6 (cruzamentos 35, 36, 37)
-- ============================================================

CREATE TABLE IF NOT EXISTS efd_icms_0000 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0000',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    nome             TEXT,
    uf               TEXT,
    ie               TEXT,
    ind_perfil       TEXT,
    ind_ativ         TEXT
);
CREATE INDEX IF NOT EXISTS idx_icms_0000_cnpj ON efd_icms_0000(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_icms_c100 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'C',
    registro         TEXT    NOT NULL DEFAULT 'C100',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_oper         TEXT
);
CREATE INDEX IF NOT EXISTS idx_icms_c100_cnpj_ano ON efd_icms_c100(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_icms_c170 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem      TEXT    NOT NULL,
    linha_arquivo       INTEGER NOT NULL,
    bloco               TEXT    NOT NULL DEFAULT 'C',
    registro            TEXT    NOT NULL DEFAULT 'C170',
    cnpj_declarante     TEXT    NOT NULL,
    dt_ini_periodo      TEXT    NOT NULL,
    dt_fin_periodo      TEXT    NOT NULL,
    ano_mes             INTEGER NOT NULL,
    ano_calendario      INTEGER NOT NULL,
    cod_ver             TEXT    NOT NULL,
    c100_linha_arquivo  INTEGER,
    num_item            TEXT,
    cod_item            TEXT,
    cfop                TEXT,
    cst_icms            TEXT,
    vl_item             REAL    DEFAULT 0,
    vl_bc_icms          REAL    DEFAULT 0,
    aliq_icms           REAL    DEFAULT 0,
    vl_icms             REAL    DEFAULT 0,
    cst_pis             TEXT,
    vl_bc_pis           REAL    DEFAULT 0,
    aliq_pis            REAL    DEFAULT 0,
    vl_pis              REAL    DEFAULT 0,
    cst_cofins          TEXT,
    vl_bc_cofins        REAL    DEFAULT 0,
    aliq_cofins         REAL    DEFAULT 0,
    vl_cofins           REAL    DEFAULT 0,
    cod_cta             TEXT
);
CREATE INDEX IF NOT EXISTS idx_icms_c170_cnpj_ano ON efd_icms_c170(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_icms_c170_cfop     ON efd_icms_c170(cfop);

CREATE TABLE IF NOT EXISTS efd_icms_g110 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'G',
    registro         TEXT    NOT NULL DEFAULT 'G110',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_ini           TEXT,
    dt_fin           TEXT,
    saldo_in_icms    REAL    DEFAULT 0,
    som_parc         REAL    DEFAULT 0,
    vl_trib_exp      REAL    DEFAULT 0,
    vl_total         REAL    DEFAULT 0,
    ind_per_sai      REAL    DEFAULT 0,
    icms_aprop       REAL    DEFAULT 0,
    som_icms_oc      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_icms_g110_cnpj_ano ON efd_icms_g110(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_icms_g125 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem      TEXT    NOT NULL,
    linha_arquivo       INTEGER NOT NULL,
    bloco               TEXT    NOT NULL DEFAULT 'G',
    registro            TEXT    NOT NULL DEFAULT 'G125',
    cnpj_declarante     TEXT    NOT NULL,
    dt_ini_periodo      TEXT    NOT NULL,
    dt_fin_periodo      TEXT    NOT NULL,
    ano_mes             INTEGER NOT NULL,
    ano_calendario      INTEGER NOT NULL,
    cod_ver             TEXT    NOT NULL,
    cod_ind_bem         TEXT,
    ident_bem           TEXT,
    dt_mov              TEXT,
    tipo_mov            TEXT,
    vl_imob_icms_op     REAL    DEFAULT 0,
    vl_imob_icms_st     REAL    DEFAULT 0,
    vl_imob_icms_frt    REAL    DEFAULT 0,
    vl_imob_icms_dif    REAL    DEFAULT 0,
    num_parc            TEXT,
    vl_parc_pass        REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_icms_g125_cnpj_ano ON efd_icms_g125(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_icms_h005 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'H',
    registro         TEXT    NOT NULL DEFAULT 'H005',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_inv           TEXT,
    vl_inv           REAL    DEFAULT 0,
    mot_inv          TEXT
);
CREATE INDEX IF NOT EXISTS idx_icms_h005_cnpj_ano ON efd_icms_h005(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS efd_icms_h010 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem      TEXT    NOT NULL,
    linha_arquivo       INTEGER NOT NULL,
    bloco               TEXT    NOT NULL DEFAULT 'H',
    registro            TEXT    NOT NULL DEFAULT 'H010',
    cnpj_declarante     TEXT    NOT NULL,
    dt_ini_periodo      TEXT    NOT NULL,
    dt_fin_periodo      TEXT    NOT NULL,
    ano_mes             INTEGER NOT NULL,
    ano_calendario      INTEGER NOT NULL,
    cod_ver             TEXT    NOT NULL,
    h005_linha_arquivo  INTEGER,
    cod_item            TEXT,
    unid                TEXT,
    qtd                 REAL    DEFAULT 0,
    vl_unit             REAL    DEFAULT 0,
    vl_item             REAL    DEFAULT 0,
    ind_prop            TEXT,
    cod_part            TEXT,
    txt_compl           TEXT,
    cod_cta             TEXT,
    vl_item_ir          REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_icms_h010_cnpj_ano ON efd_icms_h010(cnpj_declarante, ano_mes);

-- ============================================================
-- ECD — Sprint 7 (cruzamentos 38-42)
-- ============================================================

CREATE TABLE IF NOT EXISTS ecd_0000 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0000',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    nome             TEXT,
    uf               TEXT,
    cod_mun          TEXT,
    ind_fin_esc      TEXT,
    ind_grande_porte TEXT,
    tip_ecd          TEXT,
    ident_mf         TEXT,
    ind_mudanc_pc    TEXT    NOT NULL DEFAULT '0',
    cod_plan_ref     TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_0000_cnpj ON ecd_0000(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecd_i010 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'I',
    registro         TEXT    NOT NULL DEFAULT 'I010',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    ind_esc          TEXT,
    cod_ver_lc       TEXT
);

-- Bloco C da ECD (recuperação do ano anterior, CLAUDE.md §16).
-- C050 espelha I050 da ECD anterior (plano de contas pré-mudança).
-- C155 espelha I155 da ECD anterior (saldos finais reclassificados).
CREATE TABLE IF NOT EXISTS ecd_c050 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'C',
    registro         TEXT    NOT NULL DEFAULT 'C050',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_alt           TEXT,
    cod_nat          TEXT    NOT NULL,
    ind_cta          TEXT    NOT NULL,
    nivel            TEXT,
    cod_cta          TEXT    NOT NULL,
    cod_cta_sup      TEXT,
    cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_c050_cnpj_ano ON ecd_c050(cnpj_declarante, ano_calendario);
CREATE INDEX IF NOT EXISTS idx_ecd_c050_cod_cta  ON ecd_c050(cnpj_declarante, cod_cta);

CREATE TABLE IF NOT EXISTS ecd_c155 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'C',
    registro              TEXT    NOT NULL DEFAULT 'C155',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    cod_cta               TEXT    NOT NULL,
    cod_ccus              TEXT,
    vl_sld_ini            REAL    DEFAULT 0,
    ind_dc_ini            TEXT,
    vl_sld_fin            REAL    DEFAULT 0,
    ind_dc_fin            TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_c155_cnpj_ano ON ecd_c155(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecd_i050 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'I',
    registro         TEXT    NOT NULL DEFAULT 'I050',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_alt           TEXT,
    cod_nat          TEXT    NOT NULL,
    ind_cta          TEXT    NOT NULL,
    nivel            TEXT,
    cod_cta          TEXT    NOT NULL,
    cod_cta_sup      TEXT,
    cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_i050_cnpj_ano ON ecd_i050(cnpj_declarante, ano_calendario);
CREATE INDEX IF NOT EXISTS idx_ecd_i050_cod_cta  ON ecd_i050(cnpj_declarante, cod_cta);

CREATE TABLE IF NOT EXISTS ecd_i150 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'I',
    registro         TEXT    NOT NULL DEFAULT 'I150',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_ini_per       TEXT,
    dt_fin_per       TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_i150_cnpj_ano ON ecd_i150(cnpj_declarante, ano_mes);

CREATE TABLE IF NOT EXISTS ecd_i155 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'I',
    registro              TEXT    NOT NULL DEFAULT 'I155',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    i150_linha_arquivo    INTEGER NOT NULL DEFAULT 0,
    cod_cta               TEXT    NOT NULL,
    cod_ccus              TEXT,
    vl_sld_ini            REAL    DEFAULT 0,
    ind_dc_ini            TEXT,
    vl_deb                REAL    DEFAULT 0,
    vl_cred               REAL    DEFAULT 0,
    vl_sld_fin            REAL    DEFAULT 0,
    ind_dc_fin            TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_i155_cnpj_ano ON ecd_i155(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_ecd_i155_cod_cta  ON ecd_i155(cnpj_declarante, cod_cta);

CREATE TABLE IF NOT EXISTS ecd_i200 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'I',
    registro         TEXT    NOT NULL DEFAULT 'I200',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    num_lcto         TEXT,
    dt_lcto          TEXT,
    vl_lcto          REAL    DEFAULT 0,
    ind_lcto         TEXT,
    dt_lcto_ext      TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_i200_cnpj_ano  ON ecd_i200(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_ecd_i200_ind_lcto  ON ecd_i200(cnpj_declarante, ind_lcto);

CREATE TABLE IF NOT EXISTS ecd_j005 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'J',
    registro         TEXT    NOT NULL DEFAULT 'J005',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    dt_ini_dem       TEXT,
    dt_fin_dem       TEXT,
    id_dem           TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_j005_cnpj_ano ON ecd_j005(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecd_j150 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'J',
    registro              TEXT    NOT NULL DEFAULT 'J150',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    j005_linha_arquivo    INTEGER NOT NULL DEFAULT 0,
    nu_ordem              TEXT,
    cod_agl               TEXT,
    ind_cod_agl           TEXT,
    nivel_agl             TEXT,
    cod_agl_sup           TEXT,
    descr_cod_agl         TEXT,
    vl_cta_ini            REAL    DEFAULT 0,
    ind_dc_ini            TEXT,
    vl_cta_fin            REAL    DEFAULT 0,
    ind_dc_fin            TEXT,
    ind_grp_dre           TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_j150_cnpj_ano ON ecd_j150(cnpj_declarante, ano_calendario);

-- ============================================================
-- Sprint 8 — ECF (Leiaute 12, AC 2025)
-- ============================================================

CREATE TABLE IF NOT EXISTS ecf_0000 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0000',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    nome             TEXT,
    ind_sit_ini_per  TEXT,
    sit_especial     TEXT,
    dt_ini           TEXT,
    dt_fin           TEXT,
    retificadora     TEXT,
    tip_ecf          TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_0000_cnpj ON ecf_0000(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecf_0010 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '0',
    registro         TEXT    NOT NULL DEFAULT '0010',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    forma_trib       TEXT,
    forma_apur       TEXT,
    cod_qualif_pj    TEXT,
    tip_esc_pre      TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_0010_cnpj ON ecf_0010(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecf_k155 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'K',
    registro         TEXT    NOT NULL DEFAULT 'K155',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_cta          TEXT    NOT NULL,
    cod_ccus         TEXT,
    vl_sld_ini       REAL    DEFAULT 0,
    ind_vl_sld_ini   TEXT,
    vl_deb           REAL    DEFAULT 0,
    vl_cred          REAL    DEFAULT 0,
    vl_sld_fin       REAL    DEFAULT 0,
    ind_vl_sld_fin   TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_k155_cod_cta ON ecf_k155(cnpj_declarante, ano_calendario, cod_cta);

CREATE TABLE IF NOT EXISTS ecf_k355 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'K',
    registro         TEXT    NOT NULL DEFAULT 'K355',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_cta          TEXT    NOT NULL,
    cod_ccus         TEXT,
    vl_sld_ini       REAL    DEFAULT 0,
    ind_vl_sld_ini   TEXT,
    vl_deb           REAL    DEFAULT 0,
    vl_cred          REAL    DEFAULT 0,
    vl_sld_fin       REAL    DEFAULT 0,
    ind_vl_sld_fin   TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_k355_cod_cta ON ecf_k355(cnpj_declarante, ano_calendario, cod_cta);

CREATE TABLE IF NOT EXISTS ecf_m300 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem      TEXT    NOT NULL,
    linha_arquivo       INTEGER NOT NULL,
    bloco               TEXT    NOT NULL DEFAULT 'M',
    registro            TEXT    NOT NULL DEFAULT 'M300',
    cnpj_declarante     TEXT    NOT NULL,
    dt_ini_periodo      TEXT    NOT NULL,
    dt_fin_periodo      TEXT    NOT NULL,
    ano_mes             INTEGER NOT NULL,
    ano_calendario      INTEGER NOT NULL,
    cod_ver             TEXT    NOT NULL,
    codigo              TEXT,
    descricao           TEXT,
    tipo_lancamento     TEXT,
    ind_relacao         TEXT,
    valor               REAL    DEFAULT 0,
    hist_lan_lal        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_m300_cnpj_ano   ON ecf_m300(cnpj_declarante, ano_calendario);
CREATE INDEX IF NOT EXISTS idx_ecf_m300_tipo        ON ecf_m300(cnpj_declarante, tipo_lancamento);

CREATE TABLE IF NOT EXISTS ecf_m312 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M312',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    m300_linha_arquivo    INTEGER NOT NULL DEFAULT 0,
    num_lcto              TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_m312_num_lcto ON ecf_m312(cnpj_declarante, ano_calendario, num_lcto);

CREATE TABLE IF NOT EXISTS ecf_m350 (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem      TEXT    NOT NULL,
    linha_arquivo       INTEGER NOT NULL,
    bloco               TEXT    NOT NULL DEFAULT 'M',
    registro            TEXT    NOT NULL DEFAULT 'M350',
    cnpj_declarante     TEXT    NOT NULL,
    dt_ini_periodo      TEXT    NOT NULL,
    dt_fin_periodo      TEXT    NOT NULL,
    ano_mes             INTEGER NOT NULL,
    ano_calendario      INTEGER NOT NULL,
    cod_ver             TEXT    NOT NULL,
    codigo              TEXT,
    descricao           TEXT,
    tipo_lancamento     TEXT,
    ind_relacao         TEXT,
    valor               REAL    DEFAULT 0,
    hist_lan_lal        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_m350_cnpj_ano ON ecf_m350(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecf_m362 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'M',
    registro              TEXT    NOT NULL DEFAULT 'M362',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    m350_linha_arquivo    INTEGER NOT NULL DEFAULT 0,
    num_lcto              TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_m362_num_lcto ON ecf_m362(cnpj_declarante, ano_calendario, num_lcto);

CREATE TABLE IF NOT EXISTS ecf_m500 (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem          TEXT    NOT NULL,
    linha_arquivo           INTEGER NOT NULL,
    bloco                   TEXT    NOT NULL DEFAULT 'M',
    registro                TEXT    NOT NULL DEFAULT 'M500',
    cnpj_declarante         TEXT    NOT NULL,
    dt_ini_periodo          TEXT    NOT NULL,
    dt_fin_periodo          TEXT    NOT NULL,
    ano_mes                 INTEGER NOT NULL,
    ano_calendario          INTEGER NOT NULL,
    cod_ver                 TEXT    NOT NULL,
    cod_cta_b               TEXT,
    cod_tributo             TEXT,
    sd_ini_lal              REAL    DEFAULT 0,
    ind_sd_ini_lal          TEXT,
    vl_lcto_parte_a         REAL    DEFAULT 0,
    ind_vl_lcto_parte_a     TEXT,
    vl_lcto_parte_b         REAL    DEFAULT 0,
    ind_vl_lcto_parte_b     TEXT,
    sd_fim_lal              REAL    DEFAULT 0,
    ind_sd_fim_lal          TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_m500_cnpj_ano ON ecf_m500(cnpj_declarante, ano_calendario);
CREATE INDEX IF NOT EXISTS idx_ecf_m500_cta_b    ON ecf_m500(cnpj_declarante, ano_calendario, cod_cta_b);

CREATE TABLE IF NOT EXISTS ecf_x480 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'X',
    registro         TEXT    NOT NULL DEFAULT 'X480',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    codigo           TEXT,
    descricao        TEXT,
    valor            REAL    DEFAULT 0,
    ind_valor        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_x480_cnpj_ano ON ecf_x480(cnpj_declarante, ano_calendario);

-- X460 — Inovação tecnológica (Lei do Bem — Lei 11.196/2005, §8.6 CLAUDE.md)
CREATE TABLE IF NOT EXISTS ecf_x460 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'X',
    registro         TEXT    NOT NULL DEFAULT 'X460',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    codigo           TEXT,
    descricao        TEXT,
    valor            REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ecf_x460_cnpj_ano ON ecf_x460(cnpj_declarante, ano_calendario);

-- 9100 — Avisos da escrituração emitidos pelo PGE na validação (§22.1 ECF layout)
CREATE TABLE IF NOT EXISTS ecf_9100 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT '9',
    registro         TEXT    NOT NULL DEFAULT '9100',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    cod_aviso        TEXT,
    descr_aviso      TEXT,
    reg_ref          TEXT,
    campo_ref        TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecf_9100_cnpj_ano ON ecf_9100(cnpj_declarante, ano_calendario);

CREATE TABLE IF NOT EXISTS ecf_y570 (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem   TEXT    NOT NULL,
    linha_arquivo    INTEGER NOT NULL,
    bloco            TEXT    NOT NULL DEFAULT 'Y',
    registro         TEXT    NOT NULL DEFAULT 'Y570',
    cnpj_declarante  TEXT    NOT NULL,
    dt_ini_periodo   TEXT    NOT NULL,
    dt_fin_periodo   TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    ano_calendario   INTEGER NOT NULL,
    cod_ver          TEXT    NOT NULL,
    per_apu          TEXT,
    nat_rend         TEXT,
    vl_ir_ret        REAL    DEFAULT 0,
    vl_csll_ret      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_ecf_y570_cnpj_ano ON ecf_y570(cnpj_declarante, ano_calendario);

-- ============================================================
-- Output do motor de cruzamentos
-- ============================================================

-- Colunas revisado_em/revisado_por/nota: revisão por-linha do auditor
-- (decisão #12 do planejamento GUI). Persistidas via Repositorio.marcar_revisada
-- e Repositorio.atualizar_nota; lidas pelo T4 (DetailPanel).
CREATE TABLE IF NOT EXISTS crossref_oportunidades (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_regra                TEXT    NOT NULL,
    descricao                   TEXT    NOT NULL,
    severidade                  TEXT    NOT NULL,
    valor_impacto_conservador   REAL    DEFAULT 0,
    valor_impacto_maximo        REAL    DEFAULT 0,
    evidencia_json              TEXT    NOT NULL,  -- JSON array
    cnpj_declarante             TEXT    NOT NULL,
    ano_mes                     INTEGER,
    ano_calendario              INTEGER NOT NULL,
    gerado_em                   TEXT    NOT NULL,
    revisado_em                 TEXT,              -- ISO-8601 ou NULL
    revisado_por                TEXT,              -- usuário responsável
    nota                        TEXT               -- texto livre do auditor
);
CREATE INDEX IF NOT EXISTS idx_op_cnpj_ano ON crossref_oportunidades(cnpj_declarante, ano_calendario);
CREATE INDEX IF NOT EXISTS idx_op_regra    ON crossref_oportunidades(codigo_regra);

CREATE TABLE IF NOT EXISTS crossref_divergencias (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_regra     TEXT    NOT NULL,
    descricao        TEXT    NOT NULL,
    severidade       TEXT    NOT NULL,
    evidencia_json   TEXT    NOT NULL,
    cnpj_declarante  TEXT    NOT NULL,
    ano_mes          INTEGER,
    ano_calendario   INTEGER NOT NULL,
    gerado_em        TEXT    NOT NULL,
    revisado_em      TEXT,
    revisado_por     TEXT,
    nota             TEXT
);
CREATE INDEX IF NOT EXISTS idx_div_cnpj_ano ON crossref_divergencias(cnpj_declarante, ano_calendario);
