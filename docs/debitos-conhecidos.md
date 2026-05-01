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

**Status:** resolvido em `af3b55f` + `c8d6379` (2026-05-01)
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

### Resolução (commits `fd2a63f` + `af3b55f` + `c8d6379`, 2026-05-01)

Combinação de duas opções da seção "Solução proposta" original:

**(a) Opção 2 (DELETE prévio) — núcleo do fix.** `Repositorio`
ganha método `deletar_dados_anteriores(conn, sped_tipo, cnpj, *,
ano_mes, ano_calendario)` que apaga todas as tabelas SPED filhas
do tipo para o (cnpj × período) antes de inserir novas rows.
Cada parser chama o método dentro de `with conn:` antes de
`registrar_importacao` + `inserir_xxx`. Single source of truth
em `_TABELAS_POR_SPED_TIPO` (mapa estático em `src/db/repo.py`).

**(b) Opção 3 (`--force-reimport`) — camada UX complementar.**
`Repositorio` ganha `existe_import_com_hash(conn, sped_tipo,
cnpj, periodo, hash)`. Cada parser, antes do bloco transacional,
verifica se hash já existe em `_importacoes` para o (sped_tipo ×
cnpj × período). Se sim e `force_reimport=False` (default),
retorna `ResultadoImportacao(sucesso=False, mensagem=...)` com
mensagem clara. CLI ganha `--force-reimport` que passa
`force_reimport=True` aos parsers. Protege contra acidente
operacional (operador rodando 2x); retificadora real (hash
diferente) passa naturalmente pela Opção 3 e é tratada pela
Opção 2.

**Tabelas preservadas:** `_importacoes` (mantém histórico de
versões para T8 Auditoria GUI que usa `is_reimport=True` para
identificar retificações), `_sped_contexto`,
`reconciliacao_override`, `contabil_oportunidades_essencialidade`.

**Atomicidade:** chamada de `deletar_dados_anteriores` está
dentro do `with conn:` existente, junto aos INSERTs subsequentes.
Em qualquer falha entre DELETE e INSERTs, transação rollback
automático — sem perda de dados antigos.

**Convenção `ano_mes` em `_importacoes`:** SPED mensal
(efd_contribuicoes, efd_icms) grava `ano_mes=AAAAMM`; SPED anual
(ecd, ecf) grava `ano_mes=AAAA01`. `existe_import_com_hash`
mapeia `periodo=ano_calendario` → `ano_mes=AAAA*100+1`
internamente para SPED anual, simplificando a query.

### Validação empírica final

