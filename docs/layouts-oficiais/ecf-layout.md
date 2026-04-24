# ECF — Escrituração Contábil Fiscal — Guia Prático de Importação e Referência

**Versão do leiaute coberta:** Leiaute 12 (COD\_VER 0012\) — Anexo ao Ato Declaratório Executivo Cofis nº 02/2026, atualização janeiro de 2026 **Vigência:** aplicável ao ano-calendário 2025 e situações especiais de 2026 **Base normativa:** Instrução Normativa RFB nº 2.004/2021 (e alterações) e Decreto nº 6.022/2007 (SPED) **Fonte original:** Manual de Orientação do Leiaute 12 da Escrituração Contábil Fiscal — RFB/Subsecretaria de Fiscalização **Objetivo deste documento:** servir como referência técnica instrumental para o sistema Primetax SPED Cross-Reference. O foco é extrair da ECF os elementos necessários ao cruzamento com a ECD e com a EFD-Contribuições, e à validação de teses envolvendo IRPJ, CSLL, lucro presumido, compensação de prejuízos fiscais e bases de cálculo negativas da CSLL. Este arquivo NÃO se propõe a ser enciclopédico sobre a apuração do IRPJ/CSLL em si; esse é escopo de outro projeto.

---

## Índice

1. Visão geral estrutural  
2. Blocos da ECF e hierarquia  
3. Regras gerais de preenchimento  
4. Registro 0000 — identificação e retificação  
5. Registro 0010 — Parâmetros de Tributação (discriminador central)  
6. Demais registros do Bloco 0  
7. Bloco C — informações recuperadas da ECD  
8. Bloco E — saldos da ECF anterior e cálculo fiscal sobre a ECD  
9. Bloco J — plano de contas do contribuinte e referencial  
10. Bloco K — saldos contábeis patrimoniais e referenciais  
11. Bloco L — Lucro Líquido (BP e DRE para Lucro Real)  
12. Bloco M — e-Lalur e e-Lacs (o coração fiscal da ECF)  
13. Bloco N — cálculo do IRPJ e da CSLL no Lucro Real  
14. Bloco P — Lucro Presumido  
15. Bloco Q — Livro Caixa (Lucro Presumido opcional)  
16. Bloco T — Lucro Arbitrado  
17. Bloco U — Imunes e Isentas  
18. Bloco V — DEREX (recursos em moeda estrangeira de exportação)  
19. Bloco W — Declaração País-a-País (CBCR)  
20. Bloco X — Informações Econômicas  
21. Bloco Y — Informações Gerais  
22. Bloco 9 — controle e encerramento  
23. Tabelas dinâmicas e planos referenciais  
24. Mapeamento de cruzamentos ECF ↔ ECD ↔ EFD-Contribuições  
25. Tese 69 e outras teses refletidas na ECF  
26. Divisores de águas e versionamento do leiaute  
27. Referências normativas  
28. Recomendação operacional para o parser

---

## 1\. Visão geral estrutural

A ECF é a escrituração fiscal que substitui, desde o ano-calendário 2014, a antiga DIPJ e o Livro de Apuração do Lucro Real (Lalur) em papel. Entrega obrigatória para todas as pessoas jurídicas, exceto as optantes pelo Simples Nacional, as inativas que entregam a DSPJ-Inativa, os órgãos públicos e alguns casos específicos de autarquias/fundações públicas.

Integra-se organicamente com a ECD (recupera plano de contas, saldos contábeis e DRE) e é o destino final das informações de apuração dos dois tributos federais diretos sobre o lucro: **IRPJ e CSLL**.

### 1.1 Natureza do arquivo

- Arquivo-texto codificado, campos separados pelo caractere pipe (`|`), cada linha iniciada e terminada por `|`  
- Estrutura hierárquica pai-filho identificada pelos primeiros caracteres de cada linha (`REG`)  
- Os primeiros caracteres do `REG` identificam o bloco (ex: `M300` → Bloco M; `L300` → Bloco L; `N630` → Bloco N)  
- A ECF é **anual** (um arquivo por ano-calendário, salvo situação especial), mas contém dentro de si os detalhamentos trimestrais ou mensais conforme a forma de apuração escolhida

### 1.2 Diferenças operacionais críticas em relação aos demais SPEDs

Para calibrar o parser Primetax, cinco diferenças são essenciais:

1. **A ECF não tem perfil nem forma de escrituração** — ela tem `FORMA_TRIB` (regime tributário) no registro 0010, que é o discriminador central que define quais blocos do arquivo serão preenchidos.  
2. **Muitos registros da ECF são baseados em tabelas dinâmicas** publicadas separadamente pela RFB (M300, M350, L100, L300, N500, N620, N630, N650, N660, N670, P100, P150, P200, P300, P400, P500, T120, T150, T170, T181, U100, U150, U180, U182, K156, K356, E155, E355). Isso significa que o campo `CODIGO` desses registros referencia uma planilha externa (`Tabelas_Dinamicas_ECF_Leiaute_X_...xlsx`) disponibilizada no Portal SPED, com semântica que pode evoluir entre anos-calendário. **O parser Primetax deve manter um snapshot por ano-calendário dessas tabelas dinâmicas** — sem elas, os códigos do M300 (adições/exclusões) são números opacos.  
3. **A ECF recupera automaticamente a ECD do mesmo período** (via hashcode no Bloco C) e a ECF do período imediatamente anterior (via hashcode no Bloco E). A integridade dessas cadeias é checada por regras próprias (REGRA\_COMPATIBILIDADE\_K155\_E155, REGRA\_EXISTENCIA\_E015\_K155, etc.).  
4. **O e-Lalur e o e-Lacs são integralmente eletrônicos** nos Blocos M e N (para Lucro Real). Não existe Lalur em papel desde 2014\. A Parte A do e-Lalur fica no M300; a Parte B, no M305/M410/M500; o espelho para CSLL (e-Lacs) está em M350/M355/M410/M500.  
5. **A ECF consolida o livro caixa do Lucro Presumido** (Bloco Q) quando o contribuinte opta por não entregar a ECD — substituindo-a como documento de memória dos fatos contábeis-fiscais.

### 1.3 Campo-chave de unicidade

O registro 0000 identifica unicamente uma escrituração no PGE por:

```
(0000.CNPJ básico — 8 primeiras posições, 0000.COD_SCP, 0000.DT_FIN)
```

Qualquer retransmissão para o mesmo conjunto é tratada como retificadora — e o PGE exige o `NUM_REC` (hashcode) da ECF anterior para permitir a substituição.

---

## 2\. Blocos da ECF e hierarquia

A ECF tem **15 blocos** (0, C, E, J, K, L, M, N, P, Q, T, U, V, W, X, Y, 9), sendo nem todos obrigatórios para cada tipo de contribuinte. A tabela a seguir indica o uso de cada bloco conforme a forma de tributação:

| Bloco | Descrição | Lucro Real | Lucro Presumido | Lucro Arbitrado | Imune/Isenta |
| :---: | :---- | :---: | :---: | :---: | :---: |
| **0** | Abertura, identificação, parâmetros | O | O | O | O |
| **C** | Informações recuperadas da ECD | O (se tem ECD) | O (se tem ECD) | O (se tem ECD) | O (se tem ECD) |
| **E** | Saldos da ECF anterior e cálculo fiscal da ECD | O | O | O | O |
| **J** | Plano de contas do contribuinte e referencial | O | O | O | O |
| **K** | Saldos contábeis patrimoniais e referenciais | O | O | O | O |
| **L** | Lucro Líquido — BP e DRE | **O** | N | N | N |
| **M** | e-Lalur (IRPJ) e e-Lacs (CSLL) | **O** | N | N | N |
| **N** | Cálculo do IRPJ e da CSLL — Lucro Real | **O** | N | N | N |
| **P** | Lucro Presumido — BP, DRE, apuração IRPJ/CSLL | N | **O** | N | N |
| **Q** | Livro Caixa | N | O (se sem ECD) | N | N |
| **T** | Lucro Arbitrado | N | N | **O** | N |
| **U** | Imunes e Isentas — BP, DRE, apuração | N | N | N | **O** |
| **V** | DEREX | OC | OC | OC | OC |
| **W** | Declaração País-a-País (CBCR) | OC (grupo multinacional) | OC | OC | N |
| **X** | Informações Econômicas | O | O | O | OC |
| **Y** | Informações Gerais | O | O | O | O |
| **9** | Encerramento e controle | O | O | O | O |

Legenda: **O** \= obrigatório; **OC** \= obrigatório se ocorrer o fato; **N** \= não aplicável.

### 2.1 Chave hierárquica

Cada registro declara nível (0 a 4\) e ocorrência (1:1, 1:N, 0:N). A chave de cada registro varia — para Primetax, as mais importantes são:

- **M010**: `COD_CTA_B` (conta da Parte B do e-Lalur/e-Lacs criada pelo contribuinte)  
- **M300/M350**: `CODIGO` (código da tabela dinâmica de adições/exclusões)  
- **M500**: `COD_CTA_B + COD_TRIBUTO` (I=IRPJ, C=CSLL)  
- **K155/K355**: `COD_CTA + COD_CCUS`  
- **J050**: `COD_CTA` (conta do plano contábil do contribuinte)  
- **L300/P150**: `CODIGO` (conta referencial da DRE fiscal)

---

## 3\. Regras gerais de preenchimento

### 3.1 Formato dos campos

- **C (alfanumérico):** texto. Conteúdo livre, com restrições de caracteres de controle.  
- **N (numérico sem sinal):** valores positivos. Vírgula como separador decimal; sem separador de milhar.  
- **NS (numérico com sinal):** valores podem vir positivos ou negativos; sinal `-` quando negativo.  
- **Datas:** formato `DDMMAAAA` sem separadores.

### 3.2 Situações especiais (0000.SIT\_ESPECIAL)

Distintas da ECD: a ECF tem 10 valores:

| Código | Situação |
| :---: | :---- |
| 0 | Normal (sem situação especial) |
| 1 | Extinção |
| 2 | Fusão |
| 3 | Incorporação / Incorporada |
| 4 | Incorporação / Incorporadora |
| 5 | Cisão Total |
| 6 | Cisão Parcial |
| 7 | Mudança de Qualificação da Pessoa Jurídica |
| 8 | Desenquadramento de Imune/Isenta |
| 9 | Inclusão no Simples Nacional |

