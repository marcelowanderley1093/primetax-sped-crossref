# Layout da EFD-Contribuições — Parte 1 de 3

> **Documento-fonte:** Guia Prático da EFD-Contribuições, versão 1.35, atualizado em 18/06/2021, publicado pela Receita Federal do Brasil.
>
> **Propósito deste arquivo:** servir de contexto técnico-normativo para o sistema Primetax de cruzamento de declarações SPED, com foco em identificação de créditos de PIS/Pasep e COFINS pagos indevidamente.
>
> **Parte 1 cobre:** visão geral da escrituração, regras gerais de preenchimento, tabelas externas críticas (CST-PIS, CST-COFINS, Tipos de Crédito, Natureza da Base do Crédito, Códigos de Ajuste), estrutura hierárquica de todos os blocos (0, A, C, D, F, I, M, P, 1, 9), registros detalhados do Bloco 0 e do Bloco C, e **a Seção 12 do manual sobre operacionalização da exclusão do ICMS da base de cálculo do PIS/Cofins** — tese nuclear da consultoria Primetax.
>
> **Partes seguintes:** Parte 2 (Blocos D, F, I); Parte 3 (Bloco M — apuração e crédito; Bloco 1 — operações extemporâneas; Bloco P — CPRB; Bloco 9 — encerramento).
>
> **Atenção — versionamento de layout:** a versão 1.35 é de junho/2021. Versões mais recentes (1.36+) podem conter alterações pontuais especialmente em registros relacionados à exclusão do ICMS. O sistema Primetax deve manter controle de versão do layout aplicável a cada competência processada. Registros recebidos com leiaute diferente devem ser marcados para revisão manual.

---

## 1. Visão geral da EFD-Contribuições

A EFD-Contribuições é escrituração fiscal digital destinada à apuração da Contribuição para o PIS/Pasep, da COFINS e da Contribuição Previdenciária sobre a Receita Bruta (CPRB), por pessoa jurídica de direito privado, inclusive equiparadas e imunes/isentas do IRPJ.

### 1.1 Natureza do arquivo

- Arquivo-texto codificado em **Latin1 (ISO-8859-1)**
- Cada registro em uma linha, campos separados pelo caractere **pipe (`|`)**
- Cada linha inicia e termina com `|`
- Estrutura **hierárquica pai-filho**, identificada pelos 4 primeiros caracteres após o pipe inicial (`REG`)
- Os primeiros caracteres do `REG` identificam o bloco (ex: `M100` → Bloco M)

### 1.2 Blocos

| Bloco | Descrição |
|:---:|---|
| **0** | Abertura, Identificação e Referências |
| **A** | Documentos Fiscais – Serviços (ISS) |
| **C** | Documentos Fiscais I – Mercadorias (ICMS/IPI) |
| **D** | Documentos Fiscais II – Serviços (ICMS) |
| **F** | Demais Documentos e Operações |
| **I** | Operações das Instituições Financeiras e Assemelhadas, Seguradoras, Entidades de Previdência Privada e Operadoras de Planos de Assistência à Saúde |
| **M** | Apuração da Contribuição e Crédito de PIS/Pasep e da COFINS |
| **P** | Apuração da Contribuição Previdenciária sobre a Receita Bruta |
| **1** | Complemento da Escrituração – Controle de Saldos de Créditos e de Retenções, Operações Extemporâneas e Outras Informações |
| **9** | Controle e Encerramento do Arquivo Digital |

### 1.3 Regras gerais de preenchimento de campos

- **Tipo `C` (caractere):** texto. Conteúdo em maiúsculas, sem acentuação (exceto nos casos legais).
- **Tipo `N` (numérico):** valores numéricos sem formatação. Decimais separados por vírgula ou ponto, conforme implementação do PVA; na especificação aparecem como números inteiros com indicação de decimais implícitos.
- **`Tam` (tamanho):** tamanho fixo quando marcado com `*`; caso contrário, tamanho máximo.
- **`Dec`:** número de casas decimais implícitas (para valores monetários é sempre `02`).
- **Campos de data:** formato `ddmmaaaa`, sem separadores.
- **Campos de período:** formato `mmaaaa`.
- **Obrigatoriedade do campo:**
  - `S` — Sim, preenchimento obrigatório
  - `N` — Não obrigatório (pode vir vazio)
- **Obrigatoriedade do registro (na tabela dos blocos):**
  - `O` — Obrigatório
  - `OC` — Obrigatório se a situação descrita ocorrer
  - Condicionais específicos descritos no manual para cada registro

### 1.4 Regimes de apuração

Definidos no Registro `0110`, Campo `COD_INC_TRIB`:

| Indicador | Regime |
|:---:|---|
| **1** | Escrituração exclusivamente no regime **não-cumulativo** |
| **2** | Escrituração exclusivamente no regime **cumulativo** |
| **3** | Escrituração em **ambos** os regimes (cumulativo e não-cumulativo) |

O foco da recuperação de créditos indevidos da Primetax concentra-se predominantemente no **regime não-cumulativo** (Leis 10.637/2002 e 10.833/2003) e no **regime misto**.

### 1.5 Métodos de apropriação de créditos comuns

Definido no Registro `0110`, Campo `IND_APRO_CRED` (aplicável quando `COD_INC_TRIB = 1 ou 3`):

| Indicador | Método |
|:---:|---|
| **1** | Apropriação Direta (exige contabilidade de custos integrada) |
| **2** | Rateio Proporcional com base na Receita Bruta (obriga Registro 0111) |

---

## 2. Tabelas externas críticas para o sistema de cruzamento

### 2.1 Tabela 4.3.3 — CST-PIS (Código de Situação Tributária PIS/Pasep)

Referenciada no Anexo Único da IN RFB nº 1.009/2010. Aplicável aos campos `CST_PIS` em registros de documentos fiscais (A170, C170, C175, C181, C381, C481, C491, C601, D201, F100, etc.).

#### Operações geradoras de débito (saídas):

| CST | Descrição |
|:---:|---|
| **01** | Operação Tributável com Alíquota Básica |
| **02** | Operação Tributável com Alíquota Diferenciada |
| **03** | Operação Tributável com Alíquota por Unidade de Medida de Produto |
| **04** | Operação Tributável Monofásica – Revenda a Alíquota Zero |
| **05** | Operação Tributável por Substituição Tributária |
| **06** | Operação Tributável a Alíquota Zero |
| **07** | Operação Isenta da Contribuição |
| **08** | Operação sem Incidência da Contribuição |
| **09** | Operação com Suspensão da Contribuição |
| **49** | Outras Operações de Saída |

#### Operações geradoras de crédito (entradas/aquisições) — série 50:

| CST | Descrição |
|:---:|---|
| **50** | Operação com Direito a Crédito – Vinculada exclusivamente a Receita Tributada no Mercado Interno |
| **51** | Operação com Direito a Crédito – Vinculada exclusivamente a Receita Não Tributada no Mercado Interno |
| **52** | Operação com Direito a Crédito – Vinculada exclusivamente a Receita de Exportação |
| **53** | Operação com Direito a Crédito – Vinculada a Receitas Tributadas e Não Tributadas no Mercado Interno |
| **54** | Operação com Direito a Crédito – Vinculada a Receitas Tributadas no Mercado Interno e de Exportação |
| **55** | Operação com Direito a Crédito – Vinculada a Receitas Não Tributadas no Mercado Interno e de Exportação |
| **56** | Operação com Direito a Crédito – Vinculada a Receitas Tributadas e Não Tributadas no Mercado Interno e de Exportação |
| **60** | Crédito Presumido – Operação de Aquisição Vinculada exclusivamente a Receita Tributada no Mercado Interno |
| **61** | Crédito Presumido – Operação de Aquisição Vinculada exclusivamente a Receita Não Tributada no Mercado Interno |
| **62** | Crédito Presumido – Operação de Aquisição Vinculada exclusivamente a Receita de Exportação |
| **63** | Crédito Presumido – Operação de Aquisição Vinculada a Receitas Tributadas e Não Tributadas no Mercado Interno |
| **64** | Crédito Presumido – Operação de Aquisição Vinculada a Receitas Tributadas no Mercado Interno e de Exportação |
| **65** | Crédito Presumido – Operação de Aquisição Vinculada a Receitas Não Tributadas no Mercado Interno e de Exportação |
| **66** | Crédito Presumido – Operação de Aquisição Vinculada a Receitas Tributadas e Não Tributadas no Mercado Interno e de Exportação |
| **67** | Crédito Presumido – Outras Operações |
| **70** | Operação de Aquisição sem Direito a Crédito |
| **71** | Operação de Aquisição com Isenção |
| **72** | Operação de Aquisição com Suspensão |
| **73** | Operação de Aquisição a Alíquota Zero |
| **74** | Operação de Aquisição sem Incidência da Contribuição |
| **75** | Operação de Aquisição por Substituição Tributária |
| **98** | Outras Operações de Entrada |
| **99** | Outras Operações |

> **Nota técnica para o parser Primetax:** os CST de crédito (50–56 e 60–66) são o universo primário de análise para a recuperação. Notas com CST 70–75 merecem auditoria específica: frequentemente há reclassificação possível para série 50+, especialmente em itens que o cliente tratou conservadoramente como "sem crédito" mas que se enquadram no conceito de insumo (REsp 1.221.170/PR).

### 2.2 Tabela 4.3.4 — CST-COFINS

A tabela é **idêntica em códigos e descrições** à CST-PIS (Tabela 4.3.3). O cruzamento entre os dois campos em um mesmo item é, aliás, um dos testes de integridade mais básicos: salvo exceções muito específicas, `CST_PIS = CST_COFINS` na mesma linha C170/A170/etc. Divergências sistemáticas podem indicar erro de classificação ou oportunidade de recuperação.

### 2.3 Tabela 4.3.6 — Código de Tipo de Crédito

Utilizada no `COD_CRED` dos registros M100, M500 e 1100/1500. Identifica a natureza do crédito apurado:

#### Grupo 100 — Crédito vinculado à receita tributada no mercado interno

