# Layout da EFD-Contribuições — Parte 2 de 3

> **Documento-fonte:** Guia Prático da EFD-Contribuições, versão 1.35, atualizado em 18/06/2021, publicado pela Receita Federal do Brasil.
>
> **Parte 2 cobre:**
> - Bloco D (Documentos Fiscais II — Serviços de Transporte e Comunicação): D100, D101, D105, D200, D201, D205, D300, D350, D500, D501, D505, D600, D601, D605
> - Bloco F (Demais Documentos e Operações): F100, F120, F130, F150, F200, F205, F210, F500, F510, F525, F550, F600, F700, F800
> - Visão geral do Bloco I (Instituições Financeiras e equiparadas)
>
> **Partes complementares:** Parte 1 (visão geral, tabelas externas, Seção 12 ICMS, Blocos 0 e C); Parte 3 (Bloco M — apuração completa; Bloco 1 — operações extemporâneas; Bloco P; Bloco 9).
>
> **Nota importante:** o Bloco F concentra alguns dos registros de **maior valor estratégico** para a Primetax — especialmente F120 e F130 (créditos sobre ativo imobilizado) e F100 (demais operações com crédito). É frequente encontrar nesses registros créditos não aproveitados ou aproveitados parcialmente.

---

## 1. Bloco D — Documentos Fiscais II – Serviços de Transporte e Comunicação

### 1.1 Visão geral do Bloco D

O Bloco D trata dos serviços que, por sua natureza, têm documentação fiscal própria, distinta da nota fiscal convencional do Bloco C: **transporte de cargas**, **transporte de passageiros**, e **comunicação/telecomunicações**. A lógica de escrituração segue o mesmo padrão do Bloco C: um registro "pai" de documento ou consolidação, seguido de registros "filhos" segregando base de cálculo, CST e alíquota para PIS e COFINS separadamente.

**Importância para a Primetax:** o Bloco D concentra o creditamento sobre **fretes** — uma das teses mais frutíferas em revisão tributária. A legislação permite crédito sobre:

1. Fretes nas operações de **revenda de mercadorias**, quando o ônus for do adquirente titular da escrituração
2. Fretes nas operações de **venda de produtos fabricados**, quando o ônus for da PJ titular da escrituração
3. **Crédito presumido** para empresas de transporte rodoviário de carga na **subcontratação** de PF transportadora autônoma ou PJ optante pelo Simples (alíquotas especiais: PIS 1,2375% e COFINS 5,7%)

Operações que **não** dão direito a crédito:
- Transportes entre estabelecimentos da mesma PJ (transferências)
- Transporte de bens em devolução do estabelecimento comprador para o vendedor

### 1.2 Tabela do Bloco D

| Registro | Descrição | Nível | Contrib. | Crédito |
|:---:|---|:---:|:---:|:---:|
| `D001` | Abertura do Bloco D | 1 | – | – |
| `D010` | Identificação do Estabelecimento | 2 | – | – |
| `D100` | Aquisição de Serviços de Transporte – NF/CT-e (cód. 07, 08, 8B, 09, 10, 11, 26, 27, 57, 63, 67) | 3 | N | **S** |
| `D101` | Complemento do Documento de Transporte – PIS/Pasep | 4 | N | S |
| `D105` | Complemento do Documento de Transporte – COFINS | 4 | N | S |
| `D111` | Processo Referenciado (D100) | 4 | N | S |
| `D200` | Resumo da Escrituração Diária – Prestação de Serviços de Transporte | 3 | S | N |
| `D201` | Totalização do Resumo Diário – PIS/Pasep | 4 | S | N |
| `D205` | Totalização do Resumo Diário – COFINS | 4 | S | N |
| `D209` | Processo Referenciado (D200) | 4 | S | N |
| `D300` | Resumo Diário – Bilhetes Consolidados de Passagem (cód. 2E, 13, 14, 15, 16) | 3 | S | N |
| `D309` | Processo Referenciado (D300) | 4 | S | N |
| `D350` | Resumo Diário de Cupom Fiscal Emitido por ECF – Bilhete de Passagem | 3 | S | N |
| `D359` | Processo Referenciado (D350) | 4 | S | N |
| `D500` | NF de Serviço de Comunicação (cód. 21) e NF de Serviço de Telecomunicação (cód. 22) – Aquisições com Crédito | 3 | N | S |
| `D501` | Complemento da Operação – PIS/Pasep | 4 | N | S |
| `D505` | Complemento da Operação – COFINS | 4 | N | S |
| `D509` | Processo Referenciado (D500) | 4 | N | S |
| `D600` | Consolidação da Prestação de Serviços – NF Serviço de Comunicação/Telecom (cód. 21, 22) | 3 | S | N |
| `D601` | Complemento da Consolidação – PIS/Pasep | 4 | S | N |
| `D605` | Complemento da Consolidação – COFINS | 4 | S | N |
| `D609` | Processo Referenciado (D600) | 4 | S | N |
| `D990` | Encerramento do Bloco D | 1 | – | – |

### 1.3 Registro `D100` — Aquisição de Serviços de Transporte

Nível 3, ocorrência 1:N. Obrigatório para PJ adquirente de serviços de transporte cuja operação gere direito a crédito de PIS/COFINS.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "D100" | C | 004* | – | S |
| 02 | `IND_OPER` | Tipo de operação: 0 – Aquisição | C | 001* | – | S |
| 03 | `IND_EMIT` | Emitente: 0 – Própria; 1 – Terceiros | C | 001* | – | S |
| 04 | `COD_PART` | Código do participante (0150) — transportadora ou, em subcontratação, PF/PJ subcontratada | C | 060 | – | S |
| 05 | `COD_MOD` | Modelo do documento: 07, 08, 8B, 09, 10, 11, 26, 27, 57, 63, 67 | C | 002* | – | S |
| 06 | `COD_SIT` | Situação do documento: 00, 02, 04, 05, 06, 08 | N | 002* | – | S |
| 07 | `SER` | Série | C | 004 | – | N |
| 08 | `SUB` | Subsérie | C | 003 | – | N |
| 09 | `NUM_DOC` | Número do documento fiscal | N | 009 | – | S |
| 10 | `CHV_CTE` | Chave do CT-e (44 posições, obrigatória para `COD_MOD = 57` a partir de abr/2012) | N | 044* | – | N |
| 11 | `DT_DOC` | Data da emissão (`ddmmaaaa`) | N | 008* | – | S |
| 12 | `DT_A_P` | Data de aquisição/prestação (`ddmmaaaa`) | N | 008* | – | N |
| 13 | `TP_CT-e` | Tipo de CT-e (quando `COD_MOD = 57`) | N | 001* | – | N |
| 14 | `CHV_CTE_REF` | Chave do CT-e de referência (não preencher) | N | 044* | – | N |
| 15 | `VL_DOC` | Valor total do documento | N | – | 02 | S |
| 16 | `VL_DESC` | Desconto total | N | – | 02 | N |
| 17 | `IND_FRT` | Indicador do tipo de frete: **(a partir de 01/07/2012)** 0 – Por conta do emitente; 1 – Por conta do destinatário/remetente; 2 – Por conta de terceiros; 9 – Sem cobrança de frete | C | 001* | – | S |
| 18 | `VL_SERV` | Valor total da prestação de serviço (inclui pedágio e despesas) | N | – | 02 | S |
| 19 | `VL_BC_ICMS` | Base do ICMS (= `VL_SERV - VL_NT`) | N | – | 02 | N |
| 20 | `VL_ICMS` | Valor do ICMS | N | – | 02 | N |
| 21 | `VL_NT` | Valor não-tributado do ICMS | N | – | 02 | N |
| 22 | `COD_INF` | Código da informação complementar (0450) | C | 006 | – | N |
| 23 | `COD_CTA` | Conta contábil (obrigatório desde nov/2017, salvo dispensa de ECD) | C | 255 | – | N |