### 3.3 Indicador de início do período (0000.IND\_SIT\_INI\_PER)

Tem 8 valores possíveis, que refletem o motivo pelo qual uma ECF não começa em 01/01. Importante para o parser discriminar clientes "normais" (valor 0\) de situações especiais (1 a 7):

| Código | Significado |
| :---: | :---- |
| 0 | Regular (início no primeiro dia do ano) |
| 1 | Abertura (início de atividades no ano-calendário) |
| 2 | Resultante de fusão ou cisão total |
| 3 | Resultante de mudança de qualificação da PJ |
| 4 | Início de obrigatoriedade no curso do ano (exclusão do Simples) |
| 5 | Resultante de desenquadramento como imune ou isenta |
| 6 | Realizou incorporação ou remanescente de cisão parcial |
| 7 | Retorno às atividades de empresas inativas |

### 3.4 Cálculos alteráveis vs. não alteráveis

Muitos campos numéricos em registros de tabela dinâmica (N630, N670, P200, P300, T120 etc.) são tipados como CA (Cálculo Alterável) ou CNA (Cálculo Não Alterável). Campos CA podem ser sobrepostos pelo contribuinte; campos CNA são calculados automaticamente pelo PGE. O parser Primetax, lendo o arquivo .ecf transmitido, recebe valores já consolidados — mas a distinção importa quando houver reprocessamento ou simulação.

---

## 4\. Registro 0000 — identificação e retificação

Registro único, nível hierárquico 0, ocorrência 1:1. Campos essenciais (15 no total):

| \# | Campo | Descrição | Tipo | Tam | Obrig |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | Texto fixo "0000" | C | 004 | S |
| 02 | `NOME_ESC` | Texto fixo "LECF" (escrituração contábil fiscal) | C | 004 | S |
| 03 | `COD_VER` | Versão do leiaute (**0012** para AC 2025 e situações especiais 2026\) | C | 004 | S |
| 04 | `CNPJ` | CNPJ do declarante (do sócio ostensivo, se arquivo de SCP) | C | 014 | S |
| 05 | `NOME` | Nome empresarial | C | – | S |
| 06 | `IND_SIT_INI_PER` | Indicador de início do período (tabela 3.3) | N | 001 | S |
| 07 | `SIT_ESPECIAL` | Indicador de situação especial (tabela 3.2) | C | 001 | S |
| 08 | `PAT_REMAN_CIS` | Patrimônio remanescente em caso de cisão (%) — obrigatório só se SIT=6 | N | 008 | N |
| 09 | `DT_SIT_ESP` | Data do evento — obrigatório se SIT ≠ 0 | N | 008 | N |
| 10 | `DT_INI` | Data inicial (deve ser \> 01/01/2014) | N | 008 | S |
| 11 | `DT_FIN` | Data final (31/12 no caso normal; data do evento nas situações especiais) | N | 008 | S |
| 12 | `RETIFICADORA` | S=retificadora; N=original; F=original com mudança de forma de tributação | C | 001 | S |
| 13 | `NUM_REC` | Hashcode da ECF anterior — obrigatório se RETIFICADORA \= S ou F | C | 040 | N |
| 14 | `TIP_ECF` | 0=não-SCP; 1=sócio ostensivo de SCP; 2=ECF da SCP | N | 001 | S |
| 15 | `COD_SCP` | CNPJ da SCP — preenchido apenas pela própria SCP | C | 014 | N |

**Uso no sistema Primetax:** o campo `COD_VER` é o **discriminador primário da versão do leiaute** — e a ECF evolui mais rapidamente que a ECD (uma versão por ano-calendário, em regra). Para AC 2024 era a versão 0011; para AC 2025 (entrega em 2026\) é a versão 0012\. O parser deve manter tabelas de compatibilidade por versão.

O campo `RETIFICADORA = "F"` (ECF original com mudança de forma de tributação) é estrutural: indica que a PJ migrou, por exemplo, de Lucro Presumido para Lucro Real no meio do ano-calendário por obrigatoriedade superveniente (lucros no exterior, ultrapassagem do limite de receita, etc.). A consequência é que os blocos preenchidos mudam radicalmente dentro do mesmo ano — situação de **alto risco de erro fiscal não aproveitado** e alvo prioritário do diagnóstico Primetax.

---

## 5\. Registro 0010 — Parâmetros de Tributação (discriminador central)

Registro único por arquivo, nível 2, ocorrência 1:1. Este é **o registro mais importante da ECF para o parser Primetax** — ele determina quais blocos serão preenchidos e, portanto, qual estratégia de diagnóstico aplicar. Campos principais:

| \# | Campo | Descrição | Valores | Obrig |
| :---: | :---- | :---- | :---- | :---: |
| 01 | `REG` | "0010" | – | S |
| 02 | `HASH_ECF_ANTERIOR` | Hashcode da ECF do período imediatamente anterior (preenchido automaticamente pelo PGE) | – | N |
| 03 | `OPT_REFIS` | Optante pelo Refis (Lei 9.964/2000) | S / N | S |
| 04 | `FORMA_TRIB` | **Forma de tributação** | 1 a 9 (tabela 5.1) | S |
| 05 | `FORMA_APUR` | Periodicidade de apuração do IRPJ/CSLL | T=Trimestral; A=Anual | N |
| 06 | `COD_QUALIF_PJ` | Qualificação da PJ | 01=Geral; 02=Financeira; 03=Seguradora | N |
| 07 | `FORMA_TRIB_PER` | Forma de tributação por trimestre (formato XXXX, um X por trimestre) | 0, R, P, A, E | N |
| 08 | `MES_BAL_RED` | Forma de apuração da estimativa mensal (formato XXXXXXXXXXXX, um X por mês) | 0, E, B | N |
| 09 | `TIP_ESC_PRE` | Escrituração | C=obrigada/recupera ECD; L=Livro Caixa | N |
| 10 | `TIP_ENT` | Tipo de PJ imune/isenta (15 valores — tabela 5.2) | 01–15, 99 | N |
| 11 | `FORMA_APUR_I` | Apuração do IRPJ para imunes/isentas | A / T / D | N |
| 12 | `APUR_CSLL` | Apuração da CSLL para imunes/isentas | A / T / D | N |
| 13 | `IND_REC_RECEITA` | Regime de reconhecimento da receita (Lucro Presumido) | 1=Caixa; 2=Competência | N |

### 5.1 Tabela de FORMA\_TRIB (campo 04\)

| Código | Forma de tributação |
| :---: | :---- |
| 1 | Lucro Real |
| 2 | Lucro Real / Arbitrado (arbitramento em algum trimestre) |
| 3 | Lucro Presumido / Real (mudança por obrigatoriedade) |
| 4 | Lucro Presumido / Real / Arbitrado |
| 5 | Lucro Presumido |
| 6 | Lucro Arbitrado |
| 7 | Lucro Presumido / Arbitrado |
| 8 | Imune do IRPJ |
| 9 | Isenta do IRPJ |

### 5.2 Tabela de TIP\_ENT (campo 10\)

| Código | Tipo de entidade |
| :---: | :---- |
| 01 | Assistência Social |
| 02 | Educacional |
| 03 | Sindicato de Trabalhadores |
| 04 | Associação Civil |
| 05 | Cultural |
| 06 | Entidade Fechada de Previdência Complementar |
| 07 | Filantrópica |
| 08 | Sindicato |
| 09 | Recreativa |
| 10 | Científica |
| 11 | Associação de Poupança e Empréstimo |
| 12 | Entidade Aberta de Previdência Complementar (Sem Fins Lucrativos) |
| 13 | Fifa e Entidades Relacionadas |
| 14 | CIO e Entidades Relacionadas |
| 15 | Partidos Políticos |
| 99 | Outras |

**Uso no sistema Primetax:** o campo `FORMA_TRIB` é o **roteador de todos os cruzamentos fiscais**. A tabela abaixo resume a lógica do parser:

| FORMA\_TRIB | Blocos principais a parsear | Cruzamento primário com EFD-Contribuições |
| :---: | :---- | :---- |
| 1 | L, M, N | Receita Bruta na DRE do L300 × M200/M600 |
| 2 | L, M, N, T | Idem para trimestres de Real; T120/T150 para trimestres arbitrados |
| 3 | L, M, N, P | Blocos separados por trimestre conforme FORMA\_TRIB\_PER |
| 5 | P | Receita Bruta no P150 × M200/M600 (atenção: no Presumido, muitas PJs estão em regime cumulativo) |
| 8 ou 9 | U | Receita Bruta no U150 × M200/M600 (se houver receita tributada) |

O campo `FORMA_TRIB_PER` (ex: "RRRP" \= 3 trimestres Real \+ 1 Presumido, impossível na prática mas ilustrativo) permite o parser processar corretamente ECFs com mudança de regime intra-anual.

O campo `TIP_ESC_PRE = "L"` (Livro Caixa) é um alerta **crítico**: indica PJ no Lucro Presumido que optou por não ter ECD contábil. Nessa hipótese, o parser **não pode fazer cruzamento ECF × ECD** — a contabilidade do cliente está no Bloco Q (Livro Caixa) da própria ECF, e as únicas fontes de cruzamento são ECF × EFD-Contribuições.

---

## 6\. Demais registros do Bloco 0

### 6.1 Registro 0020 — Parâmetros Complementares

Campos relativos a atividades específicas (imobiliária, rural, cooperativa, transporte, aviação, portuária, etc.), modalidades de financiamento (Finam/Finor/Funres), incentivos fiscais (SUDAM/SUDENE), regimes especiais (RET, RECAP, REIDI, REPES, REPORTO), atividade concessionária etc. É um registro de **muitos campos binários S/N** que determinam a disponibilidade de linhas específicas nas tabelas dinâmicas dos blocos L, M, N e X.

**Uso no sistema Primetax:** o 0020 determina se a PJ tem direito a benefícios fiscais específicos. Campos como `IND_ATIV_RURAL`, `IND_COOP` (cooperativa), `IND_REPORTO`, `IND_REIDI`, `IND_SUDAM`, `IND_SUDENE` são sinalizadores diretos de **linhas de benefício fiscal** que o parser deve marcar para priorização em diagnóstico.

### 6.2 Registro 0021 — Parâmetros de Identificação dos Tipos de Programa

