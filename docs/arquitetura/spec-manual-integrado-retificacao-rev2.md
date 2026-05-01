# Especificação Arquitetural — Manual Integrado de Retificação

**Status:** Proposta arquitetural — destinada a virar **seção 23 do CLAUDE.md (v7)** ou módulo de documentação independente, conforme decisão do operador.

**Versão:** Rev. 2, abril/2026. **Autor:** Marcelo Wanderley (Primetax Solutions), com colaboração técnica do Claude. **Pré-requisitos de leitura:** CLAUDE.md v6 do projeto Primetax SPED Cross-Reference System, com atenção especial às seções 4 (princípios não-negociáveis), 8 (49 cruzamentos), 18 (disponibilidade dos SPEDs) e 21 (catálogo de regras como infraestrutura). **Decisão pendente:** se esta especificação será formalizada como seção 23 da v7 antes do Sprint 1 começar, ou se ficará como documentação satélite até validação prática.

**Mudanças da rev. 1 → rev. 2:** (a) renomeação de "Etapa 4 — Manual acionável" para "Etapa 4 — Manual executor", reforçando que a Etapa 4 *executa o que a Etapa 1 especificou* e não inventa nada novo; (b) adição da camada `operacao_estruturada` ao schema do frontmatter dos blocos tipo `procedimento`, de forma que cada procedimento escrito hoje em prosa narrativa para humanos carregue, ao seu lado, especificação máquina-legível pronta para o gerador automático da Etapa 4 consumir. O resultado conceitual desses dois ajustes é tornar **explícito o continuum** entre escrever manual e especificar gerador automático — o trabalho da Etapa 1 é simultaneamente documentação para humanos e especificação executável para o futuro.

---

## 1\. Contexto e motivação

### 1.1 O problema que esta arquitetura resolve

O sistema Primetax SPED Cross-Reference identifica oportunidades de recuperação de PIS/COFINS e produz relatórios estruturados com rastreabilidade até a linha do SPED. Mas identificar a oportunidade é apenas metade do trabalho. A outra metade — **operacionalizar a recuperação** — exige conhecimento procedimental denso: quais registros do SPED retificar, em que ordem, quais campos preencher no PER/DCOMP, quais modelos de petição usar, quais armadilhas evitar.

Hoje esse conhecimento está distribuído entre experiência de auditores sêniores, documentos não-versionados em SharePoint/OneDrive, mensagens em chats internos e práticas tácitas. Auditores plenos precisam consultar sêniores em cada passo, sêniores precisam refazer trabalho mental para cada caso, e a Primetax não consegue escalar a operação sem perda de qualidade.

A solução proposta é integrar esse conhecimento operacional ao próprio sistema de cruzamentos, de forma que **cada oportunidade identificada venha acompanhada do manual de retificação aplicável àquele caso concreto**, com instruções, exemplos numéricos do cliente e referências legais contextualizadas.

### 1.2 Por que arquitetura, não documentação

A primeira tentação é tratar isso como "produzir um manual em PDF e referenciá-lo no relatório". É insuficiente por quatro razões:

**Manual estático perde contexto.** Um cliente Lucro Real com ação judicial pré-modulação tem fluxo de retificação diferente de um cliente Lucro Presumido em modulação geral. Um documento único força o auditor a filtrar mentalmente o que se aplica e o que não se aplica — exatamente o trabalho que o sistema deveria automatizar.

**Manual estático envelhece sem alarme.** Quando uma IN é revogada ou um precedente jurisprudencial muda, o PDF antigo continua circulando. Auditor consulta material desatualizado e gera petição inviável.

**Manual estático separa identificação e ação.** Auditor identifica oportunidade no relatório do sistema, fecha o sistema, abre o manual em outra ferramenta, procura a seção aplicável, volta ao sistema. Cada troca de contexto custa atenção e abre espaço para erro.

**Manual estático não é auditável.** Em um modelo de honorários de êxito com responsabilidade técnica sobre o resultado da recuperação, é importante saber **qual versão do manual orientou cada operação** — para defesa em eventual questionamento e para aprendizado interno (qual versão do manual produziu mais glosas? quais seções precisam de revisão?). Manual estático em PDF não tem esse rastro.

A arquitetura proposta resolve os quatro problemas:

- Conteúdo **contextual** filtrado pelo perfil do cliente e pela natureza da oportunidade.  
- Conteúdo **versionado** com vigência declarada de cada trecho.  
- Conteúdo **integrado** ao fluxo do auditor, sem troca de ferramenta.  
- Conteúdo **auditável**, com snapshot da versão consultada por análise.

### 1.3 Princípios da v6 que esta arquitetura atende

A integração se apoia diretamente em quatro dos sete princípios não-negociáveis (CLAUDE.md seção 4):

**Princípio 1 (rastreabilidade fiscal absoluta).** Cada instrução procedimental do manual carrega o registro SPED, o campo e a regra de validação que ela manipula — o auditor pode voltar do passo procedimental até a fundamentação técnica em três cliques.

**Princípio 4 (versionamento de regras com dispositivo legal).** Toda seção operacional do manual é ancorada a um dispositivo legal específico, com data de início e data de fim de vigência declaradas. Quando a vigência expira, o sistema avisa.

**Princípio 5 (português em nomes fiscais).** Manual escrito em português técnico-fiscal brasileiro, alinhado à terminologia da RFB.

**Princípio 6 (proibição de hardcoding).** Modelos de petição, fórmulas de cálculo e referências a alíquotas vivem em arquivos versionados separadamente, não embutidos no texto do manual.

---

## 2\. Decisão arquitetural

### 2.1 Decisão

**Adotar a Arquitetura C (Híbrida Estruturada)** com progressão em quatro etapas (1 estática, 2 unificada navegável, 3 personalizada com dados do cliente, 4 acionável).

A Etapa 1 entra no Sprint 1 do projeto, junto da infraestrutura do catálogo de regras (CLAUDE.md seção 21). As etapas 2, 3 e 4 entram nos sprints subsequentes conforme o sistema amadurece.

### 2.2 Por que Arquitetura C

