-- Migração 001 — Sprint 1 (schema inicial EFD-Contribuições)
-- Aplique com: sqlite3 <banco>.sqlite < 001_sprint1_initial.sql
-- Idempotente: CREATE TABLE IF NOT EXISTS em todas as tabelas.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS _importacoes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    sped_tipo        TEXT    NOT NULL,
    dt_ini           TEXT    NOT NULL,
    dt_fin           TEXT    NOT NULL,
    ano_mes          INTEGER NOT NULL,
    arquivo_hash     TEXT    NOT NULL,
    arquivo_origem   TEXT    NOT NULL,
    importado_em     TEXT    NOT NULL,
    cod_ver          TEXT    NOT NULL,
    encoding_origem  TEXT    NOT NULL,
    encoding_confianca TEXT  NOT NULL,
    status           TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS _sped_contexto (
    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj                     TEXT    NOT NULL,
    ano_calendario           INTEGER NOT NULL,
    disponibilidade_efd_contrib  TEXT DEFAULT 'pendente',
    disponibilidade_efd_icms     TEXT DEFAULT 'pendente',
    disponibilidade_ecd          TEXT DEFAULT 'pendente',
    disponibilidade_ecf          TEXT DEFAULT 'pendente',
    disponibilidade_bloco_i      TEXT DEFAULT 'pendente',
    reconciliacao_plano_contas   TEXT DEFAULT NULL,
    atualizado_em            TEXT NOT NULL,
    UNIQUE(cnpj, ano_calendario)
);

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
    c100_linha_arquivo   INTEGER NOT NULL,
    num_item             TEXT,
    cod_item             TEXT,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_desc              REAL    NOT NULL DEFAULT 0,
    cfop                 TEXT,
    vl_icms              REAL    NOT NULL DEFAULT 0,
    vl_icms_st           REAL    NOT NULL DEFAULT 0,
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
    cod_cta              TEXT
);
CREATE INDEX IF NOT EXISTS idx_c170_cnpj_ano ON efd_contrib_c170(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_c170_cst_pis  ON efd_contrib_c170(cst_pis);
CREATE INDEX IF NOT EXISTS idx_c170_linha    ON efd_contrib_c170(linha_arquivo);
CREATE INDEX IF NOT EXISTS idx_c170_c100     ON efd_contrib_c170(c100_linha_arquivo);

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
    vl_rec_brt_total      REAL    DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_m600_cnpj_ano ON efd_contrib_m600(cnpj_declarante, ano_mes);

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

CREATE TABLE IF NOT EXISTS crossref_oportunidades (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_regra                TEXT    NOT NULL,
    descricao                   TEXT    NOT NULL,
    severidade                  TEXT    NOT NULL,
    valor_impacto_conservador   REAL    DEFAULT 0,
    valor_impacto_maximo        REAL    DEFAULT 0,
    evidencia_json              TEXT    NOT NULL,
    cnpj_declarante             TEXT    NOT NULL,
    ano_mes                     INTEGER,
    ano_calendario              INTEGER NOT NULL,
    gerado_em                   TEXT    NOT NULL
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
    gerado_em        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_div_cnpj_ano ON crossref_divergencias(cnpj_declarante, ano_calendario);