Identifica programas com benefícios fiscais aos quais a PJ está vinculada. Muitos campos adicionais complementando o 0020\.

### 6.3 Registro 0030 — Dados Cadastrais

Endereço, CNAE, contato, natureza jurídica.

### 6.4 Registro 0035 — Identificação das SCP

Apenas quando `0000.TIP_ECF = 1` (sócio ostensivo que declara SCPs).

### 6.5 Registro 0930 — Identificação dos Signatários da ECF

Contador, responsável pela PJ, com CPF, nome, qualificação e código de assinatura.

### 6.6 Registro 0990 — Encerramento do Bloco 0

Campo `QTD_LIN_0`.

---

## 7\. Bloco C — informações recuperadas da ECD

O Bloco C é **gerado automaticamente pelo PGE da ECF** ao recuperar a ECD correspondente ao mesmo período — não é preenchido manualmente pelo contribuinte. Funciona como espelho das informações contábeis que servirão de base aos Blocos K, L, M, N, P, U.

| Registro | Origem na ECD | Conteúdo |
| :---: | :---- | :---- |
| `C001` | – | Abertura do Bloco C |
| `C040` | 0000 | Hash e identificação da ECD recuperada |
| `C050` | I050 | Plano de contas da ECD |
| `C051` | I051 | Plano de contas referencial |
| `C053` | I053 | Subcontas correlatas (RAS) |
| `C100` | – | Centros de custos |
| `C150` | I150 | Identificação do período dos saldos periódicos |
| `C155` | I155 | Saldos periódicos (débitos, créditos, inicial, final) |
| `C157` | I157 | Transferência de saldos de plano anterior |
| `C350` | I350 | Data dos saldos de resultado antes do encerramento |
| `C355` | I355 | Saldos de resultado antes do encerramento |
| `C990` | – | Encerramento do Bloco C |

**Uso no sistema Primetax:** o Bloco C é **redundante com a ECD primária** no banco Primetax. A recomendação é: se há ECD do mesmo período já importada no schema `ecd_*`, usar a ECD como fonte autoritativa e tratar o Bloco C da ECF apenas como **validador cruzado** (checando se o hashcode em C040 bate com o da ECD importada — inconsistência indica que o cliente transmitiu ECFs usando versões diferentes da ECD).

---

## 8\. Bloco E — saldos da ECF anterior e cálculo fiscal sobre a ECD

O Bloco E é a ponte temporal entre ECFs e entre ECD/ECF do mesmo período.

| Registro | Descrição |
| :---: | :---- |
| `E001` | Abertura do Bloco E |
| `E010` | Saldos finais recuperados da ECF anterior (via hashcode do 0010.HASH\_ECF\_ANTERIOR) |
| `E015` | Contas contábeis mapeadas (correspondência entre plano atual e anterior) |
| `E020` | Saldos finais das contas na Parte B do e-Lalur da ECF imediatamente anterior |
| `E030` | Identificação do período |
| `E155` | Saldos contábeis calculados pelo sistema com base nas ECD (por período do K030) |
| `E355` | Saldos de resultado antes do encerramento calculados pelo sistema |
| `E990` | Encerramento do Bloco E |

### 8.1 E020 — Parte B recuperada: o mapa de créditos e prejuízos

O E020 traz, por conta da Parte B do e-Lalur/e-Lacs (`COD_CTA_B`) criada em exercícios anteriores, o saldo final que entra como saldo inicial no M500 do ano atual. Separa por tributo (`COD_TRIBUTO = I` para IRPJ; `C` para CSLL).

**Uso no sistema Primetax:** o E020 é o **cadastro histórico de adições/exclusões temporais** da PJ. Contém, por exemplo:

- Saldos de prejuízos fiscais acumulados a compensar  
- Saldos de bases de cálculo negativas de CSLL acumuladas  
- Saldos de provisões indedutíveis a reverter  
- Saldos de contas de ajuste de avaliação patrimonial (MEP, RTT residual, etc.)

Identificar contas do E020 com **saldos significativos que não estão sendo movimentados** é a via direta para teses de **recuperação de exclusões fiscais não aproveitadas** — especialmente em provisões revertidas na contabilidade que deveriam gerar exclusão na Parte A e baixa simultânea na Parte B, mas que ficam "presas" no saldo.

### 8.2 E155 — Saldos calculados pela ECF a partir da ECD

O E155 é o que o PGE da ECF **calcula a partir da ECD recuperada**, para conferência contra o K155 (que é o que o contribuinte declara). A REGRA\_COMPATIBILIDADE\_K155\_E155 gera aviso quando há divergência — divergências justificadas devem constar em K915.

---

## 9\. Bloco J — plano de contas do contribuinte e referencial

Espelha o plano de contas da ECD, adaptado para os requisitos fiscais.

| Registro | Descrição |
| :---: | :---- |
| `J001` | Abertura do Bloco J |
| `J050` | Plano de contas do contribuinte (análogo ao I050 da ECD) |
| `J051` | Plano de contas referencial (análogo ao I051 da ECD) |
| `J053` | Subcontas correlatas (análogo ao I053) |
| `J100` | Centros de custos |
| `J990` | Encerramento do Bloco J |

### 9.1 Registro J050 — campos principais

| \# | Campo | Descrição | Obrig |
| :---: | :---- | :---- | :---: |
| 01 | `REG` | "J050" | S |
| 02 | `DT_ALT` | Data da inclusão/alteração | S |
| 03 | `COD_NAT` | Natureza (01=Ativo; 02=Passivo; 03=PL; 04=Resultado; 05=Compensação; 09=Outras) | S |
| 04 | `IND_CTA` | S=Sintética; A=Analítica | S |
| 05 | `NIVEL` | Nível da conta | S |
| 06 | `COD_CTA` | Código da conta — **chave** | S |
| 07 | `COD_CTA_SUP` | Conta imediatamente superior | N |
| 08 | `CTA` | Nome da conta | S |

**Uso no sistema Primetax:** o J050 da ECF deve ser idêntico ao I050 da ECD do mesmo período. Divergência entre eles é indicativo de problema grave (ECD e ECF não consistentes) e deve abortar o pipeline de cruzamento com erro. O parser deve registrar essa comparação em todos os casos.

### 9.2 Registro J051 — Plano de contas referencial

Liga cada conta analítica do J050 a uma conta do plano referencial da RFB, conforme regra do 0010 (combinação de `COD_QUALIF_PJ`, `APUR_CSLL` e `FORMA_APUR_I`). Os planos referenciais da ECF são os L100A/B/C, L300A/B/C (Lucro Real), P100, P150 (Presumido), U100A/B/C/D/E, U150A/B/C/D/E (Imunes/Isentas).

---

## 10\. Bloco K — saldos contábeis patrimoniais e referenciais

O Bloco K é o **manifesto contábil da ECF** — os saldos finais do exercício, mapeados ao plano referencial, que servirão de base ao cálculo fiscal nos Blocos L (Lucro Real), P (Presumido), T (Arbitrado) e U (Imunes/Isentas).

| Registro | Descrição | Fonte |
| :---: | :---- | :---- |
| `K001` | Abertura do Bloco K | – |
| `K030` | Identificação dos períodos e formas de apuração do IRPJ/CSLL | Derivado do 0010 |
| `K155` | Saldos contábeis das contas patrimoniais (**depois** do encerramento do resultado) | ECD recuperada ou importado |
| `K156` | Mapeamento referencial dos saldos de K155 | Derivado de J051 ou importado |
| `K355` | Saldos finais das contas de resultado **antes** do encerramento | ECD recuperada ou importado |
| `K356` | Mapeamento referencial dos saldos de K355 | Derivado de J051 ou importado |
| `K915` | Justificativa para divergência de saldos patrimoniais recuperados da ECD | Preenchimento manual |
| `K935` | Justificativa para divergência de saldos de resultado recuperados da ECD | Preenchimento manual |
| `K990` | Encerramento do Bloco K | – |

### 10.1 Registro K155 — Saldos patrimoniais pós-encerramento

| \# | Campo | Descrição | Tipo | Tam | Dec |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "K155" | C | 004 | – |
| 02 | `COD_CTA` | Conta analítica patrimonial (referencia J050) | C | – | – |
| 03 | `COD_CCUS` | Centro de custos | C | – | – |
| 04 | `VL_SLD_INI` | Saldo inicial do período | N | 019 | 02 |
| 05 | `IND_VL_SLD_INI` | D / C | C | 001 | – |
| 06 | `VL_DEB` | Total de débitos do período | N | 019 | 02 |
| 07 | `VL_CRED` | Total de créditos do período | N | 019 | 02 |
| 08 | `VL_SLD_FIN` | Saldo final do período | N | 019 | 02 |
| 09 | `IND_VL_SLD_FIN` | D / C | C | 001 | – |

Regras críticas (REGRA\_NATUREZA\_PERMITIDA\_PATRIMONIAL): só contas de `COD_NAT` 01, 02 ou 03 (Ativo, Passivo, PL). Contas de resultado vão ao K355.

### 10.2 Registro K156 — Mapeamento referencial

Para cada conta do J050 mapeada a apenas uma conta referencial, o sistema preenche automaticamente. Se a conta contábil foi mapeada a mais de uma referencial (situação prevista na regra 0000.IND\_MUDANC\_PC e na seção 1.20 do manual), o K156 precisa ser preenchido manualmente, informando `COD_CTA_REF`, `VL_SLD_INI`, `IND_VL_SLD_INI`, `VL_DEB`, `VL_CRED`, `VL_SLD_FIN`, `IND_VL_SLD_FIN`.

### 10.3 Registros K355 e K356 — Resultado antes do encerramento

Espelham o K155/K156 mas para contas de `COD_NAT = 04` (resultado), com saldos **antes** dos lançamentos de encerramento. São a base da DRE fiscal do L300 e do P150.

### 10.4 Registros K915 e K935 — Justificativas de divergência

Preenchidos quando o contribuinte discorda dos valores calculados pelo sistema (via E155/E355) e precisa justificar por escrito. Cada linha traz `COD_CTA`, `VL_SLD_FIN_CALCULADO`, `VL_SLD_FIN_INFORMADO`, `DESCR_JUSTIFICATIVA`.