A Arquitetura A (manual fragmentado por regra, em arquivos separados) tem a vantagem da inseparabilidade regra-manual mas perde coesão narrativa. Auditor que quer estudar o domínio inteiro precisa abrir 49 arquivos.

A Arquitetura B (manual único com âncoras navegáveis) tem coesão narrativa boa mas o mapeamento regra-âncora é frágil — se alguém renomeia a âncora sem atualizar o mapeamento, a integração quebra silenciosamente.

A Arquitetura C resolve as duas limitações: o conteúdo é escrito em **arquivos Markdown estruturados com frontmatter YAML por bloco**, indicando explicitamente a quais regras cada bloco se aplica e qual é seu propósito (fundamentação, procedimento, exemplo, modelo de petição, armadilha, caso especial). Um pré-processador no momento de renderização monta tanto a "visão por regra" quanto a "visão linear completa" a partir da mesma fonte única.

A complexidade adicional do pré-processador é absorvida no Sprint 1 dentro do esforço de construção do catálogo — ele compartilha o mesmo registry de regras, então boa parte da infraestrutura é reaproveitada.

### 2.3 Etapas progressivas

A arquitetura é desenhada para ser **construída em camadas**, cada uma entregando valor por si só, e cada uma **construindo sobre o trabalho da anterior, não substituindo-o**. Esse princípio é central: nenhum esforço da Etapa 1 vira desperdício quando as etapas seguintes chegam.

**Etapa 1 — Manual estático contextual (Sprint 1).** Conteúdo escrito uma vez por regra ou família de regras, exibido pelo sistema na forma estática quando o auditor abre uma oportunidade. Não há filtragem por perfil de cliente nem personalização com dados — é o mesmo conteúdo para todos os casos da regra. Já cobre 60-70% da utilidade prática porque o conteúdo *já é específico da regra* (não é genérico). Os blocos tipo `procedimento` são escritos em duas camadas desde o início: prosa narrativa para humanos (consumida na Etapa 1\) e camada `operacao_estruturada` em YAML para máquinas (declarada na Etapa 1, **consumida apenas na Etapa 4** — ver seção 4.3).

**Etapa 2 — Manual unificado navegável (Sprints 2-3).** O sistema gera, a partir dos blocos de Etapa 1 já escritos, uma visão linear completa que pode ser exportada para PDF. Auditor pode tanto "ver manual desta oportunidade" quanto "ler o manual completo do Tema 69". Acrescenta navegação cruzada entre regras relacionadas. Reaproveita 100% do conteúdo da Etapa 1\.

**Etapa 3 — Manual personalizado com dados do cliente (Sprint 4-5).** Templates Jinja-style que recebem o contexto do cliente e produzem manual com exemplos numéricos reais. "Para a NORTE GERADORES, na competência 03/2022, base correta após exclusão é R$ 4.292.345" em vez de "se a base era R$ 1.000.000 e o ICMS era R$ 180.000". Auditor copia direto para a petição. Reaproveita 100% do conteúdo da Etapa 1, apenas substitui placeholders.

**Etapa 4 — Manual executor (Sprints 6-8).** O gerador automático de retificadoras consome diretamente a camada `operacao_estruturada` dos blocos tipo `procedimento` que foram escritos na Etapa 1\. O auditor abre a oportunidade no relatório, vê o manual contextual (Etapa 1+3), e clica em "gerar SPED retificador desta competência" — o sistema executa a `operacao_estruturada` parametrizada com os dados do cliente e produz o arquivo. **A Etapa 4 não é um sistema novo; é a ativação da camada que a Etapa 1 já deixou pronta.** Análoga: "preencher PER/DCOMP", "calcular impacto da compensação", "gerar petição administrativa". Esta etapa só faz sentido depois que a integração com e-CAC (CLAUDE.md, fora do escopo da primeira iteração) estiver disponível para a parte de PER/DCOMP — para a parte de SPED retificador, pode ser construída antes.

A renomeação de "Manual acionável" (rev. 1\) para "Manual executor" (rev. 2\) reflete a relação entre as etapas: a Etapa 4 não cria comportamento novo — ela executa procedimentos que a Etapa 1 já especificou em sua camada estruturada. Sem Etapa 1, não há Etapa 4 possível.

### 2.4 O que esta especificação cobre

Esta especificação foca na **Etapa 1**, com gancho explícito para as etapas seguintes. O design da Etapa 1 não pode bloquear as etapas 2-4 — escolhas de hoje precisam ser compatíveis com necessidades de amanhã.

A especificação detalhada das Etapas 2, 3 e 4 será feita no momento de implementação de cada uma, com revisão desta especificação se necessário.

---

## 3\. Estrutura de pastas e arquivos

### 3.1 Localização no projeto

```
primetax-sped-crossref/
├── docs/
│   ├── contexto-fiscal/
│   │   └── manuais-retificacao/
│   │       ├── meta/
│   │       │   ├── frontmatter-schema.yaml      # Schema oficial dos blocos
│   │       │   ├── glossario.md                 # Termos comuns
│   │       │   └── modelos-peticao/             # Petições reutilizáveis
│   │       ├── tema-69-icms-na-base/
│   │       │   ├── 00-fundamentacao.md          # Núcleo doutrinário
│   │       │   ├── 10-modulacao-temporal.md     # Os três cenários
│   │       │   ├── 20-quantificacao.md          # Como calcular o crédito
│   │       │   ├── 30-retificacao-sped.md       # Operacional SPED
│   │       │   ├── 40-per-dcomp.md              # Operacional e-CAC
│   │       │   ├── 50-armadilhas.md             # Erros comuns
│   │       │   └── 60-casos-especiais.md        # Lucro Presumido, exportação etc.
│   │       ├── tema-cred-presumido-frete/
│   │       │   └── ...
│   │       └── ...
│   └── layouts-oficiais/
│       └── ...
└── src/
    ├── crossref/
    │   ├── catalogo/                            # Seção 21 do CLAUDE.md v6
    │   └── camada_2_oportunidades/
    │       └── cr_07_tese_69.py                 # Decorator referencia o manual
    └── manuais/                                 # Pré-processador
        ├── __init__.py
        ├── modelo.py                            # Dataclass BlocoManual
        ├── carregador.py                        # Lê arquivos .md e parseia frontmatter
        ├── filtros.py                           # Filtragem por regra/perfil/contexto
        ├── renderizador.py                      # Saída para terminal/web/PDF
        └── validador.py                         # Verifica integridade dos blocos
```

