# ECD — Escrituração Contábil Digital — Guia Prático de Importação e Referência

**Versão do leiaute coberta:** Leiaute 9 (v9.00) — Anexo ao Ato Declaratório Executivo Cofis nº 01/2026, atualização janeiro de 2026 **Vigência:** aplicável a escriturações referentes a fatos contábeis a partir do ano-calendário 2020 **Base normativa:** Instrução Normativa RFB nº 2.003/2021 (e alterações) e Decreto nº 6.022/2007 (SPED) **Fonte original:** Manual de Orientação do Leiaute 9 da Escrituração Contábil Digital — RFB/Subsecretaria de Fiscalização **Objetivo deste documento:** servir como referência técnica instrumental para o sistema Primetax SPED Cross-Reference. O foco é extrair da ECD os elementos necessários ao cruzamento com a EFD-Contribuições e a EFD ICMS/IPI, e à validação de teses envolvendo receita bruta, exclusão do ICMS da base de PIS/COFINS, e identificação de créditos não aproveitados. Este arquivo NÃO se propõe a ser enciclopédico sobre contabilidade comercial ou sobre a ECD como obrigação autônoma — esse é escopo de outro projeto.

---

## Índice

1. Visão geral estrutural  
2. Pessoas jurídicas obrigadas e dispensadas  
3. Regras gerais de preenchimento  
4. Tabelas externas e internas  
5. Registro 0000 — abertura e identificação  
6. Registros do Bloco 0 (demais)  
7. Bloco C — informações recuperadas da ECD anterior  
8. Registro I010 — identificação da escrituração  
9. Registro I050 — plano de contas (âncora do cruzamento)  
10. Registros I051/I052/I053 — plano referencial, aglutinação e subcontas  
11. Registros I150 e I155 — saldos periódicos (nó central de cruzamento)  
12. Registros I200 e I250 — lançamentos e partidas  
13. Registros I300/I310 e I350/I355 — balancetes diários e saldos de resultado  
14. Bloco J — demonstrações contábeis (J005, J100, J150, J210)  
15. Bloco K — conglomerados econômicos  
16. Bloco 9 — encerramento  
17. Mapeamento de cruzamentos ECD ↔ EFD-Contribuições ↔ EFD ICMS/IPI  
18. Tese 69 na camada contábil  
19. Divisores de águas e versionamento do leiaute  
20. Referências normativas  
21. Recomendação operacional para o parser

---

## 1\. Visão geral estrutural

A ECD é a versão digital, transmitida ao SPED, dos livros contábeis comerciais: Diário, Razão, Balancetes Diários e Balanços, e Razão Auxiliar. Substitui a escrituração em papel para fins de registro mercantil e serve de insumo para outras escriturações (ECF, DME, etc.) e para procedimentos fiscais da RFB, da PGFN, dos fiscos estaduais conveniados, das Juntas Comerciais e do Conselho Federal de Contabilidade.

### 1.1 Natureza do arquivo

- Arquivo-texto codificado (Latin1 ou UTF-8, conforme definido no programa gerador)  
- Cada registro em uma linha, campos separados pelo caractere **pipe (`|`)**  
- Cada linha inicia e termina com `|`  
- Estrutura **hierárquica pai-filho**, identificada pelos primeiros caracteres após o pipe inicial (`REG`)  
- Os primeiros caracteres do `REG` identificam o bloco (ex: `I155` → Bloco I; `J150` → Bloco J)

### 1.2 Blocos do arquivo

| Bloco | Descrição | Papel no cruzamento fiscal |
| :---: | :---- | :---- |
| **0** | Abertura, Identificação e Referências | Identificação do declarante, tipo de ECD, período, plano referencial escolhido |
| **C** | Informações Recuperadas da Escrituração Contábil Anterior | Saldos recuperados, plano anterior, DRE anterior — ponte entre exercícios |
| **I** | Lançamentos Contábeis | **Coração da ECD** — plano de contas, saldos mensais, lançamentos, balancetes |
| **J** | Demonstrações Contábeis | BP, DRE, DLPA/DMPL — ponto de amarração com a realidade fiscal declarada |
| **K** | Conglomerados Econômicos | Demonstrações consolidadas (grupos empresariais) |
| **9** | Controle e Encerramento do Arquivo Digital | Totalizadores e controle |

Não há Blocos A, B, D, E, F, G, H, M ou P na ECD — esta é uma diferença estrutural importante em relação à EFD-Contribuições e à EFD ICMS/IPI.

### 1.3 Hierarquia e chave dos registros

Cada registro declara seu nível hierárquico (0 a 4\) e ocorrência (1:1, 1:N, 0:N, V). O `CLAUDE.md` do projeto exige que a rastreabilidade seja preservada linha a linha — isso inclui, para a ECD, os campos de chave primária de cada registro (ex: `COD_CTA` no I050; `COD_CTA + COD_CCUS` no I155; `NUM_LCTO` no I200; `COD_AGL` no J100/J150).

### 1.4 Diferenças operacionais em relação aos demais SPEDs

Para calibrar o parser, três diferenças são críticas:

1. **A ECD não tem perfil de declarante.** Diferente da EFD ICMS/IPI (perfis A/B/C), a granularidade de detalhamento da ECD é definida pela forma de escrituração (`I010.IND_ESC`): G, R, A, B ou Z. O parser não precisa interpretar "perfil"; precisa sim interpretar o tipo de livro.  
2. **A periodicidade da ECD é anual** (um arquivo por ano-calendário, salvo situação especial), enquanto a EFD-Contribuições e a EFD ICMS/IPI são mensais. Qualquer cruzamento ECD × EFD envolve agregar 12 competências da EFD para uma única ECD.  
3. **A ECD não traz informações de tributos por lançamento**, apenas os valores contábeis. A amarração com a apuração de PIS/COFINS passa obrigatoriamente pelo `COD_CTA` (conta contábil) referenciado nos registros fiscais (C170.campo37, M105.COD\_CTA etc.).

---

## 2\. Pessoas jurídicas obrigadas e dispensadas

Obrigada a entregar ECD, nos termos da IN RFB 2.003/2021 e atualizações:

- Pessoas jurídicas tributadas pelo IRPJ com base no **Lucro Real**  
- Pessoas jurídicas tributadas pelo **Lucro Presumido** que distribuam, a título de lucros, parcela superior ao valor da base de cálculo do IRPJ diminuída dos tributos devidos  
- **Pessoas jurídicas imunes e isentas** obrigadas à escrituração contábil (em regra, as que arrecadam contribuições sociais ou têm receita, doações ou aplicações financeiras significativas)  
- **SCP** (Sociedades em Conta de Participação) enquadradas nas hipóteses acima — cada SCP entrega sua própria ECD, assinada pelo sócio ostensivo  
- Entidades de grande porte sujeitas a auditoria independente (Lei 11.638/2007, art. 3º: ativo total \> R$ 240 milhões OU receita bruta anual \> R$ 300 milhões) — refletido no campo `IND_GRANDE_PORTE` do 0000

Dispensadas: pessoas jurídicas optantes pelo Simples Nacional, órgãos públicos, pessoas físicas e algumas imunes/isentas de pequeno porte — hipóteses detalhadas na IN.

**Uso no sistema Primetax:** a identificação do regime tributário do declarante no momento do processamento orienta quais cruzamentos fazem sentido. Cliente optante pelo Lucro Presumido raramente terá EFD-Contribuições não-cumulativa; cliente de Grande Porte terá plano de contas mais detalhado e provavelmente ECD consolidada (Bloco K). Esses sinalizadores devem ser capturados da ECD e propagados ao relatório de diagnóstico.

---

## 3\. Regras gerais de preenchimento

### 3.1 Formato dos campos

- **Tipo `C` (caractere/alfanumérico):** texto. Em regra em maiúsculas, sem acentuação. Sem caracteres de controle (\< espaço) nem pipe no conteúdo.  
- **Tipo `N` (numérico):** valores numéricos sem formatação. Separador decimal vírgula; sem separador de milhar; sem sinais; sem caracteres especiais. Quando representam datas, no formato `DDMMAAAA` sem separadores (ex: `31122025`).  
- Campos com tamanho **fixo** são marcados com asterisco no manual (ex: `008*` para datas).  
- Campos numéricos com **casas decimais** têm o indicador `Decimal` explícito — tipicamente `02` para valores monetários.

