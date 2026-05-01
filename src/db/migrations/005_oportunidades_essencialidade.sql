-- Migração — tabela de marcações de oportunidades de essencialidade
-- Tema 779 (REsp 1.221.170/PR) na aba T9 Despesas × Crédito PIS/COFINS.
-- Aditiva: bancos antigos não tinham; CREATE TABLE IF NOT EXISTS.

CREATE TABLE IF NOT EXISTS contabil_oportunidades_essencialidade (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cnpj_declarante TEXT    NOT NULL,
    ano_calendario  INTEGER NOT NULL,
    cod_cta         TEXT    NOT NULL,
    marcado_em      TEXT    NOT NULL,
    marcado_por     TEXT,
    nota            TEXT,
    UNIQUE(cnpj_declarante, ano_calendario, cod_cta)
);
CREATE INDEX IF NOT EXISTS idx_contabil_oport_cnpj_ano
    ON contabil_oportunidades_essencialidade(cnpj_declarante, ano_calendario);