A escolha de manter o conteúdo em `docs/contexto-fiscal/manuais-retificacao/` (e não dentro de `src/`) é deliberada: o conteúdo é **fiscal-jurídico**, escrito majoritariamente por consultores Primetax (não por desenvolvedores). Mantê-lo fora do `src/` reduz a barreira de contribuição e deixa claro que é conteúdo, não código.

### 3.2 Granularidade dos arquivos

Cada **tema** (família de regras tratando o mesmo objeto fiscal) ocupa uma pasta. Exemplos de temas:

- Tema 69 (exclusão do ICMS da base) — cobre CR-07, CR-08, CR-09 e CR-26.  
- Crédito presumido sobre frete subcontratado — cobre CR-21.  
- Ativo imobilizado e CIAP — cobre CR-14, CR-15, CR-27, CR-35.  
- Retenções não compensadas — cobre CR-16, CR-17, CR-18, CR-19.

A granularidade do **arquivo dentro do tema** é semântica: cada arquivo cobre um aspecto específico (fundamentação, modulação, quantificação, retificação SPED, PER/DCOMP, armadilhas, casos especiais). Os números no nome (`00-`, `10-`, `20-`) controlam a ordem na visão linear (Etapa 2\) — múltiplos de 10 deixam espaço para inserir conteúdo intermediário sem renomear vizinhos.

Não há arquivo único por regra. Múltiplas regras podem compartilhar arquivos do mesmo tema, e o frontmatter de cada bloco declara quais regras ele atende.

---

## 4\. Schema do frontmatter por bloco

### 4.1 Conceito

Cada arquivo Markdown contém um ou mais **blocos** delimitados por frontmatter YAML. Um bloco é a unidade mínima de filtragem — quando o sistema decide se exibe ou não determinado conteúdo, decide bloco a bloco.

```
---
bloco_id: tese69-modulacao-acao-anterior
tipo: procedimento
regras: [CR-07, CR-08, CR-09, CR-26]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "RE 574.706/PR (STF, Repercussão Geral)"
  - "Embargos declaratórios (julgamento 13/05/2021)"
  - "Parecer SEI 7698/2021/ME"
referencias_cruzadas:
  - bloco_id: tese69-fundamentacao-jurisprudencial
  - bloco_id: tese69-quantificacao-base
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
---

## Cliente com ação judicial ajuizada antes de 15/03/2017

Para clientes que ajuizaram ação...
[conteúdo do bloco]
```

### 4.2 Campos do frontmatter — obrigatórios

**`bloco_id`** — identificador único global em todo o sistema. Formato sugerido: `{tema-slug}-{aspecto}-{detalhe-opcional}`. Exemplo: `tese69-modulacao-acao-anterior`. Validação: regex `^[a-z0-9-]+$`, comprimento entre 8 e 80 caracteres.

**`tipo`** — natureza do bloco. Enum:

- `fundamentacao` — explicação técnica/jurídica do que é a tese.  
- `procedimento` — instrução operacional (como retificar, como preencher).  
- `exemplo` — exemplo numérico ilustrativo.  
- `modelo` — modelo de petição, formulário ou comunicação ao cliente.  
- `armadilha` — alerta sobre erro comum.  
- `caso-especial` — variação aplicável a perfil restrito.  
- `glossario` — definição de termo técnico.

A separação por tipo permite ao auditor filtrar a visão. Quando ele clica "como retifico esse caso?", o sistema mostra apenas os blocos `procedimento`, `exemplo` e `modelo` aplicáveis. Quando ele clica "por que isso é uma oportunidade?", mostra apenas `fundamentacao`.

**`regras`** — lista de códigos do catálogo (seção 21 do CLAUDE.md v6) a que o bloco se aplica. Pelo menos uma regra. Validação cruzada: o sistema verifica que todos os códigos existem no registry.

**`vigencia_inicio`** — data ISO em que a orientação do bloco passou a ser válida. Útil para distinguir orientação aplicável a fatos geradores recentes vs. fatos antigos.

**`vigencia_fim`** — data ISO em que a orientação deixou de ser válida, ou `null` se ainda vigente. Quando a vigência expira, o sistema marca visualmente o bloco como obsoleto e sugere revisão.

**`fundamentacao_legal`** — lista de dispositivos legais que sustentam o conteúdo. Materializa o princípio 4 do CLAUDE.md.

**`ultima_revisao`** — data ISO da última revisão de conteúdo. Validação: blocos com `ultima_revisao` há mais de 18 meses geram aviso de revisão pendente.

**`revisor`** — nome do consultor que revisou pela última vez. Rastreabilidade humana.

### 4.3 Campos do frontmatter — opcionais

**`aplicavel_quando`** — condições estruturadas que filtram a aplicabilidade do bloco ao caso concreto. Mecanismo central da contextualização.

Exemplos de chaves padronizadas (catálogo a expandir):

- `cliente_regime_apuracao: lucro-real | lucro-presumido | simples-nacional`  
- `cliente_setor: industria | comercio | servicos | agro | financeiro`  
- `cliente_tem_acao_judicial_pre_modulacao: true | false`  
- `cliente_tem_exportacao: true | false`  
- `cliente_aliquota_pis_cofins: zero | reduzida | basica | majorada`  
- `competencia_anterior_a: "2019-01-01"`  
- `competencia_posterior_a: "2017-03-15"`  
- `prescricao_situacao: vigente | iminente | prescrita`

A semântica é **AND** entre as chaves: o bloco se aplica somente quando todas as condições são verdadeiras. Para semântica OR, criar bloco separado com cópia do conteúdo.