### 3.2 Regras de preenchimento comuns

- Campos não aplicáveis ou não obrigatórios podem vir vazios, mas os delimitadores pipe devem ser mantidos.  
- Valor zero em campo numérico obrigatório pode ser preenchido como `0` ou `0,00`.  
- Em campos indicadores de débito/crédito (`IND_DC_INI`, `IND_DC_FIN`, `IND_DC`), mesmo quando o saldo é zero, o indicador (`D` ou `C`) é obrigatório — não pode ficar em branco.

### 3.3 Regras específicas que impactam o parser Primetax

- **Moeda funcional** (`0000.IDENT_MF = "S"`): quando a empresa escritura em moeda funcional (art. 287 IN RFB 1.700/2017), os registros I155, I157, I200, I250, I310 e I355 recebem **campos adicionais** em reais via registro I020. Esses campos têm nomes específicos (`VL_SLD_INI_MF`, `VL_DEB_MF`, `VL_CRED_MF`, `VL_SLD_FIN_MF`, `IND_DC_INI_MF`, `IND_DC_FIN_MF`, `VL_LCTO_MF`, etc.) e são os que devem ser usados para cruzamento com a ECF e, indiretamente, com a EFD-Contribuições. O parser deve detectar `0000.IDENT_MF = "S"` e, se afirmativo, priorizar os campos `_MF` nas comparações fiscais.  
- **Lançamento de quarta fórmula** (múltiplos débitos e múltiplos créditos): gera aviso no PGE, mas é permitido conforme CTG 2001 (R3) do CFC. O parser não deve rejeitar.  
- **Plano de contas com 4 níveis mínimos:** a CTG 2001 (R3) exige que o plano tenha pelo menos 4 níveis (sintéticos \+ analíticos), e a REGRA\_VALIDA\_NIVEL\_CONTAS do I050 só admite contas analíticas de ativo/passivo/PL em `NIVEL >= 4`.

---

## 4\. Tabelas externas e internas

A ECD é relativamente auto-contida — as tabelas críticas estão nos registros 0000, I050 e na tabela de Planos de Contas Referenciais. Destacam-se:

### 4.1 Código do Plano de Contas Referencial (`0000.COD_PLAN_REF`)

Define qual dos 10 planos referenciais publicados pela RFB será usado para o mapeamento das contas analíticas do I050 via registro I051.

| Código | Plano Referencial |
| :---: | :---- |
| 1 | PJ em Geral – Lucro Real |
| 2 | PJ em Geral – Lucro Presumido |
| 3 | Financeiras – Lucro Real |
| 4 | Seguradoras – Lucro Real |
| 5 | Imunes e Isentas em Geral |
| 6 | Imunes e Isentas – Financeiras |
| 7 | Imunes e Isentas – Seguradoras |
| 8 | Entidades Fechadas de Previdência Complementar |
| 9 | Partidos Políticos |
| 10 | Financeiras – Lucro Presumido |

Campo em branco indica que a PJ optou por não realizar o mapeamento — situação rara e geralmente indicativa de ECD de baixa qualidade técnica.

**Uso no sistema Primetax:** o código do plano referencial é um discriminador crítico. Planos 1 e 2 (Lucro Real e Presumido não-financeiros) são a grande maioria dos clientes-alvo da Primetax; planos 3, 4 e 10 exigem lógica de cruzamento própria (contas setoriais específicas, regime cumulativo obrigatório em parte da receita, etc.). O parser deve registrar o plano referencial em todas as linhas derivadas para que os relatórios segreguem corretamente.

### 4.2 Natureza das Contas (I050.COD\_NAT)

| Código | Grupo |
| :---: | :---- |
| 01 | Contas de Ativo |
| 02 | Contas de Passivo |
| 03 | Patrimônio Líquido |
| 04 | Contas de Resultado |
| 05 | Contas de Compensação |
| 09 | Outras |

### 4.3 Situação Especial (0000.IND\_SIT\_ESP)

| Código | Descrição |
| :---: | :---- |
| 0 | Normal (Início do Período) |
| 1 | Abertura |
| 2 | Cisão |
| 3 | Fusão |
| 4 | Incorporação |
| 5 | Extinção |

### 4.4 Indicador de Forma de Escrituração (I010.IND\_ESC)

| Código | Tipo de Livro |
| :---: | :---- |
| G | Livro Diário (Completo, sem escrituração auxiliar) |
| R | Livro Diário com Escrituração Resumida (com auxiliares) |
| A | Livro Diário Auxiliar ao Diário com Escrituração Resumida |
| B | Livro Balancetes Diários e Balanços |
| Z | Razão Auxiliar (Livro Contábil Auxiliar com leiaute parametrizável) |

**Uso no sistema Primetax:** tipos `G` e `R` são os predominantes e concentram os cruzamentos. Tipo `B` (balancetes diários e balanços) exige lógica diferente: não há I200/I250, mas sim I300/I310. Tipo `Z` (razão auxiliar parametrizável) envolve os registros I500–I555 e é, em regra, irrelevante para o cruzamento PIS/COFINS direto — mas pode conter o Razão Auxiliar das Subcontas (RAS) do art. 8º da IN 1.700/2017, relevante quando há ajustes societários específicos.

---

## 5\. Registro 0000 — abertura e identificação

Registro único, nível hierárquico 0, ocorrência 1:1.

| \# | Campo | Descrição | Tipo | Tam | Obrig |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | Texto fixo "0000" | C | 004 | S |
| 02 | `LECD` | Texto fixo "LECD" | C | 004 | S |
| 03 | `DT_INI` | Data inicial do arquivo | N | 008 | S |
| 04 | `DT_FIN` | Data final do arquivo | N | 008 | S |
| 05 | `NOME` | Nome empresarial | C | – | S |
| 06 | `CNPJ` | CNPJ da PJ (da sócia ostensiva, no caso de SCP) | C | 014 | S |
| 07 | `UF` | Sigla da UF | C | 002 | S |
| 08 | `IE` | Inscrição Estadual | C | – | N |
| 09 | `COD_MUN` | Código IBGE do município | N | 007 | N |
| 10 | `IM` | Inscrição Municipal | C | – | N |
| 11 | `IND_SIT_ESP` | Indicador de situação especial (tabela 4.3) | N | 001 | N |
| 12 | `IND_SIT_INI_PER` | Indicador de situação no início do período | N | 001 | S |
| 13 | `IND_NIRE` | Indicador de existência de NIRE (0=não; 1=sim) | N | 001 | S |
| 14 | `IND_FIN_ESC` | Finalidade: 0=Original; 1=Substituta | N | 001 | S |
| 15 | `COD_HASH_SUB` | Hash da escrituração substituída | C | 040 | N |
| 16 | `IND_GRANDE_PORTE` | 0=não é grande porte; 1=é grande porte (auditoria independente) | N | 001 | S |
| 17 | `TIP_ECD` | Tipo: 0=PJ não-SCP; 1=PJ sócia ostensiva de SCP; 2=ECD da SCP | N | 001 | S |
| 18 | `COD_SCP` | CNPJ da SCP (preenchido apenas pela própria SCP) | C | 014 | N |
| 19 | `IDENT_MF` | Escrituração em moeda funcional: S=sim; N=não | C | 001 | S |
| 20 | `IND_ESC_CONS` | Escrituração consolidada: S=sim; N=não | C | 001 | S |
| 21 | `IND_CENTRALIZADA` | 0=Centralizada; 1=Descentralizada | N | 001 | S |
| 22 | `IND_MUDANC_PC` | 0=sem mudança de PC; 1=houve mudança no plano de contas | N | 001 | S |
| 23 | `COD_PLAN_REF` | Código do plano referencial (tabela 4.1) ou vazio | C | 002 | N |

