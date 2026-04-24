# EFD ICMS/IPI — Guia Prático de Importação e Referência

**Versão do leiaute coberta:** 3.2.2 (publicada em 11 de fevereiro de 2026\) **Base normativa:** Ato COTEPE/ICMS nº 44/2018 e alterações **Fonte original:** GT 48 SPED FISCAL — Guia Prático da Escrituração Fiscal Digital — EFD-ICMS/IPI **Instituição da obrigação:** Convênio ICMS 143/2006 e Ajuste SINIEF 02/2009 **Objetivo deste documento:** servir como referência técnica instrumental para o sistema Primetax SPED Cross-Reference. O foco é extrair da EFD ICMS/IPI os elementos necessários ao cruzamento com a EFD-Contribuições e à validação de teses envolvendo ICMS (notadamente a Tese 69 — exclusão do ICMS da base de PIS/COFINS), ativo permanente, inventário e produção. Este arquivo NÃO se propõe a ser enciclopédico sobre a apuração do ICMS/IPI em si; esse é escopo de outro projeto.

---

## Índice

1. Visão geral estrutural  
2. Perfis do declarante e obrigatoriedade  
3. Tabelas externas críticas  
4. Registro C100 — documentos fiscais de mercadorias  
5. Registro C170 — itens do documento  
6. Registros analíticos e de ajustes (C190, C197)  
7. Apuração do ICMS (Bloco E)  
8. Ativo Permanente e CIAP (Bloco G)  
9. Inventário (Bloco H)  
10. Controle da Produção e do Estoque (Bloco K)  
11. Mapeamento de cruzamentos EFD ICMS/IPI ↔ EFD-Contribuições  
12. Reforma Tributária sobre o Consumo — tratamento transitório  
13. Tabela de situação do documento (4.1.2)  
14. Referências normativas  
15. Recomendação operacional para o parser

---

## 1\. Visão geral estrutural

A EFD ICMS/IPI é o arquivo digital em que o contribuinte escrituração suas operações de ICMS e IPI. Diferentemente da EFD-Contribuições, que é federal e apura PIS/COFINS, a EFD ICMS/IPI tem natureza híbrida — é submetida via SPED à Receita Federal mas os destinatários primários são os fiscos estaduais (para o ICMS) e a RFB (para o IPI).

### 1.1 Blocos da EFD ICMS/IPI

A ordem de apresentação dos blocos no arquivo é obrigatória e sequencial.

| Bloco | Descrição | Observação |
| :---- | :---- | :---- |
| 0 | Abertura, Identificação e Referências | Obrigatório |
| B | Escrituração e Apuração do ISS | Incluído a partir de jan/2019, exclusivo para contribuintes do Distrito Federal |
| C | Documentos Fiscais I — Mercadorias (ICMS/IPI) | Obrigatório quando houver movimento |
| D | Documentos Fiscais II — Serviços (ICMS) | Transporte, comunicação, energia |
| E | Apuração do ICMS e do IPI | Obrigatório |
| G | Controle do Crédito de ICMS do Ativo Permanente — CIAP | Incluído a partir de jan/2011 |
| H | Inventário Físico | Obrigatório |
| K | Controle da Produção e do Estoque | Incluído a partir de jan/2017, conforme Ajuste SINIEF 02/2009 |
| 1 | Outras Informações | Obrigatório |
| 9 | Controle e Encerramento do Arquivo Digital | Obrigatório |

Todos os blocos são delimitados por um registro de abertura (`{BLOCO}001`) e um registro de encerramento (`{BLOCO}990`). A presença ou ausência de registros intermediários depende do perfil do declarante e da natureza de suas operações.

### 1.2 Regras gerais da estrutura

Cada registro é composto por campos delimitados pelo caractere pipe (`|`), que é o único separador permitido. Dentro da hierarquia, a ordem de apresentação dos registros é sequencial e ascendente. Todos os campos obrigatórios devem estar presentes, inclusive quando não houver informação (apresentados vazios). Registros "Pai" podem ter "Filhos" com ocorrência 1:1 ou 1:N.

Documentos fiscais que representam a mesma operação em modelos distintos são mutuamente excludentes — o contribuinte apresenta o registro correspondente ao modelo efetivamente emitido (C100 para NF-e modelo 55 e NFC-e modelo 65; C500 para energia elétrica modelo 06; D100 para conhecimento de transporte modelo 08/8B; D500 para serviço de comunicação modelo 21/22).

### 1.3 Divisores de águas no leiaute

A EFD ICMS/IPI teve evoluções significativas desde sua instituição. Para o sistema Primetax, os divisores mais relevantes são:

- **Janeiro de 2011** — criação do Bloco G (CIAP)  
- **Janeiro de 2015** — inclusão do campo `VL_ITEM_IR` no H010 para finalidades do IR  
- **Janeiro de 2017** — criação do Bloco K (controle de produção e estoque)  
- **Janeiro de 2019** — criação do Bloco B (ISS-DF)  
- **Janeiro de 2020** — regra de correspondência entre itens em C180/C185/C330/C380/C430/C480/C815/C870 e registros H010  
- **Janeiro de 2023** — descontinuação dos códigos 04 (denegado) e 05 (numeração inutilizada) da tabela 4.1.2  
- **Janeiro/Dezembro de 2026** — acomodação transitória da Reforma Tributária sobre o Consumo (CBS, IBS, IS)

---

## 2\. Perfis do declarante e obrigatoriedade

O campo `IND_PERFIL` do registro 0000 indica o grau de detalhamento exigido pelo fisco estadual. O perfil é determinado pela UF de acordo com critérios próprios (porte, setor, regime de apuração) e não é opção do contribuinte.

| Perfil | Nível de detalhe | Característica |
| :---- | :---- | :---- |
| A | Máximo | Documento fiscal item a item, registros C170 obrigatórios para NF-e |
| B | Sintético | Totalizações por período, privilegiando registros agregados |
| C | Mais sintético que B | Introduzido em 2015; agregação ainda maior |

O arquivo é **rejeitado** no PVA se o declarante informar perfil distinto do estabelecido pelo fisco estadual. A obrigatoriedade de cada registro é codificada da seguinte forma:

