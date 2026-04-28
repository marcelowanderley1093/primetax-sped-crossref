---
bloco_id: tese69-caso-especial-lucro-presumido
tipo: caso-especial
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_regime_apuracao: lucro-presumido
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 9.718/1998, art. 3º (regime cumulativo PIS/COFINS)"
  - "RE 574.706/PR (tese aplicável independente do regime)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-fundamentacao
  - bloco_id: tese69-retificacao-sped
---

# Caso especial — Cliente Lucro Presumido (regime cumulativo)

## Aplicabilidade

Empresas optantes pelo Lucro Presumido apuram PIS e COFINS pelo **regime cumulativo** com alíquotas reduzidas: 0,65% de PIS e 3% de COFINS sobre a receita bruta — total de 3,65% (Lei 9.718/1998, art. 3º).

A Tese 69 **aplica-se** ao regime cumulativo: a fundamentação do RE 574.706 é que o ICMS não compõe a base de PIS/COFINS por não ser receita do contribuinte, e essa razão vale independentemente do regime de apuração da pessoa jurídica.

## Diferenças mecânicas em relação ao Lucro Real (não-cumulativo)

A retificação no Lucro Presumido tem diferenças importantes:

**Não há crédito a recalcular.** No regime cumulativo, a empresa não toma crédito de PIS/COFINS sobre insumos — apenas debita sobre a receita. Logo, os registros de crédito (M105, M505, F100, F120, F130) **não existem** ou estão zerados na escrituração. A retificação foca exclusivamente nos registros de débito.

**O ganho da retificação é direto e imediato.** Como não há sistema de crédito que pudesse compensar débito menor com crédito menor, a redução da base no C170 (ou correlato) reflete-se integralmente em redução de imposto devido. Para alíquotas básicas, o ganho é exatamente 3,65% do ICMS destacado por item.

**Alíquotas aplicáveis nos C170.** No Lucro Presumido em regime cumulativo, os campos `ALIQ_PIS` e `ALIQ_COFINS` no C170 trazem 0,65% e 3% respectivamente — não os 1,65% e 7,60% do regime não-cumulativo. A `operacao_estruturada` do bloco `tese69-retificacao-sped` continua válida porque referencia os campos de alíquota do próprio registro, não constantes hardcoded.

**EFD-Contribuições simplificada.** Empresas no Lucro Presumido podem ter EFD-Contribuições sem alguns blocos que aparecem em Lucro Real (M105, M505 zerados ou ausentes; Bloco F simplificado). A retificação respeita essa estrutura — não preenche blocos que não existiam no original.

## Cenário de modulação aplicável

Mesmas três modalidades do CRT geral (modulação geral, ação anterior, ação posterior). Para Lucro Presumido, é particularmente comum o cenário 1 (modulação geral) — empresas menores tipicamente não ajuizaram ação antes da modulação.

## Magnitude esperada do crédito

No Lucro Presumido, o ganho é tipicamente **menor em valor absoluto** (porque a base receita-bruta é menor que em empresas Lucro Real comparáveis) mas **maior em proporção da receita líquida** (porque o regime cumulativo já é mais oneroso por base bruta).

Cliente Lucro Presumido típico com R$ 10 milhões de receita bruta anual com ICMS de 18% sobre receita gera aproximadamente R$ 65 mil de PIS/COFINS anual recuperáveis pela Tese 69 (R$ 1,8 milhão × 3,65%).

---

---
bloco_id: tese69-caso-especial-mix-exportacao
tipo: caso-especial
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_exportacao: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 10.637/2002, art. 5º, I (não-incidência sobre exportação)"
  - "Lei nº 10.833/2003, art. 6º, I (idem)"
  - "Tabela CST PIS/COFINS"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
---

# Caso especial — Empresa com mix significativo de exportação

## Aplicabilidade

Empresas com parcela relevante (> 20%) de receita oriunda de **operações de exportação**. Inclui exportadoras puras (100% exportação) e empresas com vendas mistas (exportação + mercado interno).

## Restrição central

Receitas de exportação **não compõem a base de PIS/COFINS**, por força das Leis 10.637/2002 (art. 5º, I) e 10.833/2003 (art. 6º, I). Operacionalmente, isso aparece nos C170 como CST de PIS/COFINS na faixa de **não-incidência por exportação**: tipicamente CST 06 ou 08 (alíquota zero / suspensão por exportação), com `VL_BC_PIS = 0`.

A Tese 69 **não tem aplicação** sobre itens de exportação porque já não há base de cálculo para reduzir — o item já está fora do alcance do tributo. Tentar aplicar a exclusão a itens de exportação é a Armadilha 5 (CST fora do conjunto correto).

## Particularidade — combinação com a tese da Lei 9.718/1998 (créditos sobre insumos para exportação)

Empresas exportadoras frequentemente têm tese complementar de **crédito presumido sobre insumos vinculados à exportação** (Leis 10.637/2002 art. 6º; 10.833/2003 art. 6º) — a empresa apropria crédito sobre insumos mas não paga débito sobre a receita exportada, gerando saldo credor.

