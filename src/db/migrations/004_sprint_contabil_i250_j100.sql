-- Migração Sprint Contábil — I250 (partidas dos lançamentos) e J100 (BP).
-- Necessárias para a tela T9 Análise Contábil:
--   - I250 alimenta o "Razão da conta" com débito/crédito/contrapartida
--   - J100 alimenta o "Balanço Patrimonial" estruturado (Ativo/Passivo/PL)
-- Executada de forma aditiva — bancos antigos com ECD parseada sem essas
-- tabelas vão precisar reimportar a ECD pra popular.

CREATE TABLE IF NOT EXISTS ecd_i250 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'I',
    registro              TEXT    NOT NULL DEFAULT 'I250',
    cnpj_declarante       TEXT    NOT NULL,
    dt_ini_periodo        TEXT    NOT NULL,
    dt_fin_periodo        TEXT    NOT NULL,
    ano_mes               INTEGER NOT NULL,
    ano_calendario        INTEGER NOT NULL,
    cod_ver               TEXT    NOT NULL,
    i200_linha_arquivo    INTEGER NOT NULL DEFAULT 0,
    cod_cta               TEXT    NOT NULL,
    cod_ccus              TEXT,
    vl_deb_cred           REAL    DEFAULT 0,
    ind_dc                TEXT,
    hist_lcto_ccus        TEXT,
    cod_hist_pad          TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_i250_cnpj_ano ON ecd_i250(cnpj_declarante, ano_mes);
CREATE INDEX IF NOT EXISTS idx_ecd_i250_cod_cta  ON ecd_i250(cnpj_declarante, cod_cta, ano_mes);
CREATE INDEX IF NOT EXISTS idx_ecd_i250_i200     ON ecd_i250(cnpj_declarante, i200_linha_arquivo);

CREATE TABLE IF NOT EXISTS ecd_j100 (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    arquivo_origem        TEXT    NOT NULL,
    linha_arquivo         INTEGER NOT NULL,
    bloco                 TEXT    NOT NULL DEFAULT 'J',
    registro              TEXT    NOT NULL DEFAULT 'J100',
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
    ind_grp_bal           TEXT,
    descr_cod_agl         TEXT,
    vl_cta_ini            REAL    DEFAULT 0,
    ind_dc_ini            TEXT,
    vl_cta_fin            REAL    DEFAULT 0,
    ind_dc_fin            TEXT
);
CREATE INDEX IF NOT EXISTS idx_ecd_j100_cnpj_ano ON ecd_j100(cnpj_declarante, ano_calendario);