- **O** — registro sempre obrigatório  
- **O (condição)** — obrigatório quando a condição ocorre  
- **OC** — obrigatório se houver informação a prestar  
- **N** — registro não pode ser apresentado

Para o sistema Primetax, a regra prática é parsear tudo que estiver presente no arquivo, sem pressupor perfil: uma operação em perfil B pode não ter C170, forçando o cruzamento a buscar dados no C190. O parser deve ser tolerante à ausência de registros opcionais.

---

## 3\. Tabelas externas críticas

### 3.1 Tabela 4.3.1 — Situação Tributária do ICMS (CST-ICMS)

O CST-ICMS tem **três posições** (diferente do CST-PIS/COFINS, que tem duas):

**1ª posição — Origem da mercadoria:**

| Código | Descrição |
| :---- | :---- |
| 0 | Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8 |
| 1 | Estrangeira — Importação direta, exceto a indicada no código 6 |
| 2 | Estrangeira — Adquirida no mercado interno, exceto a indicada no código 7 |
| 3 | Nacional, conteúdo de importação superior a 40% e inferior ou igual a 70% |
| 4 | Nacional com processo produtivo básico (DL 288/67 e Leis 8.248/91, 8.387/91, 10.176/01, 11.484/07) |
| 5 | Nacional, conteúdo de importação inferior ou igual a 40% |
| 6 | Estrangeira — Importação direta, sem similar nacional, constante em lista CAMEX e gás natural |
| 7 | Estrangeira — Adquirida no mercado interno, sem similar nacional, constante em lista CAMEX e gás natural |
| 8 | Nacional, com conteúdo de importação superior a 70% |

**2ª e 3ª posições — Tributação:**

| Código | Descrição |
| :---- | :---- |
| 00 | Tributada integralmente |
| 10 | Tributada e com cobrança do ICMS por substituição tributária |
| 20 | Com redução de base de cálculo |
| 30 | Isenta ou não tributada e com cobrança do ICMS por substituição tributária |
| 40 | Isenta |
| 41 | Não tributada |
| 50 | Suspensão |
| 51 | Diferimento |
| 60 | ICMS cobrado anteriormente por substituição tributária |
| 70 | Com redução de base de cálculo e cobrança do ICMS por substituição tributária |
| 90 | Outras |

Exemplo: `CST_ICMS = 060` significa origem nacional (0) \+ ICMS cobrado anteriormente por ST (60). Para o sistema Primetax, este é um código crítico: operações com CST terminando em **40, 41 ou 50** costumam ser isentas/não tributadas/suspensas de ICMS, o que implica ausência de ICMS destacado — e portanto nenhuma exclusão a fazer na base de PIS/COFINS para a Tese 69 naquele item específico.

### 3.2 Tabela CSOSN — Código de Situação da Operação no Simples Nacional

Aplicável quando o declarante é optante pelo Simples Nacional (campo `IND_ATIV` \= 1 e observação fiscal cabível):

| Código | Descrição |
| :---- | :---- |
| 101 | Tributada pelo Simples Nacional com permissão de crédito |
| 102 | Tributada pelo Simples Nacional sem permissão de crédito |
| 103 | Isenção do ICMS no Simples Nacional para faixa de receita bruta |
| 201 | Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por ST |
| 202 | Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por ST |
| 203 | Isenção do ICMS no Simples Nacional com cobrança do ICMS por ST |
| 300 | Imune |
| 400 | Não tributada pelo Simples Nacional |
| 500 | ICMS cobrado anteriormente por ST (substituído) ou por antecipação |
| 900 | Outros |

### 3.3 Tabela 4.3.2 — Situação Tributária do IPI (CST-IPI)

Dois dígitos, aplicados no campo `CST_IPI` do C170:

| Código | Descrição |
| :---- | :---- |
| 00 | Entrada com recuperação de crédito |
| 01 | Entrada tributada com alíquota zero |
| 02 | Entrada isenta |
| 03 | Entrada não tributada |
| 04 | Entrada imune |
| 05 | Entrada com suspensão |
| 49 | Outras entradas |
| 50 | Saída tributada |
| 51 | Saída tributada com alíquota zero |
| 52 | Saída isenta |
| 53 | Saída não tributada |
| 54 | Saída imune |
| 55 | Saída com suspensão |
| 99 | Outras saídas |

### 3.4 Tabela 4.1.1 — Modelos de documento fiscal (principais)

| Código | Modelo | Registro destino |
| :---- | :---- | :---- |
| 01 | Nota Fiscal, modelo 1 ou 1A | C100 |
| 1B | Nota Fiscal Avulsa | C100 |
| 02 | Nota Fiscal de Venda a Consumidor | C300 ou C350 |
| 04 | Nota Fiscal de Produtor | C100 |
| 06 | Nota Fiscal/Conta de Energia Elétrica | C500 |
| 07 | Nota Fiscal de Serviço de Transporte | D100 |
| 08 / 8B | Conhecimento de Transporte Rodoviário de Cargas / Eletrônico | D100 |
| 21 | Nota Fiscal de Serviço de Comunicação | D500 |
| 22 | Nota Fiscal de Serviço de Telecomunicação | D500 |
| 55 | Nota Fiscal Eletrônica (NF-e) | C100 |
| 57 | Conhecimento de Transporte Eletrônico (CT-e) | D100 |
| 65 | Nota Fiscal de Consumidor Eletrônica (NFC-e) | C100 |
| 66 | Nota Fiscal de Energia Elétrica Eletrônica (NF3e) | C500 |

---

## 4\. Registro C100 — documentos fiscais de mercadorias

Este registro representa a nota fiscal em si (cabeçalho). É gerado para cada documento fiscal dos modelos 01, 1B, 04, 55 e 65\. Suas filhas detalham itens (C170), informações complementares (C110/C111/C112/C113/C114/C115/C116), impostos específicos (C120/C130/C140/C141), registros analíticos (C190) e ajustes (C197).

### 4.1 Regra de chave única

A partir de abril/2012, `CHV_NFE` é obrigatório em todas as situações exceto numeração inutilizada (`COD_SIT = 05`, descontinuado em jan/2023). A chave que torna o registro único varia conforme o emitente:

- **Emissão própria** (`IND_EMIT = 0`): `IND_OPER + IND_EMIT + COD_MOD + COD_SIT + SER + NUM_DOC + CHV_NFE`  
- **Terceiros** (`IND_EMIT = 1`): `IND_OPER + IND_EMIT + COD_PART + COD_MOD + COD_SIT + SER + NUM_DOC + CHV_NFE`

Para o sistema Primetax, isso significa que ao cruzar C100 da EFD ICMS com C100 da EFD-Contribuições, a chave natural é `CHV_NFE` — que é única por documento em todo o território nacional. Divergências entre os dois SPEDs no mesmo CHV\_NFE são sintomas quase sempre de erro de apuração em PIS/COFINS.

### 4.2 Layout do C100

| Nº | Campo | Descrição | Tipo | Tam | Dec | Obrig |
| ----: | :---- | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "C100" | C | 004 | \- | O |
| 02 | IND\_OPER | Indicador de operação: 0=Entrada, 1=Saída | C | 001 | \- | O |
| 03 | IND\_EMIT | Emitente: 0=Próprio, 1=Terceiros | C | 001 | \- | O |
| 04 | COD\_PART | Código do participante (campo 02 do 0150\) | C | 060 | \- | O |
| 05 | COD\_MOD | Modelo do documento (tabela 4.1.1) | C | 002 | \- | O |
| 06 | COD\_SIT | Situação do documento (tabela 4.1.2) | N | 002 | \- | O |
| 07 | SER | Série do documento | C | 003 | \- | OC |
| 08 | NUM\_DOC | Número do documento | N | 009 | \- | O |
| 09 | CHV\_NFE | Chave da NF-e (44 dígitos) | N | 044 | \- | OC |
| 10 | DT\_DOC | Data de emissão | N | 008 | \- | O |
| 11 | DT\_E\_S | Data de entrada/saída | N | 008 | \- | OC |
| 12 | VL\_DOC | Valor total do documento fiscal | N | \- | 02 | O |
| 13 | IND\_PGTO | Tipo de pagamento: 0=À vista, 1=A prazo, 2=Outros | C | 001 | \- | O |
| 14 | VL\_DESC | Valor total do desconto | N | \- | 02 | OC |
| 15 | VL\_ABAT\_NT | Abatimento não tributado e não comercial | N | \- | 02 | OC |
| 16 | VL\_MERC | Valor total das mercadorias e serviços | N | \- | 02 | O |
| 17 | IND\_FRT | Indicador do tipo do frete | C | 001 | \- | O |
| 18 | VL\_FRT | Valor do frete | N | \- | 02 | OC |
| 19 | VL\_SEG | Valor do seguro | N | \- | 02 | OC |
| 20 | VL\_OUT\_DA | Valor de outras despesas acessórias | N | \- | 02 | OC |
| 21 | VL\_BC\_ICMS | Base de cálculo do ICMS | N | \- | 02 | OC |
| 22 | VL\_ICMS | Valor do ICMS | N | \- | 02 | OC |
| 23 | VL\_BC\_ICMS\_ST | Base de cálculo do ICMS-ST | N | \- | 02 | OC |
| 24 | VL\_ICMS\_ST | Valor do ICMS-ST | N | \- | 02 | OC |
| 25 | VL\_IPI | Valor do IPI | N | \- | 02 | OC |
| 26 | VL\_PIS | Valor do PIS | N | \- | 02 | OC |
| 27 | VL\_COFINS | Valor do COFINS | N | \- | 02 | OC |
| 28 | VL\_PIS\_ST | Valor do PIS-ST | N | \- | 02 | OC |
| 29 | VL\_COFINS\_ST | Valor do COFINS-ST | N | \- | 02 | OC |

**Observação crítica:** os 29 campos do C100 da EFD ICMS/IPI são **idênticos** aos do C100 da EFD-Contribuições. Isso é consequência deliberada do leiaute unificado estabelecido pelo Ato COTEPE/ICMS nº 44/2018. Divergências entre os dois arquivos no mesmo `CHV_NFE` são fortes indicativos de erro de escrituração.

---

## 5\. Registro C170 — itens do documento

Este é o registro mais granular da EFD ICMS/IPI para documentos fiscais de mercadoria. Contém a tributação individual de cada item por incidência (ICMS, IPI, PIS, COFINS).

### 5.1 Peculiaridade do C170 na EFD ICMS/IPI

O C170 da EFD ICMS/IPI tem **38 campos**, enquanto o equivalente na EFD-Contribuições tem **37 campos**. A diferença é o **campo 38 `VL_ABAT_NT`** (valor do abatimento não tributado e não comercial), que existe apenas no SPED Fiscal e reflete situações como desconto incondicional do ICMS nas remessas para Zona Franca de Manaus.

Os campos 25 a 36, relacionados a PIS e COFINS, são idênticos nos dois SPEDs — o que permite cruzamento direto linha a linha.