| Código | Descrição |
|:---:|---|
| **101** | Alíquota Básica |
| **102** | Alíquotas Diferenciadas |
| **103** | Alíquota por Unidade de Produto |
| **104** | Estoque de Abertura |
| **105** | Aquisição Embalagens para revenda |
| **106** | Presumido da Agroindústria |
| **107** | Outros Créditos Presumidos |
| **108** | Importação |
| **109** | Atividade Imobiliária |
| **199** | Outros |

#### Grupo 200 — Crédito vinculado à receita não tributada no mercado interno

| Código | Descrição |
|:---:|---|
| **201** | Alíquota Básica |
| **202** | Alíquotas Diferenciadas |
| **203** | Alíquota por Unidade de Produto |
| **204** | Estoque de Abertura |
| **205** | Aquisição Embalagens para revenda |
| **206** | Presumido da Agroindústria |
| **207** | Outros Créditos Presumidos |
| **208** | Importação |
| **299** | Outros |

#### Grupo 300 — Crédito vinculado à receita de exportação

| Código | Descrição |
|:---:|---|
| **301** | Alíquota Básica |
| **302** | Alíquotas Diferenciadas |
| **303** | Alíquota por Unidade de Produto |
| **304** | Estoque de Abertura |
| **305** | Aquisição Embalagens para revenda |
| **306** | Presumido da Agroindústria |
| **307** | Outros Créditos Presumidos |
| **308** | Importação |
| **399** | Outros |

### 2.4 Tabela 4.3.7 — Código de Natureza da Base de Cálculo do Crédito (`NAT_BC_CRED`)

Utilizada nos registros M105, M505, 1101, 1501, F100, F120, F130, F150 e outros. Identifica a origem da base de cálculo do crédito:

| Código | Descrição |
|:---:|---|
| **01** | Aquisição de bens para revenda |
| **02** | Aquisição de bens utilizados como insumo |
| **03** | Aquisição de serviços utilizados como insumo |
| **04** | Energia elétrica e térmica, inclusive sob a forma de vapor |
| **05** | Aluguéis de prédios |
| **06** | Aluguéis de máquinas e equipamentos |
| **07** | Armazenagem de mercadoria e frete na operação de venda |
| **08** | Contraprestações de arrendamento mercantil |
| **09** | Máquinas, equipamentos e outros bens incorporados ao ativo imobilizado (crédito sobre encargos de depreciação) |
| **10** | Máquinas, equipamentos e outros bens incorporados ao ativo imobilizado (crédito com base no valor de aquisição) |
| **11** | Amortização e Depreciação de edificações e benfeitorias em imóveis |
| **12** | Devolução de Vendas Sujeitas à Incidência Não-Cumulativa |
| **13** | Outras Operações com Direito a Crédito |
| **14** | Atividade de Transporte de Cargas – Subcontratação |
| **15** | Atividade Imobiliária – Custo Incorrido de Unidade Imobiliária |
| **16** | Atividade Imobiliária – Custo Orçado de unidade não concluída |
| **17** | Atividade de Prestação de Serviços de Limpeza, Conservação e Manutenção – vale-transporte, vale-refeição ou vale-alimentação, fardamento ou uniforme |
| **18** | Estoque de abertura de bens |

> **Nota para regras de cruzamento Primetax:** `NAT_BC_CRED = 13` ("Outras Operações") exige preenchimento obrigatório do campo `DESC_CRED` no M105/M505. Essa é uma das áreas de maior discricionariedade técnica e, na prática da Primetax, é onde mais se concentram oportunidades de recuperação (especialmente para insumos classificáveis sob a tese da essencialidade/relevância firmada no REsp 1.221.170/PR).

### 2.5 Tabela 4.3.8 — Código de Ajustes de Contribuição ou Créditos

Utilizada no `COD_AJ` dos registros M110, M115, M220, M225, M510, M515, M620, M625.

| Código | Descrição |
|:---:|---|
| **01** | Ajuste Oriundo de Ação Judicial |
| **02** | Ajuste Oriundo de Processo Administrativo |
| **03** | Ajuste Oriundo da Legislação Tributária |
| **04** | Ajuste Oriundo Especificamente do RTT |
| **05** | Ajuste Oriundo de Outras Situações |
| **06** | Estorno |
| **07** | Ajuste da CPRB: Adoção do Regime de Caixa |
| **08** | Ajuste da CPRB: Diferimento de Valores a Recolher no Período |
| **09** | Ajuste da CPRB: Adição de Valores Diferidos em Período(s) Anterior(es) |

> **Nota para motor de cruzamento:** ajustes com `COD_AJ = 01` (Ação Judicial) implicam obrigatoriamente a presença de registro `1010` no Bloco 1. Cruzamento crítico: todo ajuste de redução (`IND_AJ = 0`) com código 01 deve ter contrapartida rastreável em processo judicial — ausência de `1010` correspondente é sinal de fragilidade na defesa do crédito em eventual autuação. A partir de janeiro/2020 o Registro `1011` (Detalhamento das Contribuições com Exigibilidade Suspensa) também é exigido.

### 2.6 Outras tabelas relevantes (referenciadas, mas externas ao manual)

- **Tabela 4.3.5** — Código de Contribuição Social Apurada (usada em `COD_CONT` dos M210/M610)
- **Tabela 4.3.9** — Alíquotas de Créditos Presumidos da Agroindústria
- **Tabela 4.3.10** — Produtos Sujeitos a Alíquotas Diferenciadas (Monofásica e por Pauta): bebidas frias, combustíveis, farmacêuticos, veículos, autopeças, pneus
- **Tabela 4.3.11** — Produtos Sujeitos a Alíquotas por Unidade de Medida de Produto
- **Tabela 4.3.12** — Produtos Sujeitos à Substituição Tributária (CST 05)
- **Tabela 4.3.13** — Produtos Sujeitos à Alíquota Zero (CST 06)
- **Tabela 4.3.14** — Operações com Isenção (CST 07)
- **Tabela 4.3.15** — Operações sem Incidência (CST 08)
- **Tabela 4.3.16** — Operações com Suspensão (CST 09)
- **Tabela 4.3.17** — Outros Produtos e Operações Sujeitos a Alíquotas Diferenciadas (CST 02)
- **Tabela 4.3.18** — Códigos de Ajuste da Base de Cálculo Mensal das Contribuições (usada em M215/M615)
- **Tabela CFOP – Operações Geradoras de Crédito** — lista de CFOPs que, quando presentes em C170/C191, habilitam creditamento (disponibilizada no portal do SPED)

Essas tabelas devem ser baixadas separadamente do Portal SPED da RFB (`sped.rfb.gov.br`) e mantidas como arquivos versionáveis em `config/tabelas-externas/` do sistema Primetax. Contra essas tabelas validam-se códigos em runtime.

### 2.7 Alíquotas de referência

| Contribuição | Regime Cumulativo | Regime Não-Cumulativo |
|---|:---:|:---:|
| **PIS/Pasep** | 0,65% | 1,65% |
| **COFINS** | 3,0% | 7,6% |

Alíquotas específicas aplicáveis a produtos monofásicos, ST, regimes especiais e substituição são definidas em legislação própria e referenciadas nas Tabelas 4.3.10 e 4.3.11.

---

## 3. Seção 12 do Manual — Operacionalização da exclusão do ICMS da base do PIS/Cofins

> Esta seção é reproduzida do Guia Prático por sua **centralidade absoluta** para a operação da Primetax. É a operacionalização da tese vencida no **RE 574.706/PR** (Tema 69 da Repercussão Geral), com definição em embargos de declaração em 13/05/2021.

### 3.1 Síntese do posicionamento firmado (Parecer SEI nº 7698/2021/ME):

- **Receitas a partir de 16/03/2017:** o ICMS destacado em nota fiscal **não integra** a base de cálculo do PIS/Pasep e da COFINS, **independentemente** de ação judicial.
- **Receitas até 15/03/2017:** a exclusão aplica-se **exclusivamente** se a pessoa jurídica houver protocolado ação judicial até 15/03/2017.
- **O ICMS a excluir é o destacado em nota fiscal** (não o recolhido).

### 3.2 Tabela-chave: onde operacionalizar o ajuste de exclusão do ICMS

Esta é uma das tabelas mais importantes do manual para o motor de cruzamento Primetax. Indica, **por registro**, qual campo deve receber o ajuste:

| Registro | Campo para exclusão do ICMS | Campo para descontos incondicionais | Campo para demais exclusões |
|:---:|---|---|---|
| **C170** | Campo 15 — `VL_ICMS` | Campo 08 — `VL_DESC` | Campo 08 — `VL_DESC` |
| **C175** | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` |
| **C181** | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` |
| **C185** | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` |
| **C381** | Campo 05 — `VL_BC_PIS` ¹ | Campo 05 — `VL_BC_PIS` | Campo 05 — `VL_BC_PIS` |
| **C385** | Campo 05 — `VL_BC_COFINS` ¹ | Campo 05 — `VL_BC_COFINS` | Campo 05 — `VL_BC_COFINS` |
| **C481** | Campo 04 — `VL_BC_PIS` ¹ | Campo 04 — `VL_BC_PIS` | Campo 04 — `VL_BC_PIS` |
| **C485** | Campo 04 — `VL_BC_COFINS` ¹ | Campo 04 — `VL_BC_COFINS` | Campo 04 — `VL_BC_COFINS` |
| **C491** | Campo 06 — `VL_BC_PIS` ¹ | Campo 06 — `VL_BC_PIS` | Campo 06 — `VL_BC_PIS` |
| **C495** | Campo 06 — `VL_BC_COFINS` ¹ | Campo 06 — `VL_BC_COFINS` | Campo 06 — `VL_BC_COFINS` |
| **C601** | Campo 04 — `VL_BC_PIS` ¹ | Campo 04 — `VL_BC_PIS` | Campo 04 — `VL_BC_PIS` |
| **C605** | Campo 04 — `VL_BC_COFINS` ¹ | Campo 04 — `VL_BC_COFINS` | Campo 04 — `VL_BC_COFINS` |
| **C870** | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` | Campo 05 — `VL_DESC` |
| **D201** | Campo 04 — `VL_BC_PIS` ¹ | Campo 04 — `VL_BC_PIS` | Campo 04 — `VL_BC_PIS` |
| **D205** | Campo 04 — `VL_BC_COFINS` ¹ | Campo 04 — `VL_BC_COFINS` | Campo 04 — `VL_BC_COFINS` |
| **D300** | Campo 10 — `VL_DESC` | Campo 10 — `VL_DESC` | Campo 10 — `VL_DESC` |
| **D350** | Campo 12 — `VL_BC_PIS` e Campo 18 — `VL_BC_COFINS` ¹ | idem | idem |
| **D601** | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` |
| **D605** | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` | Campo 04 — `VL_DESC` |
| **F100** ² | Campo 08 — `VL_BC_PIS` e Campo 12 — `VL_BC_COFINS` | idem | idem |
| **F500** ³ | Campo 04 — `VL_DESC_PIS` e Campo 09 — `VL_DESC_COFINS` | idem | idem |
| **F550** ³ | Campo 04 — `VL_DESC_PIS` e Campo 09 — `VL_DESC_COFINS` | idem | idem |