**Regra especial de chave única:**

- Emissão de terceiros: `IND_EMIT + NUM_DOC + COD_MOD + SER + SUB + COD_PART` deve ser único
- Emissão própria: `IND_EMIT + NUM_DOC + COD_MOD + SER + SUB` deve ser único

> **Uso no sistema Primetax:** para cada registro D100 com direito a crédito, deve existir **obrigatoriamente** um D101 (PIS) e um D105 (COFINS) filhos. Cruzamento crítico: `sum(D101.VL_BC_PIS) ≤ D100.VL_SERV`. Se a base de crédito é menor que o valor do serviço, isso pode indicar parcela do frete sem direito a crédito (por exemplo, transferências entre estabelecimentos — `IND_NAT_FRT = 4 ou 5`). Identifique casos em que a PJ está deixando de creditar fretes que deveria creditar.

### 1.4 Registro `D101` — Complemento do Documento de Transporte – PIS/Pasep

Nível 4, ocorrência 1:N. **Um registro para cada indicador de natureza do frete.**

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "D101" | C | 004* | – | S |
| 02 | `IND_NAT_FRT` | **Indicador da natureza do frete:** 0 – Venda com ônus do vendedor; 1 – Venda com ônus do adquirente; 2 – Compras de bens **geradores** de crédito; 3 – Compras de bens **não geradores** de crédito; 4 – Transferência de produtos acabados entre estabelecimentos; 5 – Transferência de produtos em elaboração entre estabelecimentos; 9 – Outras | C | 001* | – | S |
| 03 | `VL_ITEM` | Valor total dos itens | N | – | 02 | S |
| 04 | `CST_PIS` | CST-PIS (tabela 4.3.3) | N | 002* | – | S |
| 05 | `NAT_BC_CRED` | Natureza da base de crédito (tabela 4.3.7) | C | 002* | – | N |
| 06 | `VL_BC_PIS` | Base de cálculo do PIS | N | – | 02 | N |
| 07 | `ALIQ_PIS` | Alíquota do PIS (%) | N | 008 | 04 | N |
| 08 | `VL_PIS` | Valor do PIS | N | – | 02 | N |
| 09 | `COD_CTA` | Conta contábil | C | 255 | – | N |

**CSTs aplicáveis no D101/D105:** 50–56, 60–66, 70–75, 98, 99.

**Regras especiais:**

- Para **subcontratação de transporte** por PJ de transporte de cargas: usar **CST 60–66** (crédito presumido) e `NAT_BC_CRED = 14` (Atividade de Transporte de Cargas – Subcontratação). Alíquotas especiais: **PIS 1,2375%** e **COFINS 5,7%**.
- Para **transferências entre estabelecimentos** (`IND_NAT_FRT ∈ {4, 5}`): deve-se usar o CST que reflita o tratamento legal, sendo que operações sem previsão de crédito devem ser informadas com **CST 70**.
- **Frete de compra de mercadoria que gera crédito:** alternativamente à escrituração em C170/C191, pode-se escriturar aqui com `IND_NAT_FRT = 2`.

> **Uso no sistema Primetax:** cruzamento de alta sensibilidade — empresas frequentemente classificam **todos** os fretes como `IND_NAT_FRT = 0` ou `IND_NAT_FRT = 3`, perdendo créditos válidos. Auditar especialmente: (i) fretes classificados como "3 – não geradores" cuja PJ pagadora é industrial ou comercial de revenda (provável reclassificação para "2"); (ii) presença de CST 70 em D101 com CFOP de aquisição de insumo no documento pai.

### 1.5 Registro `D105` — Complemento do Documento de Transporte – COFINS

Estrutura idêntica ao D101, substituindo PIS por COFINS em todos os campos.

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "D105" |
| 02 | `IND_NAT_FRT` | Mesmo conteúdo que D101 |
| 03 | `VL_ITEM` | Valor total dos itens |
| 04 | `CST_COFINS` | CST-COFINS |
| 05 | `NAT_BC_CRED` | Natureza da base de crédito |
| 06 | `VL_BC_COFINS` | Base de cálculo da COFINS |
| 07 | `ALIQ_COFINS` | Alíquota (%) |
| 08 | `VL_COFINS` | Valor da COFINS |
| 09 | `COD_CTA` | Conta contábil |

### 1.6 Registro `D200` — Resumo da Escrituração Diária – Prestação de Serviços de Transporte

Nível 3, ocorrência 1:N. Consolidação diária dos documentos fiscais válidos emitidos na prestação de serviços de transporte pela PJ titular.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "D200" | C | 004* | – | S |
| 02 | `COD_MOD` | Modelo: 07, 08, 8B, 09, 10, 11, 26, 27, 57, 63, 67 | C | 002* | – | S |
| 03 | `COD_SIT` | Situação: 00, 01, 06, 07, 08 (não incluir cancelados/denegados/inutilizados) | N | 002* | – | S |
| 04 | `SER` | Série | C | 004 | – | N |
| 05 | `SUB` | Subsérie | C | 003 | – | N |
| 06 | `NUM_DOC_INI` | Nº do documento inicial | N | 009 | – | S |
| 07 | `NUM_DOC_FIN` | Nº do documento final | N | 009 | – | S |
| 08 | `CFOP` | CFOP | N | 004* | – | S |
| 09 | `DT_REF` | Data de referência do resumo (`ddmmaaaa`) | N | 008* | – | S |
| 10 | `VL_DOC` | Valor total dos documentos | N | – | 02 | S |
| 11 | `VL_DESC` | Valor total dos descontos | N | – | 02 | N |

### 1.7 Registros `D201` e `D205` — Totalização do Resumo Diário – PIS/COFINS

Análogos aos C181/C185. Segregam o consolidado do D200 por CST, base, alíquota.

Campos principais do D201 (PIS): `REG`, `CST_PIS`, `VL_ITEM`, `VL_BC_PIS` (onde se faz a exclusão do ICMS quando aplicável — Seção 12), `ALIQ_PIS`, `QUANT_BC_PIS`, `ALIQ_PIS_QUANT`, `VL_PIS`, `COD_CTA`.

Campos principais do D205 (COFINS): `REG`, `CST_COFINS`, `VL_ITEM`, `VL_BC_COFINS`, `ALIQ_COFINS`, `QUANT_BC_COFINS`, `ALIQ_COFINS_QUANT`, `VL_COFINS`, `COD_CTA`.

### 1.8 Registros `D300` e `D350` — Bilhetes de Passagem

`D300` — Resumo de Bilhetes Consolidados de Passagem (modelos 2E, 13, 14, 15, 16). `D350` — Resumo Diário de Cupom Fiscal emitido por ECF-Bilhete de Passagem.

Campos-chave do D300: `COD_MOD`, `COD_SIT`, `NUM_DOC_INI`, `NUM_DOC_FIN`, `CFOP`, `DT_REF`, `VL_DOC`, `VL_DESC` (onde se faz a exclusão do ICMS — Seção 12), `CST_PIS`, `VL_BC_PIS`, `ALIQ_PIS`, `VL_PIS`, `CST_COFINS`, `VL_BC_COFINS`, `ALIQ_COFINS`, `VL_COFINS`.