Reimport de PISCOFINS jan/2024 NG sobre banco existente
(`data/db/63876114000110/2024.sqlite`):
- Sem `--force-reimport`: aborta com mensagem clara
  ("Arquivo ja importado em 2026-04-29T18:57:59... id=1. Use
  --force-reimport"). `_importacoes` inalterada.
- Com `--force-reimport`: log "Reimport detectado: 79 rows
  antigas removidas (Bug-002 fix)". Status final = `ok`.
  Tabelas filhas: 1 row 0000, 10 F600, 1 M200 (sem duplicação).
  `_importacoes`: 2 rows com mesmo hash (histórico preservado
  para T8 GUI).

pytest -x: 463 passed (440 → 463 com 23 testes regressivos novos
em `tests/db/test_repo_dedup.py` e `tests/parsers/test_dedup_reimport.py`).

### Referência cruzada

- Validação empírica em 2026-04-29 (descoberta) e 2026-05-01
  (validação do fix) — sessões Norte Geradores
- Tabela _importacoes: registro completo de imports históricos
  já existe — base usada pela Opção 3
- src/db/repo.py — `deletar_dados_anteriores`,
  `existe_import_com_hash`, mapa `_TABELAS_POR_SPED_TIPO`

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

---

## BUG-005 — Engine de cruzamentos duplica rows em re-execução

**Status:** resolvido em `f96a45a` (2026-05-01) com limitação documentada
**Severidade:** média (era alta latente; descoberto durante Sprint Hardening)
**Descoberto em:** 2026-04-30, durante investigação Bug-002.

### Sintoma observado

Cada chamada de `Motor.diagnosticar_ano(ano_calendario)` insere
novas rows em `crossref_oportunidades` e `crossref_divergencias`
sem apagar as anteriores. Verificado empiricamente em 2026-04-30:
**132 → 264 oportunidades** em 2 execuções consecutivas no banco
da NG 2024 (cópia isolada para não tocar produção).

### Causa raiz

`src/crossref/engine.py:223-235` faz INSERT puro via
`inserir_oportunidade` / `inserir_divergencia` por achado, sem
DELETE prévio. Padrão estrutural idêntico ao Bug-002, escopo
distinto (output de diagnóstico vs dados de import SPED).

### Resolução (commit `f96a45a`, 2026-05-01)

- `src/db/repo.py` (commit `fd2a63f` da mesma sprint): novo método
  `deletar_diagnostico_anterior(conn, cnpj, ano_calendario)` apaga
  rows de `crossref_oportunidades` + `crossref_divergencias` para
  (cnpj × ano).
- `src/crossref/engine.py`: `Motor.diagnosticar_ano` chama o método
  ANTES do loop de inserts, dentro de `with conn:` (atômico).

**Validação empírica:** após fix, sequência 132 → 132 (era 132 →
264). Cópia isolada do banco NG 2024 preservada; produção não
tocada.

### Limitação documentada

**Re-diagnóstico apaga anotações prévias** (`revisado_em`,
`revisado_por`, `nota` em `crossref_*`). Decisão consciente
baseada em verificação empírica:

1. **Zero anotações em todos os bancos do projeto** na data da
   resolução. Feature implementada (T4 Oportunidades GUI:
   `marcar_revisada`, `salvar_nota` em `oportunidade_controller.py`)
   mas não usada em produção real.
2. Alternativas avaliadas como over-engineering para o cenário
   atual:
   - **Snapshot + restore por chave de negócio** (codigo_regra +
     ano_mes + evidencia_json): complexidade alta, sem demanda
     real.
   - **Versionamento via FK em `_importacoes.id`** ou
     `diagnostico_id`: propaga `import_id` em todas as queries do
     sistema; mudança arquitetural maior.
3. Mitigação UX prevista para sprint futura: mensagem de
   confirmação na T4 Oportunidades GUI ao disparar re-diagnóstico
   ("Esta ação apagará N anotações prévias. Continuar?").

**Quando reabrir como Bug-005-bis** (gatilho explícito):
aparecer 1+ banco em `data/db/*/*.sqlite` com
`revisado_em IS NOT NULL OR (nota IS NOT NULL AND nota != '')`
em `crossref_oportunidades` ou `crossref_divergencias`.
Nesse momento, a feature está em uso real e o trade-off
muda de "limitação aceitável" para "perda de trabalho".

Teste regressivo `test_re_execucao_apaga_anotacoes_LIMITACAO`
em `tests/crossref/test_dedup_diagnostico.py` documenta
explicitamente o comportamento — sua presença é o gatilho de
revisão se o fix for reformulado para preservar anotações.

### Referência cruzada

- Verificação empírica em 2026-04-30 (descoberta — execução
  dupla do `Motor.diagnosticar_ano(2024)` sobre cópia isolada
  do banco NG 2024 confirmou duplicação 132 → 264)
- Verificação empírica em 2026-05-01 (validação do fix —
  mesmo cenário pós-fix: 132 → 132)
- src/crossref/engine.py:222-244 — bloco com DELETE prévio
- src/db/repo.py — `deletar_diagnostico_anterior`
- Discussão arquitetural relacionada em
  `docs/historico/analise-ng-frente1-suspensa-2026-04-29.md`
  (seção 9 — implicações para Adaptação T9)
