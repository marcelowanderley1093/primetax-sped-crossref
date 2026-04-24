# Layout da EFD-Contribuições — Parte 3 de 3

> **Documento-fonte:** Guia Prático da EFD-Contribuições, versão 1.35, atualizado em 18/06/2021, publicado pela Receita Federal do Brasil.
>
> **Parte 3 cobre:**
> - Bloco M completo (apuração da contribuição e do crédito): M100 detalhado (complementando Parte 1), M110/M115, M200, M205, M210, M211, M215, M220/M225, M230, M300, M350, M400/M410, e análogos M500/M505/M510/M515, M600, M605, M610, M611, M615, M620/M625, M630, M700, M800/M810
> - Bloco 1 integral (operações extemporâneas e controles): 1001, 1010, 1011, 1020, 1050, 1100, 1101, 1102, 1200, 1210, 1220, 1300, 1500, 1501, 1502, 1600, 1610, 1620, 1700, 1800, 1900, 1990
> - Bloco P (visão geral): CPRB
> - Bloco 9 (encerramento)
> - **Síntese final de cruzamentos consolidados** para o motor da Primetax
>
> **Parte 3 concentra os registros de maior valor estratégico para recuperação tributária:**
>
> 1. **M210 e M610** — detalhamento da contribuição apurada, ponto de aplicação dos ajustes de exclusão do ICMS (Tema 69) via `VL_AJUS_REDUC_BC`
> 2. **1100/1101/1102 (PIS) e 1500/1501/1502 (COFINS)** — **créditos extemporâneos**, área com prazo decadencial de 5 anos onde a Primetax pode recuperar créditos não aproveitados em competências passadas
> 3. **1300 (PIS) e 1700 (COFINS)** — controle de retenções na fonte, muitas vezes não deduzidas integralmente em M200/M600
> 4. **1010 e 1050** — registros vinculados a decisões judiciais com exigibilidade suspensa, essenciais para a operacionalização da tese do ICMS

---

## 1. Bloco M — Apuração da Contribuição e do Crédito (completo)

### 1.1 Arquitetura lógica do Bloco M

O Bloco M é o **coração da apuração**. Organiza-se em duas metades paralelas e simétricas:

- **Série M1xx–M4xx:** apuração de **PIS/Pasep** (crédito, débito, ajustes, diferimento, folha, isenções)
- **Série M5xx–M8xx:** apuração de **COFINS** (estrutura idêntica à PIS)

Fluxo lógico (replicado para PIS e COFINS):

```
Documentos dos Blocos A/C/D/F
           │
           ├──── CST de crédito (50–56, 60–66)
           │                │
           │                └──► M105/M505 (detalhamento da base) ──► M100/M500 (crédito apurado)
           │                                                                      │
           │                                                                      └──► M110/M115/M510/M515 (ajustes)
           │
           └──── CST de débito (01, 02, 03, 05)
                            │
                            └──► M210/M610 (detalhamento da contribuição)
                                           │
                                           ├──► M211/M611 (cooperativas)
                                           ├──► M215/M615 (ajustes de base)
                                           ├──► M220/M225/M620/M625 (ajustes da contribuição)
                                           └──► M230/M630 (diferimento)
                                                                      │
                                                                      ▼
                                         M200/M600 (consolidação do período)
                                                       │
                                                       ├──► M205/M605 (por código de receita DCTF)
                                                       └──► Deduz: créditos M100/M500, saldos 1100/1500, retenções F600/1300/1700, outras F700
```

Adicionalmente:
- **M300/M700:** diferimento de períodos anteriores (valores a pagar agora)
- **M350:** PIS sobre folha de salários (entidades sem fins lucrativos — Lei 9.718/98, art. 13)
- **M400/M410/M800/M810:** receitas isentas, não tributadas, alíquota zero, suspensão

### 1.2 Registros M100, M105 — já detalhados na Parte 1

Referência completa dos registros `M100` (Crédito de PIS/Pasep Relativo ao Período) e `M105` (Detalhamento da Base de Cálculo do Crédito) encontra-se na **Parte 1, seções 2.3 e 2.4**, incluindo:

- Estrutura dos 15 campos do M100 e 10 campos do M105
- Tabela de `COD_CRED` (códigos 101–399) da Tabela 4.3.6
- Tabela de `NAT_BC_CRED` (códigos 01–18) da Tabela 4.3.7
- Regras de rateio proporcional para CSTs 53/54/55/56/63/64/65/66 com exemplo numérico oficial do manual

### 1.3 Registro `M110` — Ajustes do Crédito de PIS/Pasep Apurado

Nível 3, ocorrência 1:N. Detalha os valores dos campos 09 (acréscimo) e 10 (redução) do M100.

**Uso obrigatório do M110 para:** devoluções de compras (a ser informado como **redução** — `IND_AJ = 0`), ajustes decorrentes de ação judicial, processo administrativo, mudanças na legislação, estornos, ou outras situações.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "M110" | C | 004* | – | S |
| 02 | `IND_AJ` | Tipo: 0 – Redução; 1 – Acréscimo | C | 001* | – | S |
| 03 | `VL_AJ` | Valor do ajuste | N | – | 02 | S |
| 04 | `COD_AJ` | Código do ajuste (tabela 4.3.8) | C | 002* | – | S |
| 05 | `NUM_DOC` | Número do processo/documento vinculado | C | – | – | N |
| 06 | `DESCR_AJ` | Descrição resumida do ajuste | C | – | – | N |
| 07 | `DT_REF` | Data de referência (`ddmmaaaa`) | N | 008* | – | N |

**Propagação:** soma de `VL_AJ` com `IND_AJ = 1` → `M100.VL_AJUS_ACRES`. Soma de `VL_AJ` com `IND_AJ = 0` → `M100.VL_AJUS_REDUC`.

### 1.4 Registro `M115` — Detalhamento dos Ajustes do Crédito de PIS/Pasep (a partir de out/2015)

Nível 4, ocorrência 1:N. **Disponibilizado para fatos geradores a partir de 01/10/2015** (versão 2.12 do PVA).

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "M115" | S |
| 02 | `DET_VALOR_AJ` | Valor detalhado do ajuste (fração do `M110.VL_AJ`) | S |
| 03 | `CST_PIS` | CST referente à operação ajustada | N |
| 04 | `DET_BC_CRED` | Base de cálculo geradora do ajuste | N |
| 05 | `DET_ALIQ` | Alíquota do ajuste | N |
| 06 | `DT_OPER_AJ` | Data da operação ajustada | S |
| 07 | `DESC_AJ` | Descrição das operações detalhadas | N |
| 08 | `COD_CTA` | Conta contábil (obrigatório desde nov/2017) | N |
| 09 | `INFO_COMPL` | Informação complementar | N |

> **Cruzamento Primext — ajustes de redução por devolução de compras:** para cada `M110` com `IND_AJ = 0` e `COD_AJ ∈ {01, 05, 06}`, verificar se há `C170` ou `C191` com CFOP de devolução (1.202, 1.411, 2.202, 2.411, etc.) no mesmo período. Ausência pode indicar ajuste lançado manualmente sem lastro documental.

### 1.5 Registro `M200` — Consolidação da Contribuição para o PIS/Pasep do Período

Nível 2, ocorrência 1 por arquivo, **obrigatório**. **Registro-síntese da apuração mensal do PIS/Pasep.**

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "M200" | C | – | S |
| 02 | `VL_TOT_CONT_NC_PER` | **Total da contribuição não-cumulativa do período** (soma do `M210.VL_CONT_PER` com `COD_CONT` ∈ {01, 02, 03, 04, 32, 71}) | N | 02 | S |
| 03 | `VL_TOT_CRED_DESC` | **Crédito descontado apurado no próprio período** (soma do `M100.VL_CRED_DESC`) | N | 02 | S |
| 04 | `VL_TOT_CRED_DESC_ANT` | **Crédito descontado de período anterior** (soma do `1100.VL_CRED_DESC_EFD`) | N | 02 | S |
| 05 | `VL_TOT_CONT_NC_DEV` | Contribuição NC devida (= 02 − 03 − 04) | N | 02 | S |
| 06 | `VL_RET_NC` | Retenção na fonte deduzida (regime NC) | N | 02 | S |
| 07 | `VL_OUT_DED_NC` | Outras deduções (soma de `F700.VL_DED_PIS` com `IND_NAT_DED = 0`) | N | 02 | S |
| 08 | `VL_CONT_NC_REC` | **Contribuição NC a recolher** (= 05 − 06 − 07) | N | 02 | S |
| 09 | `VL_TOT_CONT_CUM_PER` | **Total da contribuição cumulativa do período** (soma do `M210.VL_CONT_PER` com `COD_CONT` ∈ {31, 32, 51, 52, 53, 54, 72}) | N | 02 | S |
| 10 | `VL_RET_CUM` | Retenção na fonte deduzida (regime cumulativo) | N | 02 | S |
| 11 | `VL_OUT_DED_CUM` | Outras deduções (soma de `F700.VL_DED_PIS` com `IND_NAT_DED = 1`) | N | 02 | S |
| 12 | `VL_CONT_CUM_REC` | **Contribuição cumulativa a recolher** (= 09 − 10 − 11) | N | 02 | S |
| 13 | `VL_TOT_CONT_REC` | **Total da contribuição a recolher no período** (= 08 + 12) | N | 02 | S |