### 5.2 Layout do C170

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "C170" | C | 004 | \- |
| 02 | NUM\_ITEM | Número sequencial do item | N | 003 | \- |
| 03 | COD\_ITEM | Código do item (campo 02 do 0200\) | C | 060 | \- |
| 04 | DESCR\_COMPL | Descrição complementar | C | \- | \- |
| 05 | QTD | Quantidade | N | \- | 05 |
| 06 | UNID | Unidade (campo 02 do 0190\) | C | 006 | \- |
| 07 | VL\_ITEM | Valor total do item | N | \- | 02 |
| 08 | VL\_DESC | Valor do desconto comercial | N | \- | 02 |
| 09 | IND\_MOV | Movimentação física: 0=Sim, 1=Não | C | 001 | \- |
| 10 | CST\_ICMS | CST-ICMS (tabela 4.3.1) | N | 003 | \- |
| 11 | CFOP | Código Fiscal de Operação e Prestação | N | 004 | \- |
| 12 | COD\_NAT | Código da natureza (campo 02 do 0400\) | C | 010 | \- |
| 13 | VL\_BC\_ICMS | Base de cálculo do ICMS | N | \- | 02 |
| 14 | ALIQ\_ICMS | Alíquota do ICMS | N | 006 | 02 |
| 15 | VL\_ICMS | Valor do ICMS creditado/debitado | N | \- | 02 |
| 16 | VL\_BC\_ICMS\_ST | Base de cálculo do ICMS-ST | N | \- | 02 |
| 17 | ALIQ\_ST | Alíquota do ICMS-ST na UF de destino | N | \- | 02 |
| 18 | VL\_ICMS\_ST | Valor do ICMS-ST | N | \- | 02 |
| 19 | IND\_APUR | Período de apuração IPI: 0=Mensal, 1=Decendial | C | 001 | \- |
| 20 | CST\_IPI | CST-IPI (tabela 4.3.2) | C | 002 | \- |
| 21 | COD\_ENQ | Código de enquadramento legal IPI | C | 003 | \- |
| 22 | VL\_BC\_IPI | Base de cálculo do IPI | N | \- | 02 |
| 23 | ALIQ\_IPI | Alíquota do IPI | N | 006 | 02 |
| 24 | VL\_IPI | Valor do IPI | N | \- | 02 |
| 25 | CST\_PIS | CST-PIS | N | 002 | \- |
| 26 | VL\_BC\_PIS | Base de cálculo do PIS | N | \- | 02 |
| 27 | ALIQ\_PIS | Alíquota do PIS (percentual) | N | 008 | 04 |
| 28 | QUANT\_BC\_PIS | Quantidade — base de cálculo PIS | N | \- | 03 |
| 29 | ALIQ\_PIS | Alíquota do PIS (em reais) | N | \- | 04 |
| 30 | VL\_PIS | Valor do PIS | N | \- | 02 |
| 31 | CST\_COFINS | CST-COFINS | N | 002 | \- |
| 32 | VL\_BC\_COFINS | Base de cálculo da COFINS | N | \- | 02 |
| 33 | ALIQ\_COFINS | Alíquota da COFINS (percentual) | N | 008 | 04 |
| 34 | QUANT\_BC\_COFINS | Quantidade — base de cálculo COFINS | N | \- | 03 |
| 35 | ALIQ\_COFINS | Alíquota da COFINS (em reais) | N | \- | 04 |
| 36 | VL\_COFINS | Valor da COFINS | N | \- | 02 |
| 37 | COD\_CTA | Código da conta contábil | C | \- | \- |
| 38 | **VL\_ABAT\_NT** | **Abatimento não tributado e não comercial** | N | \- | 02 |

### 5.3 Regra de enfoque do declarante

"IMPORTANTE: para documentos de entrada, os campos de valor de imposto, base de cálculo e alíquota só devem ser informados se o adquirente tiver direito à apropriação do crédito (enfoque do declarante)."

Esta regra é central para o sistema Primetax. Ela significa que se o contribuinte não preencheu `VL_ICMS` em uma entrada, está declarando que não se creditou daquele ICMS — o que pode ou não estar correto conforme a legislação aplicável ao CFOP e ao CST. Divergências entre o que deveria ser creditado e o que foi efetivamente escriturado são pontos de oportunidade (e de risco) que o motor de cruzamento precisa avaliar.

### 5.4 Integridade C170 ↔ C190

"A combinação dos valores dos campos CST\_ICMS, CFOP e ALIQ\_ICMS deve existir nos respectivos registros de itens do C170, quando este registro for exigido."

O somatório dos valores do C170 por combinação de `CST_ICMS + CFOP + ALIQ_ICMS` deve bater com os campos correspondentes no C190. Esta é uma das validações estruturais da Camada 1 do motor Primetax.

---

## 6\. Registros analíticos e de ajustes (C190, C197)

### 6.1 C190 — Registro analítico do documento

Agregação do documento fiscal por combinação de `CST_ICMS + CFOP + ALIQ_ICMS`. Obrigatório quando houver C100.

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "C190" | C | 004 | \- |
| 02 | CST\_ICMS | CST-ICMS | N | 003 | \- |
| 03 | CFOP | Código Fiscal de Operação e Prestação | N | 004 | \- |
| 04 | ALIQ\_ICMS | Alíquota do ICMS | N | 006 | 02 |
| 05 | VL\_OPR | Valor da operação na combinação | N | \- | 02 |
| 06 | VL\_BC\_ICMS | Parcela da base de cálculo do ICMS | N | \- | 02 |
| 07 | VL\_ICMS | Parcela do valor do ICMS | N | \- | 02 |
| 08 | VL\_BC\_ICMS\_ST | Parcela da base de cálculo do ICMS-ST | N | \- | 02 |
| 09 | VL\_ICMS\_ST | Parcela do valor do ICMS-ST | N | \- | 02 |
| 10 | VL\_RED\_BC | Valor não tributado por redução de base | N | \- | 02 |
| 11 | VL\_IPI | Parcela do valor do IPI | N | \- | 02 |
| 12 | COD\_OBS | Código da observação (campo 02 do 0460\) | C | 006 | \- |

**Regra de preenchimento do VL\_OPR** (crítica para Reforma Tributária):

"Informar neste campo o valor das mercadorias somadas aos valores de fretes, seguros e outras despesas acessórias e os valores de ICMS\_ST, FCP\_ST e IPI (somente quando o IPI está destacado na NF), subtraídos o desconto incondicional e o abatimento não tributado e não comercial. Não devem ser incluídos neste campo os valores relativos a CBS, IBS e IS incidentes na operação."

### 6.2 C197 — Outras obrigações tributárias e ajustes

Registra ajustes de débito e crédito aplicados ao documento fiscal. Os códigos usados no campo `COD_AJ` seguem tabela da UF e têm estrutura semântica no 3º e 4º caracteres que determinam o tipo de ajuste (débito, crédito, estorno, dedução, especial). O E111 consolida esses ajustes na apuração do período.

Combinações de `COD_AJ` relevantes (3º \+ 4º caractere):

- `30` a `50` \+ `0, 3-8` — ajustes a débito  
- `00` a `20` \+ `0, 3-8` — ajustes a crédito  
- `00` \+ `2` — estorno de crédito  
- `00` \+ `3` — estorno de débito  
- `60` \+ `0` — dedução do imposto  
- `70` \+ `0` — débito especial (extemporâneo)