### 1.9 Registros `D500`, `D501`, `D505` — NF de Comunicação e Telecomunicação (Aquisições com Crédito)

`D500` é a nota fiscal de aquisição de serviço de comunicação (cód. 21) ou telecom (cód. 22) com direito a crédito. `D501` e `D505` são os complementos PIS e COFINS.

Campos-chave do D500: `IND_OPER` (0 – Aquisição), `IND_EMIT`, `COD_PART`, `COD_MOD`, `COD_SIT`, `SER`, `NUM_DOC`, `DT_DOC`, `VL_DOC`, `VL_DESC`, `VL_SERV`, `VL_BC_ICMS`, `VL_ICMS`, `VL_NT`, `COD_CTA`.

Campos-chave do D501/D505: `CST_PIS`/`CST_COFINS`, `NAT_BC_CRED`, `VL_ITEM`, `VL_BC_PIS`/`VL_BC_COFINS`, `ALIQ_PIS`/`ALIQ_COFINS`, `VL_PIS`/`VL_COFINS`, `COD_CTA`.

> **Uso no sistema Primetax:** aquisição de serviços de comunicação/telecom é creditável **apenas** quando se enquadra como insumo. A reclassificação para PJ prestadora de serviços (onde telefonia/internet é essencial à atividade-fim) é área de oportunidade, mas exige fundamentação técnica sólida caso a caso.

### 1.10 Registros `D600`, `D601`, `D605` — Consolidação da Prestação de Serviços de Comunicação

Análogos ao `C600`/`C601`/`C605` para energia elétrica, porém para serviços de comunicação/telecom. **Registros de consolidação em que a exclusão do ICMS é aplicada diretamente na base de cálculo** — ver Seção 12 da Parte 1.

Campos-chave do D601/D605: `CST_PIS`/`CST_COFINS`, `CFOP`, `VL_ITEM`, `VL_BC_PIS`/`VL_BC_COFINS` (com ICMS excluído quando aplicável), `ALIQ_PIS`/`ALIQ_COFINS`, `VL_PIS`/`VL_COFINS`, `COD_CTA`.

---

## 2. Bloco F — Demais Documentos e Operações

### 2.1 Visão geral do Bloco F

O Bloco F é o **bloco-coringa** da EFD-Contribuições. Comporta tudo que, por sua natureza ou por falta de documento fiscal específico, não se encaixa nos Blocos A, C ou D:

- Receitas financeiras, JCP, aluguéis
- Despesas de aluguéis, armazenagem, arrendamento mercantil
- Operações documentadas por outros instrumentos (contratos, extratos de cooperativas)
- Aquisições de insumos sem nota fiscal nos Blocos A/C/D
- **Importação com apropriação pela DI** (não pela entrada da nota)
- **Ativo imobilizado** (F120 e F130) — crítico
- **Crédito presumido sobre estoque de abertura** (F150)
- **Atividade imobiliária** (F200/F205/F210)
- **Regime de Caixa** para lucro presumido (F500, F510, F525)
- **Regime de Competência** para lucro presumido (F550, F560)
- **Retenções na fonte** (F600)
- **Deduções diversas** (F700)
- **Créditos recebidos em eventos de sucessão** (F800)
- **Créditos presumidos específicos de setores** (café Lei 12.599/2012, soja/margarina/biodiesel Lei 12.865/2013, etc.) — escriturados em F100 com `NAT_BC_CRED = 13`

**Importância estratégica para a Primetax:** o Bloco F é provavelmente a **maior fonte de oportunidades de recuperação** em auditorias da Primetax, pelos seguintes motivos:

1. **F120/F130** — ativos imobilizados frequentemente sub-aproveitados; a escolha entre depreciação e valor de aquisição é otimizável
2. **F150** — estoque de abertura quase sempre mal apurado em migrações de regime
3. **F100 com `NAT_BC_CRED = 13`** — créditos presumidos setoriais frequentemente esquecidos
4. **F600** — retenções na fonte que não são automaticamente recuperadas em M200/M600, exigindo preenchimento ativo pelo contribuinte — fonte comum de retenções não aproveitadas

### 2.2 Tabela do Bloco F

| Registro | Descrição | Nível | Contrib. | Crédito |
|:---:|---|:---:|:---:|:---:|
| `F001` | Abertura do Bloco F | 1 | – | – |
| `F010` | Identificação do Estabelecimento | 2 | – | – |
| `F100` | Demais Documentos e Operações Geradoras de Contribuição e Créditos | 3 | S | S |
| `F111` | Processo Referenciado (F100) | 4 | S | S |
| `F120` | **Bens Incorporados ao Ativo Imobilizado – Crédito sobre Encargos de Depreciação/Amortização** | 3 | N | **S** |
| `F129` | Processo Referenciado (F120) | 4 | N | S |
| `F130` | **Bens Incorporados ao Ativo Imobilizado – Crédito sobre Valor de Aquisição** | 3 | N | **S** |
| `F139` | Processo Referenciado (F130) | 4 | N | S |
| `F150` | **Crédito Presumido sobre Estoque de Abertura** | 3 | N | **S** |
| `F200` | Atividade Imobiliária – Unidade Imobiliária Vendida | 3 | S | N |
| `F205` | Atividade Imobiliária – Custo Incorrido | 4 | N | S |
| `F210` | Atividade Imobiliária – Custo Orçado | 4 | N | S |
| `F211` | Processo Referenciado (F200/F205/F210) | 4 | S | S |
| `F500` | Consolidação – Regime de Caixa (PJ Lucro Presumido) | 3 | S | N |
| `F509` | Processo Referenciado (F500) | 4 | S | N |
| `F510` | Consolidação – Regime de Caixa – Alíquotas por Unidade de Medida | 3 | S | N |
| `F519` | Processo Referenciado (F510) | 4 | S | N |
| `F525` | Composição das Receitas do F500 | 4 | S | N |
| `F550` | Consolidação – Regime de Competência (PJ Lucro Presumido) | 3 | S | N |
| `F559` | Processo Referenciado (F550) | 4 | S | N |
| `F560` | Consolidação – Regime de Competência – Alíquotas por Unidade de Medida | 3 | S | N |
| `F569` | Processo Referenciado (F560) | 4 | S | N |
| `F600` | **Contribuição Retida na Fonte** | 3 | N | – |
| `F700` | **Deduções Diversas** | 3 | S | – |
| `F800` | **Créditos Decorrentes de Eventos de Incorporação, Fusão e Cisão** | 3 | N | S |
| `F990` | Encerramento do Bloco F | 1 | – | – |

### 2.3 Registro `F100` — Demais Documentos e Operações Geradoras de Contribuição e Créditos