**Uso no sistema Primetax:** o preenchimento de K915 ou K935 é um **sinal de alerta** — indica que há discrepância entre a ECD e a ECF do mesmo período que o contribuinte reconheceu formalmente. O conteúdo da `DESCR_JUSTIFICATIVA` deve ser capturado e anexado ao relatório de diagnóstico como evidência de ajustes que podem ter conteúdo fiscal relevante (ex: "ajuste de consolidação não refletido na ECD", "reclassificação de conta", "ajuste de subcontas da Lei 12.973/2014").

---

## 11\. Bloco L — Lucro Líquido (BP e DRE para Lucro Real)

Obrigatório somente quando `0010.FORMA_TRIB_PER` tem algum "R" (Lucro Real) ou "E" (Real Estimativa) em algum trimestre.

| Registro | Descrição |
| :---: | :---- |
| `L001` | Abertura do Bloco L |
| `L030` | Identificação dos períodos e formas de apuração no ano-calendário |
| `L100` | **Balanço Patrimonial** — plano referencial, por trimestre ou período |
| `L200` | Método de avaliação do estoque final (PEPS, UEPS, Média Ponderada etc.) |
| `L210` | Informativo da composição de custos (só quando método é lucro real integral) |
| `L300` | **Demonstração do Resultado Líquido no Período Fiscal** — base de toda a apuração |
| `L990` | Encerramento do Bloco L |

### 11.1 Registro L100 — Balanço Patrimonial

Por código de aglutinação do plano referencial. Trimestral ou anual conforme `L030.FORMA_APUR`. Diferente do J100 da ECD (que usa código de aglutinação do contribuinte), aqui as linhas são do **plano referencial da RFB** — tornando os BPs comparáveis entre PJs.

### 11.2 Registro L300 — Demonstração do Resultado Líquido no Período Fiscal

| \# | Campo | Descrição | Tipo | Obrig |
| :---: | :---- | :---- | :---: | :---: |
| 01 | `REG` | "L300" | C | S |
| 02 | `CODIGO` | Código da conta referencial (tabela dinâmica L300A/B/C) | C | S |
| 03 | `DESCRICAO` | Descrição da conta referencial | C | N |
| 04 | `TIPO` | S=Sintética; A=Analítica | C | S |
| 05 | `NIVEL` | Nível da conta | N | N |
| 06 | `COD_NAT` | "04" (resultado) | C | N |
| 07 | `COD_CTA_SUP` | Conta superior | C | N |
| 08 | `VALOR` | Saldo final da conta referencial | N | S |
| 09 | `IND_VALOR` | D / C | C | S |

### 11.3 Tabelas dinâmicas do L300

- **L300A** — PJ em Geral (plano mais comum)  
- **L300B** — Financeiras  
- **L300C** — Seguradoras, Capitalização, EAPC

A estrutura é hierárquica, começando em nível 1 ("Receita Bruta de Vendas e Serviços") e descendo até nível analítico (linhas de "Receitas de Recuperação de Tributos", "Custo das Mercadorias Vendidas", etc.).

**Uso no sistema Primetax:** o L300 é a **DRE fiscal por plano referencial** — é ela que permite cruzar Receita Bruta da ECF contra Receita Bruta declarada na EFD-Contribuições (via M200/M210/M600/M610) em um vocabulário consistente (plano referencial da RFB, não o plano interno da PJ). Em clientes com vários códigos de aglutinação contábeis mapeados à mesma linha do L300, o cruzamento no nível referencial é mais confiável que no nível contábil do K155.

---

## 12\. Bloco M — e-Lalur e e-Lacs (o coração fiscal da ECF)

**Este é o bloco mais importante da ECF para a prática Primetax.** Contém todas as adições, exclusões, compensações e controles de saldos que transformam o Lucro Líquido contábil em Lucro Real (base do IRPJ) e em Base de Cálculo da CSLL.

| Registro | Descrição |
| :---: | :---- |
| `M001` | Abertura do Bloco M |
| `M010` | **Identificação da conta na Parte B do e-Lalur e do e-Lacs** (criada pelo contribuinte) |
| `M030` | Identificação dos períodos e formas de apuração no Lucro Real |
| `M300` | **Lançamentos da Parte A do e-Lalur (IRPJ)** — adições e exclusões |
| `M305` | Conta da Parte B do e-Lalur relacionada ao lançamento da Parte A |
| `M310` | Contas contábeis relacionadas ao lançamento da Parte A do e-Lalur |
| `M312` | Números dos lançamentos contábeis (da ECD) relacionados à conta do M310 |
| `M315` | Processos judiciais/administrativos relacionados ao lançamento |
| `M350` | **Lançamentos da Parte A do e-Lacs (CSLL)** — espelho do M300 para CSLL |
| `M355` | Conta da Parte B do e-Lacs |
| `M360` | Contas contábeis relacionadas ao lançamento da Parte A do e-Lacs |
| `M362` | Números dos lançamentos contábeis relacionados à conta do M360 |
| `M365` | Processos judiciais/administrativos relacionados ao lançamento |
| `M410` | Lançamento na Parte B sem reflexo na Parte A |
| `M415` | Processos judiciais/administrativos do M410 |
| `M500` | **Controle de saldos das contas da Parte B do e-Lalur e do e-Lacs** (visão sintética anual) |
| `M510` | Controle de saldos das contas padrão da Parte B |
| `M990` | Encerramento do Bloco M |

### 12.1 Registro M010 — Cadastro das contas da Parte B

Cada linha representa uma conta da Parte B criada pelo contribuinte para controlar valores que serão adicionados ou excluídos em períodos subsequentes. Campos principais: `COD_CTA_B` (chave), `IND_CTA_B` (tipo), `COD_TRIBUTO` (I=IRPJ; C=CSLL; IC=ambos), `CTA` (nome), `CTA_RES_LAL` (indicador de natureza), `DT_INI_UTIL`, `DT_FIN_UTIL`.

**Uso no sistema Primetax:** o M010 é o **cadastro permanente** da PJ para controle temporal fiscal. Contas típicas aqui incluem:

- Prejuízos fiscais de períodos anteriores (a compensar)  
- Bases de cálculo negativas da CSLL de períodos anteriores  
- Provisões indedutíveis (a excluir quando reversão)  
- Amortização diferida de ágio  
- Ajustes do RTT (residual, para operações pré-2014)  
- Receitas com diferimento fiscal  
- Exclusões de subvenções para investimento (Lei 12.973/14, art. 30\)

A leitura do M010 é a **porta de entrada** para identificar o "estoque fiscal" da PJ — valores que geram ou vão gerar ajustes fiscais no futuro e que frequentemente estão mal controlados.

### 12.2 Registro M300 — Adições e Exclusões do e-Lalur (Parte A, IRPJ)

| \# | Campo | Descrição | Obrig |
| :---: | :---- | :---- | :---: |
| 01 | `REG` | "M300" | S |
| 02 | `CODIGO` | Código do lançamento (tabela dinâmica M300A/R/B/C) | S |
| 03 | `DESCRICAO` | Descrição do tipo de lançamento | N |
| 04 | `TIPO_LANCAMENTO` | A=Adição; E=Exclusão; P=Compensação de Prejuízo; L=Lucro (rótulo) | N |
| 05 | `IND_RELACAO` | 1=com conta da Parte B; 2=com conta contábil; 3=ambos; 4=sem relação | N |
| 06 | `VALOR` | Valor do lançamento | N |
| 07 | `HIST_LAN_LAL` | Histórico descritivo | N |

### 12.3 Tabelas dinâmicas do M300 — o dicionário das adições e exclusões

O campo `CODIGO` remete a uma planilha da RFB com **centenas de linhas**, cada uma correspondendo a uma adição ou exclusão tipificada. As variantes são:

- **M300A** — PJ em Geral, Atividade Geral  
- **M300R** — PJ em Geral, Atividade Rural (tratamento fiscal diferenciado)  
- **M300B** — Financeiras  
- **M300C** — Seguradoras, Capitalização, EAPC

Exemplos típicos de linhas nas tabelas dinâmicas (para entender a ordem de grandeza):

- Códigos de adições: multas indedutíveis, provisões indedutíveis, depreciações não dedutíveis, despesas com brindes/alimentação de sócios, ajustes de preços de transferência  
- Códigos de exclusões: reversão de provisões indedutíveis, RECEITAS NÃO TRIBUTÁVEIS, compensação de prejuízos fiscais (limitada a 30%), subvenções para investimento (Lei 12.973/14, art. 30), resultados positivos de equivalência patrimonial, recuperações de tributos (**aqui entra a Tese 69\!**), etc.  
- Códigos de prejuízo (P): apuração e compensação de prejuízos fiscais de exercícios anteriores

### 12.4 Lógica dos sinais (tabela-chave para o parser)

A relação entre o tipo de lançamento no M300, o sinal do valor e os indicadores no M305/M310 é rigorosamente definida no manual. Resumidamente:

| Tipo de linha A do M300 | Sinal do M300.VALOR | IND\_VL\_CTA do M305 | IND\_VL\_CTA do M310 (se conta de resultado) | IND\_VL\_CTA do M310 (se conta patrimonial) |
| :---: | :---: | :---: | :---: | :---: |
| **Adição** (A) ou **Lucro** (L) | Positivo | D | D | C |
| **Adição** / **Lucro** | Negativo | C | C | D |
| **Exclusão** (E) ou **Compensação de prejuízo** (P) | Positivo | C | C | D |
| **Exclusão** / **Compensação de prejuízo** | Negativo | D | D | C |

A REGRA\_VALOR\_DETALHADO do M300 valida essa correspondência: a soma dos filhos (M305 \+ M310) deve bater com o valor do M300, considerando a conversão de sinais.

### 12.5 Registros M305 (Parte B) e M310 (contas contábeis)

- **M305**: identifica a conta da Parte B (M010.COD\_CTA\_B) impactada pelo lançamento do M300. Tem `VALOR_CTA` e `IND_VL_CTA`. Um M300 pode ter múltiplos M305 filhos.  
- **M310**: identifica as contas contábeis (J050.COD\_CTA) envolvidas. Permite o rastreamento até a ECD: **dada uma adição/exclusão na ECF, identifica qual conta contábil lhe deu origem** — link direto entre e-Lalur e livro diário.  
- **M312**: filho do M310, identifica os números específicos de lançamento (I200.NUM\_LCTO) da ECD que compõem aquele valor. É o nível máximo de rastreabilidade fiscal — **da adição/exclusão até a partida do Diário**.