**Uso no sistema Primetax:** este é o registro-âncora. Os campos 16 (IND\_GRANDE\_PORTE), 19 (IDENT\_MF), 20 (IND\_ESC\_CONS), 22 (IND\_MUDANC\_PC) e 23 (COD\_PLAN\_REF) devem ser propagados como colunas de contexto em todas as linhas importadas, da mesma forma que `cnpj_declarante` e `dt_ini_periodo`. O campo 14 (IND\_FIN\_ESC=1) indica escrituração substituta e é sinal de que pode existir ECD original a ser descartada/comparada. O campo 22 (IND\_MUDANC\_PC=1) é especialmente crítico: ele indica que houve mudança de plano de contas no período, o que quebra qualquer cruzamento baseado em `COD_CTA` contra EFDs de períodos anteriores — o Bloco C (registros C050/C052/C155) deve ser consultado para reconciliação via códigos de aglutinação.

---

## 6\. Registros do Bloco 0 (demais)

### 6.1 Registro 0001 — abertura do Bloco 0

Registro fixo, sem campos relevantes além da marcação de abertura. Campo `IND_DAD`: 0=bloco com dados; 1=bloco sem dados.

### 6.2 Registro 0007 — Outras Inscrições Cadastrais da PJ

Nível 2, ocorrência 1:N. Informa inscrições cadastrais adicionais (estaduais e municipais) quando a PJ atua em mais de uma UF ou município. Campos: `COD_ENT` (código do órgão — tabela 5.1.1 do manual) e `COD_INSCR` (inscrição).

### 6.3 Registro 0020 — Escrituração Contábil Descentralizada

Obrigatório quando `0000.IND_CENTRALIZADA = 1`. Identifica os estabelecimentos cujos livros estão consolidados nesta ECD.

### 6.4 Registro 0035 — Identificação das SCP

Obrigatório quando `0000.TIP_ECD = 1` (sócio ostensivo que declara SCPs no próprio arquivo — embora atualmente a regra predominante seja ECD separada por SCP). Contém `COD_SCP` e `NOME_SCP`.

### 6.5 Registro 0150 — Tabela de Cadastro do Participante

Nível 2, ocorrência 1:N. Contém os participantes referenciados nos lançamentos (I250.COD\_PART). Relevante para rastrear contrapartes em lançamentos específicos quando aplicável.

| \# | Campo | Descrição | Tipo | Tam | Obrig |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "0150" | C | 004 | S |
| 02 | `COD_PART` | Código do participante | C | – | S |
| 03 | `NOME` | Nome empresarial | C | 100 | S |
| 04 | `COD_PAIS` | Código do país (tabela BACEN) | N | 005 | S |
| 05 | `CNPJ` | CNPJ (PJ nacional) | N | 014 | N |
| 06 | `CPF` | CPF (PF) | N | 011 | N |
| 07 | `IE` | Inscrição Estadual | C | 014 | N |
| 08 | `COD_MUN` | Município | N | 007 | N |
| 09 | `SUFRAMA` | SUFRAMA | C | 009 | N |
| 10 | `END` | Endereço | C | – | N |
| 11 | `NUM` | Número | C | 010 | N |
| 12 | `COMPL` | Complemento | C | – | N |
| 13 | `BAIRRO` | Bairro | C | – | N |

### 6.6 Registro 0180 — Identificação do Relacionamento com o Participante

Nível 3, ocorrência 1:N. Informa, para cada participante do 0150 informado em lançamentos, o tipo de relacionamento (coligada, controlada, vinculada, etc.) — chave para detecção de operações intercompany.

### 6.7 Registro 0990 — Encerramento do Bloco 0

Totalizador. Campo: `QTD_LIN_0` (quantidade total de linhas do Bloco 0).

---

## 7\. Bloco C — informações recuperadas da ECD anterior

O Bloco C preserva dados da ECD imediatamente anterior, para fins de continuidade dos saldos e das demonstrações. Não é preenchido manualmente pelo declarante — é gerado pelo PGE do Sped Contábil ao recuperar o arquivo anterior na funcionalidade "Recuperar ECD Anterior".

| Registro | Descrição | Origem |
| :---: | :---- | :---- |
| `C001` | Abertura do Bloco C | Marcador |
| `C040` | Identificação da ECD Recuperada | 0000 da ECD anterior |
| `C050` | Plano de Contas Recuperado | I050 da ECD anterior |
| `C051` | Plano de Contas Referencial Recuperado | I051 da ECD anterior |
| `C052` | Indicação dos Códigos de Aglutinação Recuperados | I052 da ECD anterior |
| `C150` | Saldos Periódicos Recuperados – Identificação do Período | I150 da ECD anterior (último mês) |
| `C155` | Detalhe dos Saldos Periódicos Recuperados | I155 da ECD anterior (saldos finais do exercício) |
| `C600` | Demonstrações Contábeis Recuperadas | J005/J100 da ECD anterior |
| `C650` | Demonstração do Resultado do Exercício Recuperada | J150 da ECD anterior |
| `C990` | Encerramento do Bloco C | Totalizador |

**Uso no sistema Primetax:** o Bloco C é a **única ponte confiável entre exercícios** quando há mudança de plano de contas (`0000.IND_MUDANC_PC = 1`). Permite o cruzamento de tendências plurianuais de contas de receita, de ICMS a recuperar, e de estoques sem os falsos positivos causados pela renomeação/reclassificação de contas. Em clientes com histórico longo, o C650 (DRE recuperada) serve de espelho independente para conferência contra o J150 do período imediatamente anterior.

---

## 8\. Registro I010 — identificação da escrituração

Nível 2, ocorrência 1:1.

| \# | Campo | Descrição | Tipo | Tam | Valores |
| :---: | :---- | :---- | :---: | :---: | :---- |
| 01 | `REG` | "I010" | C | 004 | – |
| 02 | `IND_ESC` | Forma de escrituração | C | 001 | G, R, A, B, Z |
| 03 | `COD_VER_LC` | Versão do Leiaute Contábil | C | – | **9.00** (a partir do AC 2020\) |

**Uso no sistema Primetax:** o `COD_VER_LC` é o campo que identifica o **leiaute estruturalmente aplicável**. Leiaute 9 (valor `9.00`) é vigente para escriturações cujos períodos sejam iguais ou posteriores ao ano-calendário 2020\. Arquivos com versões anteriores (8.00, 7.00, ...) correspondem a períodos pré-2020 e têm estruturas de campo ligeiramente diferentes em I155, I200 e J150 — o parser deve manter tabelas de compatibilidade por versão, como previsto na seção 15 do arquivo-irmão `efd-icms-ipi-layout.md` e no `CLAUDE.md`. A regra `REGRA_VERSAO_LC` rejeita versões inválidas no PGE, mas um parser tolerante em ambiente fora do PGE deve apenas emitir aviso, nunca abortar.

---

## 9\. Registro I050 — plano de contas (âncora do cruzamento)

Nível 3, ocorrência 1:N. Um registro por conta do plano (sintética ou analítica). Regra de duplicidade: `COD_CTA` é único por arquivo.

| \# | Campo | Descrição | Tipo | Tam | Obrig |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "I050" | C | 004 | S |
| 02 | `DT_ALT` | Data da inclusão/alteração da conta | N | 008 | S |
| 03 | `COD_NAT` | Código da natureza (tabela 4.2) | C | 002 | S |
| 04 | `IND_CTA` | S=Sintética; A=Analítica | C | 001 | S |
| 05 | `NIVEL` | Nível no plano | N | – | S |
| 06 | `COD_CTA` | Código da conta — **chave** | C | – | S |
| 07 | `COD_CTA_SUP` | Código da conta de nível imediatamente superior | C | – | N (S se NIVEL \> 1\) |
| 08 | `CTA` | Nome da conta | C | 060 | S |

### 9.1 Regras essenciais