**`referencias_cruzadas`** — outros blocos que o auditor talvez queira ver junto. Permite construir grafos de leitura recomendada.

**`exemplo_dados_minimos`** — quando o `tipo` é `exemplo`, declara quais dados do cliente o exemplo consome (`competencia`, `vl_item`, `vl_icms`, etc.). Habilita a Etapa 3 (personalização) sem mudança de schema.

**`acoes_disponiveis`** — quando o `tipo` é `procedimento`, declara quais ações automatizadas estão disponíveis (`gerar_sped_retificador`, `preencher_per_dcomp`, etc.). Habilita a Etapa 4 (executor) sem mudança de schema.

**`operacao_estruturada`** — quando o `tipo` é `procedimento`, declara em formato máquina-legível a **mesma operação** que a prosa narrativa do bloco descreve em português técnico-fiscal. É o coração da continuidade Etapa 1 → Etapa 4: a prosa narrativa serve o auditor humano hoje; a `operacao_estruturada` serve o gerador automático amanhã. Ambas descrevem a mesma realidade fiscal, em linguagens diferentes.

Schema da `operacao_estruturada`:

- `registros_alvo` — lista de tipos de registro SPED que o procedimento manipula (ex: `[C170]`, `[F100, F120]`, `[M210, M610]`).  
- `alteracoes` — lista de operações de campo a executar:  
  - `campo` — nome do campo a alterar (ex: `VL_BC_PIS`).  
  - `formula` — expressão de cálculo do novo valor, em sintaxe Python-like, referenciando outros campos do mesmo registro ou variáveis de contexto (ex: `"VL_ITEM - VL_DESC - VL_ICMS"`).  
  - `condicao` — predicado que define para quais linhas a alteração se aplica (ex: `"CST_PIS in [01, 02, 03, 05]"`). Ausência significa "todas as linhas do registro alvo".  
- `registros_dependentes` — lista de registros que precisam de recálculo após a alteração principal (ex: ao alterar C170, recalcular C190 que agrega C170 por CST/CFOP/alíquota; recalcular M210 que totaliza C170 na apuração). O gerador automático recalcula esses registros encadeadamente.  
- `validacao_pos_alteracao` — lista de invariantes que devem ser verdadeiras após a operação (ex: `"VL_BC_PIS >= 0"`, `"VL_BC_PIS <= VL_ITEM"`). Se alguma invariante falha, o gerador aborta com erro reportável.  
- `efeitos_apuracao` — lista declarativa de efeitos esperados na apuração (ex: `"reducao_base_pis_nao_cumulativo"`, `"reducao_imposto_devido"`). Útil para validação cruzada com o impacto financeiro estimado pelo motor de cruzamentos.

**Exemplo completo** — bloco procedimental do Tema 69 (exclusão do ICMS no C170):

```
operacao_estruturada:
  registros_alvo: [C170]
  alteracoes:
    - campo: VL_BC_PIS
      formula: "VL_ITEM - VL_DESC - VL_ICMS"
      condicao: "CST_PIS in [01, 02, 03, 05]"
    - campo: VL_BC_COFINS
      formula: "VL_ITEM - VL_DESC - VL_ICMS"
      condicao: "CST_COFINS in [01, 02, 03, 05]"
    - campo: VL_PIS
      formula: "round(VL_BC_PIS * ALIQ_PIS / 100, 2)"
      condicao: "CST_PIS in [01, 02, 03, 05]"
    - campo: VL_COFINS
      formula: "round(VL_BC_COFINS * ALIQ_COFINS / 100, 2)"
      condicao: "CST_COFINS in [01, 02, 03, 05]"
  registros_dependentes:
    - C190  # Agregado por CST/CFOP/alíquota — recalcular somatórios
    - M210  # Apuração PIS — recalcular base e contribuição
    - M610  # Apuração COFINS — recalcular base e contribuição
    - M200  # Totalizador PIS
    - M600  # Totalizador COFINS
  validacao_pos_alteracao:
    - "VL_BC_PIS >= 0"
    - "VL_BC_PIS <= VL_ITEM"
    - "VL_BC_COFINS >= 0"
    - "VL_BC_COFINS <= VL_ITEM"
  efeitos_apuracao:
    - reducao_base_pis_nao_cumulativo
    - reducao_base_cofins_nao_cumulativo
    - reducao_imposto_devido
```

**Política de preenchimento da `operacao_estruturada` na Etapa 1\.** O campo é **opcional na Etapa 1** — pode ser deixado vazio. **Obrigatório a partir da Etapa 4** para qualquer bloco que pretenda ter botão "executar" no manual. O recomendável é preenchê-lo desde a Etapa 1 sempre que o consultor que escreve a prosa narrativa souber traduzir o procedimento em operações de campo — captura conhecimento procedimental que de outra forma fica apenas implícito no texto. Quando o consultor não tem segurança técnica para preencher (ex: procedimento envolve cálculo complexo com múltiplos cenários), deixa vazio e a `operacao_estruturada` é completada depois pelo desenvolvedor que implementa o gerador automático no momento da Etapa 4\.

A validação do schema garante que **a prosa e a `operacao_estruturada` se referem à mesma operação** — não há mecanismo automático de validação cruzada, mas o validador exige que o consultor declare em `operacao_estruturada.referencia_secao_prosa` qual subseção da prosa corresponde àquela operação estruturada, criando rastro humano de coerência.

---

## 5\. Tipos de bloco — diretrizes editoriais

A seção 4 estabelece o schema. Esta seção 5 estabelece **como escrever cada tipo de bloco** para que a coleção mantenha qualidade e consistência ao longo do tempo.

### 5.1 Bloco tipo `fundamentacao`

Objetivo: dar ao auditor pleno o suficiente para entender por que aquela é uma oportunidade e qual o risco/benefício de pleitear.

Estrutura recomendada:

1. **Síntese em duas frases** — o que é a tese e o que ela permite recuperar.  
2. **Fundamentação jurídica** — dispositivos legais e jurisprudência consolidada.  
3. **Operacionalização contábil-fiscal** — como o erro aparece na escrituração.  
4. **Magnitude esperada do crédito** — ordem de grandeza típica em % da receita ou da base.