### 12.6 Registros M350, M355, M360, M362, M365 — e-Lacs (CSLL)

Espelham exatamente a estrutura do M300/M305/M310/M312/M315, mas para a Contribuição Social sobre o Lucro Líquido. Os códigos das tabelas dinâmicas do M350 (M350A/R/B/C) **são diferentes** dos códigos do M300 — porque as adições e exclusões fiscais de IRPJ e CSLL não são idênticas. Exemplo clássico: a exclusão de resultado positivo de equivalência patrimonial é tratada de forma ligeiramente distinta entre IRPJ e CSLL.

### 12.7 Registro M410 — Lançamentos na Parte B sem reflexo na Parte A

Situações em que uma conta da Parte B é movimentada sem que haja um lançamento correspondente na Parte A naquele período. Exemplo: transferência de saldo entre duas contas da Parte B; reconhecimento contábil sem efeito fiscal imediato. Campo-chave: `COD_LCTO` (código do tipo de lançamento sem reflexo).

### 12.8 Registro M500 — Controle de saldos das contas da Parte B

Registro-síntese gerado pelo sistema. Um registro por `COD_CTA_B + COD_TRIBUTO` ativo no período. Campos:

| \# | Campo | Descrição |
| :---: | :---- | :---- |
| 01 | `REG` | "M500" |
| 02 | `COD_CTA_B` | Conta da Parte B |
| 03 | `COD_TRIBUTO` | I=IRPJ; C=CSLL |
| 04 | `SD_INI_LAL` | Saldo inicial da conta no período |
| 05 | `IND_SD_INI_LAL` | D (exclusões futuras) / C (adições futuras) |
| 06 | `VL_LCTO_PARTE_A` | Somatório dos lançamentos da Parte B com reflexo na Parte A |
| 07 | `IND_VL_LCTO_PARTE_A` | D / C |
| 08 | `VL_LCTO_PARTE_B` | Somatório dos lançamentos sem reflexo na Parte A (M410) |
| 09 | `IND_VL_LCTO_PARTE_B` | D / C |
| 10 | `SD_FIM_LAL` | Saldo final do período |
| 11 | `IND_SD_FIM_LAL` | D / C |

O campo `SD_FIM_LAL` \+ `IND_SD_FIM_LAL` do último período é transportado automaticamente para o E020 da próxima ECF — fechando o ciclo multi-exercício.

**Uso no sistema Primetax:** o M500 é o **balanço fiscal** da Parte B — uma fotografia do "estoque fiscal" acumulado. Cruzamentos críticos:

1. **Saldo inicial do M500 do ano atual** deve ser igual ao **saldo final do M500 do ano anterior** (E020 daquela ECF anterior). Divergência \= erro estrutural.  
2. **Contas com saldo significativo e zero movimentação há vários anos** (`VL_LCTO_PARTE_A = 0` e `VL_LCTO_PARTE_B = 0`, mas `SD_FIM_LAL` alto) são fortes candidatas a **exclusão fiscal não aproveitada** — prejuízos fiscais em risco de prescrição, reversões de provisões que deveriam ter sido feitas, subvenções para investimento esquecidas.  
3. **Prejuízos fiscais consumidos no ano atual** (linhas específicas do M300 com TIPO\_LANCAMENTO \= P) são medidos contra o saldo inicial do M500 da conta correspondente — e são limitados a 30% do lucro real antes da compensação (artigo 15 da Lei 9.065/1995).

---

## 13\. Bloco N — cálculo do IRPJ e da CSLL no Lucro Real

Obrigatório no Lucro Real. Traz os cálculos finais do IRPJ e da CSLL para cada trimestre (na apuração trimestral) ou para cada mês de estimativa \+ ajuste anual (na apuração anual).

| Registro | Descrição |
| :---: | :---- |
| `N001` | Abertura do Bloco N |
| `N030` | Identificação dos períodos e formas de apuração no Lucro Real |
| `N500` | Base de cálculo do IRPJ após compensações de prejuízos |
| `N600` | Demonstração do Lucro da Exploração (para empresas com benefícios regionais) |
| `N605` | Contas contábeis usadas na apuração do Lucro da Exploração |
| `N610` | Cálculo da isenção e redução do IRPJ (SUDAM/SUDENE) |
| `N615` | Informações da base de cálculo dos incentivos fiscais |
| `N620` | **Apuração do IRPJ Mensal por Estimativa** |
| `N630` | **Apuração do IRPJ com base no Lucro Real** (anual ou trimestral) |
| `N650` | Base de cálculo da CSLL após compensações de base negativa |
| `N660` | **Apuração da CSLL Mensal por Estimativa** |
| `N670` | **Apuração da CSLL com base no Lucro Real** |
| `N990` | Encerramento do Bloco N |

Todos os registros do Bloco N usam tabelas dinâmicas com `CODIGO + DESCRICAO + VALOR`. As variantes das tabelas dinâmicas (N630A, N630B, N630C, N670A, N670B, N670C) refletem PJ em Geral, Financeiras e Seguradoras.

### 13.1 Linhas típicas de interesse no N630 (IRPJ Lucro Real)

As tabelas dinâmicas incluem:

- Lucro real antes das compensações  
- (-) Compensação de prejuízos fiscais (limitado a 30%)  
- Lucro real após compensações  
- IRPJ devido à alíquota de 15%  
- Adicional de 10% sobre a parcela excedente  
- (-) Incentivos fiscais (SUDAM, SUDENE, Pronon/Pronas, PAT, Rouanet, Lei do Audiovisual, etc.)  
- (-) IRRF (retenção na fonte) de rendimentos  
- (-) IRPJ pago por estimativa no ano (nos meses anteriores)  
- IRPJ a pagar ou a compensar

O `N630A.CODIGO = 21` é "(-) Imposto de Renda Mensal Pago por Estimativa" — bate com a soma dos recolhimentos mensais por DARF código específico.

### 13.2 Linhas típicas de interesse no N670 (CSLL Lucro Real)

- Base de cálculo da CSLL antes das compensações  
- (-) Compensação de base negativa (limitado a 30%)  
- Base de cálculo após compensações  
- CSLL devida à alíquota de 9% (ou 15% para financeiras)  
- (-) CSRF (retenção na fonte)  
- (-) CSLL paga por estimativa no ano  
- CSLL a pagar ou a compensar

**Uso no sistema Primetax:** o cruzamento central do Bloco N com outros SPEDs é:

1. **N630/N670 × DARFs recolhidos** — as linhas de "(-) IRPJ/CSLL pago por estimativa" e as linhas de IRRF/CSRF podem ser cruzadas contra DCTFWeb e DARFs para identificar recolhimentos indevidos ou não compensados.  
2. **N630/N670 × IRPJ/CSLL na DCTF** — discrepâncias indicam falha de integração entre a apuração da ECF e a declaração formal em DCTFWeb.  
3. **N615 (incentivos fiscais)** — cliente com benefício declarado mas sem registro X480/X485 (Benefícios Fiscais Parte I e II) em coerência é indicador de perda de benefício ou falha formal.

---

## 14\. Bloco P — Lucro Presumido

Obrigatório quando `0010.FORMA_TRIB` ∈ {3, 4, 5, 7} e o período específico é Presumido. Estrutura paralela ao Bloco L/N para Lucro Real, simplificada.

| Registro | Descrição |
| :---: | :---- |
| `P001` | Abertura do Bloco P |
| `P030` | Identificação dos períodos do Lucro Presumido |
| `P100` | Balanço Patrimonial (plano referencial Lucro Presumido) |
| `P130` | Demonstração das receitas incentivadas do Lucro Presumido |
| `P150` | Demonstrativo do Resultado Líquido no Período Fiscal |
| `P200` | Apuração da base de cálculo do IRPJ com base no Lucro Presumido |
| `P230` | Cálculo da isenção e redução do Lucro Presumido |
| `P300` | Cálculo do IRPJ com base no Lucro Presumido |
| `P400` | Apuração da base de cálculo da CSLL com base no Lucro Presumido |
| `P500` | Cálculo da CSLL com base no Lucro Presumido |
| `P990` | Encerramento do Bloco P |

### 14.1 Registro P150 — DRE fiscal do Presumido

Estrutura idêntica ao L300 (CODIGO, DESCRICAO, TIPO, NIVEL, COD\_NAT, COD\_CTA\_SUP, VALOR, IND\_VALOR). Tabelas dinâmicas P150A (PJ em Geral), P150B (Financeiras Lucro Presumido), P150C (Seguradoras).

### 14.2 Registros P200 e P300 — Apuração do IRPJ Presumido

O P200 traz a base de cálculo do lucro presumido: receita bruta da atividade × percentual de presunção (8% para revenda/indústria geral, 16% para transporte de cargas, 32% para serviços, etc.) \+ outras adições (ganhos de capital, receitas financeiras, etc.). O P300 converte essa base em IRPJ devido e aplica deduções.

### 14.3 Registros P400 e P500 — Apuração da CSLL Presumida

Análogo ao P200/P300, mas para CSLL. Percentuais de presunção são diferentes: 12% para a maioria dos casos; 32% para serviços.

**Uso no sistema Primetax:** no Lucro Presumido, o cruzamento central é:

1. **Receita bruta do P150 × Receita bruta na EFD-Contribuições** — atenção: a maioria das PJs no Lucro Presumido está no **regime cumulativo** de PIS/COFINS (alíquotas 0,65% \+ 3% sobre receita bruta), o que simplifica a conciliação.  
2. **Receita bruta do P150 × Receita efetivamente recebida (se `0010.IND_REC_RECEITA = 1` — regime de caixa)** — divergência pode indicar inadimplência não reconhecida tributariamente.  
3. Cliente do Lucro Presumido com receita bruta acima de R$ 78 milhões no ano anterior **não poderia estar no regime** (IN 2.004/2021 e art. 13 Lei 9.718/98) — verificar coerência com o 0010.FORMA\_TRIB.

---

## 15\. Bloco Q — Livro Caixa (Lucro Presumido opcional)

Obrigatório quando `0010.TIP_ESC_PRE = "L"` (PJ que optou pela não-entrega da ECD). O Livro Caixa aqui é uma memória simplificada dos fatos contábeis.