Nessa configuração, a retificação Tese 69 aplica-se à parcela **mercado interno** dos insumos rateados — quando a empresa usa rateio proporcional (`0110.IND_APRO_CRED = 2`), parte do crédito vai para "vinculado a exportação" e parte para "vinculado a mercado interno". A redução de base nos itens de mercado interno reduz o débito; o saldo credor de exportação fica preservado.

A complexidade do rateio proporcional torna esse caso especial mais delicado em validação. Recomenda-se:
- Cruzar a retificação Tese 69 com a tese de **rateio proporcional × apropriação direta** (CR-28) — pode ser que mudar o método seja mais vantajoso após retificação.
- Confirmar que os percentuais de rateio do `0111` foram recalculados com as bases corrigidas.

## Magnitude esperada do crédito

Tipicamente **menor que em empresa não-exportadora** de mesmo porte, porque a base aplicável é apenas a parcela mercado interno. Para exportadora com 60% de exportação, o ganho da Tese 69 é proporcional aos 40% de mercado interno — não os 100% da operação.

---

---
bloco_id: tese69-caso-especial-monofasico-parcial
tipo: caso-especial
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_regime_monofasico_parcial: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 10.485/2002 (autopeças)"
  - "Lei nº 10.833/2003, art. 51 (combustíveis)"
  - "Lei nº 13.097/2015 (bebidas frias)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
---

# Caso especial — Cliente com regime monofásico parcial (combustíveis, bebidas, autopeças)

## Aplicabilidade

Empresas que comercializam produtos sujeitos a **regime monofásico de PIS/COFINS** — em que o tributo é concentrado no produtor/importador e os elos seguintes da cadeia (atacadistas, varejistas) operam com alíquota zero por substituição. Setores típicos: combustíveis e lubrificantes (Lei 10.833/2003, art. 51), bebidas frias e cervejas (Lei 13.097/2015), autopeças (Lei 10.485/2002), produtos farmacêuticos e cosméticos selecionados.

Em distribuidoras, atacadistas ou varejistas desses setores, a maioria dos itens de C170 traz **CST 04** (revenda de produto monofásico) com `VL_BC_PIS = 0`. ICMS pode estar destacado no C170 mas não há base PIS/COFINS sobre a qual se exclua o ICMS.

## Restrição central

Tese 69 **não se aplica** aos itens monofásicos do elo não-tributado — o produto já não tem PIS/COFINS na revenda por força do regime monofásico. Tentar aplicar a tese é a Armadilha 5 com volume tipicamente massivo (porque em distribuidoras de combustíveis, por exemplo, 95%+ dos itens são CST 04).

A tese **aplica-se sim** aos itens **não-monofásicos** que coexistem na mesma escrituração — itens de outras categorias (acessórios não-monofásicos, serviços, mercadorias gerais) com CST tributado normal. Em distribuidora típica, esses itens podem representar 5-15% da receita total — base menor mas legítima.

## Cuidado com a fase produtor/importador

A regra acima vale para o **elo não-tributado** (atacadistas, varejistas). No **elo tributado** do regime monofásico — o produtor ou importador do produto monofásico — a Tese 69 **aplica-se normalmente** porque o item tem CST tributado (geralmente 03 ou similar) com base normal de PIS/COFINS.

Distinguir os dois elos é crítico:
- Indústria que **produz** combustível, bebida ou autopeça monofásica → aplica Tese 69 sobre os itens dos seus C170 (são CST tributado).
- Distribuidor ou varejista que **revende** esses produtos → não aplica Tese 69 sobre os itens monofásicos (são CST 04), apenas sobre eventuais itens não-monofásicos da mesma escrituração.

## Magnitude esperada do crédito

Para o elo não-tributado (revendedor), o crédito é **muito menor** que em empresa não-monofásica de receita comparável — proporcional apenas ao % de itens não-monofásicos. Para revendedor 100% monofásico, o crédito da Tese 69 pode ser literalmente zero — ainda que haja milhões em ICMS destacado nas notas.

Para o elo tributado (produtor/importador), magnitude similar a outras empresas industriais não-monofásicas — Tese 69 plenamente aplicável.

---

---
bloco_id: tese69-caso-especial-mudanca-regime-no-ano
tipo: caso-especial
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_mudanca_regime_no_periodo: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "Lei nº 9.718/1998 (regime cumulativo)"
  - "Leis nº 10.637/2002 e 10.833/2003 (regime não-cumulativo)"
  - "IN RFB nº 1.911/2019 (consolidada IN 2.121/2022)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
  - bloco_id: tese69-retificacao-sped
---

# Caso especial — Mudança de regime cumulativo ↔ não-cumulativo no mesmo ano

## Aplicabilidade

Empresas que **mudaram o regime de apuração de PIS/COFINS** durante o período recuperável — tipicamente porque migraram de Lucro Presumido para Lucro Real (ou vice-versa) ou porque o porte cresceu/diminuiu cruzando o limite de obrigatoriedade.