**ATENÇÃO — avisos críticos do manual:**

1. Os valores de **retenção na fonte** (Campos 06 e 10) e **outras deduções** (Campos 07 e 11) **NÃO são recuperados automaticamente** pela funcionalidade "Gerar Apurações" do PVA. Devem ser preenchidos pela própria PJ, correlacionados com registros `F600`, `1300` (PIS) ou `1700` (COFINS), e `F700`.

2. A soma `VL_TOT_CRED_DESC + VL_TOT_CRED_DESC_ANT` deve ser **menor ou igual** a `VL_TOT_CONT_NC_PER`. Não pode haver desconto superior ao débito.

3. `M200` é único no arquivo — sempre há um e apenas um registro M200 por escrituração.

**Exemplo oficial do manual (crédito apurado = 400, crédito de períodos anteriores usado = 400, débito do mês = 500):**

```
M100:  campo 08 = 400   (apurado)
       campo 12 = 400   (disponível)
       campo 13 = "1"   (aproveitamento parcial)
       campo 14 = 100   (descontado no período)
       campo 15 = 300   (saldo para período futuro)

M200:  campo 02 = 500   (débito NC)
       campo 03 = 100   (crédito do mês descontado)
       campo 04 = 400   (crédito de período anterior descontado)
       campo 05 = 0     (contribuição NC devida)

1100:  campo 02 = xx/yyyy  (período anterior)
       campo 06 = 2.000    (crédito apurado no período anterior)
       campo 08 = 2.000    (total)
       campo 13 = 400      (descontado na EFD atual)
       campo 18 = 1.600    (saldo para períodos futuros)
```

> **Cruzamentos primários centrados em M200:**
>
> 1. **Integridade vertical:** `M200.VL_TOT_CONT_NC_PER` = Σ `M210.VL_CONT_PER` onde `COD_CONT ∈ {01, 02, 03, 04, 32, 71}`. Divergência indica manipulação manual do M200 sem ajuste em M210.
>
> 2. **Retenções não deduzidas:** comparar `Σ F600.VL_RET_PIS` no período (com `IND_DEC = 0`) **vs.** `M200.VL_RET_NC + M200.VL_RET_CUM`. Se Σ F600 > M200 retido, há retenções não deduzidas — perda de crédito. Verificar saldo em `1300`.
>
> 3. **Outras deduções não computadas:** comparar `Σ F700.VL_DED_PIS` **vs.** `M200.VL_OUT_DED_NC + M200.VL_OUT_DED_CUM`. Divergência = dedução escriturada mas não aproveitada.
>
> 4. **Saldo futuro não declarado:** para cada `M100.SLD_CRED > 0`, conferir se há `1100` correspondente no período seguinte com `VL_CRED_APU` coerente. Ausência indica perda de carry-forward de crédito.

### 1.6 Registro `M205` — Contribuição para o PIS/Pasep a Recolher – Detalhamento por Código de Receita (DCTF)

Nível 3, ocorrência 1:N. **Obrigatório a partir de abril/2014** quando `M200.VL_CONT_NC_REC > 0` ou `M200.VL_CONT_CUM_REC > 0`.

Função: detalhar a contribuição a recolher dos Campos 08 (NC) e 12 (CUM) do M200 por **código de receita da DCTF** (composto de seis dígitos, não os quatro do DARF).

| # | Campo | Descrição | Tipo | Obrig |
|:---:|---|---|:---:|:---:|
| 01 | `REG` | "M205" | C | S |
| 02 | `NUM_CAMPO` | Nº do campo do M200 detalhado: `08` (NC) ou `12` (CUM) | C | S |
| 03 | `COD_REC` | Código da receita — 6 dígitos conforme DCTF (ADE Codac/RFB nº 36/2014) | C | S |
| 04 | `VL_DEBITO` | Valor do débito correspondente | N | S |

**Regra:** soma de `VL_DEBITO` no M205 deve ser igual ao valor de `M200.VL_CONT_NC_REC` + `M200.VL_CONT_CUM_REC` detalhado.

> **Cruzamento Primetax:** `M205.COD_REC × VL_DEBITO` **vs.** códigos e valores declarados na DCTF da PJ no mesmo período. Divergências indicam inconsistência entre EFD-Contribuições e DCTF — fragilidade em eventual autuação. A Primetax pode construir este cruzamento integrando com consulta e-CAC via mTLS certificate A1 (padrão já adotado no sistema e-CAC da Primetax).

### 1.7 Registro `M210` — Detalhamento da Contribuição para o PIS/Pasep do Período

Nível 3, ocorrência 1:N. **Registro de maior densidade semântica do Bloco M.** Um registro por **combinação única** de `COD_CONT + ALIQ_PIS + ALIQ_PIS_QUANT`, recuperando valores dos Blocos A, C, D, F.

**Leiaute aplicável a fatos geradores até 31/12/2018** (para 2019+ há versão ampliada com mais campos — verificar versão do arquivo):

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "M210" | C | – | S |
| 02 | `COD_CONT` | **Código da contribuição apurada (tabela 4.3.5)** | C | – | S |
| 03 | `VL_REC_BRT` | Valor da receita bruta | N | 02 | S |
| 04 | `VL_BC_CONT` | **Base de cálculo da contribuição** (recuperada de `VL_BC_PIS` dos Blocos A/C/D/F com mesmo CST) | N | 02 | S |
| 05 | `ALIQ_PIS` | Alíquota PIS (%) | N | 04 | N |
| 06 | `QUANT_BC_PIS` | Base em quantidade | N | 03 | N |
| 07 | `ALIQ_PIS_QUANT` | Alíquota em reais | N | 04 | N |
| 08 | `VL_CONT_APUR` | Valor total da contribuição apurada | N | 02 | S |
| 09 | `VL_AJUS_ACRES` | Ajustes de acréscimo (soma de `M220` com `IND_AJ = 1`) | N | 02 | S |
| 10 | `VL_AJUS_REDUC` | Ajustes de redução (soma de `M220` com `IND_AJ = 0`) | N | 02 | S |
| 11 | `VL_CONT_DIFER` | Contribuição a diferir no período | N | 02 | N |
| 12 | `VL_CONT_DIFER_ANT` | Contribuição diferida em períodos anteriores (recuperada no atual) | N | 02 | N |
| 13 | `VL_CONT_PER` | **Contribuição do período** (= 08 + 09 − 10 − 11 + 12) | N | 02 | S |

**Obrigatoriedade do M210:** se existirem registros nos Blocos A, C, D ou F com CST ∈ {01, 02, 03, 05}.

**Leiaute ampliado (fatos geradores a partir de 2019) — campos adicionais:**

- `VL_AJUS_ACRES_BC_PIS`, `VL_AJUS_REDUC_BC_PIS` — ajustes **na base de cálculo** antes da aplicação da alíquota (essencial para o ajuste do ICMS)
- `VL_BC_CONT_AJUS` — base ajustada
- Separação granular entre ajustes de base e ajustes do valor apurado

> **Uso central para a Primetax — operacionalização do Tema 69 em M210:**
>
> A partir de 2019, a exclusão do ICMS pode ser operacionalizada via **ajuste de redução na base de cálculo mensal**, usando `VL_AJUS_REDUC_BC_PIS` (e o detalhamento obrigatório em `M215`). Para fatos geradores **anteriores a 2019**, o ajuste deve ser feito **item a item** nos registros de origem (C170.VL_DESC ou redução direta em C381/C385/C481/C485/C491/C495/C601/C605/F500/F550 — ver Tabela da Seção 12 na Parte 1).
>
> **Regra operacional crítica:** se a PJ tem ação judicial protocolada **até 15/03/2017** autorizando a exclusão retroativa, os ajustes para períodos anteriores a 2019 devem ser feitos **diretamente nos documentos originais** via EFD-Contribuições retificadora, não em M215/M615. Tentar ajustar em M215 para períodos anteriores a 2019 é **erro de operacionalização** que pode levar à glosa.

### 1.8 Tabela 4.3.5 — Código de Contribuição Social Apurada (`COD_CONT`)

Utilizada no `COD_CONT` do M210/M610. Combinação chave para o PVA gerar o M210 automaticamente: **CST da receita + `COD_INC_TRIB` do registro 0110 + alíquota**.

**Grupo Não-Cumulativo (1x):**