- `COD_CTA` e `COD_CTA_SUP` **nunca podem ser iguais** na mesma linha.  
- Contas analíticas de ativo, passivo ou PL (`COD_NAT` ∈ {01, 02, 03}) exigem `NIVEL >= 4` quando `IND_ESC` ∈ {G, R, B}.  
- A natureza da conta-filha deve igualar a da conta-pai em níveis \> 2 (REGRA\_NATUREZA\_CONTA).  
- Só podem constar no plano contas com saldo ou movimento no período completo da ECD (item 8 da CTG 2001 R3).

### 9.2 Por que o I050 é o nó central do cruzamento Primetax

O campo `COD_CTA` é **a chave de amarração** entre os sistemas contábil e fiscal:

- **EFD-Contribuições** — `C170.COD_CTA` (campo 37), `C175.COD_CTA` (campo 11), `F100.COD_CTA`, `F120.COD_CTA`, `F130.COD_CTA`, `M105.COD_CTA` (a partir de 11/2017), `M505.COD_CTA` referenciam contas desta tabela I050.  
- **EFD ICMS/IPI** — `C170.COD_CTA` (campo 37 no SPED Fiscal) idem.

Qualquer cruzamento horizontal entre EFD-Contribuições e ECD passa por `(cnpj_declarante, ano_calendario, cod_cta)`. Para o cruzamento ser válido, o parser deve verificar:

1. Se `0000.IND_MUDANC_PC = 1` na ECD atual, **usar o Bloco C (C050/C052) para reconstituir a correspondência** entre o plano antigo (usado na EFD dos meses anteriores à mudança) e o plano novo.  
2. Se a ECD está em moeda funcional (`IDENT_MF = S`), usar os valores convertidos em reais dos campos adicionais `_MF`, não os valores originais em moeda funcional.  
3. Se a ECD é consolidada (Bloco K), não usar as contas consolidadas diretamente — só as individuais da própria PJ declarante.

---

## 10\. Registros I051/I052/I053 — plano referencial, aglutinação e subcontas

### 10.1 Registro I051 — Plano de Contas Referencial

Nível 4, ocorrência 1:N. Liga cada conta analítica do I050 a uma conta do plano referencial escolhido em `0000.COD_PLAN_REF`.

| \# | Campo | Descrição |
| :---: | :---- | :---- |
| 01 | `REG` | "I051" |
| 02 | `COD_CCUS` | Código do centro de custos (se houver) |
| 03 | `COD_CTA_REF` | Código da conta no plano referencial |

Obrigatório quando `0000.COD_PLAN_REF` foi preenchido (REGRA\_I051\_OBRIGATORIO).

**Uso no sistema Primetax:** o I051 é a porta para agregar dezenas/centenas de contas analíticas heterogêneas de clientes diferentes em **uma linguagem comum** (o plano referencial da RFB). Permite que o sistema rode relatórios comparativos entre clientes, benchmarks por CNAE, e detecte outliers setoriais — todos pela via da conta referencial, não da conta analítica da PJ.

### 10.2 Registro I052 — Indicação dos Códigos de Aglutinação

Nível 4, ocorrência 1:N. Liga cada conta analítica do I050 a um **código de aglutinação** atribuído pela PJ, que será usado na composição das linhas do Balanço (J100) e da DRE (J150).

| \# | Campo | Descrição |
| :---: | :---- | :---- |
| 01 | `REG` | "I052" |
| 02 | `COD_CCUS` | Código do centro de custos (se houver) |
| 03 | `COD_AGL` | Código de aglutinação (definido pela PJ) |

**Código de aglutinação ≠ código de conta contábil.** O código de aglutinação é um rótulo criado pela PJ para agrupar contas analíticas numa mesma linha de demonstração. Exemplo: contas "Banco A", "Banco B" e "Banco C" (três analíticas do I050) podem ter o mesmo `COD_AGL` e aparecer como uma única linha "Disponibilidades" no J100.

**Uso no sistema Primetax:** o I052 é o que liga o **nível contábil (I050/I155)** ao **nível demonstrativo (J100/J150)**. Essa ponte é decisiva para validar a consistência da DRE contra os saldos de resultado antes do encerramento — um dos cruzamentos mais poderosos da ECD.

### 10.3 Registro I053 — Subcontas Correlatas

Relacionado ao Razão Auxiliar das Subcontas (RAS) da IN 1.700/2017, art. 295 e seguintes, usado para demonstrar ajustes de avaliação (valor justo, depreciação diferenciada, etc.) para fins de adições/exclusões no Lalur. Relevante em cruzamentos mais avançados envolvendo ECF.

---

## 11\. Registros I150 e I155 — saldos periódicos (nó central de cruzamento)

### 11.1 Registro I150 — Identificação do Período

Nível 3, ocorrência 0:N. Delimita cada mês-calendário (ou fração, em situações especiais) para o qual haverá detalhamento de saldos.

| \# | Campo | Descrição | Tipo | Tam |
| :---: | :---- | :---- | :---: | :---: |
| 01 | `REG` | "I150" | C | 004 |
| 02 | `DT_INI` | Data inicial do período (1º dia do mês, salvo situação especial) | N | 008 |
| 03 | `DT_FIN` | Data final do período (último dia do mês, salvo situação especial) | N | 008 |

Regra crítica: deve existir um I150 para **cada mês** do intervalo do arquivo (REGRA\_CONTINUIDADE\_SALDOS\_PERIODICOS). Um arquivo anual sempre tem 12 I150, exceto em abertura, cisão, fusão, incorporação ou extinção.

### 11.2 Registro I155 — Detalhe dos Saldos Periódicos

Nível 4, ocorrência 0:N. Filho do I150. **Este é o registro mais importante da ECD para cruzamento com a EFD-Contribuições.**

Traz, para cada conta analítica (eventualmente por centro de custos), dentro do mês identificado pelo I150 pai:

| \# | Campo | Descrição | Tipo | Tam | Dec |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "I155" | C | 004 | – |
| 02 | `COD_CTA` | Código da conta analítica (remete ao I050) | C | – | – |
| 03 | `COD_CCUS` | Código do centro de custos | C | – | – |
| 04 | `VL_SLD_INI` | Valor do saldo inicial do período | N | 019 | 02 |
| 05 | `IND_DC_INI` | D=Devedor; C=Credor (situação do saldo inicial) | C | 001 | – |
| 06 | `VL_DEB` | Valor total dos débitos no período | N | 019 | 02 |
| 07 | `VL_CRED` | Valor total dos créditos no período | N | 019 | 02 |
| 08 | `VL_SLD_FIN` | Valor do saldo final do período | N | 019 | 02 |
| 09 | `IND_DC_FIN` | D=Devedor; C=Credor (situação do saldo final) | C | 001 | – |

Em moeda funcional, acrescem os campos 10–15 (`VL_SLD_INI_MF`, `IND_DC_INI_MF`, `VL_DEB_MF`, `VL_CRED_MF`, `VL_SLD_FIN_MF`, `IND_DC_FIN_MF`).

### 11.3 Regras de consistência do I155 (críticas para o parser)

- **Fechamento do balanço:** a soma dos saldos iniciais de todas as contas, considerando D/C, é zero por período (REGRA\_VALIDACAO\_SOMA\_SALDO\_INICIAL). Idem para os saldos finais.  
- **Partida dobrada mensal:** soma de `VL_DEB` \= soma de `VL_CRED` por período (REGRA\_VALIDACAO\_DEB\_DIF\_CRED).  
- **Continuidade mensal:** o `VL_SLD_INI` de cada mês (a partir do 2º) é igual ao `VL_SLD_FIN` do mês imediatamente anterior (REGRA\_VALIDACAO\_SALDO\_INI\_DIF\_FIN).  
- **Coerência com lançamentos:** a soma dos débitos dos I250 por conta e período é igual ao `VL_DEB` do I155 da mesma conta/período (REGRA\_VALIDACAO\_VALOR\_DEB). Idem para créditos.  
- **Coerência com balancete:** quando `I010.IND_ESC = B`, a validação anterior é feita contra I300/I310 em vez de I200/I250.

### 11.4 Por que o I155 é o coração do cruzamento Primetax

