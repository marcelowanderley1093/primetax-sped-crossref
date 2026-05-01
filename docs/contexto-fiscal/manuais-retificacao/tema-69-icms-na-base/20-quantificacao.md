---
bloco_id: tese69-quantificacao
tipo: fundamentacao
regras: [CR-07, CR-08, CR-09, CR-26]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 10.637/2002, art. 1º, § 3º, V; art. 2º"
  - "Lei nº 10.833/2003, art. 1º, § 3º, V; art. 2º"
  - "Solução de Consulta COSIT nº 13/2018 (revogada, mantida como referência histórica)"
  - "Parecer SEI nº 7698/2021/ME"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-fundamentacao
  - bloco_id: tese69-retificacao-sped
---

# Quantificação do crédito da Tese 69

## Fórmula geral

Para cada item de C170 (e correlatos) com CST de débito (01, 02, 03, 05) e ICMS destacado em valor positivo:

```
Base correta de PIS/COFINS = VL_ITEM - VL_DESC - VL_ICMS
PIS recuperável (item)     = (VL_ICMS) × ALIQ_PIS / 100
COFINS recuperável (item)  = (VL_ICMS) × ALIQ_COFINS / 100
```

A fórmula equivale a calcular o que seria a contribuição sobre o valor do ICMS isoladamente — esse é o valor recuperável por item. Na maioria dos clientes não-cumulativos com alíquotas básicas, isso significa **9,25% do ICMS destacado** (1,65% PIS + 7,60% COFINS) por item retificado.

## Quantificação no nível da apuração mensal

A soma de todos os valores recuperáveis por item, agrupados por competência, dá o **crédito apurado no mês**. Esse crédito mensal:

1. **Reduz o débito apurado em M210/M610** quando há débito no período. Efeito: redução do imposto a recolher (se a competência ainda não foi recolhida) ou geração de saldo a recuperar (se já foi recolhida).
2. **Compõe saldo credor** em 1100/1500 quando o débito do período não absorve toda a redução. Esse saldo segue para a competência seguinte e pode ser usado em compensação futura.

A retificação é, portanto, um exercício de **recalcular a apuração inteira do período** com a base reduzida — não basta calcular o "valor recuperável" sem propagar para os totalizadores.

## Tratamento de operações isentas e monofásicas

Itens com CST de PIS/COFINS fora do conjunto {01, 02, 03, 05} **não geram recuperação pela Tese 69**, ainda que tenham ICMS destacado. Quatro situações típicas para cuidado:

- **CST 04 (revenda de monofásico)** — a receita não compõe a base de PIS/COFINS do revendedor (alíquota zero por substituição), portanto não há base para reduzir.
- **CST 06, 07, 08, 09 (alíquota zero, isenção, suspensão, sem incidência)** — análogo.
- **CST 10 (suspensão de incidência)** — a base existe formalmente mas o tributo não foi devido; sem tributo devido não há recuperação.
- **CST 49 (outras operações de saída)** — depende da semântica da operação no caso concreto; auditoria individual.

Em cliente com mix de operações, é comum que apenas 60-80% dos itens com ICMS destacado sejam efetivamente recuperáveis. O motor de cruzamentos (CR-07) aplica essa filtragem automaticamente; cálculo manual deve seguir mesma lógica para evitar superestimação do potencial.

## Atualização monetária e juros

O crédito recuperável é atualizado pela **taxa SELIC acumulada** desde o mês seguinte ao do recolhimento indevido até o mês da efetiva compensação ou restituição (Lei 9.430/1996, art. 39, § 4º). Em horizontes recuperáveis longos — sobretudo no cenário 2 (ação anterior) — a atualização pode dobrar ou triplicar o valor nominal do crédito.

A SELIC aplicada é a **acumulada do período**, não a SELIC mensal multiplicada por número de meses. Erros aritméticos nessa atualização são causa frequente de glosa parcial — o auditor da RFB recalcula com a SELIC oficial e ajusta o valor habilitado se houver divergência. A Primetax mantém em `src/tables/selic_acumulada.py` a tabela mensal oficial atualizada para evitar esse erro.

## Quantificação da Norte Geradores como benchmark

O caso NORTE GERADORES (período 2021-2022, R$ 51,86 milhões de base bruta no período) gerou aproximadamente **R$ 3,1 milhões em PIS/COFINS recuperáveis pela Tese 69 isoladamente** (65% do total de R$ 4,79 milhões identificados). O percentual sobre receita bruta foi de aproximadamente 6%, dentro do intervalo típico esperado para clientes industriais com operações majoritariamente tributadas.

Após atualização SELIC (estimando recolhimento mensal e compensação em 2026), o valor atualizado fica em torno de R$ 4,1 milhões — representando um adicional de 32% sobre o valor nominal. Essa magnitude reforça por que o cálculo correto da SELIC é elemento crítico do trabalho.