Para o sistema Primetax, o C197 é relevante porque benefícios fiscais de ICMS concedidos via ajuste (por exemplo, crédito presumido vinculado à operação) frequentemente têm reflexo na apuração de PIS/COFINS quando constituem subvenção para investimento.

---

## 7\. Apuração do ICMS (Bloco E)

### 7.1 E100 — Período de apuração do ICMS

Abre o período de apuração. Campos: `DT_INI` e `DT_FIN` delimitando o mês-calendário. É o registro "Pai" de E110, E111, E112, E113, E115 e E116.

### 7.2 E110 — Apuração do ICMS, operações próprias

Registro obrigatório, ainda que o período não tenha movimento (neste caso os valores são zerados). Representa a totalização da apuração do ICMS de operações próprias (não-ST).

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "E110" | C | 004 | \- |
| 02 | VL\_TOT\_DEBITOS | Débitos por saídas e prestações com débito | N | \- | 02 |
| 03 | VL\_AJ\_DEBITOS | Ajustes a débito decorrentes do documento fiscal | N | \- | 02 |
| 04 | VL\_TOT\_AJ\_DEBITOS | Total de ajustes a débito (E111) | N | \- | 02 |
| 05 | VL\_ESTORNOS\_CRED | Total de estornos de crédito | N | \- | 02 |
| 06 | VL\_TOT\_CREDITOS | Créditos por entradas com crédito | N | \- | 02 |
| 07 | VL\_AJ\_CREDITOS | Ajustes a crédito decorrentes do documento fiscal | N | \- | 02 |
| 08 | VL\_TOT\_AJ\_CREDITOS | Total de ajustes a crédito (E111) | N | \- | 02 |
| 09 | VL\_ESTORNOS\_DEB | Total de estornos de débito | N | \- | 02 |
| 10 | VL\_SLD\_CREDOR\_ANT | Saldo credor do período anterior | N | \- | 02 |
| 11 | VL\_SLD\_APURADO | Saldo devedor apurado | N | \- | 02 |
| 12 | VL\_TOT\_DED | Deduções | N | \- | 02 |
| 13 | VL\_ICMS\_RECOLHER | ICMS a recolher (campo 11 − campo 12\) | N | \- | 02 |
| 14 | VL\_SLD\_CREDOR\_TRANSPORTAR | Saldo credor a transportar | N | \- | 02 |
| 15 | DEB\_ESP | Valores recolhidos ou a recolher, extra-apuração | N | \- | 02 |

### 7.3 Fórmula do saldo apurado (campo 11\)

`VL_SLD_APURADO = (VL_TOT_DEBITOS + VL_AJ_DEBITOS + VL_TOT_AJ_DEBITOS + VL_ESTORNOS_CRED) − (VL_TOT_CREDITOS + VL_AJ_CREDITOS + VL_TOT_AJ_CREDITOS + VL_ESTORNOS_DEB + VL_SLD_CREDOR_ANT)`

Se o resultado for ≥ 0, é lançado em `VL_SLD_APURADO` e o `VL_SLD_CREDOR_TRANSPORTAR` recebe zero. Se for negativo, o valor absoluto vai para `VL_SLD_CREDOR_TRANSPORTAR` (acrescido das deduções) e `VL_SLD_APURADO` recebe zero.

### 7.4 E111, E112, E113, E115, E116

- **E111** — Detalhamento dos ajustes totalizados em E110 campos 04, 05, 08 e 09\. Cada ajuste tem um `COD_AJ_APUR` com semântica posicional.  
- **E112** — Informações adicionais dos ajustes (processo administrativo, judicial).  
- **E113** — Documentos fiscais referenciados pelos ajustes.  
- **E115** — Informações adicionais específicas da apuração (saídas isentas, não-tributadas, etc.) conforme exigência da UF.  
- **E116** — Obrigações do ICMS recolhido ou a recolher. Validação cruzada: `VL_ICMS_RECOLHER + DEB_ESP` deve ser igual à soma do `VL_OR` dos E116.

---

## 8\. Ativo Permanente e CIAP (Bloco G)

O CIAP (Controle de Créditos do ICMS do Ativo Permanente) materializa o direito ao crédito de ICMS sobre aquisições de bens do ativo imobilizado, apropriado em **48 parcelas** (1/48 ao mês). Este bloco é fundamental para o sistema Primetax porque cruza diretamente com os registros F120/F130 da EFD-Contribuições, que tratam dos créditos de PIS/COFINS sobre os mesmos bens.

### 8.1 G110 — Apuração do CIAP no período

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "G110" | C | 004 | \- |
| 02 | DT\_INI | Data inicial de apuração | N | 008 | \- |
| 03 | DT\_FIN | Data final de apuração | N | 008 | \- |
| 04 | SALDO\_IN\_ICMS | Saldo inicial de ICMS do CIAP | N | \- | 02 |
| 05 | SOM\_PARC | Somatório das parcelas de ICMS do período | N | \- | 02 |
| 06 | VL\_TRIB\_EXP | Saídas tributadas \+ saídas de exportação | N | \- | 02 |
| 07 | VL\_TOTAL | Valor total de saídas | N | \- | 02 |
| 08 | IND\_PER\_SAI | Índice de participação (campo 06 / campo 07\) | N | \- | 08 |
| 09 | ICMS\_APROP | ICMS apropriado no período (campo 05 × campo 08\) | N | \- | 02 |
| 10 | SOM\_ICMS\_OC | Outros créditos de CIAP | N | \- | 02 |

### 8.2 Raciocínio central do CIAP

O crédito de ICMS do imobilizado é proporcional à atividade tributada do contribuinte. O índice `IND_PER_SAI` (saídas tributadas \+ exportação / total de saídas) reduz o crédito mensal quando há saídas isentas ou não tributadas. Isso **não tem paralelo** na EFD-Contribuições — os créditos de PIS/COFINS sobre imobilizado (F120/F130) não sofrem essa proporcionalização, são integrais na modalidade escolhida (1, 12, 24, 48 ou 4 meses conforme Natureza da Base de Cálculo).

Consequência prática para o sistema Primetax: divergências sistemáticas entre G125 (detalhamento por bem) e F120/F130 podem indicar bens cadastrados para ICMS mas não aproveitados para PIS/COFINS, ou vice-versa — ambos os cenários são oportunidade de revisão.

