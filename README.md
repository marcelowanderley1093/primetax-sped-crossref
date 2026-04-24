# Primetax SPED Cross-Reference

Sistema de análise cruzada de SPEDs (EFD-Contribuições, EFD ICMS/IPI, ECD, ECF)
para identificação de oportunidades de recuperação de créditos tributários
federais. Uso interno da Primetax Solutions.

Implementa os 47 cruzamentos fiscais definidos em `.claude/CLAUDE.md §8`,
com rastreabilidade absoluta até a linha original do arquivo SPED (§4 princípio 1).

## Instalação

Requer Python 3.12 (`3.14` é incompatível com dependências transitivas).

```
pip install -e .
```

Ou, em ambiente isolado:

```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

A instalação cria o script `primetax-sped` no PATH.

## Quickstart

```
# 1. Coloque os SPEDs do cliente em data/input/<cnpj>/<período>/
#    Ex: data/input/12345678000100/2025/efd_contrib_202501.txt
#        data/input/12345678000100/2025/ecd_2025.txt
#        data/input/12345678000100/2025/ecf_2025.txt

# 2. Importa todos os SPEDs encontrados (auto-detecta o tipo)
primetax-sped import data/input/12345678000100/2025/

# 3. Roda os 47 cruzamentos e gera o Excel de diagnóstico
primetax-sped diagnose 12345678000100 2025