Tamanho: 600 a 1.200 palavras. Texto denso, sem floreios. Linguagem da RFB.

### 5.2 Bloco tipo `procedimento`

Objetivo: instruir passo a passo como executar a retificação/recuperação. Este é o tipo de bloco mais sensível à evolução do sistema porque carrega **duas camadas de conteúdo** que precisam permanecer sincronizadas entre si: a prosa narrativa para humanos e a `operacao_estruturada` em YAML para máquinas.

Estrutura recomendada da prosa narrativa (camada para humanos):

1. **Pré-condições** — o que precisa ser verdadeiro antes de iniciar.  
2. **Sequência de passos numerados** — cada passo com (a) ação concreta, (b) campo/registro afetado, (c) valor a preencher, (d) validação esperada.  
3. **Pós-condições** — como verificar que o procedimento foi bem-sucedido.

A `operacao_estruturada` (camada para máquinas, conforme seção 4.3) acompanha a prosa no mesmo bloco e descreve a mesma operação em formato executável. Ambas precisam dizer a mesma coisa em linguagens diferentes — quando uma é alterada, a outra precisa ser revisada na sequência.

**Quando preencher a `operacao_estruturada` na Etapa 1\.** Idealmente sempre. Na prática:

- Se o procedimento é **direto e algorítmico** (ex: alterar campo X com fórmula Y quando condição Z), preencher já na Etapa 1\. O consultor que escreve a prosa tem conhecimento suficiente para preencher a estrutura.  
- Se o procedimento é **complexo e exige julgamento humano** (ex: classificar item entre múltiplas hipóteses tributárias com base em descrição da operação), deixar vazio na Etapa 1\. A camada estruturada será preenchida no momento da Etapa 4, possivelmente com auxílio de modelo de linguagem para classificação assistida.  
- Se o procedimento é **sensível a casos especiais** (ex: aplica-se diferente para cliente Lucro Presumido), criar **blocos separados por caso especial** com `aplicavel_quando` específico, cada um com sua `operacao_estruturada` própria. Não tentar capturar todos os casos em um único bloco com lógica condicional embutida.

Tamanho da prosa: 400 a 800 palavras. Imperativo direto. Sem exemplos genéricos no procedimento — exemplos são bloco separado.

### 5.3 Bloco tipo `exemplo`

Objetivo: tornar concreto o que o procedimento descreve abstratamente.

Estrutura recomendada:

1. **Cenário** — descrição curta do caso (perfil do cliente, competência, valores principais).  
2. **Aplicação do procedimento** — passo a passo do exemplo, com valores reais.  
3. **Resultado** — qual o crédito gerado, qual o impacto na apuração.

Quando a Etapa 3 estiver implementada, exemplos são gerados automaticamente com dados do cliente. Na Etapa 1, são exemplos estáticos representativos.

Tamanho: 300 a 600 palavras. Cálculos completos, sem omissões.

### 5.4 Bloco tipo `modelo`

Objetivo: oferecer texto pronto para uso em petições, ofícios ou comunicações ao cliente.

Estrutura: o próprio modelo, com placeholders Jinja para campos variáveis (`{{ cliente.razao_social }}`, `{{ valor_credito_apurado }}`, etc.). Comentários sobre quando usar e como adaptar.

Modelos ficam em `meta/modelos-peticao/` e são referenciados por outros blocos. Não há texto livre fora do modelo.

### 5.5 Bloco tipo `armadilha`

Objetivo: alertar sobre erro comum que invalida ou compromete a recuperação.

Estrutura recomendada:

1. **Descrição do erro** — o que o auditor faz por engano.  
2. **Consequência** — o que acontece (glosa, autuação, perda de prazo).  
3. **Como evitar** — verificação preventiva concreta.  
4. **Como corrigir se já cometido** — caminho de remediação se aplicável.

Tamanho: 200 a 400 palavras. Tom de alerta, mas técnico.

### 5.6 Bloco tipo `caso-especial`

Objetivo: tratar variações aplicáveis a perfis restritos de cliente.

Use sempre que a aplicação geral do procedimento não cobre todos os clientes. Exemplos: empresas Lucro Presumido em parte do período, exportadoras com regime monofásico, empresas com mudança de regime no exercício, sucessões de fato gerador.

Cada caso especial é um bloco independente com `aplicavel_quando` restritivo. O auditor não vê o bloco se o cliente não se enquadra.

### 5.7 Bloco tipo `glossario`

Objetivo: definir termo técnico que aparece nos demais blocos.

Estrutura: termo \+ definição de uma frase \+ definição expandida \+ referência cruzada.

Glossário compartilhado entre todos os temas vive em `meta/glossario.md`.

---

## 6\. Pré-processador — comportamento

O módulo `src/manuais/` é o **pré-processador** que carrega os arquivos Markdown, parseia o frontmatter, valida os blocos contra o schema, e oferece três projeções para consumo do sistema.

### 6.1 Carregamento

Na inicialização, `carregador.py` percorre `docs/contexto-fiscal/manuais-retificacao/`, lê todos os arquivos `.md`, extrai os blocos delimitados por frontmatter YAML, e popula um registry interno indexado por `bloco_id`.

Validações executadas no carregamento:

- **Schema do frontmatter** — todos os campos obrigatórios presentes.  
- **Unicidade de `bloco_id`** — duplicação é erro de carregamento.  
- **Existência das regras referenciadas** — códigos no campo `regras` precisam existir no registry de regras (catálogo da seção 21).  
- **Vigência coerente** — `vigencia_inicio < vigencia_fim` quando ambos preenchidos.  
- **Referências cruzadas válidas** — `bloco_id` em `referencias_cruzadas` precisa existir.  
- **Idade da revisão** — blocos com `ultima_revisao` há mais de 18 meses geram aviso (não erro).

Falhas de validação **bloqueiam a inicialização do sistema**. Princípio: melhor não rodar do que rodar com manual quebrado.

### 6.2 Filtragem por contexto

