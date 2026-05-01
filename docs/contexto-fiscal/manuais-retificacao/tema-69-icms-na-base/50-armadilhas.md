---
bloco_id: tese69-armadilha-cenario2-sem-habilitacao
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: true
vigencia_inicio: "2021-05-13"
vigencia_fim: null
fundamentacao_legal:
  - "IN RFB nº 2.055/2021, art. 100 e seguintes"
  - "Parecer SEI nº 7698/2021/ME"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-modulacao-acao-anterior
  - bloco_id: tese69-per-dcomp
---

# Armadilha 1 — Cenário 2 sem habilitação prévia do crédito

## Descrição do erro

Cliente tem ação judicial pré-modulação transitada em julgado favorável. O auditor, vendo que a tese é a mesma do RE 574.706 (vinculante), assume que pode pular a habilitação prévia e transmitir PER/DCOMP direto, com fundamento na decisão vinculante do STF — caminho válido para o cenário 1 (modulação geral).

## Consequência

Glosa imediata por "ausência de habilitação do crédito decorrente de ação judicial". A RFB **não aceita** que sentença individual transitada em julgado seja aplicada diretamente em PER/DCOMP, ainda que a sentença replique a decisão vinculante. A IN RFB 2.055/2021 estabelece que crédito originado em ação judicial **exige habilitação prévia** — é requisito formal autônomo, não suprível pela vinculação ao Tema 69.

A glosa pode ser parcial (apenas a parcela da sentença que excede o cenário modulação geral é glosada) ou total (toda a compensação é desfeita), dependendo de como o cliente fundamentou o pleito. Em ambos os casos, há exigência de pagamento de débito que se considerou compensado, com multa e juros desde a data da compensação indevida.

## Como evitar

**Antes de qualquer PER/DCOMP no cenário 2**, executar o Passo 1 do bloco `tese69-per-dcomp`: habilitação prévia do crédito no e-CAC, anexando trânsito em julgado e sentença/acórdão. A RFB tem 30 dias para validar e gera número de habilitação que será referenciado no PER/DCOMP subsequente.

Sinal claro de que o cliente está no cenário 2: existe número de processo judicial sobre o tema com data de ajuizamento anterior a 15/03/2017. Se há essa informação, **sempre** habilitar antes — mesmo quando a tese coincide com a vinculante. A regra prática Primetax: "no cenário 2, habilitação primeiro, sempre".

## Como corrigir se já cometido

Após a glosa, há dois caminhos:

1. **Manifestação de Inconformidade** dentro de 30 dias contados da ciência, alegando que a sentença replica decisão vinculante e portanto não exigia habilitação. Caminho de baixa probabilidade de sucesso administrativamente — a RFB tem entendimento consolidado no sentido contrário. Pode chegar até CARF (3ª instância) com chance moderada, mas com prazo total de 5-7 anos.

2. **Aceitar a glosa**, pagar o débito reconstituído (com multa de 75% e juros), e refazer o pleito **com habilitação prévia regular**. Caminho mais rápido (12-18 meses) e com alta probabilidade de sucesso, mas com perda financeira pela multa.

A escolha entre os dois caminhos é decisão comercial-estratégica que envolve avaliar o valor do crédito remanescente, o apetite por contencioso do cliente, e o custo de oportunidade. Em geral, para créditos < R$ 500 mil, refazer regular é melhor; para créditos maiores, vale tentar a manifestação.

---

---
bloco_id: tese69-armadilha-1010-ausente
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Guia Prático EFD-Contribuições versão 1.35, Bloco 1"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-modulacao-acao-anterior
  - bloco_id: tese69-retificacao-sped
---

# Armadilha 2 — Registro 1010 ausente em retificadora de cliente cenário 2

## Descrição do erro

Auditor retifica EFD-Contribuições para cliente cenário 2 (ação judicial pré-modulação) ajustando a base de cálculo nos C170 corretamente, mas **esquece de incluir o registro 1010** referenciando o processo judicial que ampara a retificação. A retificadora é tecnicamente válida (passa pelo PVA), mas fica sem ancoragem jurídica explícita.

## Consequência