Nível 3, ocorrência 1:N. Registro-coringa para operações não contempladas pelos Blocos A, C, D ou pelos demais registros do F.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F100" | C | 004* | – | S |
| 02 | `IND_OPER` | **Tipo de operação:** 0 – Operação com direito a crédito (CST 50–66); 1 – Receita tributada (CST 01, 02, 03, 05); 2 – Receita não tributada (CST 04, 06, 07, 08, 09, 49, 99) | C | 001* | – | S |
| 03 | `COD_PART` | Código do participante (0150) — obrigatório quando `IND_OPER = 0` | C | 060 | – | N |
| 04 | `COD_ITEM` | Código do item (0200) | C | 060 | – | N |
| 05 | `DT_OPER` | Data da operação (`ddmmaaaa`) | N | 008* | – | S |
| 06 | `VL_OPER` | Valor da operação/item | N | – | 02 | S |
| 07 | `CST_PIS` | CST-PIS (tabela 4.3.3) | N | 002* | – | S |
| 08 | `VL_BC_PIS` | Base de cálculo do PIS (com exclusão ICMS aplicada diretamente — Seção 12) | N | – | 04 | N |
| 09 | `ALIQ_PIS` | Alíquota PIS | N | 008 | 04 | N |
| 10 | `VL_PIS` | Valor do PIS | N | – | 02 | N |
| 11 | `CST_COFINS` | CST-COFINS (tabela 4.3.4) | N | 002* | – | S |
| 12 | `VL_BC_COFINS` | Base de cálculo da COFINS (com exclusão ICMS aplicada diretamente — Seção 12) | N | – | 04 | N |
| 13 | `ALIQ_COFINS` | Alíquota COFINS | N | 008 | 04 | N |
| 14 | `VL_COFINS` | Valor da COFINS | N | – | 02 | N |
| 15 | `NAT_BC_CRED` | Natureza da base de crédito (tabela 4.3.7) — obrigatório se CST for de crédito | C | 002* | – | N |
| 16 | `IND_ORIG_CRED` | Origem do crédito: 0 – Mercado Interno; 1 – Importação | C | 001* | – | N |
| 17 | `COD_CTA` | Conta contábil (obrigatório desde nov/2017) | C | 255 | – | N |
| 18 | `COD_CCUS` | Código do centro de custos | C | 255 | – | N |
| 19 | `DESC_DOC_OPER` | Descrição do documento/operação | C | – | – | N |

**Operações típicas a escriturar em F100:**

*Lado de receitas:*
- Rendimentos de aplicações financeiras
- Receitas de títulos vinculados ao mercado aberto
- Receitas de consórcios (arts. 278–279 da Lei 6.404/76)
- Receitas de locação de bens móveis e imóveis
- Receita da venda de bens imóveis do ativo não-circulante
- JCP (Juros sobre Capital Próprio) recebidos
- Receitas da execução de obras de construção civil por administração/empreitada
- Receita auferida com produtos/serviços convencionada por contrato
- Receita de serviços de educação, saúde
- Montante do faturamento atribuído a PJ associada/cooperada

*Lado de créditos:*
- Despesas de aluguéis de prédios, máquinas e equipamentos
- Contraprestações de arrendamento mercantil
- Despesas de armazenagem
- Aquisição de insumos com documentação fora dos Blocos A/C/D
- **Importação com apropriação pela DI** (crédito no desembaraço aduaneiro)
- **Crédito presumido da subcontratação** de transporte rodoviário de cargas
- **Créditos presumidos setoriais:** café (Lei 12.599/2012), soja/margarina/biodiesel (Lei 12.865/2013), etc.

**Exemplo prático do manual (crédito presumido de exportação de café):**

Considerando receita de exportação de café (NCM 0901.1) de R$ 1.000.000,00:

```
- IND_OPER: 0 (operação com direito a crédito)
- VL_OPER: 1.000.000,00
- CST_PIS: 62 (crédito presumido vinculado à exportação)
- VL_BC_PIS: 1.000.000,00
- ALIQ_PIS: 0,1650% (Item 110, Tabela 4.3.9)
- VL_PIS: 1.650,00
- CST_COFINS: 62
- VL_BC_COFINS: 1.000.000,00
- ALIQ_COFINS: 0,76%
- VL_COFINS: 7.600,00
- NAT_BC_CRED: 13 (outras operações com direito a crédito)
```

> **Quando `NAT_BC_CRED = 13`, é obrigatório preencher o campo `DESC_CRED` no M105/M505** com descrição como "Crédito Presumido da Exportação de café – Lei nº 12.599/2012".

> **Uso no sistema Primetax — áreas de alta oportunidade em F100:**
>
> 1. **Créditos presumidos setoriais** frequentemente esquecidos: exportação de café, soja/derivados, carnes, etc. Auditar PJ exportadoras de commodities contra a presença de F100 com CST 62 e `NAT_BC_CRED = 13`.
> 2. **Aluguéis de prédios/máquinas (NAT_BC_CRED = 05 ou 06):** PJ muitas vezes não escrituram esses créditos por dúvida sobre enquadramento. Cruzar com o plano de contas (ECD — contas de despesa de aluguel) para identificar créditos não aproveitados.
> 3. **Armazenagem e frete em operação de venda (`NAT_BC_CRED = 07`):** frequentemente escriturado parcialmente ou só em um dos tributos.
> 4. **Arrendamento mercantil (`NAT_BC_CRED = 08`):** créditos válidos, mas pouco explorados.
> 5. **Importação com apropriação pela DI** (`IND_ORIG_CRED = 1`): conferir com SISCOMEX se há operações não escrituradas.

### 2.4 Registro `F120` — Bens Incorporados ao Ativo Imobilizado – Crédito sobre Encargos de Depreciação/Amortização

Nível 3, ocorrência 1:N. **Registro crítico para a Primetax.**

Registro para a escrituração dos créditos determinados **com base nos encargos de depreciação** de bens incorporados ao Ativo Imobilizado, adquiridos para uso na **produção de bens**, **prestação de serviços** ou **locação a terceiros**. Também aplicável a encargos de amortização de edificações e benfeitorias.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F120" | C | 004* | – | S |
| 02 | `NAT_BC_CRED` | Natureza da base: **09** – Depreciação; **11** – Amortização | C | 002* | – | S |
| 03 | `IDENT_BEM_IMOB` | Identificação do bem/grupo: 01 – Edificações/benfeitorias em imóveis próprios; 02 – Idem em imóveis de terceiros; 03 – Instalações; 04 – Máquinas; 05 – Equipamentos; 06 – Veículos; 99 – Outros | N | 002* | – | S |
| 04 | `IND_ORIG_CRED` | Origem: 0 – Mercado Interno; 1 – Importação | C | 001* | – | N |
| 05 | `IND_UTIL_BEM_IMOB` | **Utilização: 1 – Produção de bens destinados a venda; 2 – Prestação de serviços; 3 – Locação a terceiros; 9 – Outros** | N | 001* | – | S |
| 06 | `VL_OPER_DEP` | Valor do encargo de depreciação/amortização no período | N | – | 02 | S |
| 07 | `PARC_OPER_NAO_BC_CRED` | Parcela do encargo a **excluir** da base de crédito (itens sem direito) | N | – | 02 | N |
| 08 | `CST_PIS` | CST-PIS (tabela 4.3.3) | N | 002* | – | S |
| 09 | `VL_BC_PIS` | Base PIS (= Campo 06 − Campo 07) | N | – | 02 | N |
| 10 | `ALIQ_PIS` | Alíquota (%) | N | 008 | 04 | N |
| 11 | `VL_PIS` | Valor do crédito PIS | N | – | 02 | N |
| 12 | `CST_COFINS` | CST-COFINS | N | 002* | – | S |
| 13 | `VL_BC_COFINS` | Base COFINS (= Campo 06 − Campo 07) | N | – | 02 | N |
| 14 | `ALIQ_COFINS` | Alíquota (%) | N | 008 | 04 | N |
| 15 | `VL_COFINS` | Valor do crédito COFINS | N | – | 02 | N |
| 16 | `COD_CTA` | Conta contábil | C | 255 | – | N |
| 17 | `COD_CCUS` | Centro de custos | C | 255 | – | N |
| 18 | `DESC_BEM_IMOB` | Descrição complementar do bem/grupo | C | – | – | N |