| Código | Descrição |
|:---:|---|
| **01** | Apuração não-cumulativa com alíquota básica (1,65% PIS / 7,6% COFINS) |
| **02** | Apuração não-cumulativa com alíquotas específicas (diferenciadas) |
| **03** | Apuração não-cumulativa com alíquota por unidade de medida |
| **04** | Apuração não-cumulativa da SCP |

**Grupo Cumulativo (3x e 5x):**

| Código | Descrição |
|:---:|---|
| **31** | Apuração cumulativa com alíquota básica (0,65% PIS / 3,0% COFINS) |
| **32** | Apuração cumulativa/não-cumulativa de SCP |
| **51** | Apuração cumulativa com alíquotas específicas |
| **52** | Apuração cumulativa por unidade de medida |
| **53** | Apuração cumulativa com alíquotas específicas da ZFM |
| **54** | Apuração cumulativa de bebidas frias |

**Grupo SCP (7x):**

| Código | Descrição |
|:---:|---|
| **71** | SCP — Regime Não-Cumulativo |
| **72** | SCP — Regime Cumulativo |

### 1.9 Registro `M211` — Sociedades Cooperativas – Composição da Base – PIS/Pasep

Nível 4, ocorrência 1:1. **Obrigatório se `0000.IND_NAT_PJ = 01`** (sociedade cooperativa).

Detalha as exclusões da base de cálculo aplicáveis exclusivamente às cooperativas (Lei 9.532/97, art. 93; Lei 10.676/03; MP 2.158-35/01, art. 15 e 16).

Campos principais: `VL_BC_CONT`, `VL_EXC_COOP_GER` (exclusão geral cooperativas), `VL_EXC_ESP_COOP` (exclusões específicas), `VL_BC_CONT_AJUS`.

### 1.10 Registro `M215` — Detalhamento dos Ajustes da Base de Cálculo Mensal do PIS/Pasep

Nível 4, ocorrência 1:N. **Obrigatório quando M210 tiver `VL_AJUS_ACRES_BC_PIS > 0` ou `VL_AJUS_REDUC_BC_PIS > 0`** (campos do leiaute ampliado, fatos geradores a partir de 2019).

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "M215" |
| 02 | `IND_AJ_BC` | 0 – Redução; 1 – Acréscimo |
| 03 | `VL_AJ_BC` | Valor do ajuste |
| 04 | `COD_AJ_BC` | Código do ajuste (tabela 4.3.18) |
| 05 | `NUM_DOC` | Número do processo/documento |
| 06 | `DESCR_AJ_BC` | Descrição |
| 07 | `DT_REF` | Data de referência |
| 08 | `COD_CTA` | Conta contábil |
| 09 | `CNPJ` | CNPJ do estabelecimento |
| 10 | `INFO_COMPL` | Informação complementar |

> **Uso central para a Primetax — ajuste da base via Tema 69:** a partir de 2019, o ajuste mensal de redução da base pela exclusão do ICMS pode ser escriturado em M215/M615 com `COD_AJ_BC` específico da Tabela 4.3.18. A PGFN vinha recomendando códigos específicos — verificar a versão atual da Tabela 4.3.18 no portal SPED.
>
> **Cruzamento crítico:** `Σ M215.VL_AJ_BC` com `IND_AJ_BC = 0` no período deve ser igual à parcela de ICMS excluída da base — que por sua vez deve bater com `Σ VL_ICMS` dos `C170` da mesma competência (com CST de débito).

### 1.11 Registro `M220` — Ajustes da Contribuição para o PIS/Pasep Apurada

Nível 4, ocorrência 1:N. Ajustes **sobre o valor apurado da contribuição** (não sobre a base de cálculo).

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "M220" | S |
| 02 | `IND_AJ` | 0 – Redução; 1 – Acréscimo | S |
| 03 | `VL_AJ` | Valor do ajuste | S |
| 04 | `COD_AJ` | Código (tabela 4.3.8) | S |
| 05 | `NUM_DOC` | Nº do processo/documento | N |
| 06 | `DESCR_AJ` | Descrição | N |
| 07 | `DT_REF` | Data de referência | N |

### 1.12 Registro `M225` — Detalhamento dos Ajustes da Contribuição (a partir de out/2015)

Nível 5, ocorrência 1:N. Análogo ao M115 (detalhamento do M110), mas para ajustes do valor apurado. Mesma estrutura do M115 (9 campos).

### 1.13 Registro `M230` — Informações Adicionais de Diferimento

Nível 4, ocorrência 1:N. Detalha a contribuição diferida prevista em M210.VL_CONT_DIFER, aplicável a:

- **Contratos com pessoa jurídica de direito público** (parágrafo único e caput do art. 7º da Lei 9.718/98)
- Receitas de construção por empreitada ou fornecimento a preço predeterminado

### 1.14 Registro `M300` — PIS/Pasep Diferido em Períodos Anteriores a Pagar no Período

Nível 2, ocorrência V. Registra parcelas de contribuição diferida em períodos anteriores que estão vencendo no período atual (receita foi recebida — o fato gerador antes diferido se concretiza).

### 1.15 Registro `M350` — PIS/Pasep sobre Folha de Salários

Nível 2, ocorrência 1. **Aplicável a entidades sem fins lucrativos** que calculam PIS sobre folha de salários (alíquota 1%) conforme art. 13 da Lei 9.718/98, não sobre faturamento.

Campos principais: `VL_TOT_FOL` (total da folha), `VL_EXC_BC` (exclusões), `VL_TOT_BC` (base), `ALIQ_PIS_FOL` (1,00), `VL_TOT_CONT_FOL`.

> **Nota Primetax:** empresas que em algum momento usaram M350 indevidamente (por exemplo, entidade com fim lucrativo que erroneamente tributou PIS sobre folha) podem ter crédito de restituição. Cruzar com `0000.IND_NAT_PJ` e verificar cabimento.

### 1.16 Registros `M400` e `M410` — Receitas Isentas / Alíquota Zero / Suspensão – PIS/Pasep

`M400`: nível 2, ocorrência V. Consolida receitas não sujeitas ao pagamento da contribuição, segregadas por CST (04, 06, 07, 08, 09).

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "M400" | S |
| 02 | `CST_PIS` | CST (04, 06, 07, 08, 09) | S |
| 03 | `VL_TOT_REC` | Receita bruta total no período referente a esse CST | S |
| 04 | `COD_CTA` | Conta contábil | N |
| 05 | `DESC_COMPL` | Descrição complementar | N |

**Recuperação automática:** `VL_TOT_REC` é somatório dos campos `VL_ITEM` dos registros A170, C170 (com `COD_MOD ≠ 55` ou condicional), C181, C491, C481, C381, C601, D201, D601, `VL_DOC` do D300, `VL_BRT` do D350, `VL_OPR` do C175, `VL_OPER` do F100 (com `IND_OPER ∈ {1, 2}`), `VL_TOT_REC` do F200, `VL_REC_CAIXA` dos F500/F510, `VL_REC_COMP` dos F550/F560, `VL_REC` do I100.

`M410`: nível 3, ocorrência 1:N. **Detalhamento obrigatório** do M400. **Não é preenchido automaticamente** pelo PVA — a PJ deve preencher manualmente, vinculando cada receita a um código de natureza específica (tabelas 4.3.13 a 4.3.17).

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "M410" |
| 02 | `NAT_REC` | Código da natureza da receita (tabelas 4.3.13 a 4.3.17) |
| 03 | `VL_REC` | Valor da receita |
| 04 | `COD_CTA` | Conta contábil |
| 05 | `DESC_COMPL` | Descrição complementar |

### 1.17 Registros `M500`, `M505`, `M510`, `M515` — Crédito de COFINS (estrutura idêntica à PIS)

Estrutura análoga aos `M100`/`M105`/`M110`/`M115`, trocando PIS → COFINS em todos os campos. Alíquota básica no regime não-cumulativo: **7,6%** (vs. 1,65% no PIS).

### 1.18 Registros `M600`, `M605`, `M610` — Apuração da COFINS

Estrutura **idêntica** aos `M200`/`M205`/`M210` para COFINS:

- `M600` — consolidação com os mesmos 13 campos do M200 (trocando PIS → COFINS; alíquotas 3,0% cumulativo e 7,6% não-cumulativo)
- `M605` — detalhamento por código de receita DCTF (obrigatório desde abr/2014)
- `M610` — detalhamento da contribuição com os mesmos campos do M210

**Códigos de contribuição no M610** seguem a mesma tabela 4.3.5 do M210.

### 1.19 Registros `M611`, `M615`, `M620`, `M625`, `M630` — Análogos ao M211–M230 para COFINS

Estrutura idêntica à série M2xx, trocando PIS → COFINS. Todas as regras de obrigatoriedade e propagação se aplicam identicamente.

### 1.20 Registro `M700` — COFINS Diferida em Períodos Anteriores a Pagar

Análogo ao M300 para COFINS.