Em fiscalização posterior, o auditor da RFB ao consultar a EFD-Contribuições retificadora vê base reduzida sem motivo aparente — não há indicação no arquivo de que a redução decorre de decisão judicial transitada em julgado. Isso gera **fragilidade probatória crítica**: a fiscalização tipicamente abre intimação solicitando esclarecimento sobre a redução, e a empresa precisa carrear a documentação processual em separado (sentença, trânsito em julgado, habilitação) para sustentar a retificação.

Casos extremos: a fiscalização interpreta a redução como sub-faturamento ou erro de declaração, e lavra auto de infração antes mesmo de pedir esclarecimento. O auto é cancelado depois quando a documentação processual é apresentada, mas o processo administrativo já foi iniciado e exige defesa formal — custo de tempo e atenção que era evitável.

A consequência indireta mais grave: ausência do 1010 sinaliza descuido na retificação como um todo, e tende a desencadear fiscalização aprofundada de **todo o período retificado**, inclusive em outras teses — exposição que poderia ter sido evitada com correto preenchimento.

## Como evitar

Para todo cliente cenário 2, no **Passo 8 do bloco `tese69-retificacao-sped`**, preencher o registro 1010 com:

- `IND_NAT_ACAO` = "01" (ação judicial transitada em julgado favorável).
- `NUM_PROC` = número completo do processo, sem máscaras.
- `IND_PROC` = "1" (Justiça Federal) ou "2" (Justiça Estadual).
- `VARA` = identificação da vara.
- `DT_DEC` = data do trânsito em julgado.

Validar no PVA: o validador da RFB verifica se há coerência entre 1010 e os ajustes de base nos M210/M610 quando o `IND_NAT_ACAO` é de exigibilidade suspensa.

## Como corrigir se já cometido

Se a retificadora já foi transmitida sem o 1010, **nova retificação** da retificadora é o caminho. Não há custo formal nem multa — apenas o trabalho de regerar o arquivo, agora com 1010 incluído, e transmitir. A nova retificação **substitui integralmente** a anterior; o histórico fica registrado mas a referência efetiva passa a ser a última versão.

Se já houve fiscalização parcial sobre o período sem o 1010, vale primeiro responder à intimação carreando a documentação processual, e só depois retificar a retificadora — para não dar impressão de manipulação reativa do arquivo. Auditoria conservadora.

---

---
bloco_id: tese69-armadilha-selic-erro-aritmetico
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 9.430/1996, art. 39, § 4º"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
---

# Armadilha 3 — Cálculo errado da SELIC acumulada

## Descrição do erro

Auditor calcula a atualização do crédito multiplicando a SELIC mensal média (ex.: 0,8%) pelo número de meses (ex.: 36 meses) para chegar à atualização total (28,8%). Erro aritmético clássico: SELIC é **acumulada**, não somada.

A fórmula correta é multiplicativa: o fator de atualização do mês X até o mês Y é o produtório de (1 + SELIC_mensal_i) para i de X a Y, que difere significativamente da soma simples das taxas — ainda mais em horizontes longos.

## Consequência

PER/DCOMP transmitido com valor atualizado superior ao correto. A RFB recalcula com SELIC oficial (Lei 9.430/1996, art. 39, § 4º) e ajusta o valor habilitado para baixo. **Glosa parcial** automática.

Em DCOMPs, isso pode gerar problema adicional: como a compensação foi feita pelo valor maior, a RFB recalcula o crédito disponível pela SELIC correta, encontra crédito menor do que o usado, e os débitos compensados com a parcela "excedente" voltam a ser exigíveis — com multa de mora e juros a partir do vencimento original.

Em PERs, o efeito é apenas restituição menor do que pleiteada — sem multa, mas com perda financeira proporcional ao erro.

## Como evitar

Usar a tabela oficial da SELIC acumulada por mês inicial (em `src/tables/selic_acumulada.py`, atualizada mensalmente pela Primetax conforme divulgação da RFB). Para crédito originado em recolhimento de competência X, o fator de atualização até o mês de transmissão Y é exatamente o valor da tabela na linha X, coluna Y.

Nunca calcular SELIC manualmente em planilhas com fórmula simplificada. Erros de SELIC são frequentemente apontados pela RFB e geram retrabalho desnecessário.

## Como corrigir se já cometido

