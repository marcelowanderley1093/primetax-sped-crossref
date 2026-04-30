# Débitos conhecidos

Registro formal de débitos técnicos e arquiteturais identificados
e ainda não resolvidos. Cada entrada inclui sintoma, causa raiz,
workaround atual e solução proposta para sprint dedicada futura.

Buscável via `git log --grep="débito"` para commits que
referenciam esses débitos.

---

## BUG-001 — Validação de Bloco 9 hard-coded vazia em 3 parsers

**Status:** resolvido em `0141560` (2026-04-30)
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

### Resolução (commits 84f830b + 0141560, 2026-04-30)

(a) **Função compartilhada criada.** Lógica de validação extraída
para `src/parsers/common/bloco9.py` em `validar_bloco9()` —
função pura que recebe `contagens_reais`, `regs_9900`, `reg9999`
e `total_linhas_sped` e retorna `(contagens_declaradas,
divergencias)`. Padrão simétrico ao `truncar_em_9999()` introduzido
em commit 73811d5.

(b) **3 parsers atualizados em paridade com EFD-Contribuições.**
ECD, EFD ICMS/IPI e ECF agora:
- acumulam `contagens_reais` cumulativo por `reg_tipo` no loop;
- parseiam registros 9900 e 9999 (via `parsear_9900`/`parsear_9999`
  já existentes em `bloco_9.py`);
- chamam `validar_bloco9()` antes do retorno;
- derivam `status='ok'` ou `'parcial'` conforme presença de erros
  ou divergências.

(c) **Achado adicional durante validação empírica — caso J801.**
Re-importação dos 4 ECDs anuais da Norte Geradores expôs
divergência sistemática de 704 linhas no ECD 2023 (substituidora
final 2CFE6DA9). Investigação revelou que `9999.QTD_LIN` do PVA
conta apenas **linhas SPED válidas** (com pipe inicial), enquanto
o cálculo herdado usava `len(linhas_raw)` (linhas físicas após
`truncar_em_9999`). A diferença vem do registro **J801 (Termo de
Encerramento)** que embute conteúdo RTF em Base64 multilinhas —
as continuações Base64 não começam com pipe e não são contadas
pelo PVA. Funcionava em EFD-Contribuições porque ela não tem
J801; quebraria em qualquer ECD anual com encerramento contábil.

**Correção:** introduzido `total_linhas_sped =
sum(1 for l in linhas_raw if l.startswith("|"))` calculado em
cada parser e passado como argumento a `validar_bloco9`. O campo
público `total_linhas_lidas` no `ResultadoImportacao` continua
sendo linhas físicas (preservado para diagnóstico de
encoding/truncamento); a contagem semântica do PVA é interna ao
validador. Teste regressivo
`test_arquivo_com_continuacoes_base64` em `test_bloco9.py`
documenta o cenário.

(d) **Validação final.** 4 ECDs anuais da NG (2021-2024) em
diretório isolado: todos `status='ok'` confirmado. ECD 2023
antes geraria falso positivo sob Bug-001 fix sem a correção
`total_linhas_sped`; agora valida limpo. pytest -x: **440 passed**
(439 anteriores + 1 novo teste J801).

### Referência cruzada

- Commit 73811d5 — refactor que aplicou truncamento mas não
  endereçou validação de Bloco 9
- Commit 84f830b — função compartilhada `validar_bloco9()` criada
  e EFD-Contribuições refatorada para usá-la
- Commit 0141560 — fix aplicado nos 3 parsers + correção
  `total_linhas_sped` (caso J801)
- src/parsers/common/bloco9.py — implementação canônica
- src/parsers/efd_contribuicoes.py:421-432 — implementação
  original (antes da extração)

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

---

## BUG-003 — Despesa em apuração trimestral retornava zero (refinamento parcial pendente)

**Status:** mitigado por correção parcial (Opção i aplicada).
Refinamento via Opção ii ou iii fica como débito parcial caso
apareça cliente real com estorno legítimo em conta de resultado.
**Severidade:** alta (era crítico; após fix, reduzido a refinamento)
**Descoberto em:** 2026-04-29, durante validação T9 contra Norte
Geradores 2021. Corrigido no commit do mesmo dia.

### Sintoma observado

`ContabilController._saldo_despesa_anual` (agora `_total_debito_anual`)
calculava `SUM(vl_deb) - SUM(vl_cred)` de `ecd_i155` por conta.
Para clientes com escrituração em apuração trimestral (despesa
debitada durante o trimestre e creditada em massa no último mês
para zerar contra o resultado), `SUM(vl_deb) ≈ SUM(vl_cred)` no
ano, resultando em zero exato. Consequência: T9 Análise Contábil
(`listar_despesas_vs_credito` e `listar_imobilizado_vs_credito`)
reportava 0 oportunidades — invalidando diagnóstico Tema 779.

Exemplo verificado: Norte Geradores 2021, conta 3006 Combustíveis,
`SUM(vl_deb) = R$ 715.236,93` e `SUM(vl_cred) = R$ 715.236,93`
(creditadas em mar/jun/set/dez via transferência ao resultado).
Saldo retornado: 0,00. Após fix: R$ 715.236,93 (despesa bruta
real, base correta para diagnóstico Tema 779).

### Causa raiz

Método assumia que `vl_deb - vl_cred` representaria despesa
incorrida, válido apenas para escrituração que NUNCA zera contas
de resultado durante o ano. Padrão real brasileiro mais comum
(apuração trimestral ou mensal) zera contas de resultado, e a
fórmula falha silenciosamente.

### Correção aplicada (Opção i)

- Query reduzida para `SUM(vl_deb)` apenas
- Método renomeado `_saldo_despesa_anual` → `_total_debito_anual`
  (nome reflete semântica real)
- Comentários e docstrings atualizados
- 2 testes regressivos adicionados

### Refinamentos pendentes

Caso apareça cliente real com **estorno legítimo** em conta de
resultado (raro, mas possível: nota cancelada lançada em despesa,
estornada via crédito), a Opção (i) superestima a despesa
marginalmente. Soluções refinadas:

1. **Opção (ii) — distinguir transferência de estorno.** Identificar
   créditos cuja contrapartida (via I200/I250) é uma conta de
   resultado/apuração (cod_nat='03' ou '05') vs uma conta operacional.
   Subtrair apenas créditos com contrapartida operacional (estornos
   legítimos), preservar créditos de transferência ao resultado.

2. **Opção (iii) — computar via I250 puro.** Somar `vl_deb_cred`
   onde `ind_dc='D'` em `ecd_i250` filtrado por `cod_cta`,
   excluindo lançamentos cuja contrapartida é conta de
   apuração/resultado. Mais robusto, mais caro em I/O.

### Referência cruzada

- Validação empírica contra Norte Geradores 2021 em 2026-04-29
- src/gui/controllers/contabil_controller.py — método `_total_debito_anual`
- tests/gui/controllers/test_contabil_controller.py —
  test_apuracao_trimestral_contabiliza_despesa_bruta