**Notas do manual:**

1. Não existe campo específico para exclusões de base de cálculo nesses registros. O ajuste de exclusão é feito **diretamente no campo de base de cálculo** (ou seja, a base já entra no arquivo com o ICMS excluído, não há campo destacado para rastreamento).
2. Registro utilizado de forma subsidiária, para casos excepcionais de documentação que não deva ser informada nos demais registros e tenha ocorrido destaque do ICMS.
3. A exclusão deve ser efetuada apenas em relação a operações com documento fiscal e destaque de ICMS.

> **Observação crítica para a apuração Primetax:** a distinção acima é operacionalmente decisiva. Em **C170**, o ICMS fica **rastreável** (campo separado `VL_ICMS`), o que permite auditoria retroativa da exclusão. Nos demais registros (C381, C385, C481, C491, C601, etc.), a exclusão é feita diretamente na base, tornando a auditoria **não reconstrutível** apenas pelo SPED — exige confronto com a EFD ICMS/IPI, que preserva o ICMS original em C170 (layout próprio). **Esta é a principal justificativa técnica do sistema de cruzamento da Primetax.**

### 3.3 Vinculação da exclusão à natureza da receita

Regra do manual: "A exclusão do ICMS deve ser vinculada à correspondente natureza de receita."

O valor do ICMS destacado em uma operação **tributada** (CST 01/02/05) não pode ser usado para reduzir base de cálculo de operação **não tributada** (CST 04/06/07/08/09). A exclusão é item a item, vinculada à CST correspondente.

**Exemplo oficial do manual** (venda interestadual de R$ 10.000,00):

- Item 1: R$ 6.000,00 com CST-PIS 01 (tributado), ICMS destacado R$ 720,00 → `VL_BC_PIS` = R$ 5.280,00
- Item 2: R$ 4.000,00 com CST-PIS 06 (alíquota zero), ICMS destacado R$ 480,00 → não há base a reduzir, pois a receita já é não tributada

O valor de R$ 480,00 **não pode** ser usado para reduzir a base do Item 1.

### 3.4 Implicações para o motor de cruzamento Primetax

Essa seção do manual define **quatro cruzamentos primários** a serem implementados:

1. **Aderência da exclusão em C170:** para cada `C170` com CST-PIS em {01, 02, 05}, verificar se `(VL_ITEM - VL_DESC - VL_ICMS) == VL_BC_PIS`. Divergências sistemáticas indicam exclusão não realizada (oportunidade de recuperação) ou erro de preenchimento.

2. **Consistência ICMS-destacado (EFD-Contribuições × EFD ICMS/IPI):** comparar campo `VL_ICMS` do C170 nas duas declarações, por chave de nota fiscal. Divergências indicam reconciliação pendente.

3. **Vinculação CST × exclusão:** validar que, em C170, nenhum item com CST-PIS em {04, 06, 07, 08, 09} tenha redução de base motivada por ICMS (pois nesses CSTs não há base tributada).

4. **Rastreabilidade em registros consolidados:** para C381/C385/C481/C485/C491/C495/C601/C605 (registros que **não preservam** o ICMS destacado), marcar como "exclusão não auditável no próprio SPED" e exigir triangulação com EFD ICMS/IPI e/ou NF-e original.

---

## 4. Tabela do Bloco 0 — Abertura, Identificação e Referências

| Registro | Descrição | Nível | Ocorrência | Obrigatoriedade |
|:---:|---|:---:|:---:|---|
| `0000` | Abertura do Arquivo Digital e Identificação da Pessoa Jurídica | 0 | 1 | O |
| `0001` | Abertura do Bloco 0 | 1 | 1 | O |
| `0035` | Identificação de Sociedade em Conta de Participação – SCP | 2 | 1:N | O, se `0000.IND_NAT_PJ` ∈ {03, 04, 05} |
| `0100` | Dados do Contabilista | 2 | V | OC |
| `0110` | Regimes de Apuração da Contribuição Social e de Apropriação de Crédito | 2 | 1 | O |
| `0111` | Tabela de Receita Bruta Mensal Para Fins de Rateio de Créditos Comuns | 3 | 1:1 | O se `0110.COD_INC_TRIB` ∈ {1, 3} e `0110.IND_APRO_CRED = 2` |
| `0120` | Identificação de EFD-Contribuições Sem Dados a Escriturar | 2 | V | OC |
| `0140` | Tabela de Cadastro de Estabelecimento | 2 | V | O |
| `0145` | Regime de Apuração da Contribuição Previdenciária sobre a Receita Bruta | 3 | 1:1 | OC |
| `0150` | Tabela de Cadastro do Participante | 3 | 1:N | OC |
| `0190` | Identificação das Unidades de Medida | 3 | 1:N | OC |
| `0200` | Tabela de Identificação do Item (Produtos e Serviços) | 3 | 1:N | OC |
| `0205` | Alteração do Item | 4 | 1:N | OC |
| `0206` | Código de Produto conforme Tabela ANP (Combustíveis) | 4 | 1:1 | OC |
| `0208` | Código de Grupos por Marca Comercial – REFRI (Bebidas Frias) | 4 | 1:1 | OC |
| `0400` | Tabela de Natureza da Operação/Prestação | 3 | 1:N | OC |
| `0450` | Tabela de Informação Complementar do Documento Fiscal | 3 | 1:N | OC |
| `0500` | Plano de Contas Contábeis – Contas Informadas | 2 | V | OC |
| `0600` | Centro de Custos | 2 | V | OC |
| `0900` | Composição das Receitas do Período – Receita Bruta e Demais Receitas | 2 | 1 | O, se escrituração transmitida após prazo regular |
| `0990` | Encerramento do Bloco 0 | 1 | 1 | O |

---

## 5. Tabela do Bloco A — Documentos Fiscais – Serviços (ISS)

| Registro | Descrição | Nível | Ocorrência | Obrig. Registro | Escritura Contribuição | Escritura Crédito |
|:---:|---|:---:|:---:|---|:---:|:---:|
| `A001` | Abertura do Bloco A | 1 | 1 | O | – | – |
| `A010` | Identificação do Estabelecimento | 2 | V | O se `A001.IND_MOV = 0` | – | – |
| `A100` | Documento – Nota Fiscal de Serviço | 3 | 1:N | OC | S | S |
| `A110` | Complemento do Documento – Informação Complementar da NF | 4 | 1:N | OC | S | S |
| `A111` | Processo Referenciado | 4 | 1:N | OC | S | S |
| `A120` | Informação Complementar – Operações de Importação | 4 | 1:N | OC | N | S |
| `A170` | Complemento do Documento – Itens do Documento | 4 | 1:N | O se existir A100 | S | S |
| `A990` | Encerramento do Bloco A | 1 | 1 | O | – | – |

---

## 6. Tabela do Bloco C — Documentos Fiscais I – Mercadorias (ICMS/IPI)