Quando o sistema recebe uma oportunidade do motor de cruzamentos e precisa exibir o manual aplicável, o pré-processador executa três filtros em sequência:

**Filtro 1 — Por regra.** Quais blocos têm a regra da oportunidade no campo `regras`. Filtro inicial reduz o universo.

**Filtro 2 — Por aplicabilidade.** Cada bloco com `aplicavel_quando` é avaliado contra o contexto do cliente e da competência. Bloco passa apenas se todas as condições forem verdadeiras.

**Filtro 3 — Por vigência.** Blocos com `vigencia_fim` no passado são excluídos da apresentação principal mas marcados como "histórico" (acessíveis se o auditor solicitar explicitamente — útil para fatos geradores antigos).

Os blocos resultantes são organizados em ordem natural de leitura: `fundamentacao` → `procedimento` → `exemplo` → `modelo` → `armadilha` → `caso-especial`. Dentro de cada tipo, ordem alfabética de `bloco_id`.

### 6.3 Renderização

A saída é flexível porque a Etapa 1 não decide ainda qual a interface final do sistema (CLI? GUI desktop? Web?). O `renderizador.py` produz três formatos:

**Markdown plano** — para CLI e debug. **HTML estilizado com identidade visual Primetax** — para GUI futura e exportação web. **PDF via `weasyprint` ou similar** — para entregas formais ao cliente ou para defesa.

A renderização preserva o frontmatter como **metadados visíveis** quando o auditor solicita: a vigência, a data da última revisão e a fundamentação legal aparecem como cabeçalho do bloco. Princípio 1 (rastreabilidade) atendido: o auditor sempre sabe de onde vem aquela orientação.

### 6.4 Snapshot da versão consultada

Para fins de auditoria interna e defesa em eventual questionamento, **toda execução do `primetax-sped diagnose` salva um snapshot** dos blocos do manual que foram referenciados nas oportunidades identificadas.

O snapshot inclui:

- Hash do conteúdo de cada bloco renderizado.  
- Versão Git do repositório de manuais no momento da execução.  
- Contexto do cliente que motivou a filtragem.  
- Lista de oportunidades e blocos associados.

Salvo em `data/output/{cnpj}/{ano}/snapshot-manuais.json`. Quando uma análise antiga precisa ser reproduzida ou defendida, o snapshot permite recriar exatamente o manual que orientou aquela operação.

---

## 7\. Comandos CLI relacionados

Adicionados ao CLI do projeto (CLAUDE.md seção 9):

```
primetax-sped manuais list                              # Lista todos os blocos disponíveis
primetax-sped manuais list --regra=CR-07                # Filtra por regra
primetax-sped manuais list --tipo=procedimento          # Filtra por tipo
primetax-sped manuais list --vigencia-expirada          # Apenas blocos obsoletos

primetax-sped manuais view <bloco_id>                   # Renderiza um bloco específico
primetax-sped manuais view <bloco_id> --formato=pdf     # Saída em PDF

primetax-sped manuais validate                          # Valida toda a coleção
primetax-sped manuais validate --strict                 # Falha em avisos (revisão antiga etc.)

primetax-sped manuais render --regra=CR-07 --cliente=NORTE-GERADORES --competencia=03/2022 --output=relatorio.pdf
                                                         # Renderiza manual personalizado para caso concreto

primetax-sped manuais relatorio-cobertura               # Relatório: quais regras têm manual e quais não têm
```

O comando `validate` é o gêmeo do `regras validate` da seção 21 do CLAUDE.md. Ambos rodam em pre-commit/CI: alterações que quebram a coerência regra↔manual são bloqueadas no merge.

O comando `relatorio-cobertura` é o painel de saúde do projeto: quantas regras já têm manual completo, quantas têm parcial, quantas estão sem cobertura. Indicador-chave para a equipe de conteúdo Primetax.

---

## 8\. Implementação na Etapa 1 (Sprint 1 do projeto)

### 8.1 Escopo da Etapa 1

A Etapa 1 entrega:

1. **Schema do frontmatter** formalizado em `docs/contexto-fiscal/manuais-retificacao/meta/frontmatter-schema.yaml`.  
2. **Pré-processador básico** em `src/manuais/` — carregamento, validação, filtragem por regra, renderização Markdown e HTML simples. Sem personalização (Etapa 3\) e sem ações (Etapa 4).  
3. **Comandos CLI básicos** — `manuais list`, `manuais view`, `manuais validate`, `manuais relatorio-cobertura`.  
4. **Integração com o catálogo de regras** — o decorator `@regra` da seção 21 ganha campo opcional `manual_blocos: list[str]` apontando para `bloco_id`s relevantes. Validação cruzada entre os dois registries.  
5. **Conteúdo inicial** — manual completo do **Tema 69**, cobrindo CR-07. Sete blocos: fundamentação, modulação temporal (3 cenários como blocos separados), quantificação, retificação SPED, PER/DCOMP, armadilhas, casos especiais.

A escolha do Tema 69 como conteúdo inicial reflete duas decisões já estabelecidas no CLAUDE.md v6:

- CR-07 é o cruzamento-âncora do Sprint 1\.  
- A Norte Geradores (caso de validação do CLAUDE.md seção 15\) terá Tese 69 como achado principal — ter manual completo para esse tema valida a integração ponta a ponta.

### 8.2 Sequência de entrega dentro do Sprint 1

Inserido na sequência da subseção 21.8 do CLAUDE.md (que define a ordem de entrega do Sprint 1 para o catálogo de regras):

1. Modelo, enumerações e registro do catálogo de regras (já previsto na 21.8).  
2. **\[NOVO\] Schema do frontmatter de manuais e validador básico.**  
3. Comandos CLI básicos do catálogo (já previsto na 21.8).  
4. **\[NOVO\] Comandos CLI básicos de manuais.**  
5. Export inicial do catálogo (já previsto na 21.8).  
6. Sete primeiros decorators do catálogo (já previsto na 21.8).  
7. **\[NOVO\] Sete blocos do manual do Tema 69 \+ integração com decorator do CR-07.**  
8. Testes do catálogo (já previsto na 21.8).  
9. **\[NOVO\] Testes do pré-processador de manuais.**