### 8.3 G125 — Movimentação de bem ou componente do ativo imobilizado

Detalha o ativo bem a bem. Tipos de movimentação relevantes:

- **SI** — Saldo inicial de bens imobilizados (bens escriturados em períodos anteriores com parcelas pendentes)  
- **IM** — Imobilização de bem individual (entrada)  
- **IA** — Imobilização em andamento (crédito só a partir da conclusão do bem principal)  
- **CI** — Conclusão de imobilização em andamento  
- **MC** — Alienação/perecimento/desincorporação  
- **BA** — Baixa de bem com parcelas de crédito ainda não apropriadas  
- **AT** — Outras alterações

Campos principais: `COD_IND_BEM` (liga ao 0300), `IDENT_BEM`, `DT_MOV`, `TIPO_MOV`, `VL_IMOB_ICMS_OP` (parcela do ICMS proporcional a operações próprias), `VL_IMOB_ICMS_ST`, `VL_IMOB_ICMS_FRT`, `VL_IMOB_ICMS_DIF`, `NUM_PARC` (número da parcela atual, de 1 a 48), `VL_PARC_PASS` (valor da parcela passível de apropriação).

### 8.4 G126 — Outros créditos CIAP

Registra créditos fora do fluxo padrão de 48 parcelas (ações judiciais transitadas, decisões administrativas, retificações).

### 8.5 G130, G140 — Identificação do documento fiscal do bem

Fecha o rastreio do bem até a nota fiscal de aquisição, permitindo integridade com o C100/C170 correspondente.

---

## 9\. Inventário (Bloco H)

### 9.1 H005 — Totais do inventário

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "H005" | C | 004 | \- |
| 02 | DT\_INV | Data do inventário | N | 008 | \- |
| 03 | VL\_INV | Valor total do estoque inventariado | N | \- | 02 |
| 04 | MOT\_INV | Motivo do inventário (1=Final do período; 2=Mudança de regime; 3=Desastres; 4=Solicitação fiscal; 5=Encerramento; 6=Controle ST) | C | 002 | \- |

### 9.2 H010 — Inventário item a item

Discrimina os itens em estoque na data do inventário. A partir de jan/2020, itens declarados em C180, C185, C330, C380, C430, C480, C815 e C870 devem ter pelo menos um H010 correspondente quando `MOT_INV = 06`.

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "H010" | C | 004 | \- |
| 02 | COD\_ITEM | Código do item (campo 02 do 0200\) | C | 060 | \- |
| 03 | UNID | Unidade (campo UNID\_INV do 0200\) | C | 006 | \- |
| 04 | QTD | Quantidade | N | \- | 03 |
| 05 | VL\_UNIT | Valor unitário | N | \- | 06 |
| 06 | VL\_ITEM | Valor total do item | N | \- | 02 |
| 07 | IND\_PROP | Propriedade: 0=Informante; 1=Informante em posse de terceiros; 2=Terceiros em posse do informante | C | 001 | \- |
| 08 | COD\_PART | Código do participante (se IND\_PROP ≠ 0\) | C | 060 | \- |
| 09 | TXT\_COMPL | Descrição complementar | C | \- | \- |
| 10 | COD\_CTA | Código da conta contábil | C | \- | \- |
| 11 | **VL\_ITEM\_IR** | **Valor do item para efeitos do Imposto de Renda** | N | \- | 02 |

### 9.3 O campo VL\_ITEM\_IR e a Tese do ICMS no estoque

O manual oficial estabelece uma regra técnica extremamente relevante para o sistema Primetax:

"Informar o valor do item utilizando os critérios previstos na legislação do Imposto de Renda, especificamente artigos 304 a 309 do RIR/2018 — Decreto nº 9.580/2018, por vezes discrepantes dos critérios previstos na legislação do IPI/ICMS, conduzindo-se ao valor contábil dos estoques. (...) Um exemplo de diferença entre as legislações é o valor do ICMS recuperável mediante crédito na escrita fiscal do adquirente, que não integra o custo de aquisição para efeito do Imposto de Renda. O montante desse imposto, destacado em nota fiscal, deve ser excluído do valor dos estoques para efeito do imposto de renda. Tratamento idêntico deve ser aplicado ao PIS-Pasep e à Cofins não cumulativos, instituídos pelas Leis nºs 10.637/2002 e 10.833/2003, respectivamente."

Esta passagem tem valor estratégico direto: o próprio manual da RFB reconhece que o ICMS recuperável deve ser excluído do valor dos estoques para fins de apuração de PIS/COFINS não-cumulativos. Cruzamentos envolvendo valorização de estoques (H010 versus F150) encontram lastro técnico explícito nesta orientação.

### 9.4 H020 e H030

- **H020** — Informação complementar para `MOT_INV` de 02 a 05\.  
- **H030** — Informações complementares específicas do inventário (incluído em 2021 para controle de substituição tributária).

---

## 10\. Controle da Produção e do Estoque (Bloco K)

Obrigatório a partir de jan/2017, com cronograma escalonado por porte e atividade. Detalha a movimentação diária/mensal de estoques e processos produtivos. Para o sistema Primetax, os registros críticos são K100 (período), K200 (estoque escriturado) e K235 (insumos consumidos).

### 10.1 K100 — Período de apuração

Delimita o mês-calendário ou decendial do Bloco K.

### 10.2 K200 — Estoque escriturado

Análogo ao H010 mas de periodicidade mensal:

| Nº | Campo | Descrição | Tipo | Tam | Dec |
| ----: | :---- | :---- | :---- | :---- | :---- |
| 01 | REG | Texto fixo "K200" | C | 004 | \- |
| 02 | DT\_EST | Data do estoque | N | 008 | \- |
| 03 | COD\_ITEM | Código do item (campo 02 do 0200\) | C | 060 | \- |
| 04 | QTD | Quantidade | N | \- | 03 |
| 05 | IND\_EST | Indicador de posse: 0=Informante; 1=Informante em terceiros; 2=Terceiros em informante | C | 001 | \- |
| 06 | COD\_PART | Código do participante (se IND\_EST ≠ 0\) | C | 060 | \- |

### 10.3 K235 — Insumos consumidos