| Registro | Descrição | Nível | Ocorrência | Obrig. Registro | Contrib. | Crédito |
|:---:|---|:---:|:---:|---|:---:|:---:|
| `C001` | Abertura do Bloco C | 1 | 1 | O | – | – |
| `C010` | Identificação do Estabelecimento | 2 | V | O se `C001.IND_MOV = 0` | – | – |
| `C100` | Documento – NF (cód. 01), NF Avulsa (1B), NF Produtor (04), NF-e (55) | 3 | 1:N | OC | S | S |
| `C110` | Complemento – Informação Complementar da NF | 4 | 1:N | OC | S | S |
| `C111` | Processo Referenciado | 4 | 1:N | OC | S | S |
| `C120` | Complemento – Operações de Importação (cód. 01) | 4 | 1:N | O se houver CFOP iniciado em 3 em tabela "CFOP Geradores de Crédito" | N | S |
| `C170` | Complemento – **Itens do Documento** (cód. 01, 1B, 04, 55) | 4 | 1:N | O se existir C100 | **S** | **S** |
| `C175` | Registro Analítico do Documento (cód. 65 – NFC-e) | 4 | 1:N | O se C100 e COD_MOD = 65 | S | N |
| `C180` | Consolidação de NF-e Emitidas pela PJ (cód. 55) – Vendas | 3 | 1:N | OC | S | N |
| `C181` | Detalhamento da Consolidação – Vendas – PIS/Pasep | 4 | 1:N | O se existir C180 | S | N |
| `C185` | Detalhamento da Consolidação – Vendas – COFINS | 4 | 1:N | O se existir C180 | S | N |
| `C188` | Processo Referenciado | 4 | 1:N | OC | S | N |
| `C190` | Consolidação de NF-e (cód. 55) – Aquisições com Crédito e Devoluções | 3 | 1:N | OC | N | S |
| `C191` | Detalhamento – Aquisições com Crédito e Devoluções – PIS/Pasep | 4 | 1:N | O se existir C190 | N | S |
| `C195` | Detalhamento – Aquisições com Crédito e Devoluções – COFINS | 4 | 1:N | O se existir C190 | N | S |
| `C198` | Processo Referenciado | 4 | 1:N | OC | N | S |
| `C199` | Complemento – Operações de Importação (cód. 55) | 4 | 1:N | O se houver CFOP iniciado em 3 em C191/C195 em tabela "CFOP Geradores de Crédito" | N | S |
| `C380` | NF de Venda a Consumidor (cód. 02) – Consolidação | 3 | 1:N | OC | S | N |
| `C381` | Detalhamento da Consolidação – PIS/Pasep | 4 | 1:N | O se `C380.VL_DOC > 0` | S | N |
| `C385` | Detalhamento da Consolidação – COFINS | 4 | 1:N | O se `C380.VL_DOC > 0` | S | N |
| `C395` | NF Venda a Consumidor (cód. 02, 2D, 2E, 59) – Aquisições com Crédito | 3 | 1:N | OC | N | S |
| `C396` | Itens do Documento – Aquisições com Crédito | 4 | 1:N | O se existir C395 | N | S |
| `C400` | Equipamento ECF (cód. 02 e 2D) | 3 | 1:N | OC | S | N |
| `C405` | Redução Z (cód. 02 e 2D) | 4 | 1:N | O se existir C400 | S | N |
| `C481` | Resumo Diário Docs Emitidos por ECF – PIS/Pasep | 5 | 1:N | OC | S | N |
| `C485` | Resumo Diário Docs Emitidos por ECF – COFINS | 5 | 1:N | OC | S | N |
| `C489` | Processo Referenciado | 4 | 1:N | OC | S | N |
| `C490` | Consolidação de Documentos Emitidos por ECF (cód. 02, 2D, 59, 60) | 3 | 1:N | OC | S | N |
| `C491` | Detalhamento da Consolidação ECF – PIS/Pasep | 4 | 1:N | OC | S | N |
| `C495` | Detalhamento da Consolidação ECF – COFINS | 4 | 1:N | OC | S | N |
| `C499` | Processo Referenciado – Documentos Emitidos por ECF | 4 | 1:N | OC | S | N |
| `C500` | NF/Conta Energia Elétrica (06), NF3e (66), NF/Conta Água (29), NF/Gás (28), NF-e (55) – Aquisições com Crédito | 3 | 1:N | OC | N | S |
| `C501` | Complemento da Operação (cód. 06, 28, 29) – PIS/Pasep | 4 | 1:N | O se existir C500 | N | S |
| `C505` | Complemento da Operação (cód. 06, 28, 29) – COFINS | 4 | 1:N | O se existir C500 | N | S |
| `C509` | Processo Referenciado | 4 | 1:N | OC | N | S |
| `C600` | Consolidação Diária NF Energia (06), Água (29), Gás (28) – Saídas | 3 | 1:N | OC | S | N |
| `C601` | Complemento Consolidação Diária (06, 29, 28) – Saídas – PIS/Pasep | 4 | 1:N | O se existir C600 | S | N |
| `C605` | Complemento Consolidação Diária (06, 29, 28) – Saídas – COFINS | 4 | 1:N | O se existir C600 | S | N |
| `C609` | Processo Referenciado | 4 | 1:N | OC | S | N |
| `C800` | Cupom Fiscal Eletrônico – CF-e (cód. 59) | 3 | 1:N | OC, N se existir C860 | S | N |
| `C810` | Detalhamento do CF-e (cód. 59) – PIS/Pasep e COFINS | 4 | 1:N | OC | S | N |
| `C820` | Detalhamento do CF-e (cód. 59) – Apurado por Unidade de Medida | 4 | 1:N | O se não existir C810 | S | N |
| `C830` | Processo Referenciado | 4 | 1:N | OC | S | N |
| `C860` | Identificação do Equipamento SAT-CF-e (cód. 59) | 3 | 1:N | OC | S | N |
| `C870` | Detalhamento do CF-e (cód. 59) – PIS/Pasep e COFINS (SAT) | 4 | 1:N | OC | S | N |
| `C880` | Detalhamento do CF-e (cód. 59) – Apurado por Unidade de Medida (SAT) | 4 | 1:N | O se não existir C870 | S | N |
| `C890` | Processo Referenciado | 4 | 1:N | OC | S | N |
| `C990` | Encerramento do Bloco C | 1 | 1 | O | – | – |

> **Nota — NFC-e e CF-e-SAT:** os registros referentes à NFC-e (cód. 65) foram disponibilizados na versão 2.09 do PVA (outubro/2014) e os do CF-e-SAT (cód. 59) na versão 2.11 (maio/2015). Para períodos anteriores, essas operações vinham escrituradas de forma analítica no C180 ou consolidada no C400/C490.

---

## 7. Tabela do Bloco D — Documentos Fiscais II – Serviços (ICMS)

*(Detalhamento completo dos registros D100, D101, D105, D201, D205, D300, D350, D500, D600 etc. na Parte 2 deste documento.)*

| Registro | Descrição | Nível | Contrib. | Crédito |
|:---:|---|:---:|:---:|:---:|
| `D001` | Abertura do Bloco D | 1 | – | – |
| `D010` | Identificação do Estabelecimento | 2 | – | – |
| `D100` | Conhecimento de Transporte – aquisições com crédito | 3 | N | S |
| `D101` | Complemento da Operação – PIS/Pasep (frete) | 4 | N | S |
| `D105` | Complemento da Operação – COFINS (frete) | 4 | N | S |
| `D200` | Resumo de Documentos de Transporte – Prestação de Serviços | 3 | S | N |
| `D201` | Totalização do Resumo – PIS/Pasep | 4 | S | N |
| `D205` | Totalização do Resumo – COFINS | 4 | S | N |
| `D300` | Nota Fiscal de Bilhete de Passagem | 3 | S | N |
| `D350` | Resumo Diário Bilhetes por ECF | 3 | S | N |
| `D500` | NF de Serviços de Comunicação/Telecom – Aquisições com Crédito | 3 | N | S |
| `D501` | Complemento – PIS/Pasep | 4 | N | S |
| `D505` | Complemento – COFINS | 4 | N | S |
| `D600` | Consolidação NF Comunicação/Telecom – Prestação | 3 | S | N |
| `D601` | Complemento Consolidação – PIS/Pasep | 4 | S | N |
| `D605` | Complemento Consolidação – COFINS | 4 | S | N |
| `D990` | Encerramento do Bloco D | 1 | – | – |

---

## 8. Tabela do Bloco F — Demais Documentos e Operações

*(Detalhamento na Parte 2.)*

| Registro | Descrição | Nível | Contrib. | Crédito |
|:---:|---|:---:|:---:|:---:|
| `F001` | Abertura do Bloco F | 1 | – | – |
| `F010` | Identificação do Estabelecimento | 2 | – | – |
| `F100` | Demais Documentos e Operações com Contribuição/Crédito | 3 | S | S |
| `F111` | Processo Referenciado (F100) | 4 | S | S |
| `F120` | Bens Incorporados ao Ativo Imobilizado – Crédito sobre Encargos de Depreciação | 3 | N | S |
| `F129` | Processo Referenciado (F120) | 4 | N | S |
| `F130` | Bens Incorporados ao Ativo Imobilizado – Crédito sobre Valor de Aquisição | 3 | N | S |
| `F139` | Processo Referenciado (F130) | 4 | N | S |
| `F150` | Crédito Presumido sobre Estoque de Abertura | 3 | N | S |
| `F200` | Atividade Imobiliária – Operações com Unidades | 3 | S | N |
| `F205` | Atividade Imobiliária – Custo Incorrido | 4 | N | S |
| `F210` | Atividade Imobiliária – Custo Orçado | 4 | N | S |
| `F211` | Processo Referenciado (F200/F205/F210) | 4 | S | S |
| `F500` | Consolidação – Regime de Caixa (Lucro Presumido) | 3 | S | N |
| `F509` | Processo Referenciado (F500) | 4 | S | N |
| `F510` | Consolidação – Regime de Caixa – Alíquotas Diferenciadas | 3 | S | N |
| `F519` | Processo Referenciado (F510) | 4 | S | N |
| `F525` | Composição das Receitas do F500 | 4 | S | N |
| `F550` | Consolidação – Regime de Competência (Lucro Presumido) | 3 | S | N |
| `F559` | Processo Referenciado (F550) | 4 | S | N |
| `F560` | Consolidação – Regime de Competência – Alíquotas Diferenciadas | 3 | S | N |
| `F569` | Processo Referenciado (F560) | 4 | S | N |
| `F600` | Contribuição Retida na Fonte | 3 | N | – |
| `F700` | Deduções Diversas | 3 | S | – |
| `F800` | Créditos Decorrentes de Eventos de Incorporação/Fusão/Cisão | 3 | N | S |
| `F990` | Encerramento do Bloco F | 1 | – | – |

---

## 9. Tabela do Bloco I — Instituições Financeiras, Seguradoras, Previdência, Planos de Saúde

*(Fora do escopo primário da Primetax em primeira iteração. Detalhamento sucinto na Parte 2.)*

---

## 10. Tabela do Bloco M — Apuração da Contribuição e Crédito de PIS/Pasep e da COFINS