| Registro | Descrição |
| :---: | :---- |
| `Q001` | Abertura do Bloco Q |
| `Q100` | Demonstrativo do Livro Caixa (um por lançamento de entrada/saída) |
| `Q990` | Encerramento do Bloco Q |

### 15.1 Registro Q100 — Demonstrativo

Campos: `DT_OPER`, `DESCR_OPER`, `NUM_DOC`, `CNPJ_CPF_PART`, `NOME_PART`, `TIP_OPER` (entrada/saída), `VL_OPER`, `IND_OPER`, `VL_SALDO`, `IND_SALDO`.

**Uso no sistema Primetax:** o Q100 substitui a ECD nesses clientes — é a **única fonte contábil do cliente** dentro do ecossistema SPED. Útil para contextualizar cruzamentos EFD-Contribuições × ECF quando a ECD não existe.

---

## 16\. Bloco T — Lucro Arbitrado

Obrigatório quando `0010.FORMA_TRIB` ∈ {2, 4, 6, 7} e o período específico foi arbitrado. Estrutura simplificada.

| Registro | Descrição |
| :---: | :---- |
| `T001` | Abertura do Bloco T |
| `T030` | Identificação dos períodos do Lucro Arbitrado |
| `T120` | Apuração da base de cálculo do IRPJ no Lucro Arbitrado |
| `T150` | Cálculo do IRPJ com base no Lucro Arbitrado |
| `T170` | Apuração da base de cálculo da CSLL no Lucro Arbitrado |
| `T181` | Cálculo da CSLL com base no Lucro Arbitrado |
| `T990` | Encerramento do Bloco T |

Tabela dinâmica: base do lucro arbitrado \= receita bruta × percentual de presunção majorado em 20% (art. 532 do RIR/2018). Raro em clientes Primetax regulares, mas pode ocorrer em períodos de penalidade pelo fisco.

---

## 17\. Bloco U — Imunes e Isentas

Obrigatório quando `0010.FORMA_TRIB` ∈ {8, 9}. Estrutura paralela ao L/P, mas com variantes do plano referencial específicas por tipo de entidade (U100A–E, U150A–E).

| Registro | Descrição |
| :---: | :---- |
| `U001` | Abertura do Bloco U |
| `U030` | Identificação dos períodos para Imunes/Isentas |
| `U100` | Balanço Patrimonial (plano referencial Imune/Isenta) |
| `U150` | Demonstração do Resultado |
| `U180` | Cálculo do IRPJ das Imunes/Isentas (apenas para receitas não-abrangidas pela imunidade) |
| `U182` | Cálculo da CSLL das Imunes/Isentas |
| `U990` | Encerramento do Bloco U |

---

## 18\. Bloco V — DEREX (recursos em moeda estrangeira de exportação)

| Registro | Descrição |
| :---: | :---- |
| `V001` | Abertura do Bloco V |
| `V010` | DEREX — Instituição (identificação de banco no exterior mantendo recursos) |
| `V020` | Responsável pela movimentação |
| `V030` | DEREX — Período (mês) |
| `V100` | Demonstrativo dos recursos em moeda estrangeira decorrentes de exportações |
| `V990` | Encerramento do Bloco V |

Obrigatório para PJs que mantêm no exterior recursos em moeda estrangeira decorrentes de recebimento de exportações (IN RFB 1.801/2018). Tem pouca interseção com o foco Primetax e é irrelevante para a maioria dos cruzamentos.

---

## 19\. Bloco W — Declaração País-a-País (CBCR)

Obrigatório para **entidades declarantes de grupos multinacionais** com receita consolidada acima de certos limites (IN RFB 2.158/2023 e alterações). Contém:

| Registro | Descrição |
| :---: | :---- |
| `W001` | Abertura do Bloco W |
| `W100` | Informações do grupo multinacional e da entidade declarante |
| `W200` | Declaração País-a-País — informações agregadas por jurisdição fiscal |
| `W250` | Entidades integrantes do grupo multinacional |
| `W300` | Observações adicionais |
| `W990` | Encerramento do Bloco W |

Fora do escopo primário Primetax (raramente aplicável a clientes típicos), mas é **informação de contexto poderosa** quando o cliente faz parte de um grupo multinacional: o W250 lista todas as empresas relacionadas.

---

## 20\. Bloco X — Informações Econômicas

Dados sobre atividades incentivadas, operações com o exterior, preços de transferência, pagamentos a não residentes, e um conjunto extenso de benefícios fiscais. É o **bloco mais volumoso da ECF em termos de variedade de informação**.

Registros-chave:

| Registro | Descrição |
| :---: | :---- |
| `X280` | Atividades incentivadas – PJ em Geral |
| `X292` | Operações com o exterior – pessoa não vinculada |
| `X340`–`X357` | **Participações no exterior** — resultado, imposto pago, consolidação, prejuízos acumulados, rendas ativas/passivas (CFC rules) |
| `X360`–`X375` | **Preços de transferência** — contrapartes, transações controladas, métodos, ajustes compensatórios |
| `X390` | Origem e aplicação de recursos (para imunes/isentas) |
| `X400`–`X410` | Comércio eletrônico e tecnologia da informação |
| `X420` | **Royalties** recebidos ou pagos |
| `X430` | Rendimentos de serviços, juros e dividendos recebidos |
| `X450`/`X451` | **Pagamentos/remessas a título de serviços, juros e dividendos** a beneficiários do Brasil e exterior |
| `X460` | **Inovação tecnológica e desenvolvimento tecnológico** (Lei do Bem) |
| `X470` | Capacitação de informática e inclusão digital |
| `X480`/`X485` | **Benefícios Fiscais Partes I e II** |
| `X490`–`X510` | Zona Franca, ZPE, Áreas de Livre Comércio |

**Uso no sistema Primetax:** o Bloco X é **mina de oportunidades fiscais**. Alguns pontos de alta relevância:

1. **X480/X485** — lista completa de benefícios fiscais utilizados pelo cliente. Cruzar com linhas do M300 (exclusões) e do N615 (incentivos no cálculo do IRPJ) para verificar coerência e identificar benefícios declarados mas não aproveitados.  
2. **X460** — Lei do Bem (Lei 11.196/2005): identifica gastos com P\&D/inovação tecnológica que geram exclusão no M300 (30% a 60% dos dispêndios). Clientes com X460 preenchido mas sem correspondência no M300 \= **crédito não aproveitado**.  
3. **X420/X430/X450/X451** — fluxos com o exterior. Relevante para teses envolvendo royalties, juros sobre capital próprio, limite de dedutibilidade.  
4. **X340–X357** — participações no exterior com tributação no Brasil (CFC rules — arts. 76 a 92 da Lei 12.973/14). Tese complexa, mas alto valor quando aplicável.  
5. **X280** — atividades incentivadas (SUDAM, SUDENE, ZPE). Link direto com N610/N615 (cálculo da isenção/redução).

---

## 21\. Bloco Y — Informações Gerais

Dados cadastrais complementares e informativos. Registros-chave:

| Registro | Descrição |
| :---: | :---- |
| `Y520` | Pagamentos/recebimentos do exterior ou de não residentes |
| `Y570` | **Demonstrativo do IRRF e CSLL Retidos na Fonte** |
| `Y590` | Ativos no exterior |
| `Y600` | Identificação e remuneração de sócios, titulares, dirigentes, conselheiros |
| `Y612` | Identificação e rendimentos de dirigentes/conselheiros — Imunes/Isentas |
| `Y620` | Participações avaliadas pelo MEP |
| `Y630` | Fundos/clubes de investimento |
| `Y640`/`Y650` | Participações em consórcios de empresas |
| `Y660` | Dados de sucessoras (em caso de situação especial) |
| `Y672` | Outras informações (Lucro Presumido/Arbitrado) |
| `Y680`/`Y681`/`Y682` | **Informações de optantes pelo Refis** |
| `Y720` | **Informações de períodos anteriores** (histórico fiscal) |
| `Y730` | Donatários/destinatários de deduções do IRPJ/CSLL |
| `Y750` | Informações da ECF calculadas pelo PGE |
| `Y800` | Outras informações (texto livre / RTF) |

**Uso no sistema Primetax:** o Y570 (retenções na fonte) é cruzamento direto com a EFD-Reinf — se o cliente sofreu IRRF/CSRF que não estão aqui, há **retenção não aproveitada**. O Y720 permite visão histórica. O Y681/Y682 indica Refis (cruzamento com posição fiscal PGFN).

---

## 22\. Bloco 9 — controle e encerramento

| Registro | Descrição | Obrig |
| :---: | :---- | :---: |
| `9001` | Abertura do Bloco 9 | O |
| `9100` | **Avisos da escrituração** (lista de warnings que o PGE gerou na validação) | OC |
| `9900` | Registros do arquivo — um por tipo, com quantidade | O |
| `9990` | Encerramento do Bloco 9 | O |
| `9999` | Encerramento do arquivo digital | O |

### 22.1 Registro 9100 — Avisos da escrituração

**Este registro é extremamente valioso para o diagnóstico.** Traz, para cada aviso (não erro) gerado pelo PGE na transmissão, o código do aviso, a descrição e a referência ao registro/campo impactado. Ex: "REGRA\_LINHA\_DESPREZADA em M300 código X", "REGRA\_COMPATIBILIDADE\_K155\_E155 — divergência de R$ 1.234,56 na conta Y".

**Uso no sistema Primetax:** o parser deve extrair **todos** os avisos do 9100 e anexá-los ao relatório de diagnóstico como evidências de inconsistências internas reconhecidas pelo próprio PGE no momento da transmissão. Cliente com muitos avisos 9100 \= **qualidade fiscal baixa** e maior probabilidade de créditos não aproveitados.

---

## 23\. Tabelas dinâmicas e planos referenciais

### 23.1 O que são tabelas dinâmicas

Para os registros M300, M350, M410, L100, L300, N500, N600, N620, N630, N650, N660, N670, P100, P150, P200, P300, P400, P500, T120, T150, T170, T181, U100, U150, U180, U182, o campo `CODIGO` referencia uma planilha externa da RFB (`Tabelas_Dinamicas_ECF_Leiaute_XX_ACYYYY_...xlsx`) com a estrutura hierárquica e semântica das linhas.