**Vedações legais (não há direito a crédito sobre):**

- Bens incorporados ao imobilizado com **data de aquisição anterior a maio/2004** (art. 31 da Lei 10.865/2004)
- Bens **não utilizados** em produção, serviços ou locação — por exemplo: bens em **área administrativa, comercial, gerencial, processamento de dados, almoxarifado**

**Regras de preenchimento relevantes:**

- Para bens em uso misto (parte elegível, parte não), a parcela **não creditável** deve ir no Campo 07, **não** sendo incluída na base do Campo 09/13.
- Encargos de depreciação/amortização sobre edificações e benfeitorias em imóveis **próprios ou de terceiros** usados na atividade geram crédito.
- O bem pode ser escriturado individualmente ou por **grupo/gênero** (ex: "Máquinas e Equipamentos").
- **Não** é permitido escriturar o mesmo bem em F120 e F130 (excludência mútua).

### 2.5 Registro `F130` — Bens Incorporados ao Ativo Imobilizado – Crédito sobre Valor de Aquisição

Nível 3, ocorrência 1:N. Alternativa ao F120 — crédito determinado **com base no valor de aquisição** do bem (e não sobre depreciação).

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F130" | C | 004* | – | S |
| 02 | `NAT_BC_CRED` | Fixo: **10** | C | 002* | – | S |
| 03 | `IDENT_BEM_IMOB` | 01 – Edificações/benfeitorias; 03 – Instalações; 04 – Máquinas; 05 – Equipamentos; 06 – Veículos; 99 – Outros | N | 002* | – | S |
| 04 | `IND_ORIG_CRED` | 0 – Mercado Interno; 1 – Importação | C | 001* | – | N |
| 05 | `IND_UTIL_BEM_IMOB` | 1 – Produção; 2 – Serviços; 3 – Locação; 9 – Outros | N | 001* | – | S |
| 06 | `MES_OPER_AQUIS` | Mês/Ano de aquisição (`mmaaaa`) | N | 006* | – | N |
| 07 | `VL_OPER_AQUIS` | Valor de aquisição | N | – | 02 | S |
| 08 | `PARC_OPER_NAO_BC_CRED` | Parcela a excluir da base | N | – | 02 | N |
| 09 | `VL_BC_CRED` | Valor total da base (= Campo 07 − Campo 08) | N | – | 02 | S |
| 10 | `IND_NR_PARC` | **Número de parcelas de apropriação:** 1 – Integral (mês da aquisição); 2 – 12 meses; 3 – 24 meses; 4 – 48 meses; 5 – 6 meses (embalagens de bebidas frias); 9 – Outra periodicidade em lei | N | 001* | – | S |
| 11 | `CST_PIS` | CST-PIS | N | 002* | – | S |
| 12 | `VL_BC_PIS` | Base **mensal** do crédito PIS (= Campo 09 / Nº de meses) | N | – | 02 | N |
| 13 | `ALIQ_PIS` | Alíquota (%) | N | 008 | 04 | N |
| 14 | `VL_PIS` | Crédito PIS do mês | N | – | 02 | N |
| 15 | `CST_COFINS` | CST-COFINS | N | 002* | – | S |
| 16 | `VL_BC_COFINS` | Base mensal COFINS (= Campo 09 / Nº de meses) | N | – | 02 | N |
| 17 | `ALIQ_COFINS` | Alíquota (%) | N | 008 | 04 | N |
| 18 | `VL_COFINS` | Crédito COFINS do mês | N | – | 02 | N |
| 19 | `COD_CTA` | Conta contábil | C | 255 | – | N |
| 20 | `COD_CCUS` | Centro de custos | C | 255 | – | N |
| 21 | `DESC_BEM_IMOB` | Descrição complementar | C | – | – | N |

**Regra especial (MP 540/2011, Lei 12.546/2011):** para máquinas e equipamentos destinados à produção de bens ou serviços adquiridos a partir de 03/08/2011, permite-se crédito em prazo inferior a 12 meses (**apropriação integral ou em poucas parcelas**). Nesses casos, usar `IND_NR_PARC = 9` e o Campo 06 (`MES_OPER_AQUIS`) serve como identificador do período de apropriação.

> **Estratégia Primetax — otimização F120 vs F130:**
>
> A escolha entre F120 (depreciação) e F130 (valor de aquisição) tem impacto direto no fluxo do crédito:
>
> - **F120:** crédito espalhado pela vida útil contábil do bem (muitas vezes 10 ou 20 anos) — fluxo pequeno mas longo
> - **F130:** crédito em 12, 24 ou 48 meses — fluxo maior e mais curto
> - **F130 com `IND_NR_PARC = 1` (integral):** aplicável a máquinas e equipamentos adquiridos a partir de ago/2011 — **crédito total no mês da aquisição**
>
> Oportunidades de revisão:
> 1. PJ que vem usando F120 em bens elegíveis ao F130 com apropriação em 12 meses ou imediata — recalcular crédito e apurar diferenças como extemporâneo (Bloco 1)
> 2. PJ que **não escritura** ativos em F120/F130 por desconhecimento — especialmente imóveis próprios usados na atividade, cujas benfeitorias geram crédito pela amortização
> 3. Bens em área administrativa indevidamente incluídos (Campo 07 não preenchido com parcela excluível) — risco de autuação

### 2.6 Registro `F150` — Crédito Presumido sobre Estoque de Abertura

Nível 3, ocorrência 1:N. Crédito presumido sobre estoque de bens adquiridos para revenda ou insumos, existentes na **data de início da incidência não-cumulativa**, adquiridos de PJ domiciliada no país.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F150" | C | 004* | – | S |
| 02 | `NAT_BC_CRED` | Fixo: **18** (Estoque de abertura) | C | 002* | – | S |
| 03 | `VL_TOT_EST` | Valor total do estoque de abertura | N | – | 02 | S |
| 04 | `EST_IMP` | Parcela do estoque **sem direito a crédito** (importados, adquiridos de PF, alíquota zero, etc.) | N | – | 02 | N |
| 05 | `VL_BC_EST` | Base total do crédito (= Campo 03 − Campo 04) | N | – | 02 | S |
| 06 | `VL_BC_MEN_EST` | Base mensal (= 1/12 do Campo 05) | N | – | 02 | S |
| 07 | `CST_PIS` | CST-PIS (valores válidos: 50, 51, 52, 53, 54, 55, 56) | N | 002* | – | S |
| 08 | `ALIQ_PIS` | Alíquota: **0,65** (fixa) | N | 008 | 04 | S |
| 09 | `VL_CRED_PIS` | Crédito PIS mensal (= Campo 06 × Campo 08 / 100) | N | – | 02 | S |
| 10 | `CST_COFINS` | CST-COFINS (valores válidos: 50–56) | N | 002* | – | S |
| 11 | `ALIQ_COFINS` | Alíquota: **3,0** (fixa) | N | 008 | 04 | S |
| 12 | `VL_CRED_COFINS` | Crédito COFINS mensal (= Campo 06 × Campo 11 / 100) | N | – | 02 | S |
| 13 | `DESC_EST` | Descrição do estoque (opcional — pode segregar por matéria-prima, embalagem, etc.) | C | 100 | – | N |
| 14 | `COD_CTA` | Conta contábil | C | 255 | – | N |