| Registro | Descrição | Nível | Ocorrência | Obrigatoriedade |
|:---:|---|:---:|:---:|---|
| `M001` | Abertura do Bloco M | 1 | 1 | O |
| `M100` | Crédito de PIS/Pasep Relativo ao Período | 2 | V | OC |
| `M105` | Detalhamento da Base de Cálculo do Crédito – PIS/Pasep | 3 | 1:N | OC |
| `M110` | Ajustes do Crédito de PIS/Pasep | 3 | 1:N | OC |
| `M115` | Detalhamento dos Ajustes do Crédito de PIS/Pasep | 4 | 1:N | OC (a partir de out/2015) |
| `M200` | Consolidação da Contribuição para o PIS/Pasep do Período | 2 | 1 | O |
| `M205` | Contribuição PIS/Pasep a Recolher – Detalhamento por Código de Receita | 3 | 1:N | O se `M200.VL_CONT_NC_REC > 0` ou `M200.VL_CONT_CUM_REC > 0` |
| `M210` | Detalhamento da Contribuição para o PIS/Pasep | 3 | 1:N | O se existirem registros nos Blocos A/C/D/F com CST ∈ {01, 02, 03, 05} |
| `M211` | Sociedades Cooperativas – Composição da Base – PIS/Pasep | 4 | 1:1 | O se `0000.IND_NAT_PJ = 01` |
| `M215` | Detalhamento dos Ajustes da Base de Cálculo Mensal – PIS/Pasep | 4 | 1:N | O se M210.VL_AJUS_ACRES_BC_PIS > 0 ou VL_AJUS_REDUC_BC_PIS > 0 |
| `M220` | Ajustes da Contribuição para o PIS/Pasep Apurada | 4 | 1:N | OC |
| `M225` | Detalhamento dos Ajustes da Contribuição – PIS/Pasep | 5 | 1:N | OC (a partir de out/2015) |
| `M230` | Informações Adicionais de Diferimento | 4 | 1:N | OC |
| `M300` | PIS/Pasep Diferido em Períodos Anteriores – Valores a Pagar | 2 | V | OC |
| `M350` | PIS/Pasep – Folha de Salários | 2 | 1 | OC |
| `M400` | Receitas Isentas, Não Alcançadas, Alíquota Zero ou Suspensão – PIS/Pasep | 2 | V | OC |
| `M410` | Detalhamento das Receitas Isentas/Não Tributadas – PIS/Pasep | 3 | 1:N | O se existir M400 |
| `M500` | Crédito de COFINS Relativo ao Período | 2 | V | OC |
| `M505` | Detalhamento da Base de Cálculo do Crédito – COFINS | 3 | 1:N | OC |
| `M510` | Ajustes do Crédito de COFINS | 3 | 1:N | OC |
| `M515` | Detalhamento dos Ajustes do Crédito de COFINS | 4 | 1:N | OC (a partir de out/2015) |
| `M600` | Consolidação da COFINS do Período | 2 | 1 | O |
| `M605` | COFINS a Recolher – Detalhamento por Código de Receita | 3 | 1:N | O se `M600.VL_CONT_NC_REC > 0` ou `M600.VL_CONT_CUM_REC > 0` |
| `M610` | Detalhamento da COFINS do Período | 3 | 1:N | O se existirem registros com CST ∈ {01, 02, 03, 05} |
| `M611` | Sociedades Cooperativas – Composição da Base – COFINS | 4 | 1:1 | O se `0000.IND_NAT_PJ = 01` |
| `M615` | Detalhamento dos Ajustes da Base de Cálculo Mensal – COFINS | 4 | 1:N | O se M610.VL_AJUS_ACRES_BC_COFINS > 0 ou VL_AJUS_REDUC_BC_COFINS > 0 |
| `M620` | Ajustes da COFINS Apurada | 4 | 1:N | OC |
| `M625` | Detalhamento dos Ajustes da COFINS | 5 | 1:N | OC (a partir de out/2015) |
| `M630` | Informações Adicionais de Diferimento | 4 | 1:N | OC |
| `M700` | COFINS Diferida em Períodos Anteriores – Valores a Pagar | 2 | V | OC |
| `M800` | Receitas Isentas, Não Alcançadas, Alíquota Zero ou Suspensão – COFINS | 2 | V | OC |
| `M810` | Detalhamento das Receitas Isentas/Não Tributadas – COFINS | 3 | 1:N | O se existir M800 |
| `M990` | Encerramento do Bloco M | 1 | 1 | O |

---

## 11. Tabela do Bloco P — Apuração da CPRB

*(Fora do escopo primário PIS/COFINS; detalhamento na Parte 3.)*

| Registro | Descrição |
|:---:|---|
| `P001`, `P010`, `P100`, `P110`, `P199`, `P200`, `P210`, `P990` | Apuração da Contribuição Previdenciária sobre a Receita Bruta |

---

## 12. Tabela do Bloco 1 — Complemento da Escrituração

*(Detalhamento completo na Parte 3. Muito relevante para créditos extemporâneos, a tese Primetax de recuperação de créditos não aproveitados tempestivamente.)*

| Registro | Descrição |
|:---:|---|
| `1001` | Abertura do Bloco 1 |
| `1010` | Processo Referenciado – **Ação Judicial** |
| `1011` | Detalhamento das Contribuições com Exigibilidade Suspensa (a partir de jan/2020) |
| `1020` | Processo Referenciado – Processo Administrativo |
| `1050` | Detalhamento de Ajustes de Base de Cálculo – Valores Extra Apuração |
| `1100` | Controle de Créditos Fiscais – PIS/Pasep |
| `1101` | Apuração de **Crédito Extemporâneo** – Documentos e Operações de Períodos Anteriores – PIS/Pasep |
| `1102` | Detalhamento do Crédito Extemporâneo Vinculado a Mais de um Tipo de Receita – PIS/Pasep |
| `1200` | Contribuição Social Extemporânea – PIS/Pasep |
| `1210` | Detalhamento da Contribuição Social Extemporânea – PIS/Pasep |
| `1220` | Demonstração do Crédito a Descontar da Contribuição Extemporânea – PIS/Pasep |
| `1300` | Controle dos Valores Retidos na Fonte – PIS/Pasep |
| `1500` | Controle de Créditos Fiscais – COFINS |
| `1501` | Apuração de **Crédito Extemporâneo** – COFINS |
| `1502` | Detalhamento do Crédito Extemporâneo Vinculado a Mais de um Tipo de Receita – COFINS |
| `1600` | Contribuição Social Extemporânea – COFINS |
| `1610` | Detalhamento da Contribuição Social Extemporânea – COFINS |
| `1620` | Demonstração do Crédito a Descontar da Contribuição Extemporânea – COFINS |
| `1700` | Controle dos Valores Retidos na Fonte – COFINS |
| `1800` | Incorporação Imobiliária – RET |
| `1809` | Processo Referenciado |
| `1900` | Consolidação dos Documentos Emitidos no Período por PJ Lucro Presumido |
| `1990` | Encerramento do Bloco 1 |

---

## 13. Tabela do Bloco 9 — Controle e Encerramento

| Registro | Descrição | Obrig. |
|:---:|---|:---:|
| `9001` | Abertura do Bloco 9 | O |
| `9900` | Registros do Arquivo | O (um por tipo de registro no arquivo) |
| `9990` | Encerramento do Bloco 9 | O |
| `9999` | Encerramento do Arquivo Digital | O |

---

## 14. Registros detalhados do Bloco 0

### 14.1 Registro `0000` — Abertura do Arquivo Digital e Identificação da Pessoa Jurídica

Registro único de abertura, obrigatório, nível hierárquico 0, ocorrência 1 por arquivo.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | Texto fixo "0000" | C | 004* | – | S |
| 02 | `COD_VER` | Código da versão do leiaute | N | 003* | – | S |
| 03 | `TIPO_ESCRIT` | Tipo de escrituração: 0 – Original; 1 – Retificadora | N | 001* | – | S |
| 04 | `IND_SIT_ESP` | Indicador de situação especial: 0 – Abertura; 1 – Cisão; 2 – Fusão; 3 – Incorporação; 4 – Encerramento | N | 001* | – | N |
| 05 | `NUM_REC_ANTERIOR` | Nº do recibo da escrituração anterior a ser retificada | C | 041* | – | N |
| 06 | `DT_INI` | Data inicial (`ddmmaaaa`) | N | 008* | – | S |
| 07 | `DT_FIN` | Data final (`ddmmaaaa`) | N | 008* | – | S |
| 08 | `NOME` | Nome empresarial | C | 100 | – | S |
| 09 | `CNPJ` | CNPJ da PJ | N | 014* | – | S |
| 10 | `UF` | Sigla da UF | C | 002* | – | S |
| 11 | `COD_MUN` | Código do município (tabela IBGE) | N | 007* | – | S |
| 12 | `SUFRAMA` | Inscrição na SUFRAMA | C | 009* | – | N |
| 13 | `IND_NAT_PJ` | Natureza da PJ: 00 – PJ em geral; 01 – Sociedade Cooperativa; 02 – Entidade sujeita ao PIS/Pasep exclusivamente com base na folha; 03 – PJ constituída como SCP; 04 – Sócia ostensiva de SCP; 05 – PJ em geral, com operações referentes a SCP | N | 002* | – | S |
| 14 | `IND_ATIV` | Indicador de tipo de atividade preponderante: 0 – Industrial ou equiparada a industrial; 1 – Prestador de serviços; 2 – Atividade de comércio; 3 – Atividade financeira; 4 – Atividade imobiliária; 9 – Outros | N | 001* | – | S |

> **Uso no sistema Primetax:** este registro é a âncora de identificação. Campo `IND_NAT_PJ` determina se registros de cooperativas (M211/M611) serão aplicáveis; `IND_ATIV` influencia as hipóteses de creditamento aplicáveis (PJ imobiliária tem regime próprio no F200/F205/F210).

### 14.2 Registro `0110` — Regimes de Apuração da Contribuição Social e de Apropriação de Crédito

Nível 2, ocorrência 1 por arquivo, **obrigatório**. Define o regime de incidência e o método de apropriação de créditos comuns.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "0110" | C | 004* | – | S |
| 02 | `COD_INC_TRIB` | Regime: 1 – Não-cumulativo exclusivo; 2 – Cumulativo exclusivo; 3 – Ambos | N | 001* | – | S |
| 03 | `IND_APRO_CRED` | Método de apropriação (se `COD_INC_TRIB = 1 ou 3`): 1 – Apropriação Direta; 2 – Rateio Proporcional (Receita Bruta) | N | 001* | – | N |
| 04 | `COD_TIPO_CONT` | Tipo de contribuição: 1 – Exclusivamente alíquota básica; 2 – Alíquotas específicas (diferenciadas ou por unidade) | N | 001* | – | N |
| 05 | `IND_REG_CUM` | Critério de escrituração (PJ Lucro Presumido, se `COD_INC_TRIB = 2`): 1 – Regime de Caixa (F500); 2 – Regime de Competência consolidada (F550); 9 – Regime de Competência detalhada nos Blocos A/C/D/F | N | 001* | – | N |

**Observações do manual:**

- Se `COD_TIPO_CONT = 2`, deve existir algum registro M210/M610 com `COD_CONT ∈ {02, 03, 52, 53}`.
- O Campo 05 só é aplicável em versões 2.01A+ do PVA.

> **Uso no sistema Primetax:** este é o **primeiro nó de decisão do motor de cruzamento**. A interpretação de todos os CSTs, alíquotas, rateios e créditos depende dos valores deste registro. O sistema deve ler `0110` antes de qualquer outro processamento e persistir esses parâmetros como contexto global da escrituração.

### 14.3 Registro `0111` — Tabela de Receita Bruta Mensal para Rateio de Créditos Comuns