### 1.21 Registros `M800` e `M810` — Receitas Isentas/Alíquota Zero/Suspensão – COFINS

Análogos aos M400/M410 para COFINS.

---

## 2. Bloco 1 — Operações Extemporâneas, Ações Judiciais, Controle de Saldos

### 2.1 Visão geral do Bloco 1

O Bloco 1 é o bloco de **complementos, controles e operações extemporâneas**. Concentra alguns dos registros **mais estratégicos** para recuperação tributária da Primetax:

- **1010/1011/1020:** processos judiciais e administrativos referenciados (essenciais para comprovar legitimidade de ajustes na base de cálculo)
- **1050:** ajustes de base de cálculo de natureza "extra-apuração" (a partir de jan/2019) — usado para operacionalizar **teses judiciais** de redução de base
- **1100/1500:** controle de saldos de créditos de períodos anteriores — onde **créditos não aproveitados tempestivamente** podem ser recuperados
- **1101/1501 e 1102/1502:** apuração de **crédito extemporâneo** — mas com regras restritivas (ver nota abaixo)
- **1200/1600:** contribuição social **extemporânea** (débitos)
- **1300/1700:** controle de **retenções na fonte** — saldos a aproveitar em períodos futuros
- **1800:** Regime Especial Tributário da Incorporação Imobiliária (RET)
- **1900:** consolidação de documentos emitidos por PJ Lucro Presumido

### 2.2 Tabela do Bloco 1

| Registro | Descrição | Nível | Obrig. |
|:---:|---|:---:|---|
| `1001` | Abertura do Bloco 1 | 1 | O |
| `1010` | **Processo Referenciado – Ação Judicial** | 2 | OC |
| `1011` | Detalhamento das Contribuições com Exigibilidade Suspensa (a partir de jan/2020) | 3 | OC |
| `1020` | Processo Referenciado – Processo Administrativo | 2 | OC |
| `1050` | **Detalhamento de Ajustes de Base de Cálculo – Valores Extra Apuração** (a partir de jan/2019) | 2 | OC |
| `1100` | **Controle de Créditos Fiscais – PIS/Pasep** | 2 | OC |
| `1101` | Apuração de Crédito Extemporâneo – PIS/Pasep | 3 | OC |
| `1102` | Detalhamento do Crédito Extemporâneo Vinculado a Mais de um Tipo de Receita – PIS/Pasep | 4 | OC |
| `1200` | Contribuição Social Extemporânea – PIS/Pasep | 2 | OC |
| `1210` | Detalhamento da Contribuição Social Extemporânea – PIS/Pasep | 3 | OC |
| `1220` | Demonstração do Crédito a Descontar da Contribuição Extemporânea – PIS/Pasep | 3 | OC |
| `1300` | **Controle dos Valores Retidos na Fonte – PIS/Pasep** | 2 | OC |
| `1500` | **Controle de Créditos Fiscais – COFINS** | 2 | OC |
| `1501` | Apuração de Crédito Extemporâneo – COFINS | 3 | OC |
| `1502` | Detalhamento do Crédito Extemporâneo Vinculado a Mais de um Tipo de Receita – COFINS | 4 | OC |
| `1600` | Contribuição Social Extemporânea – COFINS | 2 | OC |
| `1610` | Detalhamento da Contribuição Social Extemporânea – COFINS | 3 | OC |
| `1620` | Demonstração do Crédito a Descontar da Contribuição Extemporânea – COFINS | 3 | OC |
| `1700` | Controle dos Valores Retidos na Fonte – COFINS | 2 | OC |
| `1800` | Incorporação Imobiliária – RET | 2 | OC |
| `1809` | Processo Referenciado | 3 | OC |
| `1900` | Consolidação dos Documentos Emitidos no Período por PJ Lucro Presumido | 2 | OC |
| `1990` | Encerramento do Bloco 1 | 1 | O |

### 2.3 Registro `1010` — Processo Referenciado – Ação Judicial

Nível 2, ocorrência V. Detalha cada ação judicial cujos efeitos tributários impactem a apuração do período.

| # | Campo | Descrição | Tipo | Tam | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "1010" | C | 004* | S |
| 02 | `NUM_PROC` | Número do processo judicial | C | 020 | S |
| 03 | `ID_SEC_JUD` | Identificação da seção judiciária | C | – | S |
| 04 | `ID_VARA` | Identificação da vara | C | 002 | S |
| 05 | `IND_NAT_ACAO` | **Natureza da ação judicial** (ver tabela abaixo) | C | 002* | S |
| 06 | `DESC_DEC_JUD` | Descrição resumida dos efeitos tributários da decisão (inclui, para ações sem trânsito em julgado, valores com exigibilidade suspensa) | C | 100 | N |
| 07 | `DT_SENT_JUD` | Data da sentença/decisão (`ddmmaaaa`) | N | 008* | N |

**Tabela do `IND_NAT_ACAO` (ações sem exigibilidade suspensa):**

| Código | Descrição |
|:---:|---|
| **01** | Decisão judicial **transitada em julgado** a favor da PJ |
| **02** | Decisão judicial **não transitada em julgado** a favor da PJ |
| **03** | Liminar em mandado de segurança |
| **04** | Liminar em medida cautelar |
| **05** | Antecipação de tutela |
| **06** | Depósito administrativo ou judicial em montante integral |
| **07** | Medida judicial em que a PJ não é o autor |
| **08** | Súmula vinculante do STF ou STJ |
| **09** | Liminar em mandado de segurança coletivo |
| **99** | Outros |

**Tabela do `IND_NAT_ACAO` (códigos com exigibilidade suspensa — vigentes a partir de jan/2020):**

| Código | Descrição |
|:---:|---|
| **12** | Decisão não transitada em julgado – **Exigibilidade suspensa** |
| **13** | Liminar em mandado de segurança – Exigibilidade suspensa |
| **14** | Liminar em medida cautelar – Exigibilidade suspensa |
| **15** | Antecipação de tutela – Exigibilidade suspensa |
| **16** | Depósito integral – Exigibilidade suspensa |
| **17** | Medida judicial não autora da PJ – Exigibilidade suspensa |
| **19** | Liminar em mandado coletivo – Exigibilidade suspensa |

**Regra crítica do manual:** "A apuração mediante escrituração de valores, alíquotas ou CST diversos dos definidos pela legislação tributária, tendo por lastro decisão judicial, **só devem ser considerados na apuração caso a decisão judicial correspondente esteja com trânsito em julgado**."

Para ações **sem trânsito em julgado** mas com exigibilidade suspensa, a PJ deve:

1. Apurar a contribuição conforme legislação regular (inclusive a parcela com exigibilidade suspensa)
2. Informar no Campo 06 (`DESC_DEC_JUD`) a parcela suspensa
3. **A partir de jan/2020**, detalhar no registro filho **1011** a parcela suspensa
4. Destacar o mesmo valor na **DCTF**

**Exemplo oficial do manual** (contribuição com exigibilidade suspensa: PIS R$ 10.000,00 + COFINS R$ 18.000,00):

```
|1010|xxxxxxx-xx.2016.1.00.0000|TRF3|10|02|6912/01=R$10.000,00 e 5856/01=R$18.000,00|20032019|
```

> **Uso central para a Primetax — operacionalização da Tese 69 via Bloco 1:**
>
> **Cenário 1: PJ com decisão transitada em julgado antes de 15/03/2017** → aplicação direta da exclusão em todos os períodos, sem necessidade do 1010 salvo para lastro documental.
>
> **Cenário 2: PJ com ação ajuizada até 15/03/2017 mas sem trânsito** → usa `IND_NAT_ACAO = 02` ou (preferencialmente) `IND_NAT_ACAO = 12` (a partir de 2020), obrigatoriamente com 1011, declarando os valores com exigibilidade suspensa.
>
> **Cenário 3: PJ sem ação judicial prévia, ajustes apenas a partir de 16/03/2017** → não precisa de 1010 (conforme Parecer SEI 7698/2021/ME), pois a exclusão é reconhecida administrativamente. Os ajustes são operacionalizados diretamente nos registros fonte (ver Seção 12 na Parte 1).
>
> **Cruzamento Primetax:** para cada ajuste de redução escriturado em M110/M215/M510/M615 (e respectivos M115/M515/M615) com `COD_AJ = 01` (Ação Judicial), deve haver correspondente `1010` no mesmo arquivo. Ausência de 1010 com `COD_AJ = 01` = fragilidade em fiscalização.

### 2.4 Registro `1011` — Detalhamento das Contribuições com Exigibilidade Suspensa

Nível 3, ocorrência 1:N. **Obrigatório a partir de jan/2020** para cada `1010` com `IND_NAT_ACAO ∈ {12, 13, 14, 15, 16, 17, 19}`.

Detalha por **código de receita DCTF** (mesmo padrão de 6 dígitos do M205/M605) o valor com exigibilidade suspensa.