O I155 permite **reconstruir a contabilidade mensal conta-a-conta sem ler um único lançamento individual**, e é exatamente nesta granularidade (mês × conta analítica) que a EFD-Contribuições informa `VL_REC_BRT` nos registros M210/M610, `VL_BC_PIS`/`VL_BC_COFINS` nos registros C170/C181/C185/C481/C485 etc., e `COD_CTA` em todos eles. Cruzamentos diretos viáveis:

- Receita contábil mensal (soma dos créditos das contas de `COD_NAT = 04` com natureza de receita) × `VL_REC_BRT` do M210/M610 do mesmo mês  
- Valor contábil de ICMS recuperável (saldo de contas específicas do ativo circulante) × `VL_BC_PIS` reduzido pela exclusão do ICMS  
- Valor contábil de depreciação acumulada × créditos de PIS/COFINS sobre encargos de depreciação do F120  
- Saldo contábil de estoques (contas de `COD_NAT = 01` de tipo "Estoques") × H010 da EFD ICMS/IPI

A regra fundamental para o sistema Primetax: **o I155 deve ser indexado em banco por `(cnpj_declarante, ano_mes_competencia, cod_cta)`** para permitir joins eficientes com os registros da EFD-Contribuições.

---

## 12\. Registros I200 e I250 — lançamentos e partidas

### 12.1 Registro I200 — Lançamento Contábil

Nível 3, ocorrência 0:N. Cabeçalho do lançamento.

| \# | Campo | Descrição | Tipo | Tam | Dec |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "I200" | C | 004 | – |
| 02 | `NUM_LCTO` | Número/código único do lançamento — **chave** | C | – | – |
| 03 | `DT_LCTO` | Data do lançamento | N | 008 | – |
| 04 | `VL_LCTO` | Valor do lançamento | N | 019 | 02 |
| 05 | `IND_LCTO` | N=Normal; E=Encerramento; X=Extemporâneo | C | 001 | – |
| 06 | `DT_LCTO_EXT` | Data do fato original, se extemporâneo | N | 008 | – |

Campos adicionais em moeda funcional: `VL_LCTO_MF` (campo 07 criado via I020).

### 12.2 Registro I250 — Partidas do Lançamento

Nível 4, ocorrência 0:N. Filho do I200. Cada partida (débito ou crédito) individualmente.

| \# | Campo | Descrição | Tipo | Tam | Dec |
| :---: | :---- | :---- | :---: | :---: | :---: |
| 01 | `REG` | "I250" | C | 004 | – |
| 02 | `COD_CTA` | Conta debitada/creditada | C | – | – |
| 03 | `COD_CCUS` | Centro de custos | C | – | – |
| 04 | `VL_DC` | Valor da partida | N | 019 | 02 |
| 05 | `IND_DC` | D=Débito; C=Crédito | C | 001 | – |
| 06 | `NUM_ARQ` | Localização do documento arquivado | C | – | – |
| 07 | `COD_HIST_PAD` | Código de histórico padronizado (tabela I075) | C | – | – |
| 08 | `HIST` | Histórico completo ou complementar (tamanho até 65535\) | C | – | – |
| 09 | `COD_PART` | Código do participante (quando identificado em 0180\) | C | – | – |

### 12.3 Lançamentos extemporâneos (IND\_LCTO \= "X")

Incluído no Leiaute 9 para atender aos itens 31–36 da ITG 2000 (R1) do CFC. São lançamentos feitos no exercício atual para corrigir fatos de exercícios anteriores sem a necessidade de substituição da ECD antiga. Em face do tratamento contábil específico, o campo `DT_LCTO_EXT` passa a ser obrigatório (data do fato original) e o histórico deve especificar o motivo, a data e o número do lançamento de origem.

**Uso no sistema Primetax:** lançamentos extemporâneos `IND_LCTO = X` são **sinal fiscal de alto valor**: indicam que o declarante reconheceu, na contabilidade, um fato de exercício anterior que não foi registrado na época. Estes lançamentos frequentemente têm contrapartida fiscal não escriturada na EFD-Contribuições do período de competência original — ou seja, constituem forte candidato a **recuperação de créditos extemporâneos** via retificação da EFD-Contribuições do período `DT_LCTO_EXT`. O parser deve marcar todos os I200 com `IND_LCTO = X` para revisão priorizada, capturando especialmente os que envolvem contas de "PIS a Recuperar", "COFINS a Recuperar", "ICMS sobre Compras", "Fretes a Recuperar", ou "Depreciação de Imobilizado".

### 12.4 Regras de consistência

- Soma dos débitos do I250 \= soma dos créditos \= `VL_LCTO` do I200 pai (REGRA\_VALIDACAO\_VL\_LCTO\_DEB e REGRA\_VALIDACAO\_VL\_LCTO\_CRED).  
- Lançamento de 4ª fórmula (mais de um D e mais de um C): permitido mas emite aviso (REGRA\_LCTO\_4\_FORMULA).  
- Lançamentos de encerramento (`IND_LCTO = E`) são validados contra o registro I355 (REGRA\_VALIDACAO\_SALDO\_CONTA).

---

## 13\. Registros I300/I310 e I350/I355 — balancetes diários e saldos de resultado

### 13.1 I300/I310 — Balancetes Diários

Usados quando `I010.IND_ESC = B` (Livro Balancetes Diários e Balanços). I300 identifica a data; I310 detalha, para cada conta e centro de custos, débitos/créditos do dia. Mesma estrutura conceitual do I150/I155, mas em granularidade diária.

### 13.2 I350/I355 — Saldos das Contas de Resultado Antes do Encerramento

**I350** identifica a data de apuração do resultado (normalmente 31/12 ou último dia do exercício social); **I355** detalha, para cada conta de resultado (`COD_NAT = 04`), o saldo antes dos lançamentos de encerramento do tipo "E".

| I355 | Campo | Descrição |
| :---: | :---- | :---- |
| 01 | `REG` | "I355" |
| 02 | `COD_CTA` | Conta de resultado |
| 03 | `COD_CCUS` | Centro de custos |
| 04 | `VL_CTA` | Saldo antes do encerramento |
| 05 | `IND_DC` | D ou C |

Em moeda funcional: campo `VL_CTA_MF` (06).

**Uso no sistema Primetax:** o I355 é o **ponto de verdade contábil da receita e da despesa do exercício** — antes que o encerramento do resultado misture tudo em "Lucros Acumulados". O J150 (DRE) é construído agregando estes valores via códigos de aglutinação. Qualquer cruzamento Receita Bruta contábil × Receita Bruta PIS/COFINS deve partir daqui (ou, equivalentemente, do I155 consolidado das contas de receita).

---

## 14\. Bloco J — demonstrações contábeis

### 14.1 Registro J005 — Demonstrações Contábeis

Nível 2, ocorrência 0:N. Cabeçalho de cada conjunto de demonstrações do período. Chave: `DT_INI + DT_FIN + ID_DEM`.

| \# | Campo | Descrição |
| :---: | :---- | :---- |
| 01 | `REG` | "J005" |
| 02 | `DT_INI` | Data inicial das demonstrações (normalmente o dia seguinte ao último encerramento) |
| 03 | `DT_FIN` | Data final das demonstrações |
| 04 | `ID_DEM` | 1=Demonstrações da própria PJ; 2=Demonstrações consolidadas/de outras PJ |
| 05 | `CAB_DEM` | Cabeçalho (obrigatório quando ID\_DEM=2) |

Regra-chave: quando o encerramento do exercício social (`I030.DT_EX_SOCIAL`) cai dentro do período do arquivo e a forma de escrituração é G, R ou B, deve existir pelo menos um J005 cujo `DT_FIN` seja igual ao `DT_EX_SOCIAL`, acompanhado de J100 (BP) e J150 (DRE).

### 14.2 Registro J100 — Balanço Patrimonial

Nível 3, ocorrência 0:N. Chave: `COD_AGL`.