Registra o consumo de insumos no processo produtivo. Relevante para cruzamento com créditos de PIS/COFINS sobre insumos (M100/M105/F100) em regimes onde o conceito de insumo é delimitado pela essencialidade/relevância à atividade-fim (tese do STJ REsp 1.221.170).

---

## 11\. Mapeamento de cruzamentos EFD ICMS/IPI ↔ EFD-Contribuições

Esta seção é o propósito operacional do presente arquivo no contexto Primetax. Abaixo, os pontos de ancoragem entre os dois SPEDs que alimentam o motor de 34 cruzamentos descrito no CLAUDE.md.

### 11.1 Chave de cruzamento de documento: CHV\_NFE

Todos os cruzamentos de documento fiscal (NF-e modelo 55\) entre EFD ICMS/IPI e EFD-Contribuições usam `CHV_NFE` como chave primária. Para modelos não eletrônicos (01, 04, 1B), usa-se a composição `COD_PART + COD_MOD + SER + NUM_DOC + DT_DOC`.

### 11.2 Cruzamento 7 — Tese do ICMS (RE 574.706)

- **Âncora na EFD ICMS/IPI:** C170 campo 15 (`VL_ICMS`) ou C190 campo 07 (`VL_ICMS`)  
- **Comparação na EFD-Contribuições:** C170 campos 26 e 32 (`VL_BC_PIS` e `VL_BC_COFINS`)  
- **Regra:** a base de cálculo do PIS/COFINS deve refletir a exclusão do ICMS da operação, conforme modulação do STF em maio/2021 (efeitos desde 15/03/2017 para contribuintes sem ação própria; desde a data do ajuizamento para quem ajuizou antes)  
- **Evidência Primetax:** quando `VL_BC_PIS = VL_ITEM` e há `VL_ICMS > 0` no mesmo item, há indício forte de que o ICMS não foi excluído e pode ser recuperado

### 11.3 Cruzamento 9 — Integridade de valor total

- **Âncora na EFD ICMS/IPI:** C100 campo 12 (`VL_DOC`)  
- **Comparação na EFD-Contribuições:** C100 campo 12 (`VL_DOC`)  
- **Regra:** para o mesmo `CHV_NFE`, `VL_DOC` deve ser idêntico nos dois arquivos  
- **Exceção crítica:** durante o período transitório da Reforma Tributária (exercício 2026), o `VL_DOC` do C100 da EFD ICMS/IPI pode incluir CBS/IBS/IS, enquanto o `VL_DOC` da EFD-Contribuições segue regra específica — o sistema Primetax deve tratar esta exceção com versionamento por competência

### 11.4 Cruzamento 26 — Insumo reconhecido para ICMS vs. PIS/COFINS

- **Âncora na EFD ICMS/IPI:** C170 item de entrada com `CFOP` de aquisição de insumo (ex. 1101, 1102, 2101, 2102\) e `CST_ICMS` com direito a crédito  
- **Comparação na EFD-Contribuições:** C170 correspondente com `CST_PIS` de crédito (50, 51, 52, 53, 54, 55, 56, 60, 61, 62, 63, 64, 65, 66\)  
- **Regra:** o conceito de insumo para PIS/COFINS (REsp 1.221.170/STJ) é mais amplo que o conceito de crédito integral para ICMS — portanto, divergências onde há crédito de ICMS mas não de PIS/COFINS merecem revisão  
- **Evidência Primetax:** insumo creditado na EFD ICMS/IPI e não creditado na EFD-Contribuições é um candidato natural a crédito extemporâneo

### 11.5 Cruzamento 28 — Ativo imobilizado

- **Âncora na EFD ICMS/IPI:** G125 por bem (campo `COD_IND_BEM` liga ao 0300\)  
- **Comparação na EFD-Contribuições:** F120 (bens) e F130 (encargos de depreciação/amortização)  
- **Regra:** bens reconhecidos no CIAP devem ter tratamento espelhado em F120 ou F130, com modalidade de crédito adequada (1, 12, 24 ou 48 meses)  
- **Evidência Primetax:** bens presentes em G125 sem contrapartida em F120/F130 são candidatos a revisão retroativa, respeitado o prazo decadencial de 5 anos

### 11.6 Cruzamentos adicionais sugeridos (futura incorporação ao motor Primetax)

Os seguintes cruzamentos não constam dos 34 originais mas emergem da leitura cruzada dos dois manuais e são registrados aqui para avaliação futura:

1. **G110 vs. F120/F130 — Coerência de base de bens** — verificar se os bens listados no detalhamento do CIAP (G125) têm contrapartida proporcional em F120 (novos) ou F130 (já em operação)  
2. **K200 vs. F150 — Estoque no regime de caixa** — empresas em regime de caixa (F500 na EFD-Contribuições) precisam conciliar suas posições de estoque periódicas com o inventário  
3. **CFOP de exportação em C170 vs. CST vinculado 05 em M100** — exportações reconhecidas no SPED Fiscal devem refletir-se em créditos vinculados a exportação no SPED Contribuições  
4. **C197 com benefício fiscal de ICMS vs. exclusão de subvenção em M210/M610** — benefícios fiscais concedidos via ajuste na EFD ICMS/IPI têm potencial reflexo na apuração de PIS/COFINS como subvenção

---

## 12\. Reforma Tributária sobre o Consumo — tratamento transitório

A Reforma Tributária (EC 132/2023, LC 214/2025) introduz CBS, IBS e IS, mas a EFD ICMS/IPI **não se presta à apuração desses novos tributos**. A orientação oficial do GT 48 SPED, na Seção 10 do Capítulo I do Guia 3.2.2, é de caráter transitório:

- Os novos tributos **devem** ser considerados no valor total do documento fiscal — campo 12 (`VL_DOC`) do C100 — exceto para o exercício 2026  
- Os novos tributos **não devem** ser incluídos no valor da operação dos registros analíticos, por exemplo campo 05 (`VL_OPR`) do C190  
- A regra se aplica a todos os modelos de documentos fiscais escriturados na EFD ICMS/IPI  
- Documentos fiscais que carreguem **exclusivamente** informações sobre CBS, IBS ou IS (sem ICMS ou IPI) **não devem** ser escriturados na EFD ICMS/IPI  
- Documentos fiscais emitidos nas operações do Ajuste SINIEF 49/25 que envolvam **tanto** os novos tributos **quanto** ICMS ou IPI devem ser regularmente escriturados na EFD ICMS/IPI em relação a estes tributos