Campos principais: `REG`, `NUM_CAMPO` (referência ao campo do M200/M600), `COD_REC`, `VL_CONT_SUSP`.

### 2.5 Registro `1020` — Processo Referenciado – Processo Administrativo

Nível 2, ocorrência V. Análogo ao 1010, mas para processos administrativos.

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "1020" |
| 02 | `NUM_PROC` | Número do processo administrativo |
| 03 | `IND_PROC` | Origem: 1 – Justiça Federal; 3 – RFB; 9 – Outros |

### 2.6 Registro `1050` — Detalhamento de Ajustes de Base de Cálculo – Valores Extra Apuração

Nível 2, ocorrência 1:N. **Registro específico a partir de jan/2019** (versão 3.1.0 do leiaute).

**Função crítica:** demonstrar de forma segregada, por CST, os valores de ajustes (acréscimo ou redução) da base de cálculo entre as diversas bases de contribuição. É o **registro-pai** para correspondência com `M215` (PIS) e `M615` (COFINS).

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "1050" | S |
| 02 | `DT_REF` | Data de referência (`ddmmaaaa`) | S |
| 03 | `IND_AJ_BC` | Natureza do ajuste (tabela 4.3.18) | S |
| 04 | `CNPJ` | CNPJ do estabelecimento | S |
| 05 | `VL_AJ_TOT` | Valor total do ajuste | S |
| 06 | `VL_AJ_CST01` | Parcela do ajuste referente ao CST 01 | S |
| 07 | `VL_AJ_CST02` | Parcela ajuste referente ao CST 02 | S |
| 08 | `VL_AJ_CST03` | Parcela ajuste referente ao CST 03 | S |
| 09 | `VL_AJ_CST04` | Parcela ajuste referente ao CST 04 | S |
| 10 | `VL_AJ_CST05` | Parcela ajuste referente ao CST 05 | S |
| 11 | `VL_AJ_CST06` | Parcela ajuste referente ao CST 06 | S |
| 12 | `VL_AJ_CST07` | Parcela ajuste referente ao CST 07 | S |
| 13 | `VL_AJ_CST08` | Parcela ajuste referente ao CST 08 | S |
| 14 | `VL_AJ_CST09` | Parcela ajuste referente ao CST 09 | S |
| 15 | `VL_AJ_CST49` | Parcela ajuste referente ao CST 49 | S |
| 16 | `VL_AJ_CST99` | Parcela ajuste referente ao CST 99 | S |
| 17 | `IND_APROP` | 01 – PIS e COFINS; 02 – Somente PIS; 03 – Somente COFINS | S |
| 18 | `NUM_REC` | Nº do recibo da escrituração ajustada (útil para ajustes retroativos) | N |
| 19 | `INFO_COMPL` | Informação complementar | N |

**Regra excepcional (observação 6 do manual):** "Excepcionalmente na escrituração referente a **janeiro de 2019**, poderá a PJ demonstrar valores de ajustes de redução (ou acréscimo) da base de cálculo mensal **referentes aos períodos de apuração ocorridos até 31/12/2018** (...), decorrente de processo judicial que autoriza o ajuste da base ou decorrente de disposição legal."

> **Uso estratégico Primetax:** o registro 1050 permite, em tese, **regularizar ajustes retroativos** da base de cálculo sem necessidade de retificar cada EFD-Contribuições histórica uma por uma. Contudo, a janela excepcional do manual foi **apenas para a escrituração de jan/2019**. Para períodos posteriores, retroatividade = retificação individual de cada escrituração.

### 2.7 Registro `1100` — Controle de Créditos Fiscais – PIS/Pasep

Nível 2, ocorrência V. **Registro fundamental para o controle de créditos ao longo do tempo.** Um registro para **cada combinação de período de apuração + origem + CNPJ sucedido + código de crédito** com saldo.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "1100" | C | 004* | – | S |
| 02 | `PER_APU_CRED` | **Período de apuração do crédito** (`mmaaaa`) — deve ser o mesmo ou anterior ao da escrituração atual | N | 006 | – | S |
| 03 | `ORIG_CRED` | Origem: 01 – Operações próprias; 02 – Crédito transferido por PJ sucedida | N | 002* | – | S |
| 04 | `CNPJ_SUC` | CNPJ da PJ sucedida (se `ORIG_CRED = 02`) | N | 014* | – | N |
| 05 | `COD_CRED` | Código do tipo de crédito (tabela 4.3.6) | N | 003* | – | S |
| 06 | `VL_CRED_APU` | Valor do crédito apurado na EFD (`M100.VL_CRED_DISP`) ou no DACON (Fichas 06A/06B) do período original | N | – | 02 | S |
| 07 | `VL_CRED_EXT_APU` | **Valor do crédito extemporâneo apurado** (`1101`), referente ao `PER_APU_CRED` informado | N | – | 02 | N |
| 08 | `VL_TOT_CRED_APU` | Total apurado (= 06 + 07) | N | – | 02 | S |
| 09 | `VL_CRED_DESC_PA_ANT` | Crédito utilizado por desconto em períodos anteriores | N | – | 02 | S |
| 10 | `VL_CRED_PER_PA_ANT` | Crédito utilizado por Pedido de Ressarcimento em períodos anteriores | N | – | 02 | N |
| 11 | `VL_CRED_DCOMP_PA_ANT` | Crédito utilizado por DCOMP em períodos anteriores | N | – | 02 | N |
| 12 | `SD_CRED_DISP_EFD` | **Saldo disponível para uso neste período** (= 08 − 09 − 10 − 11) | N | – | 02 | S |
| 13 | `VL_CRED_DESC_EFD` | **Crédito descontado nesta escrituração** (propaga para `M200.VL_TOT_CRED_DESC_ANT`) | N | – | 02 | N |
| 14 | `VL_CRED_PER_EFD` | Crédito pedido em ressarcimento nesta escrituração | N | – | 02 | N |
| 15 | `VL_CRED_DCOMP_EFD` | Crédito usado em DCOMP nesta escrituração | N | – | 02 | N |
| 16 | `VL_CRED_TRANS` | Crédito transferido em evento de cisão/fusão/incorporação | N | – | 02 | N |
| 17 | `VL_CRED_OUT` | Crédito utilizado por outras formas | N | – | 02 | N |
| 18 | `SLD_CRED_FIM` | **Saldo de créditos para períodos futuros** (= 12 − 13 − 14 − 15 − 16 − 17) | N | – | 02 | N |

**Regras críticas:**

1. **Granularidade temporal:** deve haver **um registro 1100 por mês** de períodos passados com saldo passível de utilização. **Não agregar ou englobar saldos de meses distintos.**

2. Campos 10 e 11 (Ressarcimento e DCOMP em períodos anteriores) **só podem ser preenchidos** se `COD_CRED ∈ {201, 202, 203, 204, 208, 301, 302, 303, 304, 307, 308}` — créditos dos grupos 200 (receita não tributada) e 300 (exportação), que admitem ressarcimento.

3. Créditos do **grupo 100** (receita tributada) são apenas descontáveis da própria contribuição, **não** são ressarcíveis.

### 2.8 Registro `1101` — Apuração de Crédito Extemporâneo – Documentos e Operações de Períodos Anteriores – PIS/Pasep

Nível 3, ocorrência 1:N.

**ATENÇÃO — aviso crucial do manual sobre limitação de uso:**

> "Os registros para informação extemporânea de créditos (1101, 1102, 1501, 1502) e de contribuições (1200, 1210, 1220, 1600, 1610, 1620) tinham justificativa de escrituração **apenas para fatos geradores ocorridos até 31/07/2013**, quando o prazo de retificação da EFD-Contribuições ainda era restrito.
>
> Com o novo disciplinamento da IN RFB 1.387/2013, que permite a retificação no prazo decadencial de **5 anos**, **deixa de ter fundamento de aplicabilidade e validade** os referidos registros a partir de agosto/2013.
>
> **Na prática:** o PVA nas versões em produção não valida nem permite a geração de registros de operação extemporânea para períodos de apuração a partir de agosto/2013. A regra correta é **retificar a escrituração original** do período em que o documento/operação deveria ter sido escriturado."

**Consequência operacional para a Primetax:**