Nível 3, ocorrência 1:1, **obrigatório quando `0110.IND_APRO_CRED = 2`** (Rateio Proporcional).

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "0111" | C | – | S |
| 02 | `REC_BRU_NCUM_TRIB_MI` | Receita Bruta Não-Cumulativa – Tributada no Mercado Interno | N | 02 | S |
| 03 | `REC_BRU_NCUM_NT_MI` | Receita Bruta Não-Cumulativa – Não Tributada no Mercado Interno (suspensão, alíquota zero, isenção, sem incidência) | N | 02 | S |
| 04 | `REC_BRU_NCUM_EXP` | Receita Bruta Não-Cumulativa – Exportação | N | 02 | S |
| 05 | `REC_BRU_CUM` | Receita Bruta Cumulativa | N | 02 | S |
| 06 | `REC_BRU_TOTAL` | Receita Bruta Total (soma dos campos 02 a 05) | N | 02 | S |

**Observações do manual (importantes para a Primetax):**

- Conforme **Lei 12.973/2014 (art. 12 do DL 1.598/77)**, a receita bruta compreende:
  - (I) produto da venda de bens em conta própria
  - (II) preço da prestação de serviços
  - (III) resultado em conta alheia
  - (IV) receitas da atividade ou objeto principal não compreendidas em I–III
- **Não se classificam como receita bruta** (e não devem entrar no rateio):
  - Receitas não operacionais (venda de ativo imobilizado)
  - Receitas financeiras, aluguéis de móveis/imóveis alheios à atividade
  - Reversões de provisões e recuperações de perdas
  - Resultado positivo de equivalência patrimonial, dividendos de investimentos avaliados pelo custo

> **Uso no sistema Primetax:** oportunidade de cruzamento clássica: **empresas que informam no 0111 receitas que não são receita bruta** (tipicamente financeiras ou de venda de imobilizado) inflam artificialmente a proporção de receita tributada, **reduzindo créditos apropriáveis**. Checagem contra a DIPJ/ECF e ECD (registro J150 — Demonstração do Resultado do Exercício) é altamente recomendada.

### 14.4 Registro `0140` — Tabela de Cadastro de Estabelecimento

Nível 2, ocorrência V (várias por arquivo — uma por estabelecimento).

| # | Campo | Descrição | Tipo | Tam | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "0140" | C | 004* | S |
| 02 | `COD_EST` | Código do estabelecimento | C | 060 | S |
| 03 | `NOME` | Nome empresarial | C | 100 | S |
| 04 | `CNPJ` | CNPJ | N | 014* | S |
| 05 | `UF` | UF | C | 002* | N |
| 06 | `IE` | Inscrição Estadual | C | 014 | N |
| 07 | `COD_MUN` | Código IBGE | N | 007* | N |
| 08 | `IM` | Inscrição Municipal | C | – | N |
| 09 | `SUFRAMA` | Inscrição SUFRAMA | C | 009* | N |

### 14.5 Registro `0150` — Tabela de Cadastro do Participante

Nível 3, ocorrência 1:N.

| # | Campo | Descrição | Tipo | Tam | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "0150" | C | 004* | S |
| 02 | `COD_PART` | Código de identificação do participante | C | 060 | S |
| 03 | `NOME` | Nome empresarial | C | 100 | S |
| 04 | `COD_PAIS` | Código do país (tabela BACEN) | N | 005 | S |
| 05 | `CNPJ` | CNPJ (se PJ nacional) | N | 014* | N |
| 06 | `CPF` | CPF (se PF) | N | 011* | N |
| 07 | `IE` | Inscrição Estadual | C | 014 | N |
| 08 | `COD_MUN` | Código do município (tabela IBGE) | N | 007* | N |
| 09 | `SUFRAMA` | Inscrição SUFRAMA | C | 009* | N |
| 10 | `END` | Endereço (logradouro) | C | 060 | N |
| 11 | `NUM` | Número | C | 010 | N |
| 12 | `COMPL` | Complemento | C | 060 | N |
| 13 | `BAIRRO` | Bairro | C | 060 | N |

### 14.6 Registro `0200` — Tabela de Identificação do Item (Produtos e Serviços)

Nível 3, ocorrência 1:N. Cadastro de itens referenciados nos blocos de documentos.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "0200" | C | 004* | – | S |
| 02 | `COD_ITEM` | Código próprio do item | C | 060 | – | S |
| 03 | `DESCR_ITEM` | Descrição do item | C | – | – | S |
| 04 | `COD_BARRA` | Código de barras (GTIN) | C | – | – | N |
| 05 | `COD_ANT_ITEM` | Código anterior do item | C | 060 | – | N |
| 06 | `UNID_INV` | Unidade de medida do inventário | C | 006 | – | S |
| 07 | `TIPO_ITEM` | Tipo do item: 00 – Mercadoria para revenda; 01 – Matéria-prima; 02 – Embalagem; 03 – Produto em processo; 04 – Produto acabado; 05 – Subproduto; 06 – Produto intermediário; 07 – Material de uso e consumo; 08 – Ativo imobilizado; 09 – Serviços; 10 – Outros insumos; 99 – Outras | N | 002* | – | S |
| 08 | `COD_NCM` | NCM | C | 008* | – | N |
| 09 | `EX_IPI` | Ex da TIPI | C | 003 | – | N |
| 10 | `COD_GEN` | Código do gênero | N | 002* | – | N |
| 11 | `COD_LST` | Código do serviço (LC 116/2003) | C | 005 | – | N |
| 12 | `ALIQ_ICMS` | Alíquota de ICMS nas saídas internas | N | 006 | 02 | N |

> **Uso no sistema Primetax:** o campo `TIPO_ITEM` é decisivo para classificação de créditos. Itens com `TIPO_ITEM = 01` (matéria-prima), `02` (embalagem), `06` (produto intermediário), `10` (outros insumos) são candidatos primários a creditamento. `TIPO_ITEM = 07` (uso e consumo) historicamente não gera crédito, **mas** é onde mais frequentemente encontram-se itens reclassificáveis sob a tese da essencialidade/relevância (REsp 1.221.170/PR) — **área de alta oportunidade para recuperação**.

### 14.7 Registro `0500` — Plano de Contas Contábeis

Nível 2, ocorrência V.

| # | Campo | Descrição | Tipo | Tam | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "0500" | C | 004* | S |
| 02 | `DT_ALT` | Data da alteração ou inclusão | N | 008* | S |
| 03 | `COD_NAT_CC` | Código da natureza da conta: 01 – Ativo; 02 – Passivo; 03 – Patrimônio Líquido; 04 – Resultado; 05 – Clearing (conta de compensação); 09 – Outras | C | 002* | N |
| 04 | `IND_CTA` | Indicador de sintético/analítico: S – Sintética; A – Analítica | C | 001* | S |
| 05 | `NIVEL` | Nível da conta no plano | N | – | S |
| 06 | `COD_CTA` | Código da conta | C | 255 | S |
| 07 | `NOME_CTA` | Nome da conta | C | 060 | S |
| 08 | `COD_CTA_REF` | Código da conta de referência | C | 255 | N |
| 09 | `CNPJ_EST` | CNPJ do estabelecimento (se a conta for específica de um) | N | 014* | N |

> **Uso no sistema Primetax:** o plano de contas é a ponte para o cruzamento EFD-Contribuições × ECD. O campo `COD_CTA` referenciado em C170 (campo 37), C175 (campo 11), M105 (a partir de nov/2017), M505, etc., permite amarrar cada lançamento fiscal à escrituração contábil. Divergências entre valores consolidados por conta no EFD-Contribuições e saldos de conta na ECD indicam inconsistência grave.

### 14.8 Registro `0900` — Composição das Receitas do Período – Receita Bruta e Demais Receitas

Nível 2, ocorrência 1 por arquivo. Obrigatório se a escrituração for transmitida após o prazo regular.

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "0900" | C | – | S |
| 02 | `REC_BRU_NCUM_TRIB_MI` | Receita Bruta Não-Cumulativa Tributada no MI | N | 02 | S |
| 03 | `REC_BRU_NCUM_NT_MI` | Receita Bruta Não-Cumulativa Não Tributada no MI | N | 02 | S |
| 04 | `REC_BRU_NCUM_EXP` | Receita Bruta Não-Cumulativa de Exportação | N | 02 | S |
| 05 | `REC_BRU_CUM` | Receita Bruta Cumulativa | N | 02 | S |
| 06 | `REC_BRU_TOTAL` | Receita Bruta Total | N | 02 | S |
| 07 | `REC_RECEB_REGIME_CX` | Receitas Recebidas (Regime de Caixa) | N | 02 | N |
| 08 | `REC_AUF_REGIME_COMP` | Receitas Auferidas (Regime de Competência) | N | 02 | N |
| 09 | `REC_BLOCO_A` | Receita dos documentos do Bloco A (serviços) | N | 02 | N |
| 10 | `REC_BLOCO_C` | Receita dos documentos do Bloco C (mercadorias) | N | 02 | N |
| 11 | `REC_BLOCO_D` | Receita dos documentos do Bloco D (transporte/telecom) | N | 02 | N |
| 12 | `REC_BLOCO_F` | Receita dos documentos do Bloco F (demais) | N | 02 | N |
| 13 | `REC_BLOCO_I` | Receita dos documentos do Bloco I (inst. financeiras) | N | 02 | N |
| 14 | `REC_TOTAL_PERIODO` | Receita Total do Período | N | 02 | S |

---

## 15. Registros detalhados do Bloco C

### 15.1 Registro `C100` — Documento Nota Fiscal

Nível 3, ocorrência 1:N. Registro de referência para notas fiscais (códigos 01, 1B, 04, 55). Estrutura definida no Leiaute da EFD ICMS/IPI (Ato COTEPE/ICMS nº 9/2008).

