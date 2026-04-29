# Débitos conhecidos

Registro formal de débitos técnicos e arquiteturais identificados
e ainda não resolvidos. Cada entrada inclui sintoma, causa raiz,
workaround atual e solução proposta para sprint dedicada futura.

Buscável via `git log --grep="débito"` para commits que
referenciam esses débitos.

---

## BUG-001 — Validação de Bloco 9 hard-coded vazia em 3 parsers

**Status:** aberto
**Severidade:** média
**Descoberto em:** 2026-04-29, durante validação contra Norte
Geradores. Registrado também em commit 73811d5
(refactor truncamento PKCS#7).

### Sintoma observado

Parsers ECD, EFD ICMS/IPI e ECF têm `divergencias_bloco9 = []`
hard-coded. Não validam contagens declaradas no Bloco 9 (registros
9900) contra contagens reais parseadas. Apenas o parser
EFD-Contribuições faz essa validação.

### Causa raiz

Decisão de implementação (deliberada ou esquecimento) durante
desenvolvimento original. Não documentada nos commits originais
desses parsers.

### Workaround atual

Nenhum. Validação de Bloco 9 simplesmente não acontece nesses
3 parsers. Em prática, parsing tem funcionado porque arquivos
SPED bem-formados tendem a ter Bloco 9 coerente. Mas não há
garantia.

### Solução proposta

Implementar validação de Bloco 9 nos 3 parsers em paridade com
EFD-Contribuições (efd_contribuicoes.py:421-432):

1. Iterar sobre registros 9900 declarados
2. Comparar com contagens reais por tipo de registro
3. Acumular divergências em `divergencias_bloco9`
4. Refletir em status='ok' ou 'parcial' conforme o caso

Considerar também extrair lógica para função compartilhada em
`src/parsers/common/` (similar a `truncar_em_9999`).

### Referência cruzada

- Commit 73811d5 — refactor que aplicou truncamento mas não
  endereçou validação de Bloco 9
- src/parsers/efd_contribuicoes.py:421-432 — implementação de
  referência

---

## BUG-002 — Ausência de dedup/upsert em reimport de SPED

**Status:** aberto, mitigado por convenção operacional
**Severidade:** alta
**Descoberto em:** 2026-04-29, durante validação contra Norte
Geradores.

### Sintoma observado

Reimport do mesmo arquivo SPED (mesmo CNPJ, mesmo período,
mesmo hash) causa duplicação completa nas tabelas filhas dos
parsers. Sem aviso, sem rejeição, sem substituição.

Exemplo verificado: import isolado de PISCOFINS jan/2024 (id=1
em _importacoes) seguido de reimport no loop (id=2). Resultado:
20 rows em efd_contrib_f600 com ano_mes=202401 (deveria ser 10).

### Causa raiz

Caminho de import faz INSERT puro nas tabelas filhas, sem:
- UNIQUE constraint em (cnpj_declarante, ano_mes) ou (arquivo_hash)
- ON CONFLICT REPLACE
- DELETE prévio antes do import

Schema de tabelas como efd_contrib_0000 não tem nenhuma constraint
UNIQUE — apenas PRIMARY KEY autoincremento.

### Workaround atual

**Convenção operacional:** sempre dropar banco
(`data/db/{cnpj}/{ano}.sqlite`) antes de reimportar arquivos
do mesmo período. Validado empiricamente em 2026-04-29 com
reimport limpo da Norte Geradores 2024.

### Implicação latente em produção

Reimport de arquivo retificador (operação comum em consultoria
fiscal real, quando cliente reentrega arquivo corrigido) gera
duplicação silenciosa. Cruzamentos baseados em F600/M200
retornam valores 2× para o período afetado, sem aviso. Risco
real de número errado em parecer entregue ao cliente.

### Solução proposta

Três alternativas (decisão de design para sprint dedicada):

1. **UNIQUE constraint + INSERT OR REPLACE.** Adicionar
   `UNIQUE(cnpj_declarante, ano_mes, arquivo_hash)` ou similar
   em tabelas relevantes. Em reimport, ON CONFLICT REPLACE
   substitui automaticamente. Exige migration.

2. **DELETE prévio antes de import.** Antes de inserir, deletar
   tudo de (cnpj, ano_mes, tipo_sped). Mais simples, sem mudança
   de schema, mas precisa coordenação entre parsers.

3. **Detecção via hash em _importacoes.** Se hash do arquivo
   já está em _importacoes para mesmo (cnpj, ano_mes), perguntar
   (ou decidir por flag --force-reimport) se substitui ou aborta.

### Referência cruzada

- Validação empírica em 2026-04-29 (sessão Norte Geradores)
- Tabela _importacoes: registro completo de imports históricos
  já existe — base para Solução 3