- **Para créditos de jul/2013 ou antes:** pode-se usar 1101/1501 se ainda não decaído (improvável em 2026).
- **Para créditos de ago/2013 em diante:** deve-se retificar a EFD-Contribuições original do período. O PVA **rejeita** 1101 para esses períodos.
- **Exceção:** a escrituração do próprio crédito no período em que é descoberto (sem retificação) via `1100` com `PER_APU_CRED` anterior e `VL_CRED_EXT_APU = 0` é **inviável** — o 1100 requer que o crédito tenha sido apurado ou retificado no período-origem.

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "1101" | S |
| 02 | `COD_PART` | Código do participante | N |
| 03 | `COD_ITEM` | Código do item | N |
| 04 | `COD_MOD` | Modelo do documento | N |
| 05 | `SER` | Série | N |
| 06 | `SUB_SER` | Subsérie | N |
| 07 | `NUM_DOC` | Número do documento | N |
| 08 | `DT_OPER` | Data da operação | S |
| 09 | `CHV_NFE` | Chave da NF-e (44 dígitos) | N |
| 10 | `VL_OPER` | Valor da operação | S |
| 11 | `CFOP` | CFOP | N |
| 12 | `NAT_BC_CRED` | Natureza da base de crédito (tabela 4.3.7) | S |
| 13 | `IND_ORIG_CRED` | 0 – Mercado Interno; 1 – Importação | S |
| 14 | `CST_PIS` | CST-PIS | S |
| 15 | `VL_BC_PIS` | Base de cálculo (em valor ou quantidade) | S |
| 16 | `ALIQ_PIS` | Alíquota | S |
| 17 | `VL_PIS` | Valor do crédito | S |
| 18 | `COD_CTA` | Conta contábil | N |
| 19 | `COD_CCUS` | Centro de custos | N |
| 20 | `DESC_COMPL` | Descrição complementar | N |
| 21 | `PER_ESCRIT` | Mês/ano da escrituração original (apropriação direta) | N |
| 22 | `CNPJ` | CNPJ do estabelecimento gerador | S |

**Propagação:** soma de `VL_PIS` dos 1101 vinculados deve ser igual a `1100.VL_CRED_EXT_APU` quando CST ∈ {50, 51, 52, 60, 61, 62}. Para CST ∈ {53, 54, 55, 56, 63, 64, 65, 66}, a propagação é via 1102.

### 2.9 Registro `1102` — Detalhamento do Crédito Extemporâneo Vinculado a Mais de um Tipo de Receita – PIS/Pasep

Nível 4, ocorrência 1:N. Obrigatório quando `1101.CST_PIS ∈ {53, 54, 55, 56, 63, 64, 65, 66}`.

Campos principais: `REG`, `VL_CRED_PIS_TRIB_MI`, `VL_CRED_PIS_NT_MI`, `VL_CRED_PIS_EXP` — segregando a parcela do crédito extemporâneo por tipo de receita (análogo ao M105 para créditos do período corrente).

### 2.10 Registro `1200` — Contribuição Social Extemporânea – PIS/Pasep

Nível 2, ocorrência V. **Mesma limitação de aplicabilidade do 1101** — só para fatos geradores até jul/2013.

Para débitos extemporâneos a partir de ago/2013, deve-se retificar a EFD-Contribuições original.

### 2.11 Registros `1210` e `1220` — Detalhamento e Crédito a Descontar da Contribuição Extemporânea – PIS/Pasep

- **1210:** detalha o 1200 por documento/operação
- **1220:** demonstra os créditos (do período ou de períodos anteriores) que estão sendo descontados dessa contribuição extemporânea

Mesma limitação operacional (pré-ago/2013).

### 2.12 Registro `1300` — Controle dos Valores Retidos na Fonte – PIS/Pasep

Nível 2, ocorrência V. **Registro estratégico para recuperação de retenções não aproveitadas.** Um registro para cada combinação de `IND_NAT_RET + PR_REC_RET` (período de recebimento/retenção).

| # | Campo | Descrição | Obrig |
|:---:|---|---|:---:|
| 01 | `REG` | "1300" | S |
| 02 | `IND_NAT_RET` | **Natureza da retenção** (ver tabela abaixo) | S |
| 03 | `PR_REC_RET` | **Período do recebimento e retenção** (`mmaaaa`) | S |
| 04 | `VL_RET_APU` | Valor total da retenção efetivamente sofrida | S |
| 05 | `VL_RET_DED` | Valor já **deduzido da contribuição** no próprio período e em períodos anteriores (acumulado) | S |
| 06 | `VL_RET_PER` | Valor utilizado em **Pedido de Restituição** (acumulado) | S |
| 07 | `VL_RET_DCOMP` | Valor utilizado em **Declaração de Compensação** (acumulado) | S |
| 08 | `SLD_RET` | **Saldo de retenção a utilizar em períodos futuros** (= 04 − 05 − 06 − 07) | S |

**Tabela do `IND_NAT_RET` (a partir de 2014):**

*Retenções sobre rendimentos sujeitos a regra geral (NC ou CUM):*

| Código | Descrição |
|:---:|---|
| **01** | Retenção por Órgãos, Autarquias e Fundações Federais |
| **02** | Retenção por outras entidades da Administração Pública Federal |
| **03** | Retenção por Pessoas Jurídicas de Direito Privado |
| **04** | Recolhimento por Sociedade Cooperativa |
| **05** | Retenção por Fabricante de Máquinas e Veículos |
| **99** | Outras Retenções |

*Retenções sobre rendimentos sujeitos ao regime cumulativo auferido por PJ tributada pelo Lucro Real (a partir de 2014):*

| Código | Descrição |
|:---:|---|
| **51** | Por Órgãos, Autarquias e Fundações Federais |
| **52** | Por outras entidades da Administração Pública Federal |
| **53** | Por Pessoas Jurídicas de Direito Privado |
| **54** | Recolhimento por Sociedade Cooperativa |
| **55** | Por Fabricante de Máquinas e Veículos |
| **59** | Outras retenções – rendimentos de regime cumulativo específico (art. 8º da Lei 10.637/2002 e art. 10 da Lei 10.833/2003) |

**Regra crítica (art. 9º da IN RFB 1.234/2012, redação da IN 1.540/2015):** retenções nas fontes dos órgãos federais **somente podem ser deduzidas da contribuição da mesma espécie e do mesmo mês**. Excedente pode ser **restituído ou compensado** (PER/DCOMP).

> **Cruzamento primário Primetax — retenções não aproveitadas:**
>
> 1. Para cada `1300` ativo, `SLD_RET > 0` representa **saldo de retenção não aproveitado**. Auditar se a PJ efetivamente pleiteou a restituição/compensação em PER/DCOMP dentro do prazo prescricional de 5 anos.
>
> 2. Comparar soma de `F600.VL_RET_PIS` (com `IND_DEC = 0`) ao longo dos últimos 60 meses com o total de `1300.VL_RET_APU`. Divergência sistemática indica retenções declaradas pela fonte mas não escrituradas — oportunidade de reconhecimento via retificação.
>
> 3. `1300.VL_RET_DED` acumulado **deve** ser igual à soma de `M200.VL_RET_NC + M200.VL_RET_CUM` nos períodos em que a retenção foi deduzida. Verificação de integridade longitudinal.
>
> 4. **Oportunidade clássica de recuperação Primetax:** PJs com contratos com órgãos federais frequentemente têm **retenções sistematicamente acumuladas** em 1300 sem PER/DCOMP formalizada — crédito passível de ressarcimento imediato.

### 2.13 Registros `1500`, `1501`, `1502`, `1600`, `1610`, `1620`, `1700` — Análogos para COFINS

Estrutura idêntica aos registros 1100, 1101, 1102, 1200, 1210, 1220, 1300, trocando PIS → COFINS. Todas as regras e limitações se aplicam identicamente.

**Especialmente relevante:**
- `1500` — Controle de créditos de COFINS (análogo ao 1100)
- `1501/1502` — Créditos extemporâneos COFINS (mesma limitação pós-ago/2013)
- `1700` — Controle de retenções na fonte de COFINS (análogo ao 1300)

### 2.14 Registros `1800` e `1809` — Incorporação Imobiliária RET

Nível 2, ocorrência V. Registros específicos para o Regime Especial Tributário da Incorporação Imobiliária (Lei 10.931/2004), aplicável a incorporações com patrimônio de afetação.

Alíquotas especiais: **PIS 0,37%** + **COFINS 1,71%** (total unificado com IRPJ+CSLL = 4% sobre receitas).

### 2.15 Registro `1900` — Consolidação dos Documentos Emitidos no Período por PJ Lucro Presumido

Nível 2, ocorrência V. **Específico para PJ tributada pelo Lucro Presumido** que escriturou receitas em outros blocos (A/C/D/F) de forma **detalhada** (não consolidada em F500/F550), consolidando todas as emissões por tipo de documento.

---

## 3. Bloco P — Apuração da Contribuição Previdenciária sobre a Receita Bruta (CPRB)

### 3.1 Natureza e aplicabilidade

O Bloco P escritura a **CPRB — Contribuição Previdenciária sobre a Receita Bruta**, instituída pela **Lei 12.546/2011** como substituição da contribuição previdenciária patronal sobre folha de salários para determinados setores. Aplicável a fatos geradores a partir de março/2012.

Setores cobertos (exaustivo na tabela de atividades da Lei 12.546/2011 e alterações):

- TI, TIC, call centers
- Hotelaria
- Transporte rodoviário e ferroviário de passageiros
- Transporte rodoviário de cargas
- Construção civil
- Indústria (diversos segmentos pela TIPI/NCM)
- Comunicação

