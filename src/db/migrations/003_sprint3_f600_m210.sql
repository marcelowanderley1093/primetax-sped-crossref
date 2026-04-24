-- Migração Sprint 3 — F600/F700 (retenções na fonte), M210/M610 (contribuição por CST)
-- Executada de forma aditiva.

-- ============================================================
-- Bloco F — Retenções na fonte (F600 PIS / F700 COFINS)
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
    dt_ret           TEXT,              -- YYYY-MM-DD
    vl_bc_ret        REAL    DEFAULT 0,
    aliq_ret         REAL    DEFAULT 0,
    vl_ret_apu       REAL    DEFAULT 0, -- total retido
    cod_rec          TEXT,
    ind_nat_rec      TEXT,
    pr_rec_ret       TEXT,              -- YYYY-MM-DD — previsão recuperação (CR-19)
    cnpj_fonte_pag   TEXT,
    vl_ret_per       REAL    DEFAULT 0, -- recuperado neste período
    vl_ret_dcomp     REAL    DEFAULT 0  -- compensado via DCOMP
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
-- Bloco M — Contribuição por CST/alíquota (M210 PIS / M610 COFINS)
-- Necessário para cruzamento CR-31 (Camada 3).
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
    cod_cont         TEXT    NOT NULL,  -- código da contribuição (mapa CST+alíq)
    vl_rec_brt       REAL    DEFAULT 0,
    vl_bc_cont       REAL    DEFAULT 0, -- base de cálculo declarada
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