Cada combinação `(Leiaute, Ano-Calendário, Registro, Variante)` tem sua própria tabela — e elas evoluem ano a ano conforme mudanças da legislação (ex: inclusão de linha nova para "Exclusão de Subvenção para Investimento", Lei 14.789/2023).

### 23.2 Variantes por qualificação da PJ

Cada registro de apuração tem variantes conforme o perfil:

- **Sufixo A**: PJ em Geral (a maioria)  
- **Sufixo R**: Atividade Rural (tratamento diferenciado de prejuízos fiscais, depreciação acelerada incentivada)  
- **Sufixo B**: Financeiras (bancos, DTVMs, CTVMs, factoring)  
- **Sufixo C**: Seguradoras, Capitalização, EAPC

A escolha da variante é controlada pelo `0010.COD_QUALIF_PJ`.

### 23.3 Variantes para imunes/isentas

Para o Bloco U, há variantes adicionais (A, B, C, D, E) conforme o `0010.TIP_ENT`, refletindo planos referenciais específicos:

- **U100A/U150A**: tipos 01–05, 07–10, 13, 14, 99 (entidades mais comuns)  
- **U100B/U150B**: tipo 11 (Associações de Poupança e Empréstimo)  
- **U100C/U150C**: tipo 12 (EAPC sem fins lucrativos)  
- **U100D/U150D**: tipo 06 (Entidades Fechadas de Previdência Complementar)  
- **U100E/U150E**: tipo 15 (Partidos Políticos)

### 23.4 Recomendação do parser Primetax

O parser deve:

1. Manter um **repositório versionado** das tabelas dinâmicas da RFB, baixadas do Portal SPED em `http://sped.rfb.gov.br/pasta/show/1644`.  
2. Carregar a tabela correspondente ao `(COD_VER, Ano-Calendário, Registro, Variante)` no momento da importação.  
3. Preservar o `CODIGO` como chave externa para consulta semântica posterior.  
4. Manter tabela de "linhas de interesse Primetax" — subconjunto dos códigos que tipicamente geram oportunidades de recuperação (exclusões de tributos recuperáveis, prejuízos fiscais, compensações etc.).

---

## 24\. Mapeamento de cruzamentos ECF ↔ ECD ↔ EFD-Contribuições

Esta é a seção operacional do documento. Os cruzamentos abaixo alimentam o motor dos 34 cruzamentos descritos no `CLAUDE.md` do projeto.

### 24.1 Chaves de cruzamento

A chave canônica para qualquer cruzamento ECF × ECD no sistema Primetax é:

```
(cnpj_declarante, ano_calendario, cod_cta)
```

Pré-requisitos:

- `cnpj_declarante`: mesmo CNPJ (do campo `0000.CNPJ` da ECF e da ECD).  
- `ano_calendario`: derivado de `0000.DT_INI/DT_FIN` em ambos.  
- `cod_cta`: mesmo plano contábil (se houver mudança, consultar J051/I051 e usar `COD_CTA_REF` como ponte).

Para cruzamento ECF × EFD-Contribuições:

```
(cnpj_declarante, ano_calendario, cod_cta_ref)
```

usando o plano referencial da RFB como linguagem comum — evita todos os problemas de mudança de plano contábil ou terminologia interna da PJ.

### 24.2 Cruzamento nuclear: L300/P150 × M200/M600 agregados

**Pergunta fiscal:** a receita bruta declarada como base de PIS/COFINS no ano todo corresponde à receita bruta da ECF?

**Lógica:**

1. Na ECF, somar as linhas analíticas do L300 (ou P150) correspondentes a "Receita Bruta de Vendas e Serviços" nos códigos do plano referencial.  
2. Na EFD-Contribuições, somar os 12 meses de `M200.VL_REC_BRT_*` (PIS) e `M600.VL_REC_BRT_*` (COFINS) do mesmo ano.  
3. Comparar.

Divergências materiais:

- **ECF \> EFD-Contribuições**: receita contabilizada e declarada no IRPJ/CSLL, mas não oferecida ao PIS/COFINS. **Risco fiscal pendente** (pode indicar tributo não recolhido — não é oportunidade Primetax).  
- **EFD-Contribuições \> ECF**: base de PIS/COFINS maior do que receita bruta. **Inconsistência favorável à tese 69** (ICMS indevidamente na base) ou indicativo de inclusão de receitas não-operacionais por erro.

### 24.3 Cruzamento: K155/K355 × I155 da ECD

**Pergunta fiscal:** os saldos contábeis que alimentam a ECF são consistentes com a ECD do mesmo período?

**Lógica:** em princípio, K155 da ECF \= I155 da ECD consolidado para o último mês do exercício (dezembro ou último mês em situação especial). Divergências justificadas aparecem em K915/K935; divergências não justificadas indicam erro estrutural.

### 24.4 Cruzamento: M300/M350 × I200 (lançamentos extemporâneos da ECD)

**Pergunta fiscal:** lançamentos extemporâneos na ECD (`I200.IND_LCTO = "X"`) têm reflexo fiscal apropriado na ECF?

**Lógica:** para cada I200 com `IND_LCTO = "X"` e `DT_LCTO_EXT` de exercício anterior, verificar se existe lançamento correspondente no M300/M350 via M310/M360/M312/M362.

- **Caso A**: há M300 com `IND_RELACAO = 2 ou 3` citando a conta do I200 extemporâneo — **ok**, lançamento reconhecido fiscalmente.  
- **Caso B**: M300 ausente — **o lançamento contábil extemporâneo não gerou ajuste no e-Lalur**. Forte candidato a revisão e potencial recuperação.

### 24.5 Cruzamento: Parte B do e-Lalur × oportunidades de exclusão

**Pergunta fiscal:** há contas da Parte B com saldo significativo e movimentação inexistente há muitos anos?

**Lógica:** para cada conta em M010 com saldo não-zero no M500:

1. Consultar o M500 dos últimos 5 exercícios (via arquivos anteriores importados).  
2. Se `VL_LCTO_PARTE_A = 0` e `VL_LCTO_PARTE_B = 0` em todos eles, com saldo crescente ou estável: **conta estagnada**.  
3. Se a natureza da conta é "valores a excluir" (`IND_SD_INI_LAL = D` segundo convenção da ECF — exclusões futuras), reportar como **exclusão não aproveitada**.

Exemplos típicos:

- Provisões para contingências já revertidas na contabilidade mas não excluídas no Lalur  
- Subvenções para investimento (Lei 12.973/14, art. 30 — e Lei 14.789/23 pós-2024)  
- Receitas com diferimento fiscal cujo fato gerador já ocorreu

### 24.6 Cruzamento: N630/N670 × compensação de prejuízos e CSLL negativa

**Pergunta fiscal:** o cliente está aproveitando corretamente prejuízos fiscais e bases negativas?

**Lógica:**

1. Obter saldo de prejuízos fiscais acumulados em M500 (conta específica com `COD_TRIBUTO = I` e natureza de exclusão).  
2. Verificar no N630/N500 se houve compensação no ano (linha correspondente nas tabelas dinâmicas).  
3. Se houve lucro real positivo no ano, mas compensação foi zero ou muito inferior ao limite de 30%: **prejuízo não aproveitado** — oportunidade Primetax.

### 24.7 Cruzamento: X480/X485 × M300 (benefícios fiscais declarados × aproveitados)

**Pergunta fiscal:** benefícios fiscais declarados no Bloco X estão efetivamente refletidos nas exclusões do M300?

**Lógica:** cada linha do X480/X485 mencionando um benefício fiscal (ex: "Lei do Bem – Dispêndios em P\&D") deve ter contrapartida em linha específica do M300 (exclusão correspondente). Ausência \= **benefício perdido**.

### 24.8 Cruzamento: COD\_CTA como ponte universal

Todos os registros da ECF que carregam `COD_CTA` (M310, M360, M312, M362, N605, K155, K355, J050) podem ser cruzados com:

- ECD: `I050.COD_CTA`, `I155.COD_CTA`, `I200.COD_CTA`, `I250.COD_CTA`  
- EFD-Contribuições: `C170.COD_CTA` (campo 37), `C175.COD_CTA`, `F100.COD_CTA`, `F120.COD_CTA`, `F130.COD_CTA`, `M105.COD_CTA`, `M505.COD_CTA`

A triangulação ECF-ECD-EFD-Contribuições por `COD_CTA` é o nível de rastreabilidade mais profundo do ecossistema SPED.

### 24.9 Cruzamentos adicionais sobre o universo dos 34

Além dos que têm a ECF como fonte direta, estes ficam registrados para incorporação futura:

1. **M500 multi-exercício × prescrição fiscal** — identificar prejuízos fiscais em risco de prescrição ou limitação.  
2. **Y570 × EFD-Reinf** — retenções declaradas × retenções efetivamente ocorridas.  
3. **Y620 × J150 da ECD (MEP)** — resultados de equivalência patrimonial e o rastreamento no balanço consolidado.  
4. **X460 (Lei do Bem) × conta contábil de P\&D** — gastos declarados × gastos contabilizados.  
5. **X292/X340 × Y520** — operações com exterior e pagamentos/recebimentos relacionados.

---

## 25\. Tese 69 e outras teses refletidas na ECF

### 25.1 Tese 69 (exclusão do ICMS da base de PIS/COFINS) na ECF

O ICMS excluído da base de PIS/COFINS gera na ECF, nos exercícios em que a tese é aplicada retroativamente (via crédito financeiro após trânsito em julgado):

1. **Receita contábil** de "Recuperação de Tributos" ou "Outras Receitas Operacionais" na DRE → entra no L300/P150 como linha referencial específica.  
2. **Tributação dessa receita** pelo IRPJ e CSLL → há posicionamento da PGFN (Parecer SEI 7698/2021/ME) no sentido de que a atualização pela SELIC sobre o indébito **não** é tributável, mas o principal recuperado **é** tributável como receita nova no exercício de seu reconhecimento.  
3. Reflexo esperado no M300: **adição** da receita contabilizada como "Recuperação de Tributos" (linha específica nas tabelas dinâmicas). Se a contabilização do cliente for como "receita financeira" ao invés de "recuperação de tributos", pode haver reclassificação fiscal via M300.  
4. Reflexo esperado no M350 (CSLL): idem.