### 3.2 Tabela do Bloco P

| Registro | Descrição | Nível |
|:---:|---|:---:|
| `P001` | Abertura do Bloco P | 1 |
| `P010` | Identificação do Estabelecimento | 2 |
| `P100` | Contribuição Previdenciária sobre a Receita Bruta | 3 |
| `P110` | Complemento da Escrituração – Detalhamento da Apuração da Contribuição | 4 |
| `P199` | Processo Referenciado | 4 |
| `P200` | Consolidação da Contribuição Previdenciária sobre a Receita Bruta | 2 |
| `P210` | Ajuste da Contribuição Previdenciária Apurada sobre a Receita Bruta | 3 |
| `P990` | Encerramento do Bloco P | 1 |

### 3.3 Registro `P100` — Contribuição Previdenciária sobre a Receita Bruta

Nível 3, ocorrência 1:N. Detalhamento da apuração por tipo de receita e alíquota.

Campos principais:

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "P100" |
| 02 | `DT_INI` | Data inicial do período |
| 03 | `DT_FIN` | Data final do período |
| 04 | `VL_REC_TOT_EST` | Receita total do estabelecimento |
| 05 | `COD_ATIV_ECON` | Código da atividade (CNAE ou código específico da Lei 12.546/2011) |
| 06 | `VL_REC_ATIV_ESTAB` | Receita da atividade sujeita à CPRB |
| 07 | `VL_EXC` | Exclusões da base |
| 08 | `VL_BC_CONT` | Base de cálculo |
| 09 | `ALIQ_CONT` | Alíquota (varia por setor: 1%, 1,5%, 2%, 2,5%, 3%, 4,5% conforme atividade) |
| 10 | `VL_CONT_APU` | Valor apurado |
| 11 | `VL_AJUS_ACRES` | Ajustes de acréscimo |
| 12 | `VL_AJUS_REDUC` | Ajustes de redução |
| 13 | `VL_CONT_DEV` | Valor devido |
| 14 | `COD_CTA` | Conta contábil |

### 3.4 Status para o sistema Primetax

O Bloco P está **fora do escopo primário** da primeira iteração do sistema Primetax, dado o foco do projeto em PIS/COFINS não-cumulativos. Contudo, clientes da Primetax em setores sujeitos à CPRB podem se beneficiar de análise específica — considerar módulo dedicado em fase futura, especialmente porque a CPRB vem passando por ondas de desoneração/reoneração com regras complexas de opção anual.

---

## 4. Bloco 9 — Controle e Encerramento

### 4.1 Propósito

O Bloco 9 é de **integridade estrutural**: enumera todos os registros presentes no arquivo e sua quantidade, funcionando como checksum de completude.

### 4.2 Registros

| Registro | Descrição | Obrig. |
|:---:|---|:---:|
| `9001` | Abertura do Bloco 9 | O |
| `9900` | Registros do Arquivo (um por tipo de registro presente) | O |
| `9990` | Encerramento do Bloco 9 | O |
| `9999` | Encerramento do Arquivo Digital | O |

### 4.3 Registro `9900` — Registros do Arquivo

Nível 2, ocorrência V. **Um registro 9900 para cada tipo de registro efetivamente presente no arquivo**, informando a quantidade total.

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "9900" |
| 02 | `REG_BLC` | Nome do registro (ex: "C170", "M100", "1100") |
| 03 | `QTD_REG_BLC` | Quantidade de ocorrências desse registro no arquivo |

### 4.4 Registro `9999` — Encerramento do Arquivo Digital

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "9999" |
| 02 | `QTD_LIN` | **Quantidade total de linhas do arquivo**, inclusive `9999` |

> **Uso no sistema Primetax:** o Bloco 9 é peça **crítica** para validação de integridade durante o parsing. O parser deve:
>
> 1. Contar todas as ocorrências de cada tipo de registro encontrado
> 2. Confrontar com o declarado nos `9900` correspondentes
> 3. Se `QTD_REG_BLC` declarado ≠ contado: arquivo potencialmente corrompido ou manipulado → recusar processamento e alertar
> 4. Confrontar `9999.QTD_LIN` com número total de linhas lidas. Divergência = arquivo truncado ou modificado → recusar

---

## 5. Síntese final — Motor de cruzamento Primetax consolidado

Os cruzamentos abaixo representam a **consolidação de todos os testes** distribuídos ao longo das três partes deste documento. Organizados em três camadas progressivas de sofisticação.

### 5.1 Camada 1 — Cruzamentos de integridade estrutural (pré-análise)

1. **Integridade do Bloco 9:** quantidades declaradas em `9900` conferem com contadores reais.
2. **Unicidade do M200 e M600:** um único registro de cada por arquivo.
3. **Presença do 0110:** obrigatório, parâmetros de regime definidos antes de qualquer análise.
4. **Consistência 0110 × 0111:** se `0110.IND_APRO_CRED = 2`, deve haver `0111` com todos os campos preenchidos.
5. **Hierarquia pai-filho:** para todo C170 deve existir C100 pai; para todo M105 deve existir M100 pai; etc.
6. **Integridade de chaves:** `C100` por `IND_EMIT + NUM_DOC + COD_MOD + SER + SUB + COD_PART`; `D100` idem; `F100` sem chave única, mas sem duplicação lógica.

### 5.2 Camada 2 — Cruzamentos de aderência legal (detecção de erros e oportunidades)

7. **Tese 69 em C170:** `C170.VL_BC_PIS == C170.VL_ITEM − C170.VL_DESC − C170.VL_ICMS` quando `CST_PIS ∈ {01, 02, 05}` após 16/03/2017.
8. **Exclusão ICMS vinculada à CST correta:** itens com CST ∈ {04, 06, 07, 08, 09} não devem ter redução motivada por ICMS.
9. **EFD-Contribuições × EFD ICMS/IPI:** `VL_ICMS` em C170 deve ser consistente entre as duas declarações para a mesma `CHV_NFE`.
10. **CST × CFOP × Alíquota:** combinações improváveis (ex: CFOP de aquisição com CST 01; CFOP de exportação com CST sem série 52/54/55/56) = revisão manual.
11. **Itens com `TIPO_ITEM = 07` (uso/consumo) e CFOP de insumo:** candidatos à reclassificação sob o REsp 1.221.170/PR.
12. **Itens com CST 70–75:** auditoria individual — muitas vezes reclassificáveis para série 50+.
13. **Fretes `IND_NAT_FRT = 3` em PJ comercial/industrial:** possível reclassificação para `IND_NAT_FRT = 2`.
14. **Ativos em F120 pós-agosto/2011:** potencial otimização via F130 com `IND_NR_PARC = 1`.
15. **F150 em PJ recém-migrada:** presença e completude.
16. **F600 não deduzido em M200/M600:** Σ F600 > Σ retenções deduzidas.
17. **F600 × DIRF:** retenções declaradas pela fonte mas não escrituradas.
18. **F700 com Indicador 04 (ST não ocorrida):** oportunidade de restituição (Tema 228 STF).
19. **1300/1700 com SLD_RET > 0 e sem PER/DCOMP:** retenções acumuladas não pleiteadas.
20. **Ajuste M110 com `COD_AJ = 01` sem 1010 correspondente:** fragilidade probatória.
21. **0111 com valores de receita não-bruta:** inflação artificial da proporção tributada (venda de imobilizado, receita financeira).
22. **Créditos presumidos setoriais em F100:** presença de CST 62/65 com `NAT_BC_CRED = 13` para exportadores de commodities específicas.

### 5.3 Camada 3 — Cruzamentos de otimização tributária (teses e recuperação)

23. **Rateio proporcional × Apropriação direta (0110.IND_APRO_CRED):** simulação comparativa do método alternativo — qual geraria maior crédito?
24. **M205/M605 × DCTF:** aderência entre códigos de receita e valores declarados (via e-CAC).
25. **Saldos carregados do 1100/1500:** consistência longitudinal dos saldos mês a mês (checagem de carry-forward).
26. **Ajuste de base do ICMS via M215/M615:** para fatos geradores a partir de 2019, aderência entre ajustes de base declarados e ICMS destacado efetivo do período.
27. **Créditos vedados por área (F120/F130 `IND_UTIL_BEM_IMOB = 9`):** revisão de classificação — bens administrativos vs. produtivos.
28. **Estoque de abertura subestimado em F150:** conferir com inventário da ECD (registro H010).
29. **Aluguéis escriturados como despesa na ECD sem F100 correspondente:** crédito de aluguel não aproveitado (`NAT_BC_CRED = 05` ou `06`).
30. **Armazenagem e frete na venda sem F100 (`NAT_BC_CRED = 07`):** conferir despesa na ECD vs. crédito escriturado.
31. **Retenções prescritas:** 1300/1700 com `PR_REC_RET` há mais de 5 anos = prescrição — marcar e excluir do saldo a recuperar.
32. **Consistência M210 ↔ M100 ↔ M200:** fluxo vertical matematicamente aderente.
33. **Consistência entre Blocos A/C/D/F e M210:** `VL_BC_PIS` agregado dos itens com CST de débito = `M210.VL_BC_CONT` (por CST e alíquota).
34. **Consistência entre Blocos A/C/D/F e M105:** `VL_BC_PIS` agregado dos itens com CST de crédito = `M105.VL_BC_PIS_TOT` (por CST e NAT_BC_CRED).