Campos principais (estrutura conforme EFD ICMS/IPI):

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "C100" |
| 02 | `IND_OPER` | 0 – Entrada; 1 – Saída |
| 03 | `IND_EMIT` | 0 – Emissão própria; 1 – Terceiros |
| 04 | `COD_PART` | Código do participante (0150) |
| 05 | `COD_MOD` | Código do modelo do documento (tabela de modelos) |
| 06 | `COD_SIT` | Situação do documento: 00 – Regular; 01 – Extemporâneo; 02 – NF complementar; 03 – NF complementar extemporânea; 04 – Regular – NF-e com operação em denegação; 05 – NF emitida com numeração inutilizada; 06 – NF Complementar – extemporâneo; 07 – NF-e com numeração inutilizada; 08 – NF-e emitida em contingência |
| 07 | `SER` | Série |
| 08 | `NUM_DOC` | Número do documento |
| 09 | `CHV_NFE` | Chave da NF-e (44 posições) |
| 10 | `DT_DOC` | Data da emissão (`ddmmaaaa`) |
| 11 | `DT_E_S` | Data de entrada/saída |
| 12 | `VL_DOC` | Valor total do documento |
| 13 | `IND_PGTO` | 0 – À vista; 1 – A prazo; 2 – Outros |
| 14 | `VL_DESC` | Desconto total do documento |
| 15 | `VL_ABAT_NT` | Abatimento não tributado |
| 16 | `VL_MERC` | Valor total das mercadorias |
| 17 | `IND_FRT` | Indicador do tipo de frete |
| 18 | `VL_FRT` | Valor do frete |
| 19 | `VL_SEG` | Valor do seguro |
| 20 | `VL_OUT_DA` | Outras despesas acessórias |
| 21 | `VL_BC_ICMS` | Base de cálculo do ICMS |
| 22 | `VL_ICMS` | Valor do ICMS |
| 23 | `VL_BC_ICMS_ST` | Base de cálculo do ICMS-ST |
| 24 | `VL_ICMS_ST` | Valor do ICMS-ST |
| 25 | `VL_IPI` | Valor do IPI |
| 26 | `VL_PIS` | Valor do PIS |
| 27 | `VL_COFINS` | Valor da COFINS |
| 28 | `VL_PIS_ST` | Valor do PIS-ST |
| 29 | `VL_COFINS_ST` | Valor da COFINS-ST |

### 15.2 Registro `C170` — Complemento do Documento – Itens do Documento

Nível 4, ocorrência 1:N. **Registro-espinha-dorsal do cruzamento Primetax.** Descreve item a item os produtos/serviços das notas C100, com ICMS, IPI, PIS e COFINS simultaneamente.

| # | Campo | Descrição | Tipo | Tam | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|:---:|
| 01 | `REG` | "C170" | C | 004 | – | S |
| 02 | `NUM_ITEM` | Número sequencial do item | N | 003 | – | S |
| 03 | `COD_ITEM` | Código do item (referencia 0200) | C | 060 | – | S |
| 04 | `DESCR_COMPL` | Descrição complementar | C | – | – | N |
| 05 | `QTD` | Quantidade | N | – | 05 | N |
| 06 | `UNID` | Unidade (referencia 0190) | C | 006 | – | N |
| 07 | `VL_ITEM` | Valor total do item | N | – | 02 | S |
| 08 | `VL_DESC` | Desconto comercial / exclusão de base de PIS/COFINS | N | – | 02 | N |
| 09 | `IND_MOV` | Movimentação física: 0 – Sim; 1 – Não | C | 001 | – | N |
| 10 | `CST_ICMS` | CST-ICMS (tabela 4.3.1) | N | 003* | – | N |
| 11 | `CFOP` | CFOP | N | 004* | – | S |
| 12 | `COD_NAT` | Código da natureza da operação (referencia 0400) | C | 010 | – | N |
| 13 | `VL_BC_ICMS` | Base de cálculo do ICMS | N | – | 02 | N |
| 14 | `ALIQ_ICMS` | Alíquota do ICMS | N | 006 | 02 | N |
| 15 | `VL_ICMS` | **Valor do ICMS destacado** | N | – | 02 | N |
| 16 | `VL_BC_ICMS_ST` | Base do ICMS-ST | N | – | 02 | N |
| 17 | `ALIQ_ST` | Alíquota do ICMS-ST destino | N | 006 | 02 | N |
| 18 | `VL_ICMS_ST` | Valor do ICMS-ST | N | – | 02 | N |
| 19 | `IND_APUR` | Período de apuração IPI: 0 – Mensal; 1 – Decendial | C | 001* | – | N |
| 20 | `CST_IPI` | CST-IPI (tabela 4.3.2) | C | 002* | – | N |
| 21 | `COD_ENQ` | Enquadramento legal do IPI | C | 003* | – | N |
| 22 | `VL_BC_IPI` | Base de cálculo do IPI | N | – | 02 | N |
| 23 | `ALIQ_IPI` | Alíquota do IPI | N | 006 | 02 | N |
| 24 | `VL_IPI` | Valor do IPI creditado/debitado | N | – | 02 | N |
| 25 | `CST_PIS` | **CST-PIS (tabela 4.3.3)** | N | 002* | – | S |
| 26 | `VL_BC_PIS` | **Base de cálculo do PIS** | N | – | 02 | N |
| 27 | `ALIQ_PIS` | Alíquota do PIS (%) | N | 008 | 04 | N |
| 28 | `QUANT_BC_PIS` | Base de cálculo PIS em quantidade | N | – | 03 | N |
| 29 | `ALIQ_PIS_QUANT` | Alíquota do PIS (em reais) | N | – | 04 | N |
| 30 | `VL_PIS` | Valor do PIS | N | – | 02 | N |
| 31 | `CST_COFINS` | **CST-COFINS (tabela 4.3.4)** | N | 002* | – | S |
| 32 | `VL_BC_COFINS` | **Base de cálculo da COFINS** | N | – | 02 | N |
| 33 | `ALIQ_COFINS` | Alíquota da COFINS (%) | N | 008 | 04 | N |
| 34 | `QUANT_BC_COFINS` | Base de cálculo COFINS em quantidade | N | – | 03 | N |
| 35 | `ALIQ_COFINS_QUANT` | Alíquota da COFINS (em reais) | N | – | 04 | N |
| 36 | `VL_COFINS` | Valor da COFINS | N | – | 02 | N |
| 37 | `COD_CTA` | Código da conta analítica (referencia 0500) | C | 255 | – | N |

**Regras críticas do manual para o sistema Primetax:**

1. **Enfoque do declarante:** em documentos de entrada, os campos de imposto só são preenchidos se o **adquirente** tiver direito ao crédito. Ausência de preenchimento não equivale a ausência de direito — pode ser erro.

2. **Propagação para o Bloco M:** os campos de base de cálculo (26, 28, 32, 34) são recuperados no Bloco M:
   - Se CST representa débito: propagado para `M210.VL_BC_CONT` (PIS) e `M610.VL_BC_CONT` (COFINS)
   - Se CST representa crédito (série 50+): propagado para `M105.VL_BC_PIS_TOT` e `M505.VL_BC_COFINS_TOT`

3. **CFOP filtra creditamento:** a funcionalidade "Gerar Apurações" do PVA só considera, para geração de M105/M505, itens cujo CFOP esteja listado na "Tabela CFOP – Operações Geradoras de Crédito" (publicada no portal SPED). CFOPs relevantes incluem:
   - Aquisição para revenda
   - Aquisição de insumos
   - Aquisição de serviços como insumo
   - Devolução de vendas sujeitas ao regime não-cumulativo
   - Outras operações com direito a crédito

4. **Ativo imobilizado:** aquisições de bens do ativo imobilizado **não** devem ser informadas em C170. Vão no F120 (crédito sobre encargos de depreciação) ou F130 (crédito sobre valor de aquisição). Se constarem em C170, os campos CST_PIS e CST_COFINS devem ser preenchidos com CST 98 ou 99.

5. **Não informar em C170 (registros próprios):**
   - Energia elétrica (C500/C600)
   - Transporte (D100/D200)
   - Bilhetes de passagem (D300/D350)
   - Comunicação/telecom (D500/D600)
   - Água canalizada/gás (C500/C600)
   - Cupom Fiscal (C400/C490)

6. **Validação de base de cálculo × alíquota:**
   - `VL_PIS = (VL_BC_PIS × ALIQ_PIS) / 100` (ou `QUANT_BC_PIS × ALIQ_PIS_QUANT`)
   - `VL_COFINS = (VL_BC_COFINS × ALIQ_COFINS) / 100` (ou `QUANT_BC_COFINS × ALIQ_COFINS_QUANT`)

7. **Campo `COD_CTA` obrigatório a partir de novembro/2017**, exceto para PJ dispensada de ECD (lucro presumido com livro caixa).

> **Cruzamentos primários do sistema Primetax centrados em C170:**
>
> 1. **Aderência VL_ICMS vs VL_BC_PIS (Tese 69):** `VL_BC_PIS == VL_ITEM - VL_DESC - VL_ICMS` quando CST_PIS ∈ {01, 02, 03, 05}.
> 2. **Consistência EFD-Contribuições × EFD ICMS/IPI:** mesmo `VL_ICMS` na mesma chave NF-e entre as duas declarações.
> 3. **Integridade CST × CFOP × alíquota:** CFOP deve ser compatível com CST (ex: CFOP de devolução com CST 50–56; CFOP de aquisição com CST 50+).
> 4. **Itens com TIPO_ITEM 07 (uso/consumo) e CFOP de insumo:** candidatos à reclassificação para creditamento sob REsp 1.221.170/PR.
> 5. **Itens com CST 70–75 (aquisição sem crédito):** auditoria individual — frequentemente reclassificáveis.

### 15.3 Registro `C175` — Registro Analítico do Documento (NFC-e — cód. 65)