Se o erro foi detectado **antes da glosa**, retransmitir o PER/DCOMP com o valor corrigido o quanto antes — substitui o anterior automaticamente.

Se a glosa já ocorreu, aceitar o valor recalculado pela RFB (geralmente correto, podendo ser conferido) e seguir com o ajuste. Em DCOMPs, regularizar imediatamente os débitos que voltaram a ser exigíveis para minimizar multa de mora — pagar via DARF dentro de 30 dias evita autuação por compensação indevida.

---

---
bloco_id: tese69-armadilha-ordem-cronologica
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Guia Prático EFD-Contribuições versão 1.35, Bloco 1100/1500"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-retificacao-sped
---

# Armadilha 4 — Retificar competências fora de ordem cronológica

## Descrição do erro

Auditor com pressa, ou trabalhando por lotes lógicos (ex.: "primeiro retifico tudo de 2022, depois 2021, depois 2020"), transmite retificadoras fora de ordem cronológica ascendente. Tecnicamente cada arquivo individual é válido, mas **a sequência de saldos credor entre competências fica quebrada**.

## Consequência

O campo `1100.VL_SLD_CRED_INI` (saldo credor inicial) de uma competência deve ser igual ao `VL_SLD_CRED_FIM` da competência imediatamente anterior. Quando se retifica fora de ordem, a competência X (mais antiga) é alterada **depois** da competência X+1, mas o `VL_SLD_CRED_INI` de X+1 já foi gravado com o valor antigo de X. Resultado: divergência detectável no PVA da próxima retificação que envolva X+1, ou na fiscalização posterior.

Em casos graves, a sequência de saldos pode ficar **logicamente inconsistente** ao longo de múltiplas competências — o saldo credor "some" entre dois meses ou aparece sem origem identificável. Isso é imediatamente visível em conferência cruzada com DCTF/DCTFWeb e gera intimação fiscal automática.

## Como evitar

Seguir o **Passo 1 do bloco `tese69-retificacao-sped`**: ordenar as competências candidatas em ordem ascendente; processar uma de cada vez; só passar para a seguinte após validar o PVA da anterior.

O sistema Primetax, na sua versão completa, deve impor essa ordem programaticamente — `primetax-sped retificar` (comando futuro da Etapa 4) recusará processar competência cuja anterior ainda não foi retificada quando há saldo credor relevante.

## Como corrigir se já cometido

Identificar todas as competências afetadas pela quebra de continuidade. Retransmitir retificadoras em **ordem cronológica ascendente** a partir da primeira competência onde a inconsistência aparece. Cada nova retificação ajusta o saldo credor inicial pelo valor correto do mês anterior.

Em casos com muitas competências afetadas, pode ser necessário um **trabalho de mais de uma rodada de retificação** — porque a primeira retificação ajusta os saldos mas pode revelar pequenos erros que demandam revisão. Auditoria detalhada antes de transmitir cada nova versão.

---

---
bloco_id: tese69-armadilha-cst-fora-do-conjunto
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "RE 574.706/PR (escopo da tese: receita tributada)"
  - "Tabelas RFB de CST PIS/COFINS"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
---

# Armadilha 5 — Aplicar a tese a CSTs fora do conjunto {01, 02, 03, 05}

## Descrição do erro

Auditor, vendo ICMS destacado em itens de C170, aplica a exclusão indistintamente — incluindo itens com CST 04 (revenda de monofásico), CST 06 (alíquota zero), CST 07 (isenção), CST 08 (suspensão) ou CST 49 (outras saídas). Tecnicamente o C170 aceita a alteração; semanticamente não há base para a recuperação porque **nesses itens não há receita tributada de PIS/COFINS sobre a qual se exclua o ICMS**.

## Consequência

Glosa do valor relativo aos itens fora do conjunto correto. Em fiscalização aprofundada, a RFB conferirá a coerência CST × redução de base e identificará os itens incorretos. O valor glosado é restituído ao débito original, com multa e juros.

Em casos de retificação extensa onde grande parte dos itens estavam fora do conjunto, a glosa pode ser **majoritária** — comprometendo o ROI do trabalho. Acontece especialmente em clientes do varejo com alto volume de CST 04 (revenda monofásica de combustíveis, bebidas frias, autopeças).