# 4. Gera parecer Word formal por tese
primetax-sped parecer 12345678000100 2025 --tese tema-69
```

Outputs ficam em `data/output/<cnpj>/<ano>/`.

## Comandos

### `import`

Importa um ou mais arquivos SPED para o banco SQLite longitudinal
(`data/db/<cnpj>/<ano>.sqlite`). Detecta automaticamente o tipo do SPED
(EFD-Contribuições, EFD ICMS/IPI, ECD ou ECF) pelo registro `0000`.

```
primetax-sped import <arquivo_ou_diretório> [--encoding auto|utf8|latin1] [--nao-interativo]
```

Encoding: padrão `auto` — tenta UTF-8 estrito, cai em Latin1 com validação
semântica (§7.2.1). Em casos ambíguos pergunta ao operador antes de prosseguir;
use `--nao-interativo` em processamento em lote.

### `diagnose`

Executa os 47 cruzamentos nos SPEDs importados e gera o Excel de diagnóstico
em `data/output/<cnpj>/<ano>/diagnostico.xlsx`.

```
primetax-sped diagnose <cnpj> <ano>
```

Abas do Excel:
- **Oportunidades** — achados da Camada 2 com impacto monetário.
- **Divergências de Integridade** — achados da Camada 1.
- **Qualidade da Análise** — quatro tabelas de metadados (§16.5, §18.5):
  disponibilidade por SPED, cruzamentos em modo degradado, pendências
  recuperáveis (ação do auditor), limitações estruturais (inaplicáveis).

### `parecer`

Gera documento Word formal por tese, consolidando oportunidades relacionadas.
Assinável pelo consultor responsável.

```
primetax-sped parecer <cnpj> <ano> --tese <código>
```

Teses disponíveis: `tema-69`, `insumos`, `retencoes`, `imobilizado`,
`prescricao-quinquenal`, `lei-14789-subvencoes`, `compensacao-prejuizos`,
`creditos-extemporaneos`.

Logo Primetax: se existir arquivo em `data/identidade/primetax-logo.png`
(ou caminho custom via `PRIMETAX_LOGO_PATH`), é embutido no cabeçalho.

### `reconciliacao-template`

Gera Excel para reconciliação manual de plano de contas quando a ECD tem
`IND_MUDANC_PC='1'` e o Bloco C está ausente ou incompleto (§16.6).

```
primetax-sped reconciliacao-template <cnpj> <ano>
```

O auditor preenche as colunas em amarelo (COD_CTA antigo, NOME antigo,
observações) e reimporta via `reconciliacao-import`.

### `reconciliacao-import`

Importa o template preenchido e grava os mapeamentos como overrides.
Quando a cobertura atinge 50% das contas analíticas, eleva a classificação
da reconciliação para `'integra'`, destravando modo integral em CR-38/39/43.

```
primetax-sped reconciliacao-import <cnpj> <ano> <arquivo.xlsx>
```

## Estrutura de diretórios

```
data/
├── input/<cnpj>/<período>/      # SPEDs do cliente (não versionados)
├── output/<cnpj>/<ano>/         # Diagnósticos e pareceres gerados
├── db/<cnpj>/<ano>.sqlite       # Banco longitudinal (um por CNPJ × AC)
├── identidade/                  # Logo Primetax para o Word (opcional)
└── tabelas-dinamicas-rfb/       # Snapshot das tabelas RFB (versionado)
```

Somente `data/tabelas-dinamicas-rfb/` é versionado — dados públicos da RFB.
Todo o restante fica no `.gitignore`.

## Fluxos operacionais

### Fluxo 1 — diagnóstico simples (EFD-Contribuições isolada)

```
primetax-sped import data/input/<cnpj>/<mes>/efd_contrib.txt
primetax-sped diagnose <cnpj> <ano>
primetax-sped parecer <cnpj> <ano> --tese tema-69
```

Roda as Camadas 1-3 sobre EFD-Contribuições. Cruzamentos inter-SPED (35-47)
ficam registrados como "Pendências recuperáveis" na aba de Qualidade.

### Fluxo 2 — diagnóstico completo (4 SPEDs)

```
primetax-sped import data/input/<cnpj>/<ano>/
primetax-sped diagnose <cnpj> <ano>
primetax-sped parecer <cnpj> <ano> --tese tema-69
primetax-sped parecer <cnpj> <ano> --tese creditos-extemporaneos
```

Todos os 47 cruzamentos (exceto CR-24, fora de escopo) executam.

### Fluxo 3 — ECD com mudança de plano de contas

Quando `ECD.0000.IND_MUDANC_PC='1'` e o Bloco C está ausente/incompleto,
os cruzamentos ECD-dependentes rodam em modo degradado (agregado por COD_NAT).
Para destravar modo integral:

```
primetax-sped import data/input/<cnpj>/<ano>/
primetax-sped reconciliacao-template <cnpj> <ano>
# auditor preenche o .xlsx manualmente
primetax-sped reconciliacao-import <cnpj> <ano> data/output/<cnpj>/<ano>/reconciliacao_template.xlsx
primetax-sped diagnose <cnpj> <ano>
```

## Limitações conhecidas

Decisões do `.claude/CLAUDE.md §13` — fora do escopo da v1:

- **Bloco I da EFD-Contribuições** (instituições financeiras, seguradoras, EAPC).
- **CR-24 e parte externa do CR-47** — dependem de integração e-CAC com
  certificado A1 mTLS.
- **Bloco K da ECF** (conglomerados econômicos consolidados).
- **Bloco W da ECF** (CBCR — Declaração País-a-País).
- **DEREX** (Bloco V da ECF).
- **Razão Auxiliar parametrizável da ECD** (registros I500-I555).

Limitação operacional: o modelo de persistência é local (SQLite por CNPJ × AC).
Análises longitudinais cross-ano ou cross-cliente ainda não têm suporte direto —
cada banco é consultado individualmente.

## Testes

```
pytest                          # suite completa (~175 testes)
pytest tests/crossref/          # apenas cruzamentos
pytest tests/reports/           # apenas geração de relatórios
pytest -v tests/crossref/test_cruzamento_07_tese69.py   # um arquivo específico
```

Fixtures em `tests/fixtures/` são SPEDs sintéticos mínimos — nunca dados
de cliente real (§10).

## Referências

Todo o projeto segue as decisões arquiteturais e princípios do
[`.claude/CLAUDE.md`](./.claude/CLAUDE.md). Os seis arquivos de layout oficial
dos SPEDs ficam em [`docs/layouts-oficiais/`](./docs/layouts-oficiais/).