**Regras críticas:**

- Crédito apropriado em **12 parcelas mensais iguais e sucessivas**, a partir do ingresso no regime não-cumulativo
- Alíquotas **fixas** e diferentes das alíquotas regulares do regime não-cumulativo: **PIS 0,65%** e **COFINS 3,0%** (não as de 1,65% e 7,6%)
- Este registro **só deve ser preenchido** se o ingresso no regime não-cumulativo ocorreu há até **12 meses** do período da escrituração
- Bens recebidos em devolução, tributados antes da mudança de regime para o lucro real, são considerados no estoque de abertura

> **Uso no sistema Primetax:** oportunidade clássica. Sempre que a PJ-cliente migrou de Lucro Presumido para Lucro Real nos últimos 12 meses, ou optou pelo regime não-cumulativo, verificar existência e completude do F150. Casos frequentes de falha:
>
> - F150 não escriturado por desconhecimento
> - Valor total do estoque subestimado (não inclui bens recebidos em devolução tributada)
> - Campo 04 (parcela sem crédito) superestimado (exclusão conservadora além do legal)

### 2.7 Registro `F200` — Operações da Atividade Imobiliária – Unidade Imobiliária Vendida

Nível 3, ocorrência 1:N. Exclusivo para PJ com **atividade imobiliária** (aquisição/venda, incorporação, loteamento, desmembramento, construção de prédio destinado à venda).

Campos principais:

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "F200" |
| 02 | `IND_OPER` | 01 – Venda a vista (concluída); 02 – Venda a prazo (concluída); 03 – Venda a vista (em construção); 04 – Venda a prazo (em construção); 05 – Outras |
| 03 | `UNID_IMOB` | 01 – Terreno adquirido para venda; 02 – Terreno de loteamento; 03 – Lote de desmembramento; 04 – Unidade de incorporação; 05 – Prédio construído/em construção; 06 – Outras |
| 04 | `IDENT_EMP` | Identificação do empreendimento |
| 05 | `DESC_UNID_IMOB` | Descrição da unidade |
| 06 | `NUM_CONT` | Número do contrato |
| 07 | `CPF_CNPJ_ADQU` | CPF/CNPJ do adquirente (não do pagador/financiador) |
| 08 | `DT_OPER` | Data da venda |
| 09 | `VL_TOT_VEND` | Valor total atualizado até o período |
| 10 | `VL_REC_ACUM` | Recebido acumulado até o mês anterior |
| 11 | `VL_TOT_REC` | Recebido no mês da escrituração |
| 12 | `CST_PIS` | CST-PIS |
| 13 | `VL_BC_PIS` | Base PIS |
| 14 | `ALIQ_PIS` | Alíquota (%) |
| 15 | `VL_PIS` | Valor PIS |
| 16 | `CST_COFINS` | CST-COFINS |
| 17 | `VL_BC_COFINS` | Base COFINS |
| 18 | `ALIQ_COFINS` | Alíquota (%) |
| 19 | `VL_COFINS` | Valor COFINS |
| 20 | `PERC_REC_RECEB` | Percentual recebido ((Campo 10 + Campo 11) / Campo 09) |
| 21 | `IND_NAT_EMP` | 1 – Consórcio; 2 – SCP; 3 – Incorporação em Condomínio; 4 – Outras |
| 22 | `INF_COMP` | Informações complementares |

**Regra especial da atividade imobiliária:** os créditos em F205/F210 **só podem ser utilizados a partir da efetivação da venda e na proporção da receita recebida**, não no momento da incorporação do custo.

### 2.8 Registros `F205` e `F210` — Custo Incorrido e Custo Orçado

`F205` — custo **incorrido** (efetivamente gasto) da unidade vendida, base do crédito proporcional ao percentual recebido.

`F210` — custo **orçado** (previsto e não incorrido) da unidade não concluída.

A diferenciação entre F205 e F210 é central no regime especial da atividade imobiliária. Créditos de F205 têm `NAT_BC_CRED = 15` (Custo Incorrido); F210 tem `NAT_BC_CRED = 16` (Custo Orçado).

### 2.9 Registros `F500` — Consolidação da PJ Lucro Presumido (Regime de Caixa)

Nível 3, ocorrência 1:N. **Registro específico para PJ Lucro Presumido optante pelo regime de caixa** (art. 20 da MP 2.158-35/2001). Escriturado quando no Registro `0110.IND_REG_CUM = 1`.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F500" | C | 004* | – | S |
| 02 | `VL_REC_CAIXA` | **Valor total da receita recebida**, por combinação de CST e alíquota | N | – | 02 | S |
| 03 | `CST_PIS` | CST-PIS (valores válidos para cumulativo: 01, 02, 04, 05, 06, 07, 08, 09, 49, 99) | N | 002* | – | S |
| 04 | `VL_DESC_PIS` | **Valor do desconto/exclusão da base PIS** (onde aplica-se a exclusão do ICMS — Seção 12) | N | – | 02 | N |
| 05 | `VL_BC_PIS` | Base PIS | N | – | 02 | N |
| 06 | `ALIQ_PIS` | Alíquota (%) | N | 008 | 04 | N |
| 07 | `VL_PIS` | Valor PIS | N | – | 02 | N |
| 08 | `CST_COFINS` | CST-COFINS | N | 002* | – | S |
| 09 | `VL_DESC_COFINS` | **Desconto/exclusão COFINS** (exclusão ICMS — Seção 12) | N | – | 02 | N |
| 10 | `VL_BC_COFINS` | Base COFINS | N | – | 02 | N |
| 11 | `ALIQ_COFINS` | Alíquota (%) | N | 008 | 04 | N |
| 12 | `VL_COFINS` | Valor COFINS | N | – | 02 | N |
| 13 | `COD_MOD` | Modelo do documento (tabela 4.1.1): 65 para NFC-e; 98 para serviços (ISS); 99 para outros | C | 002* | – | N |
| 14 | `CFOP` | CFOP | N | 004* | – | N |
| 15 | `COD_CTA` | Conta contábil | C | 255 | – | N |
| 16 | `INFO_COMPL` | Informação complementar | C | – | – | N |

**Regras:**

- Um registro F500 **para cada combinação de CST e alíquota**
- Alíquotas fixas no regime cumulativo: **PIS 0,65%** e **COFINS 3,0%**
- O total das receitas consolidadas em F500 deve corresponder ao total detalhado nos F525

### 2.10 Registro `F510` — Consolidação Regime de Caixa por Unidade de Medida

Análogo ao F500 mas para apuração **por unidade de medida de produto** (combustíveis, bebidas frias). Substitui `VL_BC_PIS/COFINS` por `QUANT_BC_PIS/COFINS` e `ALIQ_PIS/COFINS` por `ALIQ_PIS_QUANT/ALIQ_COFINS_QUANT`.

### 2.11 Registro `F525` — Composição das Receitas do F500

Nível 4, ocorrência 1:N. Detalhamento analítico das receitas recebidas consolidadas no F500, por cliente/documento/item.

Campos principais: `VL_REC`, `IND_REC` (indicador da origem: 01 – ref. a documento fiscal; 02 – contrato; 03 – outras), `CNPJ_CPF`, `COD_ITEM`, `COD_CTA`, `DESC_COMPL`.