| \# | Campo | Descrição | Valores |
| :---: | :---- | :---- | :---- |
| 01 | `REG` | "J100" | – |
| 02 | `COD_AGL` | Código de aglutinação (não duplicado) | – |
| 03 | `IND_COD_AGL` | Tipo da linha | T=Totalizador; D=Detalhe |
| 04 | `NIVEL_AGL` | Nível da linha | Só pode haver duas linhas de nível 1: Ativo e Passivo+PL |
| 05 | `COD_AGL_SUP` | Código da linha superior (obrigatório se NIVEL \> 1\) | – |
| 06 | `IND_GRP_BAL` | Grupo | A=Ativo; P=Passivo e PL |
| 07 | `DESCR_COD_AGL` | Descrição da linha | – |
| 08 | `VL_CTA_INI` | Valor inicial | – |
| 09 | `IND_DC_CTA_INI` | D ou C | – |
| 10 | `VL_CTA_FIN` | Valor final | – |
| 11 | `IND_DC_CTA_FIN` | D ou C | – |
| 12 | `NOTA_EXP_REF` | Referência a nota explicativa | – |

Regras estruturais críticas:

- Ativo \= Passivo \+ PL, tanto no saldo inicial quanto no saldo final (REGRA\_VALIDA\_ATIVO\_PASSIVO\_INI/FIN).  
- Valores de linhas "Detalhe" de cada grupo, somados, têm que bater com o grupo totalizador (REGRA\_SOMA\_DAS\_PARCELAS\_BALANCO\_INI/FIN).  
- Valores de linhas "Detalhe" amarram-se com os saldos I155 calculados pelo PGE via códigos de aglutinação (REGRA\_VALIDA\_BALANCO\_SALDO\_INI/FIN).

### 14.3 Registro J150 — Demonstração do Resultado do Exercício (DRE)

Nível 3, ocorrência 0:N. Chave: `COD_AGL` (quando tiver conteúdo). **Este é o registro nuclear do cruzamento DRE × apuração fiscal.**

| \# | Campo | Descrição | Valores |
| :---: | :---- | :---- | :---- |
| 01 | `REG` | "J150" | – |
| 02 | `NU_ORDEM` | Ordem de apresentação da linha | – |
| 03 | `COD_AGL` | Código de aglutinação | – |
| 04 | `IND_COD_AGL` | T=Totalizador; D=Detalhe | – |
| 05 | `NIVEL_AGL` | Nível | Só pode haver uma linha de nível 1 (Resultado do Exercício); totalizadores adicionais a partir do nível 2 |
| 06 | `COD_AGL_SUP` | Linha superior | – |
| 07 | `DESCR_COD_AGL` | Descrição | – |
| 08 | `VL_CTA_INI_` | Saldo final da linha no período imediatamente anterior (DRE anterior, quando houver) | – |
| 09 | `IND_DC_CTA_INI` | D ou C | – |
| 10 | `VL_CTA_FIN` | Valor da linha antes do encerramento do exercício | – |
| 11 | `IND_DC_CTA_FIN` | D ou C | – |
| 12 | `IND_GRP_DRE` | Natureza | D=Despesa (redução do lucro); R=Receita (incremento do lucro) |
| 13 | `NOTA_EXP_REF` | Referência a nota explicativa | – |

Regra essencial (REGRA\_VALIDA\_SALDO\_COM\_DRE): o valor das linhas "Detalhe" do J150, por código de aglutinação, é igual ao saldo calculado pelo PGE a partir do I155 (ou I355) das contas analíticas mapeadas naquele código via I052. Isso garante que a DRE transmitida é efetivamente a totalização dos saldos contábeis do exercício — e é o que permite auditar as linhas da DRE contra a EFD-Contribuições.

### 14.4 Registro J210 — DLPA/DMPL

Demonstração de Lucros ou Prejuízos Acumulados / Demonstração das Mutações do Patrimônio Líquido. Relevante para validação de distribuição de dividendos, ajustes de exercícios anteriores, e reservas. Fora do escopo primário do cruzamento PIS/COFINS, mas útil para teses de distribuição de lucros isentos e para contexto em clientes de Lucro Presumido.

### 14.5 Registro J215 — Fato Contábil que Altera Lucros Acumulados ou PL

Detalhamento específico de eventos que impactam lucros acumulados, prejuízos acumulados ou o patrimônio líquido inteiro.

### 14.6 Registro J800 — Outras Informações

Campo de texto livre onde a PJ pode anexar notas explicativas, parecer de auditores independentes, relatórios da administração e outros documentos complementares. Formato tipicamente RTF ou ementário estruturado. Não é diretamente parseável em dados estruturados, mas pode conter informações fiscais relevantes (menções a processos, provisões para contingências, etc.).

### 14.7 Registro J801 — Termo de Verificação para Fins de Substituição da ECD

Preenchido quando `0000.IND_FIN_ESC = 1` (escrituração substituta), documenta a autorização da substituição.

### 14.8 Registro J900 — Termo de Encerramento

Marcação do encerramento do livro.

### 14.9 Registros J930 e J932 — Signatários

J930: signatários da escrituração (contador, responsável pela PJ). J932: signatários do termo de verificação para substituição. Trazem CPF, nome, qualificação (tabela 5.1.4), endereço e-mail, telefone e código de assinatura do certificado.

### 14.10 Registro J935 — Auditores Independentes

Identificação da empresa de auditoria e do responsável técnico quando a PJ é de grande porte ou tem exigência legal/estatutária de auditoria. Informação importante para segmentação de clientes no sistema Primetax — clientes auditados têm maior confiabilidade dos dados contábeis e costumam ter maior potencial de créditos estruturados.

---

## 15\. Bloco K — conglomerados econômicos

Preenchido quando `0000.IND_ESC_CONS = S`. Contém demonstrações consolidadas nos termos do CPC 36 e dos arts. 247–250 da Lei 6.404/76.

| Registro | Descrição |
| :---: | :---- |
| `K001` | Abertura do Bloco K |
| `K030` | Período da escrituração contábil consolidada |
| `K100` | Relação das empresas consolidadas |
| `K110` | Relação dos eventos societários (aquisições, vendas de participação, etc.) |
| `K115` | Empresas participantes do evento societário |
| `K200` | Plano de contas consolidado |
| `K210` | Mapeamento para planos de contas das empresas consolidadas |
| `K300` | Saldos das contas consolidadas |
| `K310` | Empresas detentoras das parcelas do valor eliminado total |
| `K315` | Empresas contrapartes das parcelas do valor eliminado total |
| `K990` | Encerramento do Bloco K |

**Uso no sistema Primetax:** o Bloco K **não é fonte direta para cruzamento com EFD-Contribuições**, que é sempre por CNPJ individual. Mas é fonte indireta essencial: permite identificar operações intercompany (K310/K315) que possam ter sido classificadas fiscalmente de forma inadequada, e fornece contexto de grupo para diagnósticos comerciais ("seu grupo consolidado vale R$ X; identificamos Y créditos"). Em regra, o parser Primetax pode importar o Bloco K com flag de "informativo" — sem usá-lo em regras de cruzamento diretas.

---

## 16\. Bloco 9 — encerramento

| Registro | Descrição | Obrig |
| :---: | :---- | :---: |
| `9001` | Abertura do Bloco 9 | O |
| `9900` | Registros do Arquivo — um por tipo de registro presente | O |
| `9990` | Encerramento do Bloco 9 | O |
| `9999` | Encerramento do Arquivo Digital | O |

O registro 9900 contém, para cada tipo de registro do arquivo, a quantidade de ocorrências (`QTD_REG_BLC`). Permite ao parser **validar integridade do arquivo** comparando as contagens declaradas com as efetivamente lidas. Divergência \= arquivo corrompido ou truncado, e deve abortar a importação com erro.

---

## 17\. Mapeamento de cruzamentos ECD ↔ EFD-Contribuições ↔ EFD ICMS/IPI

Esta é a seção operacional do documento. Os cruzamentos abaixo alimentam o motor dos 34 cruzamentos descritos no `CLAUDE.md` do projeto.

### 17.1 Chave universal de cruzamento

A chave canônica para qualquer operação ECD × EFD no sistema Primetax é:

```
(cnpj_declarante, ano_mes_competencia, cod_cta)
```

Pré-requisitos para que o join seja válido:

- `cnpj_declarante`: deve ser o CNPJ da mesma PJ (não misturar ECD consolidada com EFD individual).  
- `ano_mes_competencia`: para ECD, derivar do `I150.DT_INI/DT_FIN`; para EFD-Contribuições, derivar do `0000.DT_INI/DT_FIN`.  
- `cod_cta`: deve referenciar contas do **mesmo plano contábil** do período. Se `0000.IND_MUDANC_PC = 1` entre o mês da EFD e o exercício da ECD, aplicar reconciliação via C050/C052.

### 17.2 Cruzamento central: I155 × M200/M600 (receita contábil × base de PIS/COFINS)

**Pergunta fiscal:** a receita bruta declarada como base de PIS/COFINS na EFD-Contribuições corresponde à receita efetivamente escriturada na contabilidade?

**Lógica:**

1. Na ECD, somar todos os `I155.VL_CRED - I155.VL_DEB` (sinal invertido, por serem contas credoras) das contas analíticas de `COD_NAT = 04` cujo código referencial (I051.COD\_CTA\_REF) corresponda a contas de receita do plano referencial aplicável.  
2. Agregar por `(cnpj, ano_mes_competencia)`.  
3. Somar os `M200.VL_REC_BRT_NAO_CUM_TOTAL + VL_REC_BRT_CUM_TOTAL + VL_REC_BRT_NT_MI + VL_REC_BRT_EXP` da EFD-Contribuições do mesmo mês. (Similar via M600 para COFINS.)  
4. Comparar. Divergências materiais (\> 1% em valor absoluto ou \> R$ 10.000 em módulo) são reportadas.

**Interpretação de divergências:**

- ECD \> EFD: receita contabilizada sem oferecimento à tributação. Investigar `IND_GRP_DRE = R` em linhas da DRE que não têm contrapartida na EFD — pode ser receita excluída indevidamente da base, ou receita escriturada em duplicidade na contabilidade.  
- EFD \> ECD: base tributária maior do que receita contábil. Frequentemente indica **desconsideração indevida de deduções/exclusões** na EFD — exatamente o que a Tese 69 busca corrigir. Forte candidato a recuperação.

### 17.3 Cruzamento central: J150 × apuração do período

**Pergunta fiscal:** as linhas da DRE são consistentes com a apuração fiscal do exercício?

**Lógica:** para cada linha "Detalhe" do J150 com `IND_GRP_DRE = R` (receita), agregar o valor anual da linha e compará-lo com a soma mensal, no mesmo exercício, do `M210.VL_REC_BRT` (PIS) e `M610.VL_REC_BRT` (COFINS) na EFD-Contribuições.

Adicionalmente, linhas de J150 com descrição/código de aglutinação compatível com "Receita Financeira", "Receita de Aluguel", "Ganho de Capital na Venda de Imobilizado" são **exclusões naturais** da receita bruta não-cumulativa — e não devem aparecer em M210/M610 como base de cálculo. Se aparecerem, há erro de classificação da EFD.

### 17.4 COD\_CTA como ponte em cruzamentos de crédito

Para cada registro fiscal que aceita `COD_CTA`:

- `C170.COD_CTA` (EFD-Contribuições e EFD ICMS/IPI, campo 37\)  
- `C175.COD_CTA` (EFD-Contribuições)  
- `F100.COD_CTA`, `F120.COD_CTA`, `F130.COD_CTA` (EFD-Contribuições — demais documentos, ativo imobilizado)  
- `M105.COD_CTA` (EFD-Contribuições — créditos de PIS consolidados por conta, a partir de 11/2017)  
- `M505.COD_CTA` (EFD-Contribuições — créditos de COFINS consolidados por conta, a partir de 11/2017)

O join direto com o `I050` da ECD (via `COD_CTA`) permite:

1. **Validar a existência da conta** referenciada no fiscal (erro comum: conta digitada errada, conta já não existe no plano atual).  
2. **Obter a natureza contábil** real da conta (`COD_NAT`, `CTA`) — auditando coerência semântica (ex: crédito de PIS sobre imobilizado em F130 deveria referenciar conta de imobilizado com `COD_NAT = 01`, não conta de resultado).  
3. **Classificar créditos por conta** — identificar concentração em contas específicas que possam estar subexploradas em outros períodos.

### 17.5 Lançamentos extemporâneos (I200.IND\_LCTO \= "X") × operações extemporâneas da EFD (1101/1501)

**Pergunta fiscal:** há simetria entre lançamentos contábeis extemporâneos na ECD e registros de apuração extemporânea na EFD-Contribuições?

**Lógica:** para cada I200 com `IND_LCTO = X`:

1. Capturar `DT_LCTO_EXT` (data do fato original, que pode ser de exercício anterior) e as contas do I250.  
2. Se as contas envolvidas referenciam PIS/COFINS a recuperar ou contrapartida de receita de créditos:  
   - **Cenário A** (há 1101/1501 na EFD-Contribuições da competência atual referenciando a mesma data): lançamento reconhecido; verificar valores.  
   - **Cenário B** (não há 1101/1501 nem retificação da EFD do período `DT_LCTO_EXT`): **crédito reconhecido contabilmente mas não fiscalmente** — inconsistência grave e oportunidade de regularização via retificação.  
3. Se as contas envolvidas referenciam despesa com contrapartida de PIS/COFINS a recuperar que antes não existia: forte candidato a crédito não aproveitado.

### 17.6 Cruzamentos adicionais sobre o universo dos 34

Além dos cruzamentos que têm a ECD como fonte direta (tipicamente os que envolvem COD\_CTA), estes ficam registrados para incorporação futura:

1. **C040/C050 (ECD recuperada) × I050 atual** — detecta mudanças de plano de contas que invalidam cruzamentos plurianuais.  
2. **J930 (signatários) × histórico de procurações e-CAC** — valida que o contador responsável pela ECD é o mesmo que assina as EFDs (inconsistência \= risco de erro recorrente).  
3. **Bloco K (K100/K300) × grupo econômico no cadastro Primetax** — identifica oportunidades cross-company para clientes que são parte de grupos.  
4. **I053 (subcontas correlatas / RAS) × ajustes na ECF parte B** — rastreia ajustes de valor justo que podem ter implicação em base PIS/COFINS.

---

## 18\. Tese 69 na camada contábil

A Tese 69 (RE 574.706 / Tema 69 — exclusão do ICMS destacado na nota da base de cálculo do PIS/COFINS) tem reflexo direto na ECD via:

### 18.1 Onde o ICMS a recuperar aparece no I155

Contas típicas (plano da PJ, mapeadas para o plano referencial):

- **"ICMS a Recuperar"** (grupo ativo circulante): crédito mensal quando há exclusão aplicada na EFD-Contribuições retroativa; débito mensal quando se compensa.  
- **"PIS a Recuperar" / "COFINS a Recuperar"**: contrapartida credora do reconhecimento do direito creditório quando a tese é operacionalizada.  
- **"Receita de Recuperação de Tributos"** ou **"Outras Receitas Operacionais — Tese 69"**: reconhecimento na DRE.

### 18.2 O que o cruzamento ECD × EFD-Contribuições deve verificar

Para clientes que **já aplicam a Tese 69**:

1. A conta "ICMS a Recuperar" no I155 deve ter movimentação consistente com os valores excluídos da base em `C170`/`C181`/`C185` da EFD-Contribuições (via `VL_ICMS` e recálculo de `VL_BC_PIS`).  
2. Deve haver linha correspondente no J150 de reconhecimento da receita (quando a tese é aplicada retroativamente via crédito financeiro).

Para clientes que **ainda não aplicam**:

1. A ausência de movimentação nessas contas no I155, combinada com `VL_BC_PIS = VL_ITEM` em C170 (sem exclusão do ICMS), é **evidência direta de crédito não aproveitado** — alvo primário de diagnóstico Primetax.

### 18.3 Código referencial da RFB aplicável

