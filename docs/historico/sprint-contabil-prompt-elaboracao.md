# Prompts para gerar Balanço Patrimonial e DRE no Claude Code

Dois prompts prontos para uso: uma **versão completa** (projetos profissionais, com validações e múltiplos entregáveis) e uma **versão curta** (uso rápido em chat ou geração ad hoc).

---

## VERSÃO COMPLETA — Para projetos profissionais

```
# Tarefa: Estruturar Balanço Patrimonial (BP) e DRE multi-nível

## Contexto
Você atuará como contador sênior brasileiro especializado em escrituração
contábil para empresas tributadas pelo Lucro Real. Preciso que estruture um
**Balanço Patrimonial** e uma **Demonstração do Resultado do Exercício (DRE)**
em formato hierárquico, compatível com o Plano de Contas Referencial da
Receita Federal (ECD/ECF) e com o SPED Contábil.

## Entrada esperada
Antes de gerar o relatório, pergunte-me (apenas se eu não tiver fornecido):
1. Razão social e CNPJ (ou use placeholders se for exemplo didático)
2. Regime tributário (Lucro Real, Presumido ou Simples Nacional)
3. Setor de atuação (indústria, comércio, serviços ou misto)
4. Exercícios sociais a comparar (ex.: 2025 x 2024)
5. Moeda e escala (R$, R$ mil ou R$ milhões)
6. Se devo gerar valores fictícios coerentes ou se fornecerei o trial balance
7. Formato de saída desejado: Markdown, .xlsx (com fórmulas) ou .docx

## Estrutura obrigatória do Plano de Contas
Use **quatro níveis hierárquicos** com numeração decimal:
- **Nível 1 — Grupo** (ex.: 1 ATIVO)
- **Nível 2 — Subgrupo** (ex.: 1.1 ATIVO CIRCULANTE)
- **Nível 3 — Conta Sintética** (ex.: 1.1.1 Disponibilidades)
- **Nível 4 — Conta Analítica** (ex.: 1.1.1.01 Caixa)

Convenção de codificação:
- 1 = ATIVO | 2 = PASSIVO + PL | 3 = RESULTADO
- Contas redutoras devem usar sufixo .99 e aparecer entre parênteses
- Totalizações por nível devem ser explícitas (em negrito) e bater por soma

## Conteúdo mínimo do BP

### ATIVO
- **Circulante**: Disponibilidades (caixa, bancos, aplicações), Clientes
  (com PCLD redutora), Estoques (MP, em elaboração, acabados, uso/consumo),
  Tributos a recuperar (ICMS, PIS, COFINS, IRPJ/CSLL), Outros créditos
  (adiantamentos, despesas antecipadas)
- **Não Circulante**: Realizável a LP (depósitos judiciais tributários e
  trabalhistas, partes relacionadas), Investimentos (coligadas, propriedades),
  Imobilizado (terrenos, edificações, máquinas, veículos, móveis, TI, com
  depreciação acumulada), Intangível (marcas, software, com amortização)

### PASSIVO + PL
- **Circulante**: Fornecedores (nacionais/estrangeiros), Empréstimos CP
  (capital de giro, FINAME), Obrigações trabalhistas (salários, INSS, FGTS,
  provisão de férias e 13º com encargos), Obrigações tributárias (ICMS, PIS,
  COFINS, IRPJ, CSLL, ISS, IRRF), Outras obrigações (dividendos,
  adiantamentos de clientes)
- **Não Circulante**: Empréstimos LP (BNDES, debêntures), **Parcelamentos
  tributários** (transação PGFN Lei 13.988/2020, parcelamento ordinário RFB),
  Provisão para contingências (cíveis, trabalhistas, tributárias)
- **PL**: Capital social, Reservas de capital, Reservas de lucros (legal e
  retenção de lucros), Lucros/prejuízos acumulados

## Conteúdo mínimo da DRE
Sequência obrigatória (art. 187 da Lei 6.404/76):
1. Receita Operacional Bruta (mercado interno, externo, serviços)
2. (-) Deduções (devoluções, ICMS, PIS, COFINS, ISS)
3. = Receita Líquida
4. (-) Custo das Vendas (CPV detalhado em MP, MOD, CIF; e CSP)
5. = Lucro Bruto
6. (-) Despesas Operacionais (vendas, administrativas, tributárias,
   depreciação/amortização) — cada uma aberta em contas analíticas
7. (+/-) Outras Receitas/Despesas Operacionais
8. = Resultado Antes do Financeiro (EBIT)
9. (+/-) Resultado Financeiro Líquido (receitas e despesas financeiras
   abertas, incluindo juros/multas tributárias)
10. = LAIR
11. (-) IRPJ e CSLL (correntes e diferidos separados)
12. = Lucro Líquido do Exercício

## Requisitos de apresentação
- Tabelas com colunas: **Código | Conta | Exercício atual | Exercício anterior**
- Para a DRE, adicionar coluna de **Análise Vertical (% sobre Receita Líquida)**
- Linhas de subtotal e total em **negrito**
- Valores negativos sempre **entre parênteses**
- Garantir que **ATIVO = PASSIVO + PL** e que o Lucro Líquido bata com a
  movimentação do PL
- Após as tabelas, incluir seção "Observações sobre a estrutura" explicando
  o mapeamento para ECD (registros J100/J150) e para a ECF

## Validações automáticas
Antes de entregar, confirme que:
- [ ] Soma das contas analíticas = saldo da sintética em cada nível
- [ ] Total do Ativo = Total do Passivo + PL
- [ ] Lucro Líquido da DRE = variação do PL ajustada por dividendos
- [ ] Todas as contas redutoras estão com sinal negativo
- [ ] AV% da DRE soma corretamente a partir da Receita Líquida = 100%

## Entregáveis
1. **Plano de Contas** completo (4 níveis) em tabela ou aba separada
2. **Balanço Patrimonial** comparativo (2 exercícios)
3. **DRE** comparativa com AV%
4. **Notas explicativas** mínimas sobre as principais rubricas
5. Se o output for .xlsx: fórmulas SOMASE por nível, formatação contábil
   brasileira (vírgula decimal, ponto separador de milhar) e abas
   separadas para Plano de Contas, BP, DRE e Validações

## Estilo
Português brasileiro, terminologia técnica contábil, sem anglicismos
desnecessários. Quando houver escolha entre nomenclatura CPC e nomenclatura
fiscal/RFB, prefira a fiscal.

## Comece agora
Faça as perguntas de entrada que faltarem e, em seguida, gere os artefatos.
```