### 2.12 Registros `F550`, `F560`, `F569` — Regime de Competência (PJ Lucro Presumido)

`F550` — análogo ao F500 mas para PJ Lucro Presumido optante pelo **regime de competência** (`0110.IND_REG_CUM = 2`). Escritura as receitas **auferidas** (não recebidas).

Estrutura idêntica ao F500, substituindo `VL_REC_CAIXA` por `VL_REC_COMP` (receita auferida por competência).

`F560` — análogo ao F510 (competência por unidade de medida).

### 2.13 Registro `F600` — Contribuição Retida na Fonte

Nível 3, ocorrência 1:N. **Registro de altíssima importância prática.** Informa valores de PIS/COFINS retidos na fonte pelas fontes pagadoras, passíveis de dedução em M200/M600.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F600" | C | 004* | – | S |
| 02 | `IND_NAT_RET` | **Natureza da retenção:** 01 – Órgãos/Autarquias/Fundações Federais (art. 64, Lei 9.430/96); 02 – Outras entidades da Administração Federal (art. 34, Lei 10.833/03); 03 – PJ de direito privado (art. 30, Lei 10.833/03 — serviços de limpeza, conservação, manutenção, segurança, vigilância, transporte de valores, locação de MO, assessoria creditícia/mercadológica, serviços profissionais); 04 – Recolhimento por Sociedade Cooperativa (art. 66, Lei 9.430/96); 05 – Retenção por Fabricante de Veículos e Peças (art. 3º, Lei 10.485/02); 99 – Outras | N | 002* | – | S |
| 03 | `DT_RET` | Data da retenção | N | 008* | – | S |
| 04 | `VL_BC_RET` | Base da retenção/recolhimento (valor líquido + contribuições retidas, se a base não for conhecida) | N | – | 04 | S |
| 05 | `VL_RET` | Valor total retido na fonte/recolhido | N | – | 02 | S |
| 06 | `COD_REC` | Código da receita | C | 004 | – | N |
| 07 | `IND_NAT_REC` | Natureza: 0 – Não Cumulativa; 1 – Cumulativa (se misto, informar 0) | N | 001* | – | N |
| 08 | `CNPJ` | CNPJ da fonte pagadora (se beneficiária da retenção declara) ou da PJ beneficiária (se responsável declara) | N | 014* | – | S |
| 09 | `VL_RET_PIS` | **Valor retido — PIS/Pasep** | N | – | 02 | S |
| 10 | `VL_RET_COFINS` | **Valor retido — COFINS** | N | – | 02 | S |
| 11 | `IND_DEC` | Condição da PJ declarante: **0 – Beneficiária (PJ cooperada, prestadora de serviço que sofreu retenção); 1 – Responsável pelo recolhimento (cooperativa que recolheu)** | N | 001* | – | S |

> **ATENÇÃO CRÍTICA do manual:** os valores informados nos Campos 09 e 10 **NÃO são automaticamente recuperados** nos registros M200/M600. **Devem sempre ser informados pela própria PJ** no arquivo importado pelo PVA ou editados no PVA.
>
> **Esta é uma das maiores fontes de perda de créditos** pelas PJ: empresas sofrem retenção na fonte mas **esquecem de declarar nos campos apropriados de M200/M600**, perdendo o direito à compensação.

> **Cruzamento primário Primetax para F600:**
>
> 1. Para cada F600 escriturado com `IND_DEC = 0`, verificar se os valores dos Campos 09 (`VL_RET_PIS`) e 10 (`VL_RET_COFINS`) estão sendo efetivamente deduzidos nos correspondentes M200 (`VL_RET_FT_NC` / `VL_RET_FT_CUM`) e M600. Retenções escrituradas mas não deduzidas = crédito perdido.
> 2. Retenções informadas em DIRF pelas fontes pagadoras mas **não escrituradas** em F600: cruzar DIRF (CNPJ beneficiário, valores de PIS/COFINS retidos) com presença de F600 correspondente. Divergências indicam retenções não aproveitadas.
> 3. **Prescrição:** retenções são compensáveis em **5 anos** a partir do fato gerador. Auditar períodos ainda não prescritos para identificar créditos recuperáveis via escrituração extemporânea no Bloco 1 (registros 1300 — PIS e 1700 — COFINS).

### 2.14 Registro `F700` — Deduções Diversas

Nível 3, ocorrência 1:N. Deduções previstas na legislação tributária que podem ser abatidas da contribuição apurada em M200/M600, **exceto** créditos do regime não-cumulativo (esses vão em M100/M500).

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F700" | C | 004* | – | S |
| 02 | `IND_ORI_DED` | **Origem da dedução:** 01 – Créditos Presumidos Medicamentos; 02 – Créditos Admitidos no Regime Cumulativo Bebidas Frias; 03 – Contribuição paga pelo ST ZFM; 04 – ST Não Ocorrência do Fato Gerador; 99 – Outras Deduções | N | 002* | – | S |
| 03 | `IND_NAT_DED` | Natureza: 0 – Não Cumulativa; 1 – Cumulativa | N | 001* | – | S |
| 04 | `VL_DED_PIS` | Valor a deduzir — PIS | N | – | 02 | S |
| 05 | `VL_DED_COFINS` | Valor a deduzir — COFINS | N | – | 02 | S |
| 06 | `VL_BC_OPER` | Base de cálculo da operação que ensejou a dedução | N | – | 02 | N |
| 07 | `CNPJ` | CNPJ da PJ relacionada à operação | N | 014* | – | N |
| 08 | `INF_COMP` | Informações complementares | C | 090 | – | N |

**Chave única:** `IND_ORI_DED + IND_NAT_DED + CNPJ`.

**Observação importante:** `ST — Não Ocorrência do Fato Gerador Presumido` (Indicador 04) refere-se ao direito à restituição quando a PJ paga PIS/COFINS por substituição tributária para frente e o fato gerador presumido não se realiza (STF, Tema 228). **Área de oportunidade tributária relevante** especialmente para setor de combustíveis, bebidas e farmacêutico.

### 2.15 Registro `F800` — Créditos Decorrentes de Eventos de Incorporação, Fusão e Cisão

Nível 3, ocorrência 1:N. Créditos oriundos de eventos de sucessão (arts. 3º das Leis 10.637/2002 e 10.833/2003, Lei 10.865/2004 para importação), transferidos à PJ sucessora.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "F800" | C | 004* | – | S |
| 02 | `IND_NAT_EVEN` | 01 – Incorporação; 02 – Fusão; 03 – Cisão Total; 04 – Cisão Parcial; 99 – Outros | N | 002* | – | S |
| 03 | `DT_EVEN` | Data do evento (`ddmmaaaa`) | N | 008* | – | S |
| 04 | `CNPJ_SUCED` | CNPJ da PJ sucedida | N | 014* | – | S |
| 05 | `PA_CONT_CRED` | Período de apuração do crédito original (`mmaaaa`) | N | 006* | – | S |
| 06 | `COD_CRED` | Código do tipo de crédito transferido (tabela 4.3.6) | N | 003* | – | S |
| 07 | `VL_CRED_PIS` | Crédito de PIS transferido | N | – | 02 | S |
| 08 | `VL_CRED_COFINS` | Crédito de COFINS transferido | N | – | 02 | S |
| 09 | `PER_CRED_CIS` | Percentual do crédito transferido (apenas em cisão) | N | 006 | 02 | N |