Nível 4, ocorrência 1:N. Disponibilizado a partir da versão 2.09 do PVA.

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "C175" | C | – | S |
| 02 | `CFOP` | CFOP | N | – | S |
| 03 | `VL_OPR` | Valor da operação | N | 02 | S |
| 04 | `VL_DESC` | Valor de desconto / exclusão (**inclui exclusão ICMS**) | N | 02 | N |
| 05 | `CST_PIS` | CST-PIS | N | – | S |
| 06 | `VL_BC_PIS` | Base de cálculo do PIS | N | 02 | N |
| 07 | `ALIQ_PIS` | Alíquota do PIS (%) | N | 04 | N |
| 08 | `QUANT_BC_PIS` | Base PIS em quantidade | N | 03 | N |
| 09 | `ALIQ_PIS_QUANT` | Alíquota PIS em reais | N | 04 | N |
| 10 | `VL_PIS` | Valor do PIS | N | 02 | N |
| 11 | `CST_COFINS` | CST-COFINS | N | – | S |
| 12 | `VL_BC_COFINS` | Base de cálculo da COFINS | N | 02 | N |
| 13 | `ALIQ_COFINS` | Alíquota da COFINS (%) | N | 04 | N |
| 14 | `QUANT_BC_COFINS` | Base COFINS em quantidade | N | 03 | N |
| 15 | `ALIQ_COFINS_QUANT` | Alíquota COFINS em reais | N | 04 | N |
| 16 | `VL_COFINS` | Valor da COFINS | N | 02 | N |
| 17 | `COD_CTA` | Conta contábil | C | – | N |
| 18 | `INFO_COMPL` | Informação complementar | C | – | N |

### 15.4 Registro `C181` — Detalhamento da Consolidação – Vendas – PIS/Pasep

Nível 4, ocorrência 1:N. Detalhamento do C180 (consolidação de NF-e de saída emitidas pela PJ), segregado por CST-PIS, CFOP e alíquotas.

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "C181" | C | – | S |
| 02 | `CST_PIS` | CST-PIS | N | – | S |
| 03 | `CFOP` | CFOP | N | – | S |
| 04 | `VL_ITEM` | Valor total dos itens (consolidado) | N | 02 | S |
| 05 | `VL_DESC` | Valor de desconto / exclusão (**inclui exclusão ICMS**) | N | 02 | N |
| 06 | `VL_BC_PIS` | Base de cálculo do PIS | N | 02 | N |
| 07 | `ALIQ_PIS` | Alíquota (%) | N | 04 | N |
| 08 | `QUANT_BC_PIS` | Base em quantidade | N | 03 | N |
| 09 | `ALIQ_PIS_QUANT` | Alíquota em reais | N | 04 | N |
| 10 | `VL_PIS` | Valor do PIS | N | 02 | N |
| 11 | `COD_CTA` | Conta contábil | C | – | N |

### 15.5 Registro `C185` — Detalhamento da Consolidação – Vendas – COFINS

Estrutura análoga ao C181, trocando PIS → COFINS.

| # | Campo | Descrição | Tipo | Dec | Obrig |
|:---:|---|---|:---:|:---:|:---:|
| 01 | `REG` | "C185" | C | – | S |
| 02 | `CST_COFINS` | CST-COFINS | N | – | S |
| 03 | `CFOP` | CFOP | N | – | S |
| 04 | `VL_ITEM` | Valor total dos itens (consolidado) | N | 02 | S |
| 05 | `VL_DESC` | Valor de desconto / exclusão (**inclui exclusão ICMS**) | N | 02 | N |
| 06 | `VL_BC_COFINS` | Base de cálculo da COFINS | N | 02 | N |
| 07 | `ALIQ_COFINS` | Alíquota (%) | N | 04 | N |
| 08 | `QUANT_BC_COFINS` | Base em quantidade | N | 03 | N |
| 09 | `ALIQ_COFINS_QUANT` | Alíquota em reais | N | 04 | N |
| 10 | `VL_COFINS` | Valor da COFINS | N | 02 | N |
| 11 | `COD_CTA` | Conta contábil | C | – | N |

### 15.6 Registros `C191` e `C195` — Detalhamento da Consolidação – Aquisições com Crédito – PIS/COFINS

Estrutura análoga aos C181/C185 porém para aquisições com direito a crédito e devoluções, incluindo identificação do fornecedor:

| # | Campo (C191/C195) | Descrição |
|:---:|---|---|
| 01 | `REG` | "C191" ou "C195" |
| 02 | `COD_PART` | Código do participante (fornecedor) |
| 03 | `CST_PIS` / `CST_COFINS` | CST da aquisição (série 50+) |
| 04 | `CFOP` | CFOP de entrada/devolução |
| 05 | `VL_ITEM` | Valor consolidado |
| 06 | `VL_DESC` | Desconto / exclusão |
| 07 | `NAT_BC_CRED` | Código da natureza da base de cálculo do crédito (tabela 4.3.7) |
| 08 | `VL_BC_PIS` / `VL_BC_COFINS` | Base de crédito |
| 09 | `ALIQ_PIS` / `ALIQ_COFINS` | Alíquota (%) |
| 10 | `QUANT_BC_PIS` / `QUANT_BC_COFINS` | Base em quantidade |
| 11 | `ALIQ_PIS_QUANT` / `ALIQ_COFINS_QUANT` | Alíquota em reais |
| 12 | `VL_PIS` / `VL_COFINS` | Valor do crédito |
| 13 | `COD_CTA` | Conta contábil |

### 15.7 Registros `C381`/`C385` — Detalhamento da Consolidação NF ao Consumidor (cód. 02)

Consolidam vendas a consumidor (NF modelo 02 — não eletrônica), segregadas por CST, CFOP e alíquota.

| # | Campo | Descrição |
|:---:|---|---|
| 01 | `REG` | "C381" ou "C385" |
| 02 | `CST_PIS` / `CST_COFINS` | CST |
| 03 | `VL_ITEM` | Valor dos itens (consolidado) |
| 04 | `VL_BC_PIS` / `VL_BC_COFINS` | Base (**onde a exclusão do ICMS é aplicada diretamente — Seção 12**) |
| 05 | `ALIQ_PIS` / `ALIQ_COFINS` | Alíquota |
| 06 | `QUANT_BC_PIS` / `QUANT_BC_COFINS` | Base em quantidade |
| 07 | `ALIQ_PIS_QUANT` / `ALIQ_COFINS_QUANT` | Alíquota em reais |
| 08 | `VL_PIS` / `VL_COFINS` | Valor |
| 09 | `COD_CTA` | Conta contábil |

### 15.8 Registros `C481`/`C485` — Resumo Diário de Documentos Emitidos por ECF – PIS/COFINS

Consolidam vendas por Emissor de Cupom Fiscal (ECF — códigos 02 e 2D), segregadas por CST, alíquota, equipamento.

Estrutura similar aos C381/C385, com campo adicional de identificação do equipamento ECF.

### 15.9 Registros `C491`/`C495` — Detalhamento da Consolidação de Documentos Emitidos por ECF

Consolidação alternativa (ao C481/C485) por CFOP, CST e alíquota, sem detalhar por equipamento.

### 15.10 Registros `C500`, `C501`, `C505` — NF/Conta de Energia Elétrica, Água, Gás (Aquisição com Crédito)

`C500` é a nota fiscal/conta de fornecimento (energia elétrica cód. 06, gás 28, água 29, NF-e 55 e NF3e 66) de entrada com crédito. `C501` (PIS) e `C505` (COFINS) são os complementos por CST, alíquota e CFOP.

Campos-chave no C501/C505: `CST_PIS`/`CST_COFINS`, `NAT_BC_CRED`, `VL_ITEM`, `VL_BC_PIS`/`VL_BC_COFINS`, `ALIQ_PIS`/`ALIQ_COFINS`, `VL_PIS`/`VL_COFINS`.

### 15.11 Registros `C600`, `C601`, `C605` — Consolidação Diária de Saídas de Energia/Água/Gás

Análogo aos C500+ mas para saídas (prestação de serviço pela concessionária). `C601`/`C605` são os complementos PIS/COFINS.

### 15.12 Registros `C800` a `C890` — CF-e (Cupom Fiscal Eletrônico cód. 59)

Série de registros para escrituração do CF-e emitido por equipamento SAT, análogos em função aos C400/C490 para ECF tradicional, com detalhamentos por CST, alíquota e unidade de medida quando aplicável.

---

## 16. Próximos passos — Partes 2 e 3

A **Parte 2** cobrirá:

- Bloco D detalhado (D100, D101, D105, D200, D201, D205, D300, D350, D500, D501, D505, D600, D601, D605) — transporte e comunicação
- Bloco F detalhado (F100, F120, F130, F150, F200, F205, F210, F500, F550, F600, F700, F800) — demais operações, incluindo ativo imobilizado (**centro de grandes créditos não aproveitados**)
- Bloco I (visão geral para instituições financeiras)

A **Parte 3** cobrirá:

- Bloco M integral (M100/M105, M110/M115, M200/M205/M210, M211, M215, M220/M225, M230, M300, M350, M400/M410, e análogos M500+ para COFINS)
- Bloco 1 integral (1010/1011 ação judicial, 1020 processo administrativo, 1050 ajustes de BC, 1100/1101/1102 créditos extemporâneos PIS, 1500/1501/1502 créditos extemporâneos COFINS, 1200/1210/1220 e 1600/1610/1620 contribuição social extemporânea, 1300/1700 controle de retenções, 1900 consolidação PJ Presumido) — **bloco crítico para teses extemporâneas da Primetax**
- Bloco P (CPRB) — visão resumida
- Bloco 9 (encerramento)

---

## 17. Referências normativas mapeadas

- **Lei 10.637/2002** — Regime não-cumulativo do PIS/Pasep
- **Lei 10.833/2003** — Regime não-cumulativo da COFINS
- **Lei 12.973/2014** — Conceito de receita bruta (art. 12 DL 1.598/77)
- **Lei 10.522/2002, art. 19-A** — Vinculação da RFB a decisões do STF após manifestação da PGFN
- **Lei 13.097/2015, arts. 14–34** — Regime de bebidas frias
- **IN RFB 1.009/2010** — Tabelas de CST-PIS e CST-COFINS (Anexo Único, Tabelas II e III)
- **IN RFB 1.252/2012 e alterações** — EFD-Contribuições
- **Ato COTEPE/ICMS 9/2008** — Leiaute da EFD ICMS/IPI (fonte da estrutura do C100/C170)
- **RE 574.706/PR (Tema 69)** — Exclusão do ICMS da base do PIS/COFINS
- **Parecer SEI nº 7698/2021/ME** — Operacionalização da Tese 69 pela PGFN
- **REsp 1.221.170/PR (Tema 779)** — Conceito de insumo (essencialidade/relevância) para PIS/COFINS não-cumulativos

---

*Fim da Parte 1 de 3.*