A mudança gera competências do mesmo CNPJ com regimes distintos: Janeiro a Junho em cumulativo (alíquotas 0,65% / 3%), Julho a Dezembro em não-cumulativo (alíquotas 1,65% / 7,60%) — ou o inverso.

## Particularidades da retificação

**Cada competência mantém o regime que tinha originalmente.** A Tese 69 não muda o regime; apenas reduz a base. Competências cumulativas pré-mudança continuam cumulativas após retificação; competências não-cumulativas idem. O `0110.COD_INC_TRIB` não é alterado.

**Cálculo do crédito recuperável usa a alíquota da competência.** Item retificado em competência cumulativa gera crédito a 3,65% do ICMS destacado; item em competência não-cumulativa gera crédito a 9,25%. Não há "média" — é por competência.

**Saldos credor não cruzam mudança de regime.** Saldo credor gerado em competência não-cumulativa (registros 1100/1500) não migra para competência cumulativa subsequente — porque no regime cumulativo não há sistema de crédito. Da mesma forma, eventual saldo credor pré-mudança no Lucro Presumido (raro, mas existe em casos de retenção na fonte) não vira crédito utilizável no regime não-cumulativo posterior automaticamente.

**Atenção ao 0110 da retificadora.** Se a retificação envolve a competência exata da mudança, o registro 0110 (parâmetros de regime) deve refletir o regime que efetivamente vigorou naquele mês — informação que costuma estar correta no original e não deve ser alterada pela retificação Tese 69.

## Risco de erro frequente

Auditor não percebe a mudança de regime e calcula todos os créditos pela alíquota predominante (geralmente a não-cumulativa, mais alta). Resultado: superestimação do crédito recuperável nas competências cumulativas, depois ajustada para baixo pela RFB.

Validação: o motor de cruzamentos (CR-07) deve ler o `0110.COD_INC_TRIB` de **cada competência individualmente** ao calcular o crédito. Cálculo manual em planilha precisa replicar a mesma lógica.

---

---
bloco_id: tese69-caso-especial-sucessao-cisao
tipo: caso-especial
regras: [CR-07, CR-08, CR-09]
aplicavel_quando:
  cliente_tem_sucessao_no_periodo: true
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "CTN, art. 132 (sucessão tributária)"
  - "IN RFB nº 2.055/2021 (compensação por sucessor)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
---

# Caso especial — Sucessão empresarial, cisão ou fusão no período recuperável

## Aplicabilidade

Empresa atual (sucessora) que pretende recuperar créditos de Tese 69 sobre fatos geradores ocorridos **antes da reorganização societária** — quando esses fatos foram cometidos por empresa antecessora (incorporada, cindida ou fundida).

Inclui também o caso simétrico: empresa que **deixou de existir formalmente** (foi incorporada por outra) mas tinha crédito reconhecível antes da incorporação.

## Restrição central

A sucessão tributária (CTN art. 132) opera tanto para débitos quanto para créditos. A sucessora **assume os créditos** da antecessora, incluindo créditos de PIS/COFINS pagos indevidamente. **Mas o pleito formal precisa ser feito pelo CNPJ atual** — não há como pedir restituição em nome de CNPJ que não existe mais.

Operacionalmente, isso significa:

**EFD-Contribuições retificadora deve ser emitida pela antecessora se ela ainda existia na época**, mesmo que esteja extinta hoje. As retificadoras consertam a base histórica; o CNPJ delas é imutável. Para retificar EFD-Contribuições de empresa extinta, é necessário gerar o arquivo com o CNPJ histórico da antecessora e transmitir via certificado digital da sucessora (que tem acesso pelo vínculo sucessório registrado na RFB).

**PER/DCOMP é transmitido pela sucessora**, referenciando o CNPJ da antecessora como origem do crédito. A IN RFB 2.055/2021 prevê esse caminho — exige juntada da documentação societária comprovando a sucessão (atas, contrato social, CNPJ baixado da antecessora).

## Complicações típicas

**Documentação societária incompleta** é a principal complicação. Sucessões antigas (mais de 5-10 anos) frequentemente têm gaps — atas perdidas, CNPJ baixado sem registro claro do sucessor. Sem documentação completa, a RFB indefere o pleito.

**Cisões parciais** são especialmente complexas. Se a empresa A foi cindida em B (que herdou parte das operações) e A continuou existindo (com outra parte), os créditos da Tese 69 ficam **divididos proporcionalmente** entre A e B conforme estabelecido no protocolo de cisão. Nem sempre o protocolo é claro sobre créditos tributários — exige interpretação que pode ser disputada pela RFB.

**Sucessões intercaladas** (A incorpora B, depois A é incorporada por C) exigem rastrear toda a cadeia — qualquer elo mal documentado quebra o pleito.

## Recomendação prática

Em qualquer caso de sucessão, **antes de iniciar a retificação**, fazer auditoria da documentação societária com escritório de advocacia especializado. Se a documentação estiver incompleta, é trabalho de regularização preliminar antes de qualquer ato fiscal — os custos e tempo desse trabalho devem ser computados na avaliação do caso (e na precificação dos honorários de êxito).