A consequência reputacional é mais grave que a financeira: glosa de natureza claramente conceitual (não erro aritmético) sinaliza que a Primetax não conhece os limites da tese — afeta credibilidade da consultoria perante o cliente e a RFB.

## Como evitar

Aplicar a exclusão apenas a itens onde **simultaneamente**:
- `CST_PIS` ∈ {01, 02, 03, 05}; e
- `CST_COFINS` ∈ {01, 02, 03, 05}; e
- `VL_ICMS` > 0.

A condição é exatamente a especificada na `operacao_estruturada` do bloco `tese69-retificacao-sped`. O motor de cruzamentos (CR-07) aplica essa filtragem automaticamente; o auditor que retifica manualmente ou em planilha precisa replicar a mesma lógica.

Validação cruzada útil: se o "valor recuperável da Tese 69" calculado é maior que aproximadamente 9% da soma de bases tributadas pelo regime básico (PIS 1,65% + COFINS 7,60% = 9,25%), há suspeita de aplicação a CST inadequada — a tese teoricamente não pode recuperar mais do que 9,25% da base tributada porque é exatamente esse o tributo incidente sobre a parcela do ICMS.

## Como corrigir se já cometido

Identificar os itens com CST fora do conjunto na retificadora transmitida. Refazer a retificadora **revertendo a alteração** desses itens (voltando ao valor original do C170 nesses casos), recalcular C190/M210/M610/M200/M600/1100/1500, transmitir nova retificadora.

Se PER/DCOMP já foi transmitido com o valor inflado, retransmitir com valor corrigido — o sistema substitui o anterior. Em DCOMPs já compensados, regularizar a parcela excedente como débito para evitar autuação.

---

---
bloco_id: tese69-armadilha-esquecer-recalcular-totalizadores
tipo: armadilha
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Guia Prático EFD-Contribuições versão 1.35, Bloco M e Bloco 1"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-retificacao-sped
---

# Armadilha 6 — Esquecer de recalcular registros totalizadores

## Descrição do erro

Auditor altera os C170 corretamente excluindo o ICMS da base, mas **não propaga a alteração** para os registros totalizadores: C190 (analítico do documento), M210/M610 (apuração por código de receita), M200/M600 (totalizador do período), 1100/1500 (saldos credor).

O resultado é uma escrituração internamente inconsistente: a soma dos itens não bate com o totalizador, o totalizador não bate com a apuração, a apuração não bate com o saldo final.

## Consequência

O PVA da EFD-Contribuições **detecta automaticamente** a inconsistência e bloqueia a transmissão. O auditor não consegue passar para a etapa de PER/DCOMP até resolver. Em si, isso é proteção — não há glosa porque a retificadora nunca chega ser válida formalmente.

Mas o impacto operacional é o **trabalho perdido**: se a inconsistência só é detectada após múltiplas competências processadas, todas precisam ser revisadas. E se o auditor tenta "ajustar" os totalizadores manualmente sem refazer o cálculo de baixo para cima, introduz erros novos que o PVA pode não detectar — e esses chegarão como glosas posteriores.

## Como evitar

Seguir **rigorosamente os Passos 4, 5, 6 e 7 do bloco `tese69-retificacao-sped`**: após alterar C170, recalcular C190; após C190, recalcular M210/M610; após M210/M610, recalcular M200/M600; após M200/M600, recalcular 1100/1500. Cada passo depende do anterior.

A camada `operacao_estruturada` desse bloco lista explicitamente os `registros_dependentes` exatamente para que o gerador automático da Etapa 4 propague as alterações encadeadamente sem esquecer nenhum. Para retificação manual, mantém-se a mesma sequência como checklist obrigatório.

Validação útil antes de transmitir: rodar o PVA em modo "validação completa" e verificar que **zero erros** aparecem. Avisos podem ser aceitáveis dependendo do contexto; erros, nunca.

## Como corrigir se já cometido

Se o PVA bloqueou a transmissão, o trabalho é apenas refazer os passos 4-7 corretamente sobre o arquivo gerado, validar no PVA novamente, e transmitir.

Se houve transmissão errada (raro, porque o PVA bloqueia), retransmitir nova retificadora corrigida.
