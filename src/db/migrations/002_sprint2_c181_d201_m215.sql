-- Migração Sprint 2 — registros C181/C185 (NFC-e), D201/D205 (transporte), M215/M615 (ajuste de base)
-- Executada de forma aditiva: não destrói dados existentes.

-- ============================================================
-- Bloco C — NFC-e consolidada (C181 PIS / C185 COFINS)
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
    -- Vínculo pai (rastreabilidade — FK não-enforced para simplicidade Sprint 2)
    c180_linha_arquivo   INTEGER NOT NULL DEFAULT 0,
    ind_oper             TEXT    NOT NULL DEFAULT '',   -- herdado do C180
    -- Campos do registro
    cst_pis              TEXT    NOT NULL,
    cfop                 TEXT,
    vl_item              REAL    NOT NULL DEFAULT 0,
    vl_desc              REAL    NOT NULL DEFAULT 0,    -- ICMS deve estar aqui se excluído
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
-- Bloco D — Serviços de transporte (D201 PIS / D205 COFINS)
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
    vl_bc_pis            REAL    NOT NULL DEFAULT 0,   -- se == vl_item, ICMS na base
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
-- Bloco M — Ajuste à base de cálculo (M215 PIS / M615 COFINS)
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
    ind_aj_bc            TEXT    NOT NULL,  -- "0"=redução, "1"=acréscimo
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