A Etapa 1 do manual integrado adiciona aproximadamente 30-40% de esforço ao Sprint 1 (estimativa subjetiva — ajustar conforme planejamento detalhado). Vale a inclusão porque a infraestrutura básica é compartilhada com o catálogo, e separar para outro sprint custaria refazer integrações.

### 8.3 O que fica fora da Etapa 1

Explicitamente fora:

- Personalização com dados do cliente (Etapa 3).  
- **Execução automatizada** dos procedimentos via gerador de SPED retificador (Etapa 4\) — embora a camada `operacao_estruturada` possa ser preenchida na Etapa 1 para procedimentos diretos, **nenhum motor consome essa camada no Sprint 1**. Ela é coletada como ativo, não usada como código.  
- Renderização PDF estilizada com identidade visual Primetax — Etapa 1 entrega Markdown e HTML básico; PDF entra na Etapa 2\.  
- Manual unificado navegável em arquivo único — Etapa 2 produz isso.  
- Conteúdo de outros temas além do Tema 69 — entram conforme novos cruzamentos são implementados.

**Política sobre `operacao_estruturada` no Sprint 1\.** Para os sete blocos do Tema 69 entregues na Etapa 1, a camada estruturada será preenchida onde possível e deixada vazia onde o procedimento exige julgamento humano não-trivial. O propósito é começar a acumular o ativo desde já — quando a Etapa 4 chegar nos sprints 6-8, parte significativa do trabalho de especificar o gerador automático já estará feita.

---

## 9\. Decisões pendentes

Pontos onde o operador (Marcelo) precisa decidir antes da implementação:

**Decisão 1 — Formalização como seção 23 da v7?**

Esta especificação tem porte arquitetural comparável às seções 15, 16, 18 e 21 da v6. Coerente com o padrão estabelecido, ela mereceria virar seção 23 do CLAUDE.md (com changelog v6→v7). A alternativa é mantê-la como documento satélite em `docs/arquitetura/manuais-integrados.md` e formalizar no CLAUDE.md apenas referências cruzadas curtas.

Recomendação: formalizar como seção 23 da v7 antes do Sprint 1 começar. Manter consistência com a tradição estabelecida na v5/v6 e garantir que o Claude Code lê a especificação completa quando inicia a implementação.

**Decisão 2 — Quem produz o conteúdo inicial?**

A Etapa 1 entrega sete blocos do Tema 69 com conteúdo real, não placeholders. Quem os escreve?

Opção A: Marcelo escreve diretamente, Claude apenas estrutura e revisa. Opção B: Claude escreve com base na sua experiência do domínio fiscal brasileiro, Marcelo revisa criticamente. Opção C: Trabalho colaborativo iterativo — Claude entrega um rascunho, Marcelo refina, Claude refina sobre os refinamentos.

Recomendação: **Opção C** para o Tema 69\. A colaboração itera mais rápido e o Claude funciona como editor técnico, não substituto do consultor.

**Decisão 3 — Frequência de revisão e responsabilidade**

Blocos do manual têm `ultima_revisao`. Quem revisa, com que frequência, e qual o gatilho?

Sugestão: revisão obrigatória anual de cada bloco; revisão extraordinária quando (a) jurisprudência relevante muda, (b) RFB publica IN ou ato declaratório que afeta o tema, (c) o validador detecta blocos com revisão há mais de 18 meses. Responsável padrão: o consultor sênior que escreveu o bloco originalmente, ou Marcelo na ausência dele.

A formalização desse processo entra na seção 23 da v7 ou em documento separado de governança da Primetax — fora do escopo desta especificação técnica.

**Decisão 4 — Escopo dos `aplicavel_quando` no Sprint 1**

O catálogo de chaves padronizadas de `aplicavel_quando` (seção 4.3) é extensível. Quais chaves são suficientes para o Tema 69 no Sprint 1?

Mínimo necessário identificado:

- `cliente_regime_apuracao`  
- `cliente_tem_acao_judicial_pre_modulacao`  
- `competencia_anterior_a` / `competencia_posterior_a`  
- `prescricao_situacao`

Outras chaves entram conforme novos temas são adicionados. Não vale tentar prever tudo no Sprint 1\.

**Decisão 5 — Linguagem dos placeholders Jinja**

A Etapa 3 introduz personalização via templates. Vale escolher já a sintaxe para que blocos escritos na Etapa 1 já sigam convenção compatível.

Sugestão: Jinja2 puro com namespaces explícitos.

- `{{ cliente.razao_social }}` — dados do cliente.  
- `{{ competencia.base_cf }}` — dados da competência analisada.  
- `{{ regra.codigo }}` — dados da regra.  
- `{{ achado.valor_credito_apurado }}` — dados da oportunidade específica.

Os blocos da Etapa 1 podem usar essas variáveis em modo "noop" (renderizadas literalmente como `{{ ... }}`) e ganhar significado real quando a Etapa 3 chegar.

**Decisão 6 — Nível mínimo de preenchimento da `operacao_estruturada` no Sprint 1**

Adicionada na rev. 2\. A camada `operacao_estruturada` (seção 4.3) é opcional na Etapa 1 e obrigatória na Etapa 4\. A pergunta operacional é: qual o nível mínimo de preenchimento esperado para os sete blocos do Tema 69 que serão escritos no Sprint 1?

Três níveis possíveis:

**Nível mínimo (apenas onde é trivial)** — preencher `operacao_estruturada` somente em procedimentos algorítmicos diretos. Procedimentos com qualquer ambiguidade ficam vazios e serão completados na Etapa 4\.

**Nível recomendado (sempre que possível, mesmo com lacunas)** — tentar preencher `operacao_estruturada` em todos os procedimentos. Onde houver decisão dependente de julgamento humano, marcar com placeholder `decisao_humana_necessaria: true` e descrever a heurística em texto. Isso captura o conhecimento do consultor antes que ele esqueça os detalhes.