**Consequência para o parser do sistema Primetax:** o módulo `src/rules/versionamento.py` precisa reconhecer a competência do arquivo e aplicar a regra transitória quando `DT_FIN` do 0000 estiver no exercício 2026 (ou posteriores, conforme regulamentação futura). A validação de integridade entre `VL_DOC` e `VL_MERC + VL_FRT + VL_SEG + VL_OUT_DA + VL_IPI − VL_DESC − VL_ABAT_NT` não será exata nesse período.

---

## 13\. Tabela de situação do documento (4.1.2)

Preenchida no campo `COD_SIT` do C100:

| Código | Descrição | Observação |
| :---- | :---- | :---- |
| 00 | Documento regular | — |
| 01 | Documento regular extemporâneo | Exclui do E110 campo 02 e campo 06; soma ao DEB\_ESP |
| 02 | Documento cancelado | — |
| 03 | Documento cancelado extemporâneo | — |
| 04 | NF-e ou CT-e denegado | **Descontinuado em jan/2023** |
| 05 | NF-e ou CT-e numeração inutilizada | **Descontinuado em jan/2023** |
| 06 | Documento fiscal complementar | — |
| 07 | Documento fiscal complementar extemporâneo | Exclui do E110 campo 02 e campo 06; soma ao DEB\_ESP |
| 08 | Documento fiscal emitido com base em regime especial ou norma específica | Ex.: Ajuste SINIEF 13/24 |

---

## 14\. Referências normativas

### 14.1 Leiaute

- **Ato COTEPE/ICMS nº 44/2018** — leiaute vigente e suas atualizações (principal fonte normativa)  
- **Ajuste SINIEF nº 02/2009** — institui a EFD ICMS/IPI  
- **Convênio ICMS 143/2006** — autoriza o uso de escrituração digital  
- **Ajuste SINIEF nº 11/2012** — regras de retificação  
- **Ajuste SINIEF nº 27/2020** — dispensa de autorização para retificação (a critério da UF)

### 14.2 Blocos específicos

- **Ajuste SINIEF nº 17/2014** — Bloco K  
- **Ajuste SINIEF nº 13/2019** — Bloco B (DF)  
- **Ajuste SINIEF nº 13/2024** — notas fiscais de retorno simbólico  
- **Ajuste SINIEF nº 34/2021 e 38/2021** — descontinuação de denegado/inutilizado a partir de dez/2021

### 14.3 Reforma Tributária

- **EC nº 132/2023** — institui CBS, IBS e IS  
- **LC nº 214/2025** — regulamentação  
- **Ajuste SINIEF nº 49/2025** — operações envolvendo simultaneamente novos tributos e ICMS/IPI

### 14.4 Fisco

- Site oficial SPED: [http://sped.rfb.gov.br](http://sped.rfb.gov.br)  
- **Nota Orientativa 01/2023** — ICMS monofásico, setor de combustíveis

---

## 15\. Recomendação operacional para o parser

### 15.1 Escopo mínimo recomendado para a primeira iteração

Para atender aos 34 cruzamentos do motor Primetax, o parser da EFD ICMS/IPI não precisa suportar todos os 269 tipos de registro do leiaute. Os registros essenciais são:

**Bloco 0** (6 registros): 0000, 0001, 0150, 0190, 0200, 0300

**Bloco C** (7 registros): C001, C100, C170, C190, C195, C197, C990

**Bloco E** (6 registros): E001, E100, E110, E111, E116, E990

**Bloco G** (6 registros): G001, G110, G125, G126, G130, G990

**Bloco H** (4 registros): H001, H005, H010, H990

**Bloco K** (4 registros, opcional no Sprint 1): K001, K100, K200, K990

**Bloco 9** (2 registros): 9001, 9999

**Total: 35 tipos de registro** (31 se omitir Bloco K). O restante pode ser deixado fora do parser inicial e incluído conforme demanda de cruzamentos específicos.

### 15.2 Resiliência a versões

Embora a versão atual do leiaute seja a 3.2.2, arquivos de períodos anteriores a 2020 podem usar versões 2.x. O parser deve:

- Ler o campo `COD_VER` do 0000 e registrá-lo em cada linha importada  
- Ter tabela de compatibilidade que mapeie campos renomeados entre versões  
- Nunca rejeitar silenciosamente campos desconhecidos — registrar aviso e continuar

### 15.3 Separação física dos schemas

Recomenda-se manter os schemas de banco da EFD ICMS/IPI (`efd_icms_*`) fisicamente separados dos da EFD-Contribuições (`efd_contribuicoes_*`), com os cruzamentos sendo feitos via joins controlados no motor. Isso permite:

- Importação independente de cada arquivo  
- Rastreabilidade fiscal preservada (coluna `arquivo_origem` no nível da tabela)  
- Testabilidade de cada parser isoladamente  
- Facilidade para evoluir cada schema conforme mudanças de leiaute dos respectivos manuais

### 15.4 Campos obrigatórios de rastreabilidade

Conforme seção 4 do `CLAUDE.md` (princípios não-negociáveis), toda linha importada de qualquer registro da EFD ICMS/IPI deve trazer obrigatoriamente:

- `arquivo_origem` — caminho ou hash do arquivo SPED de origem  
- `linha_arquivo` — número da linha física no arquivo original  
- `bloco` — identificação do bloco (0, B, C, D, E, G, H, K, 1, 9\)  
- `registro` — identificação do tipo de registro (0000, C100, etc.)  
- `cnpj_declarante` — CNPJ do campo 07 do registro 0000  
- `dt_ini_periodo`, `dt_fin_periodo` — datas do registro 0000  
- `ind_perfil` — perfil declarado (A, B ou C)  
- `cod_ver` — versão do leiaute declarada

Nenhuma linha de cruzamento deve ser gerada sem que todas essas informações possam ser recuperadas do banco — a rastreabilidade fiscal é o diferencial técnico do sistema Primetax e sua ausência invalida o valor auditorial do output.  