---

## VERSÃO CURTA — Para uso rápido

```
Atue como contador brasileiro sênior. Gere um Balanço Patrimonial e uma DRE
comparativos (2 exercícios) em formato hierárquico de 4 níveis (Grupo →
Subgrupo → Sintética → Analítica), com numeração decimal (1=Ativo,
2=Passivo+PL, 3=Resultado).

Regras:
- Padrão Lei 6.404/76 e Plano de Contas Referencial RFB (ECD/ECF)
- Tabelas com Código | Conta | Ano atual | Ano anterior; DRE com AV%
- Subtotais e totais em negrito; redutoras com sufixo .99 entre parênteses
- Inclua: tributos a recuperar/recolher detalhados, parcelamentos tributários
  (PGFN/RFB) no PNC, provisão para contingências, e CPV aberto em MP/MOD/CIF
- Garanta: Ativo = Passivo + PL, e LL bate com variação do PL

Antes de começar, pergunte: regime tributário, setor, exercícios e se devo
usar valores fictícios ou se fornecerei o balancete. Entregue em [Markdown
| .xlsx | .docx — escolha].
```

---

## Como usar no Claude Code

1. Abra o terminal na pasta do projeto e rode `claude`  
2. Cole a versão escolhida diretamente no prompt  
3. Para reuso, salve como slash command em `.claude/commands/bp-dre.md` — assim você dispara com `/bp-dre` em qualquer sessão  
4. Se quiser saída em Excel, peça explicitamente: *"Entregue em .xlsx com abas separadas e fórmulas SOMASE por nível"*

## Dicas de refinamento

- Para Lucro Presumido: troque "Lucro Real" no contexto e remova IRPJ/CSLL diferidos da DRE  
- Para Simples Nacional: substitua o detalhamento de tributos por uma única conta "DAS a recolher" e adicione anexo de receita por faixa  
- Para grupo econômico: peça a versão consolidada com eliminações intercompany destacadas em coluna separada