**Nível ambicioso (preenchimento completo na Etapa 1\)** — preencher `operacao_estruturada` integralmente, inclusive resolvendo previamente todas as ambiguidades de classificação. Mais lento de produzir, mas deixa a Etapa 4 essencialmente como "ligar o motor".

Recomendação: **Nível recomendado**. Captura o ativo da Etapa 1 sem virar gargalo, e marca explicitamente onde a Etapa 4 vai precisar de trabalho adicional. Para o caso específico do Tema 69, espera-se que a maioria dos procedimentos seja algorítmica direta (operações sobre campos com fórmulas claras), com talvez 1-2 dos 7 blocos exigindo `decisao_humana_necessaria` em pontos específicos.

---

## 10\. Riscos e mitigações

**Risco 1 — Manual desatualizado por descuido humano.**

Mitigação: validador automático no pre-commit gera aviso para blocos com `ultima_revisao` há mais de 18 meses. Validador no `--strict` falha o build. Painel de cobertura mensal mostra blocos pendentes.

**Risco 2 — Frontmatter mal preenchido por consultor não-técnico.**

Mitigação: schema YAML formal validado no carregamento. Mensagens de erro explicam o que está errado em português. Slash command `/decorar-bloco-manual` no Claude Code para ajudar consultores a preencher frontmatter sem decorar o schema.

**Risco 3 — Crescimento desorganizado da base de manuais.**

Mitigação: granularidade fixa por tema. Schema do frontmatter limita campos. Revisão mensal pelo consultor sênior responsável. Comando `relatorio-cobertura` mostra a saúde da coleção.

**Risco 4 — Filtragem `aplicavel_quando` esconde conteúdo importante por engano.**

Mitigação: o renderizador sempre indica "X blocos foram filtrados — clique para ver". Auditor pode forçar visualização completa quando suspeita que o filtro errou.

**Risco 5 — Snapshot de auditoria cresce indefinidamente.**

Mitigação: snapshot é JSON pequeno (alguns KB por análise). Para análises com 200+ oportunidades cresce mais, mas raramente passa de 5 MB. Política de retenção: snapshots mantidos enquanto o cliente for ativo \+ 5 anos após (alinhado ao prazo prescricional).

**Risco 6 — Quebra silenciosa entre regra e manual quando código é refatorado.**

Mitigação: validador cruzado regra↔manual no CI/CD. Renomear uma regra sem atualizar os blocos que a referenciam quebra o build.

**Risco 7 — Divergência entre prosa narrativa e `operacao_estruturada` ao longo do tempo.**

Adicionado na rev. 2\. Quando o consultor atualiza a prosa de um procedimento (por exemplo, em resposta a uma nova IN da RFB) sem atualizar a `operacao_estruturada` correspondente, o manual passa a ensinar uma coisa ao auditor humano e o gerador automático da Etapa 4 passa a executar outra. Risco silencioso e potencialmente caro.

Mitigação em três camadas: (a) o validador detecta blocos `procedimento` com `ultima_revisao` da prosa diferente da `ultima_revisao_estruturada`, gerando aviso para revisão pareada; (b) o slash command `/revisar-procedimento` força o consultor a revisar as duas camadas no mesmo ato; (c) políticas de governança (Decisão 3\) exigem que toda alteração de procedimento seja revisada por par antes de merge.

---

## 11\. Considerações finais

Esta especificação trata o manual de retificação como **componente arquitetural do sistema**, não como documentação satélite. A integração com o catálogo de regras (seção 21 do CLAUDE.md v6) é o que diferencia esta abordagem de uma simples coleção de PDFs.

A consequência é que escrever o manual deixa de ser tarefa de "documentar depois" e passa a ser tarefa de "implementar dentro do escopo". A Etapa 1 cabe no Sprint 1 sem comprometer entregas — e a partir dela, cada novo tema produzido por consultores Primetax automaticamente se integra ao sistema.

A rev. 2 reforça uma propriedade essencial da arquitetura: a Etapa 1 não é trabalho descartável que será substituído pela Etapa 4\. É **base permanente** sobre a qual a Etapa 4 é construída. O conteúdo procedimental escrito hoje, em duas camadas (prosa para humanos \+ `operacao_estruturada` para máquinas), serve simultaneamente o auditor de hoje e o gerador automático de amanhã. Cada bloco escrito é ativo definitivo do sistema, não rascunho.

Para a Primetax, o ganho não é apenas técnico. É **ativo de propriedade intelectual versionado, auditável e escalável**: a soma dos manuais ao longo do tempo se torna a metodologia Primetax materializada em código. Auditor pleno em onboarding aprende mais rápido. Auditor sênior produz mais. E o sistema fica mais defensável diante da Receita Federal porque cada operação carrega o lastro de manual versionado.

Quando a Etapa 4 chegar — gerador automático de SPED retificador e PER/DCOMP —, ela não será desenvolvimento do zero. Será **ativação do que a Etapa 1 já especificou**. Esse é o motivo pelo qual fazer a Etapa 1 corretamente hoje é o investimento que paga toda a progressão da arquitetura.

A decisão de seguir adiante com a especificação aqui formalizada exige confirmar cinco coisas: (a) aceitar a Arquitetura C com progressão em quatro etapas (Etapa 4 renomeada para "Manual executor"); (b) aceitar a inclusão da Etapa 1 dentro do Sprint 1; (c) decidir sobre formalização como seção 23 da v7 ou documento satélite; (d) decidir sobre como o conteúdo do Tema 69 será produzido (Opção A, B ou C da decisão 2); (e) escolher o nível mínimo de preenchimento da `operacao_estruturada` no Sprint 1 (decisão 6).

Confirmadas as cinco, a próxima entrega é o **conteúdo dos sete blocos do Tema 69** no formato definido por esta especificação, incluindo a camada `operacao_estruturada` preenchida no nível recomendado para procedimentos algorítmicos.

---

*Especificação mantida por Marcelo de Oliveira Magalhães Wanderley (Primetax Solutions). Revisão: abril/2026, rev. 2 (renomeação Etapa 4 → "Manual executor" e adição da camada `operacao_estruturada` ao schema).*  