**Uso no sistema Primetax:** quando o cliente aplica a Tese 69, o cruzamento crítico é verificar se a **adição da receita recuperada ao IRPJ/CSLL** foi feita corretamente no M300/M350. Muitos clientes esquecem essa etapa e sofrem autuação retroativa. Importante: a Primetax atua também nesse ajuste de "pós-tese", não só na operacionalização da tese em si.

### 25.2 Outras teses refletidas na ECF

- **ICMS sobre insumos na composição de custo**: linha específica nas tabelas dinâmicas do L210 (Informativo da Composição de Custos) para refletir insumos tributados com ICMS recuperável.  
- **JCP — Juros sobre Capital Próprio**: dedução no M300, limitada pelo art. 9º da Lei 9.249/1995. Clientes que não pagaram JCP em anos com base de cálculo favorável \= **oportunidade de planejamento retroativo** (via retificação).  
- **Subvenção para investimento** (Lei 14.789/2023, pós-2024): alteração significativa do tratamento tributário, com crédito fiscal específico no M300 e exclusão limitada. Tabelas dinâmicas atualizadas a partir do AC 2024\.

---

## 26\. Divisores de águas e versionamento do leiaute

A ECF teve 12 versões (2014 a 2026). Para o sistema Primetax, os divisores mais importantes:

- **Leiaute 12 (v0012)** — AC 2025 e situações especiais 2026 (este manual).  
- **Leiaute 11 (v0011)** — AC 2024 e situações especiais 2025\. Primeira versão com acomodação da Lei 14.789/2023 (subvenções).  
- **Leiaute 10 (v0010)** — AC 2023\. Primeira com ajuste para IRPJ corporativo sob Reforma Tributária (CBS/IBS em transição).  
- **Leiaute 9 e anteriores** — AC 2022 e anteriores. Diferenças pontuais em linhas das tabelas dinâmicas.  
- **Divisor 2017 (IN 1.700/2017)** — introdução definitiva da extinção do RTT e do novo regime Lei 12.973/14. Para fatos pré-2014, regras completamente diferentes.

### 26.1 Recomendação do parser

- Ler `0000.COD_VER` e registrá-lo em cada linha importada.  
- Manter tabela de mapeamento de códigos renomeados/adicionados entre versões das tabelas dinâmicas.  
- Nunca rejeitar silenciosamente códigos desconhecidos no `CODIGO` de registros de tabela dinâmica — registrar aviso e continuar.  
- Baixar e versionar as planilhas `Tabelas_Dinamicas_ECF_Leiaute_XX_ACYYYY_....xlsx` do Portal SPED.

---

## 27\. Referências normativas

- **Decreto nº 6.022/2007** — instituição do SPED.  
- **Lei nº 6.404/1976** — Lei das S.A.  
- **Decreto-Lei nº 1.598/1977, art. 12** — conceito de receita bruta (atualizado pela Lei 12.973/2014).  
- **Lei nº 9.249/1995** — IRPJ/CSLL — alíquotas, JCP, dedutibilidade.  
- **Lei nº 9.065/1995, art. 15** — compensação de prejuízos fiscais limitada a 30%.  
- **Lei nº 9.430/1996** — Lucro Presumido e outras regras gerais.  
- **Lei nº 9.718/1998** — limite de receita bruta para Lucro Presumido (R$ 78 milhões).  
- **Lei nº 9.964/2000** — Refis.  
- **Lei nº 11.196/2005** — Lei do Bem (Inovação Tecnológica).  
- **Lei nº 11.638/2007** — conceito de entidade de grande porte.  
- **Lei nº 12.973/2014** — extinção do RTT, integração ECD-ECF, Parte B do e-Lalur.  
- **Lei nº 14.789/2023** — novo regime das subvenções para investimento.  
- **Instrução Normativa RFB nº 1.700/2017** — regulamenta Lei 12.973/2014 (receita bruta, subcontas, MEP, etc.).  
- **Instrução Normativa RFB nº 2.004/2021** — entrega da ECF.  
- **Instrução Normativa RFB nº 2.158/2023** — Declaração País-a-País.  
- **Instrução Normativa RFB nº 1.801/2018** — DEREX.  
- **Ato Declaratório Executivo Cofis nº 02/2026** — aprovação do Manual de Orientação do Leiaute 12 (janeiro/2026).  
- **RE 574.706/PR (Tema 69\)** — exclusão do ICMS da base do PIS/COFINS.  
- **Parecer SEI nº 7698/2021/ME** — operacionalização da Tese 69 pela PGFN.  
- **REsp 1.221.170/PR (Tema 779\)** — conceito de insumo.

---

## 28\. Recomendação operacional para o parser

### 28.1 Escopo mínimo de parsing da ECF

Dos mais de 100 tipos de registro do Leiaute 12, o parser Primetax pode operar na primeira iteração com **24 registros críticos**:

- **Bloco 0**: 0000, 0010, 0020, 0030  
- **Bloco E**: E010, E020 (Parte B recuperada — essencial para rastreabilidade multi-exercício)  
- **Bloco J**: J050, J051 (planos contábil e referencial — validação contra ECD)  
- **Bloco K**: K030, K155, K156, K355, K356 (conferência com ECD)  
- **Bloco L**: L100, L300 (Lucro Real)  
- **Bloco M**: M010, M300, M305, M310, M312, M350, M355, M360, M362, M410, M500 (**todo o e-Lalur/e-Lacs**)  
- **Bloco N**: N500, N630, N670 (apuração final)  
- **Bloco P**: P150, P200, P300, P400, P500 (se Lucro Presumido)  
- **Bloco X**: X480, X485 (benefícios fiscais declarados)  
- **Bloco Y**: Y570 (retenções), Y681/Y682 (Refis)  
- **Bloco 9**: 9100 (avisos), 9900 (integridade)

Registros não prioritários na primeira iteração: 0021, 0035, 0930, Bloco C inteiro (redundante com ECD primária), Bloco T (raro), Bloco U (específico), Bloco Q (caso especial), Bloco V (muito específico), Bloco W (muito específico), maioria do Bloco X (exceto X480/X485), Y520, Y590, Y600–Y660, Y720, Y730, Y750, Y800.

### 28.2 Regra de resiliência de versão

- Ler `0000.COD_VER` em cada arquivo.  
- Ter tabela de compatibilidade por ano-calendário/leiaute.  
- Ter **snapshot versionado das tabelas dinâmicas da RFB** por AC.  
- Marcar códigos desconhecidos como "não mapeado" em vez de rejeitar — o sistema não pode abortar por conta de atualização da tabela.

### 28.3 Separação física dos schemas

Manter `ecf_*` separado de `ecd_*`, `efd_contribuicoes_*` e `efd_icms_*`. Cruzamentos via joins controlados no motor de regras, jamais por mistura de tabelas.

### 28.4 Campos obrigatórios de rastreabilidade

Conforme seção 4 do `CLAUDE.md`, toda linha importada da ECF deve ter:

- `arquivo_origem`  
- `linha_arquivo`  
- `bloco` (0, C, E, J, K, L, M, N, P, Q, T, U, V, W, X, Y, 9\)  
- `registro` (0000, 0010, M300, M500, N630, etc.)  
- `cnpj_declarante` — do campo 04 do 0000  
- `dt_ini_periodo`, `dt_fin_periodo` — do 0000  
- `cod_ver` — do 0000  
- `sit_especial` — do 0000  
- `retificadora` — do 0000 (N / S / F)  
- `num_rec` — do 0000 quando retificadora  
- `tip_ecf` — do 0000 (0, 1, 2\)  
- `forma_trib` — do 0010 (1 a 9\) — **roteador semântico**  
- `forma_apur` — do 0010 (T / A)  
- `cod_qualif_pj` — do 0010 (01 / 02 / 03\)  
- `tip_esc_pre` — do 0010 (C / L)  
- `tip_ent` — do 0010 (01–15, 99\) quando aplicável

Sempre que o registro traz `CODIGO` (M300, M350, L100, L300, P150, N500, N630 etc.), capturar também a **variante** resolvida (A/B/C/R/D/E) a partir da combinação de parâmetros do 0010 — isso garante que o join com a tabela dinâmica correta funcione.

Sempre que o registro traz `COD_CTA` (M310, M360, K155, etc.), indexar para cruzamento com J050 e, transitivamente, com ECD.

Sempre que o registro traz `COD_CTA_B` (M305, M355, M410, M500), indexar para cruzamento com M010 e, multi-exercício, com E020 de ECFs anteriores.

### 28.5 Indexação para performance

Considerando que uma ECF de PJ grande pode ter milhares de registros M300/M350 e centenas de milhares de M155/M155 derivados, a indexação é crítica:

- `0000`: índice único em `(cnpj, ano_calendario, tip_ecf)`  
- `0010`: índice em `(cnpj, ano_calendario, forma_trib)` para filtros rápidos por regime  
- `M010`: índice único em `(cnpj, ano_calendario, cod_cta_b)`  
- `M300/M350`: índice composto em `(cnpj, ano_calendario, codigo, tipo_lancamento)` — crítico para análise de padrões de adição/exclusão  
- `M500`: índice em `(cnpj, ano_calendario, cod_cta_b, cod_tributo)` — crítico para rastreamento multi-exercício  
- `K155/K355`: índice em `(cnpj, ano_calendario, cod_cta)`  
- `L300/P150`: índice em `(cnpj, ano_calendario, codigo)` para agregação de Receita Bruta  
- `X480/X485`: índice em `(cnpj, ano_calendario)`

Com essa indexação, os cruzamentos ECF × ECD × EFD-Contribuições centrais (seções 24.2 a 24.8) rodam em tempo aceitável mesmo para clientes com volumes grandes.

### 28.6 Recuperação multi-exercício

A ECF é **multi-exercício por design** (via E010/E020 que recuperam a ECF anterior). Para o sistema Primetax aproveitar essa característica:

- Importar **todas as ECFs disponíveis** do cliente (até 5 exercícios, mínimo legal de retenção fiscal).  
- Manter a cadeia via `0010.HASH_ECF_ANTERIOR` — cada ECF aponta para a anterior.  
- Gerar **série temporal por `COD_CTA_B`** (conta da Parte B) para identificar contas estagnadas (cruzamento 24.5).  
- Gerar **série temporal por linha do L300/P150** para identificar tendências de receita e custos — especialmente linhas de recuperação de tributos e exclusões.

---

*Fim do guia de importação e referência da ECF — Leiaute 12 (janeiro/2026).*  