**Regra:** os créditos são transferidos **sob as mesmas condições** em que foram apurados na sucedida. Se da PJ sucedida o crédito era vinculado a exportação, continua sendo vinculado a exportação na sucessora (com direito a compensação/ressarcimento).

---

## 3. Bloco I — Instituições Financeiras e Equiparadas (visão geral)

### 3.1 Natureza do bloco

O Bloco I é destinado à escrituração específica de operações das **instituições financeiras e equiparadas, seguradoras, entidades de previdência privada e operadoras de planos de assistência à saúde**, em decorrência da Lei 9.718/98, do art. 3º da Lei 9.701/98 e demais normas do regime cumulativo próprio dessas PJs.

### 3.2 Aplicabilidade

- Bancos comerciais, bancos de investimento, bancos de desenvolvimento, caixas econômicas
- Sociedades de crédito, financiamento e investimento
- Sociedades de crédito imobiliário e arrendamento mercantil
- Cooperativas de crédito
- Empresas de seguros privados
- Entidades de previdência privada (abertas e fechadas)
- Operadoras de planos de assistência à saúde
- Sociedades corretoras
- Distribuidoras de títulos e valores mobiliários
- Empresas de câmbio

### 3.3 Tabela do Bloco I (visão geral)

| Registro | Descrição |
|:---:|---|
| `I001` | Abertura do Bloco I |
| `I010` | Identificação da PJ em Situação Especial |
| `I100` | Consolidação das Operações do Período |
| `I199` | Processo Referenciado |
| `I200` | Complemento das Operações do Período |
| `I299` | Processo Referenciado |
| `I300` | Detalhamento das Operações do Período |
| `I399` | Processo Referenciado |
| `I990` | Encerramento do Bloco I |

### 3.4 Status para o sistema Primetax

**Fora do escopo primário da primeira iteração** do sistema de cruzamento Primetax, tendo em vista que:

1. O regime das instituições financeiras é majoritariamente **cumulativo**, com regras próprias de apuração e exclusões de base (art. 3º, §§ 6º e 9º, da Lei 9.718/98 e Lei 9.701/98)
2. O foco da Primetax — conforme contexto do projeto — é recuperação de **PIS/COFINS não-cumulativos**, especialmente da tese do ICMS (RE 574.706) e créditos mal aproveitados
3. Auditorias em instituições financeiras exigem especialização contábil distinta (marcação a mercado, spread bancário, receita de intermediação)

Deve o sistema:

- **Reconhecer** registros do Bloco I durante o parsing
- **Sinalizar** quando uma EFD-Contribuições contenha registros do Bloco I
- **Não processar** cruzamentos específicos do Bloco I na primeira fase — retornar apenas inventário

Em uma **fase futura** do projeto, a Primetax pode desenvolver módulo específico para clientes do segmento, com regras próprias.

---

## 4. Cruzamentos primários derivados desta Parte 2

Com base nos registros detalhados acima, o motor de cruzamento da Primetax deve implementar ao menos os seguintes testes:

### 4.1 Cruzamentos do Bloco D

1. **Integridade D100 × D101 × D105:** para cada `D100`, deve existir ao menos um `D101` e um `D105` filhos. Base agregada dos filhos deve ser consistente com o valor do serviço do pai.

2. **Reclassificação de `IND_NAT_FRT`:** identificar em `D101`/`D105` operações com `IND_NAT_FRT = 3` (compras não geradoras) em PJs cuja atividade **principal** é comércio/indústria — candidatas à reclassificação para `IND_NAT_FRT = 2` (geradoras).

3. **CST 70 em frete de insumo:** `D101.CST_PIS = 70` em documentos cujo `COD_ITEM` pai seja classificado como insumo no `0200.TIPO_ITEM` — auditoria obrigatória.

4. **Subcontratação de transporte:** para PJs de transporte rodoviário, verificar se `D101/D105` de subcontratação usam CST 60–66 e alíquotas especiais 1,2375%/5,7%.

### 4.2 Cruzamentos do Bloco F

5. **F100 com `NAT_BC_CRED = 13`:** listar todas as ocorrências e confrontar com o `DESC_CRED` do M105/M505 correspondente. Descrições genéricas ou ausentes indicam fragilidade probatória.

6. **Ativo imobilizado — otimização F120 × F130:**
   - Listar bens em F120 cuja data de aquisição seja posterior a 03/08/2011
   - Calcular valor do crédito se fossem escriturados em F130 com `IND_NR_PARC = 1` (integral)
   - Apresentar diferença como "crédito extemporâneo otimizável"

7. **F120/F130 com `IND_UTIL_BEM_IMOB = 9`:** bens classificados como "Outros" frequentemente podem ser reclassificados para 1/2/3 (atividade-fim) — auditoria caso a caso.

8. **F150 — consistência 12 parcelas:** para PJ que migrou de regime nos últimos 12 meses, verificar presença e integridade do F150. Se ausente e elegível, oportunidade de escrituração extemporânea.

9. **F600 não aproveitado em M200/M600:** soma de `F600.VL_RET_PIS` no período **vs.** valor deduzido em M200. Diferenças = crédito perdido.

10. **F600 × DIRF:** cruzar com DIRF da PJ beneficiária para identificar retenções **informadas pela fonte pagadora** mas **não escrituradas** em F600.

11. **F700 com Indicador 04 (ST não ocorrida):** identificar oportunidades de restituição de ST presumida quando o fato gerador não se realizou — dividendos da tese STF 228.

12. **F800 × registros de sucessão na ECD:** se há F800, conferir se ECD registra o evento de sucessão no período correspondente (J900/J930/J990). Divergências indicam inconsistência entre a EFD-Contribuições e a ECD.

### 4.3 Cruzamentos do Bloco I

13. **Inventário Bloco I:** sinalizar presença e listar clientes com escrituração do Bloco I para potencial desenvolvimento de módulo especializado em fase futura.

---

## 5. Referências normativas complementares desta Parte 2

- **Lei 10.485/2002** — Retenção na fonte por fabricantes de veículos e peças (aplicação no F600)
- **Lei 10.833/2003, arts. 3º, §§ 19–20** — Crédito presumido na subcontratação de transporte rodoviário
- **Lei 10.865/2004, art. 31** — Vedação de crédito sobre imobilizado anterior a maio/2004 (F120/F130)
- **Lei 12.546/2011 (conversão da MP 540/2011)** — Crédito integral em máquinas/equipamentos a partir de ago/2011 (F130 com `IND_NR_PARC = 1 ou 9`)
- **Lei 12.599/2012** — Crédito presumido na exportação de café (F100 com `NAT_BC_CRED = 13`)
- **Lei 12.865/2013** — Crédito presumido sobre derivados de soja, margarina, biodiesel (F100 com `NAT_BC_CRED = 13`)
- **Lei 9.430/96, arts. 64 e 66** — Retenção por órgãos públicos federais e recolhimento por sociedades cooperativas (F600)
- **MP 2.158-35/2001, art. 20** — Regime de caixa para Lucro Presumido (F500)
- **Lei 9.718/98 e Lei 9.701/98** — Regime das instituições financeiras (Bloco I)
- **STF, Tema 228 (ADI 2.675 e 2.777)** — Restituição de ICMS pago a maior na ST quando o fato gerador presumido não se realiza (analogia aplicável para PIS/COFINS ST — F700 com Indicador 04)

---

*Fim da Parte 2 de 3.*
