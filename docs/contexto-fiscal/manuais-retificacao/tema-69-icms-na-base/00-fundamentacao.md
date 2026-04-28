---
bloco_id: tese69-fundamentacao
tipo: fundamentacao
regras: [CR-07, CR-08, CR-09, CR-26]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "RE 574.706/PR (STF, Repercussão Geral, Tema 69)"
  - "Acórdão de embargos declaratórios do RE 574.706 (julgado em 13/05/2021)"
  - "Lei nº 10.637/2002, art. 1º, § 3º, V"
  - "Lei nº 10.833/2003, art. 1º, § 3º, V"
  - "Parecer SEI nº 7698/2021/ME (PGFN — operacionalização)"
  - "IN RFB nº 2.121/2022, art. 26"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-modulacao-modulacao-geral
  - bloco_id: tese69-modulacao-acao-anterior
  - bloco_id: tese69-quantificacao
---

# Tese 69 — Exclusão do ICMS da base de cálculo de PIS/COFINS

## Síntese

O Supremo Tribunal Federal, ao julgar o RE 574.706/PR sob o regime de Repercussão Geral (Tema 69), fixou a tese de que **o ICMS destacado em nota fiscal não compõe a base de cálculo do PIS e da COFINS**. A decisão é vinculante para toda a Administração Pública e jurisprudencialmente consolidada.

Para a Primetax, a Tese 69 é o cruzamento de maior valor financeiro recorrente: empresas tributadas pelo regime não-cumulativo de PIS/COFINS que mantiveram, em períodos não prescritos, o ICMS destacado na base de cálculo das contribuições têm direito a recuperar a diferença — via compensação administrativa (PER/DCOMP) ou restituição. O ticket médio em clientes industriais e comerciais varia de 3% a 7% da receita bruta do período recuperável.

## Fundamentação jurídica

A tese central do STF é que o ICMS, embora circule pela contabilidade do contribuinte como receita aparente (por ser parte do preço cobrado do consumidor final), **não constitui receita própria** do contribuinte: ele é mero arrecadador para o Estado. Tributo que transita pela contabilidade não é receita; e o que não é receita não pode integrar a base de cálculo de PIS/COFINS, cuja hipótese de incidência é a receita bruta auferida pela pessoa jurídica (Lei 10.637/2002, art. 1º; Lei 10.833/2003, art. 1º).

A operacionalização da tese passou por modulação no acórdão de embargos declaratórios julgado em 13/05/2021. A modulação fixou que **o efeito da exclusão do ICMS retroage a 15/03/2017** — data do julgamento original do RE 574.706 — para contribuintes que **não ajuizaram ação** sobre o tema. Para contribuintes que ajuizaram ação **antes de 15/03/2017** e cuja decisão judicial transitou em julgado, o efeito retroage à data do ajuizamento da ação (limitada ao prazo prescricional quinquenal contado da propositura).

Essa modulação tem duas consequências práticas que estruturam todo o trabalho da Primetax:

Primeiro, há **dois regimes temporais** distintos a operacionalizar. Cliente "modulação geral" (sem ação anterior) recupera ICMS destacado a partir de 15/03/2017. Cliente "ação anterior" (com ação ajuizada antes daquela data e trânsito em julgado) recupera desde a data do ajuizamento.

Segundo, há **dois caminhos processuais** distintos para formalizar a recuperação. Modulação geral usa diretamente a via administrativa (PER/DCOMP no e-CAC), com fundamento na decisão vinculante do STF. Ação anterior exige carrear ao processo o trânsito em julgado da ação judicial — geralmente formalizado em PER/DCOMP com fundamento na sentença, e em alguns casos demandando habilitação prévia do crédito.

## Operacionalização contábil-fiscal

O erro que cria a oportunidade é **manter o ICMS destacado dentro do valor da base de cálculo do PIS/COFINS** nos registros analíticos da EFD-Contribuições. Concretamente, o erro aparece em:

- **Registro C170** (itens de notas fiscais modelo 01, 1B, 04, 55) — o campo `VL_BC_PIS` deveria ser `VL_ITEM - VL_DESC - VL_ICMS` quando o item é tributado em CST de débito (01, 02, 03, 05); na escrituração errada, vem como `VL_ITEM - VL_DESC` apenas.
- **Registro C181** (itens de NFC-e modelo 65, consolidação por CFOP/CST) — análogo, mas em forma agregada.
- **Registro C185** (idem para COFINS, NFC-e).
- **Registros D100/D200** (serviços de transporte e comunicação) — análogo nos campos correspondentes.
- **Registros M210/M610** — apuração consolidada do PIS/COFINS no período. Como a base do M210 deriva do somatório dos C170 (e correlatos), o erro propaga automaticamente para a apuração.

A retificação corrige a base nos registros analíticos e, por consequência, recalcula a apuração consolidada — com redução do imposto devido no período retificado, gerando direito creditório.

## Magnitude esperada do crédito

Em clientes industriais e comerciais com regime não-cumulativo e operações majoritariamente tributadas, o crédito recuperável tipicamente fica entre **3% e 7% da receita bruta do período não prescrito**. Em clientes com forte presença de operações isentas ou monofásicas, o percentual é menor (porque parte do ICMS recai sobre receitas que não compõem a base de PIS/COFINS de qualquer forma).

A Primetax mantém como benchmark interno o caso **NORTE GERADORES** (período 2021-2022): R$ 4,79 milhões em PIS/COFINS recuperáveis sobre R$ 51,86 milhões de base, dos quais aproximadamente 65% atribuíveis isoladamente à Tese 69. O motor de cruzamentos do Sprint 1 (CR-07) deve replicar esse achado quando rodado sobre os SPEDs daquele cliente.

A decisão de pleitear a recuperação considera, além do valor do crédito, o **prazo prescricional quinquenal** (contado da entrega da escrituração ou do recolhimento, conforme o caso) e a **disponibilidade de débitos a compensar** no horizonte de 12-24 meses subsequente. Crédito sem horizonte de compensação útil é restituição em dinheiro — caminho mais lento e com maior atrito administrativo.