---

## 6. Referências normativas consolidadas

### 6.1 Leis fundamentais

- **Lei 10.637/2002** — Regime não-cumulativo do PIS/Pasep; conceito de crédito (art. 3º)
- **Lei 10.833/2003** — Regime não-cumulativo da COFINS; conceito de crédito (art. 3º); retenção na fonte (arts. 30, 33, 34); crédito presumido de subcontratação de transporte (art. 3º, §§ 19-20)
- **Lei 10.865/2004** — PIS/COFINS-Importação; art. 31 (vedação de crédito sobre imobilizado anterior a maio/2004)
- **Lei 9.718/98** — Regime cumulativo; CPRB como substituição à contribuição patronal (art. 13); instituições financeiras (art. 3º, §§ 6º e 9º)
- **Lei 12.546/2011** — CPRB; crédito integral em máquinas e equipamentos (desdobrada da MP 540/2011)
- **Lei 12.973/2014** — Conceito de receita bruta (art. 12 do DL 1.598/77)

### 6.2 Leis setoriais de crédito presumido

- **Lei 12.599/2012** — Café
- **Lei 12.865/2013** — Soja, margarina, biodiesel
- **Lei 13.097/2015** — Bebidas frias (arts. 14–34)

### 6.3 Decisões judiciais e administrativas estruturantes

- **RE 574.706/PR (Tema 69 da Repercussão Geral)** — Exclusão do ICMS da base do PIS/COFINS; embargos declaratórios julgados em 13/05/2021 (modulação)
- **REsp 1.221.170/PR (Tema 779)** — Conceito de insumo (essencialidade/relevância) para PIS/COFINS não-cumulativos
- **ADI 2.675 e 2.777 (Tema 228)** — Restituição de ICMS pago a maior na ST quando o fato gerador presumido não se realiza
- **Parecer SEI nº 7698/2021/ME** — Operacionalização da Tese 69 pela PGFN

### 6.4 Instruções Normativas e atos administrativos

- **IN RFB 1.009/2010** — Tabelas de CST-PIS e CST-COFINS (Anexo Único, Tabelas II e III)
- **IN RFB 1.252/2012 e alterações** — Regulamentação da EFD-Contribuições
- **IN RFB 1.387/2013** — Prazo decadencial de 5 anos para retificação (que invalidou os registros 1101/1501 para fatos a partir de ago/2013)
- **IN RFB 1.234/2012, redação da IN 1.540/2015** — Retenção na fonte por órgãos federais (regra de dedução no mesmo mês)
- **IN RFB 1.599/2015** — DCTF
- **IN RFB 1.052/2010** — Prazo para retificação de EFD-Contribuições (revogada pela 1.387/2013)
- **ADE Codac/RFB nº 36/2014** — Extensões dos códigos de receita da DCTF (relevante para M205/M605)

### 6.5 Tabelas externas da EFD-Contribuições (portal SPED)

- **4.1.1** — Modelos de documentos fiscais
- **4.1.2** — Situação dos documentos fiscais
- **4.2.2** — CFOP
- **4.3.1** — CST-ICMS
- **4.3.2** — CST-IPI
- **4.3.3** — **CST-PIS** (detalhada na Parte 1)
- **4.3.4** — **CST-COFINS** (detalhada na Parte 1)
- **4.3.5** — **Código de Contribuição Social Apurada** (detalhada na Parte 3, seção 1.8)
- **4.3.6** — **Código de Tipo de Crédito** (detalhada na Parte 1)
- **4.3.7** — **Natureza da Base do Crédito** (detalhada na Parte 1)
- **4.3.8** — **Código de Ajuste de Contribuição ou Créditos** (detalhada na Parte 1)
- **4.3.9** — Alíquotas de Créditos Presumidos da Agroindústria
- **4.3.10** — Produtos com Alíquotas Diferenciadas (Monofásica/Pauta)
- **4.3.11** — Produtos com Alíquotas por Unidade de Medida
- **4.3.12** — Produtos sujeitos a ST (CST 05)
- **4.3.13** — Produtos com Alíquota Zero (CST 06)
- **4.3.14** — Operações com Isenção (CST 07)
- **4.3.15** — Operações sem Incidência (CST 08)
- **4.3.16** — Operações com Suspensão (CST 09)
- **4.3.17** — Outros Produtos com Alíquotas Diferenciadas (CST 02)
- **4.3.18** — Códigos de Ajuste da Base de Cálculo Mensal (usada em M215/M615/1050)

### 6.6 Atos Cotepe

- **Ato COTEPE/ICMS 9/2008** — Leiaute da EFD ICMS/IPI (fonte do C100/C170)

---

## 7. Conclusão e próximos passos para o projeto Primetax

Este documento (Partes 1, 2 e 3) fornece o **contexto completo do leiaute da EFD-Contribuições v1.35** necessário para:

1. Implementação do **parser** da EFD-Contribuições em Python (sugestão: `python-sped` como base, estendido com validações específicas)
2. Construção do **schema de persistência** em SQLite ou PostgreSQL (normalizando por bloco e mantendo integridade referencial pai-filho)
3. Implementação do **motor de cruzamento** em três camadas (integridade, aderência legal, otimização tributária), totalizando **34 cruzamentos primários** identificados
4. Geração de **relatórios de diagnóstico** formatados com a identidade Primetax (cinza `#53565A`, teal `#008C95`), via python-docx e openpyxl

### 7.1 Considerações de versionamento

- A **versão 1.35** (jun/2021) é aderente à maior parte das escriturações de clientes da Primetax relativas a 2021–2023.
- Para **fatos geradores de 2019 em diante**, utilizar o leiaute com campos `VL_AJUS_ACRES_BC_PIS`, `VL_AJUS_REDUC_BC_PIS` (ampliado do M210/M610).
- Para **fatos geradores anteriores a 2019**, os ajustes de base devem ser operacionalizados diretamente nos documentos (C170, C181, etc.) conforme a Seção 12 do manual (Parte 1).
- Versões posteriores à 1.35 (1.36+) podem ter incluído novas tabelas (como atualizações da 4.3.18 para códigos específicos do ICMS-Tese 69). Sistema deve ser **versionável por competência** processada.

### 7.2 Arquitetura recomendada para o motor de cruzamento

```
src/
├── parsers/
│   ├── efd_contribuicoes.py        # Parser principal do arquivo .txt
│   ├── blocos/
│   │   ├── bloco_0.py              # 0000, 0110, 0140, 0150, 0200, 0500, 0900
│   │   ├── bloco_a.py              # A100, A170
│   │   ├── bloco_c.py              # C100, C170, C175, C181, etc.
│   │   ├── bloco_d.py              # D100, D101, D105, D200, etc.
│   │   ├── bloco_f.py              # F100, F120, F130, F150, F500, F600, F700, F800
│   │   ├── bloco_m.py              # M100, M105, M200, M210, M500, M600, M610
│   │   ├── bloco_1.py              # 1010, 1050, 1100, 1101, 1300, 1500, 1700
│   │   └── bloco_9.py              # Validação estrutural
├── tabelas_externas/
│   ├── cst_pis_cofins.py
│   ├── tipo_credito.py             # Tabela 4.3.6
│   ├── nat_bc_credito.py           # Tabela 4.3.7
│   ├── cod_contribuicao.py         # Tabela 4.3.5
│   └── cod_ajuste.py               # Tabela 4.3.8
├── cruzamentos/
│   ├── camada_1_integridade/
│   ├── camada_2_aderencia_legal/
│   │   ├── tese_69_icms.py
│   │   ├── creditamento_insumos.py
│   │   ├── retencoes.py
│   │   └── ativo_imobilizado.py
│   └── camada_3_otimizacao/
│       ├── rateio_vs_apropriacao_direta.py
│       ├── creditos_presumidos_setoriais.py
│       └── otimizacao_f120_f130.py
├── rules/
│   └── versionamento.py            # Mapeamento competência → versão do leiaute
└── reports/
    ├── diagnostico_geral.py        # Excel/openpyxl com identidade Primetax
    └── relatorio_recuperacao.py    # Word/python-docx
```

---

*Fim da Parte 3 de 3.*

*Este documento, em conjunto com as Partes 1 e 2, compõe o layout completo da EFD-Contribuições estruturado para consumo pelo sistema Primetax de cruzamento fiscal.*