No plano referencial 1 (Lucro Real) e 2 (Lucro Presumido), as contas de "Impostos a Recuperar" e "Recuperação de Tributos" estão mapeadas em grupos específicos que o I051 liga automaticamente — facilitando a identificação independentemente do nome dado pela PJ no seu plano interno. O parser deve priorizar busca pelo `COD_CTA_REF` nessas hipóteses, não pelo nome da conta analítica.

---

## 19\. Divisores de águas e versionamento do leiaute

A ECD teve várias versões de leiaute. Para o sistema Primetax, os divisores relevantes são:

- **Leiaute 9 (v9.00) — vigente desde o ano-calendário 2020:** introduziu o lançamento extemporâneo `IND_LCTO = X` (atendendo ITG 2000 R1), consolidou o suporte à moeda funcional via campos adicionais I020, ajustou regras de validação do plano de contas (mínimo 4 níveis com CTG 2001 R3). Este é o leiaute **primariamente suportado** pelo parser Primetax.  
- **Leiautes 8 e anteriores — até o ano-calendário 2019:** não tinham `IND_LCTO = X`; o parser deve aceitar apenas valores `N` e `E` para esses períodos.  
- **Moeda funcional** — o regime de moeda funcional existe desde 2017 (IN RFB 1.700/2017, art. 287), mas a operacionalização nos campos adicionais do I020 ganhou estabilidade nas versões do Leiaute 7 em diante.  
- **Lançamentos de 4ª fórmula** — permitidos desde o CTG 2001 R2 (2014); antes disso, eram rejeitados. O parser pode assumir que todos os arquivos em escopo atual Primetax aceitam 4ª fórmula.  
- **Plano de contas com 4 níveis mínimos** — regra CTG 2001 R3, vigente desde 2017\. Em arquivos anteriores, podem existir contas analíticas em nível 3 — exigência menos rigorosa do PGE.

### 19.1 Recomendação de versão do parser

O parser deve:

- Ler o campo `I010.COD_VER_LC` e registrá-lo em cada linha importada.  
- Ter tabela de compatibilidade que mapeie valores aceitos de `IND_LCTO` por versão.  
- Nunca rejeitar silenciosamente campos adicionais desconhecidos do I020 — registrar aviso e continuar.

---

## 20\. Referências normativas

- **Decreto nº 6.022/2007** — instituição do SPED  
- **Lei nº 6.404/1976** — Lei das S.A., estrutura patrimonial (arts. 177–182) e demonstrações consolidadas (arts. 247–250)  
- **Lei nº 11.638/2007** — conceito de entidade de grande porte (art. 3º)  
- **Lei nº 12.973/2014** — conceito de receita bruta (art. 12 do DL 1.598/1977)  
- **Instrução Normativa RFB nº 2.003/2021** e alterações — obrigação de entrega da ECD  
- **Instrução Normativa RFB nº 1.700/2017** — moeda funcional (art. 287\) e RAS (arts. 295 e seguintes)  
- **Instrução Normativa RFB nº 2.119/2022** — anexos para SCP  
- **Ato Declaratório Executivo Cofis nº 01/2026** — aprovação do Manual de Orientação do Leiaute 9 (janeiro/2026)  
- **CTG 2001 (R3) do CFC** — formalidades da escrituração contábil em forma digital  
- **ITG 2000 (R1) do CFC** — escrituração contábil (itens 31–36 sobre lançamentos extemporâneos)  
- **CPC 36** — demonstrações consolidadas (base do Bloco K)  
- **RE 574.706/PR (Tema 69\)** — exclusão do ICMS da base do PIS/COFINS  
- **Parecer SEI nº 7698/2021/ME** — operacionalização da Tese 69 pela PGFN  
- **REsp 1.221.170/PR (Tema 779\)** — conceito de insumo para PIS/COFINS não-cumulativos

---

## 21\. Recomendação operacional para o parser

### 21.1 Escopo mínimo de parsing da ECD

Dos 45 tipos de registro do Leiaute 9, o parser Primetax pode operar na primeira iteração com **16 registros críticos**:

- **Bloco 0:** 0000, 0150 (quando houver referência a participantes)  
- **Bloco C:** C050, C150, C155, C650 (para reconciliação entre exercícios quando há mudança de plano)  
- **Bloco I:** I010, I050, I051, I052, I150, I155, I200, I250 (quando há necessidade de reconstituir lançamento), I355  
- **Bloco J:** J005, J100, J150  
- **Bloco 9:** 9900 (para integridade)

Registros não prioritários na primeira iteração: 0007, 0020, 0035, 0180, I012, I015, I020, I030, I053, I075, I100, I157, I300, I310, I500–I555, J210, J215, J800, J801, J900, J930, J932, J935, K001–K990, 9001/9990/9999 (todos os de controle).

### 21.2 Regra de resiliência de versão

O parser deve:

- Ler o campo `I010.COD_VER_LC` e registrá-lo em cada linha importada.  
- Ter tabela de compatibilidade que mapeie campos renomeados/adicionados entre versões 7, 8 e 9\.  
- Detectar `0000.IDENT_MF = S` e automaticamente ler os campos `_MF` adicionais do I020.  
- Nunca rejeitar silenciosamente registros desconhecidos — registrar aviso e continuar.

### 21.3 Separação física dos schemas

Recomenda-se manter os schemas de banco da ECD (`ecd_*`) fisicamente separados dos da EFD-Contribuições (`efd_contribuicoes_*`) e da EFD ICMS/IPI (`efd_icms_*`), com os cruzamentos sendo feitos via joins controlados no motor. Isso permite:

- Importação independente de cada arquivo  
- Rastreabilidade fiscal preservada (coluna `arquivo_origem` no nível da tabela)  
- Testabilidade de cada parser isoladamente  
- Evolução independente dos schemas conforme mudanças de leiaute

### 21.4 Campos obrigatórios de rastreabilidade

Conforme seção 4 do `CLAUDE.md` (princípios não-negociáveis), toda linha importada de qualquer registro da ECD deve trazer obrigatoriamente:

- `arquivo_origem` — caminho ou hash do arquivo SPED de origem  
- `linha_arquivo` — número da linha física no arquivo original  
- `bloco` — identificação do bloco (0, C, I, J, K, 9\)  
- `registro` — identificação do tipo de registro (0000, I050, I155, etc.)  
- `cnpj_declarante` — CNPJ do campo 06 do registro 0000  
- `dt_ini_periodo`, `dt_fin_periodo` — datas do registro 0000  
- `ind_fin_esc` — 0=Original ou 1=Substituta  
- `cod_ver_lc` — versão do leiaute declarada (I010.COD\_VER\_LC)  
- `ident_mf` — indicador de moeda funcional  
- `tip_ecd` — tipo da ECD (0=PJ normal, 1=sócio ostensivo, 2=SCP)  
- `cod_plan_ref` — código do plano referencial (pode ser vazio)

Sempre que o registro traz `COD_CTA` (I155, I200, I250, I310, I355), o parser deve capturar e indexar este campo. Sempre que traz `COD_AGL` (J100, J150), idem.

Nenhuma linha de cruzamento ECD × EFD deve ser gerada sem que todas essas informações possam ser recuperadas do banco — a rastreabilidade fiscal é o diferencial técnico do sistema Primetax e sua ausência invalida o valor auditorial do output.

### 21.5 Indexação para performance

Considerando que um exercício de PJ de médio porte pode ter dezenas de milhares de registros I250 (partidas de lançamento), a indexação do banco é crítica:

- `I050`: índice único em `(cnpj, cod_cta)`  
- `I155`: índice composto em `(cnpj, ano_mes_competencia, cod_cta)` — **o mais importante**  
- `I200`: índice em `(cnpj, dt_lcto, num_lcto)` e em `(cnpj, ind_lcto)` para filtrar extemporâneos  
- `I250`: índice em `(cnpj, num_lcto)` e em `(cnpj, cod_cta)`  
- `J100`/`J150`: índice em `(cnpj, dt_fin, cod_agl)`

Com essa indexação, os cruzamentos ECD × EFD centrais (seções 17.2 e 17.3) rodam em tempo sub-segundo mesmo para cliente grande.

---

*Fim do guia de importação e referência da ECD — Leiaute 9 (janeiro/2026).*  
