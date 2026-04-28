---
bloco_id: tese69-modulacao-modulacao-geral
tipo: caso-especial
regras: [CR-07, CR-08, CR-09, CR-26]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: false
  competencia_posterior_a: "2017-03-15"
vigencia_inicio: "2021-05-13"
vigencia_fim: null
fundamentacao_legal:
  - "Acórdão de embargos declaratórios do RE 574.706 (julgado em 13/05/2021)"
  - "Parecer SEI nº 7698/2021/ME"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-fundamentacao
  - bloco_id: tese69-quantificacao
---

# Cenário 1 — Modulação geral (cliente sem ação ajuizada antes de 15/03/2017)

## Aplicabilidade

Este cenário se aplica quando o cliente **não ajuizou ação judicial** sobre o Tema 69 antes de 15/03/2017. É a situação majoritária em consultoria fiscal — a maior parte das empresas reativas só passou a discutir o tema após o julgamento do RE 574.706 e, sobretudo, após a modulação de 13/05/2021.

## Marco temporal e prescrição

A retificação alcança fatos geradores de **PIS/COFINS ocorridos a partir de 15/03/2017**, observado o prazo prescricional quinquenal contado da entrega da escrituração (ou do recolhimento, conforme o caso). Em outras palavras, ao avaliar competências disponíveis para recuperação no momento da análise, aplicam-se duas restrições simultaneamente:

- **Limite inferior pela modulação:** competência ≥ 03/2017.
- **Limite inferior pela prescrição:** competência cuja entrega da escrituração ocorreu há ≤ 5 anos contados da data atual.

A regra que efetivamente vincula é a **mais restritiva das duas**. Em análises feitas em 2026, por exemplo, a prescrição é mais restritiva (alcança até aproximadamente 03/2021 dependendo do mês de análise), e o limite da modulação fica de fora do horizonte recuperável.

## Caminho processual

Não há necessidade de ação judicial prévia. A recuperação se formaliza administrativamente via PER/DCOMP no e-CAC, com fundamento direto na decisão vinculante do STF (RE 574.706, Tema 69 da Repercussão Geral). O auditor fiscal da RFB tem dever funcional de aplicar a tese, conforme Parecer SEI 7698/2021/ME.

A vinculação administrativa significa que glosas baseadas em "não há trânsito em julgado próprio" ou "necessidade de ação judicial" são improcedentes nesse cenário e devem ser combatidas em manifestação de inconformidade. O registro 1010 da EFD-Contribuições retificadora **não é necessário** para esse cenário, pois não há ação judicial a referenciar.

## Procedimento aplicável

Seguir o bloco `tese69-retificacao-sped` para a retificação dos arquivos SPED, e o bloco `tese69-per-dcomp` para a formalização do pleito no e-CAC. Ambos os procedimentos estão escritos para o cenário modulação geral por padrão; ajustes para o cenário "ação anterior" são tratados no bloco `tese69-modulacao-acao-anterior`.

---

---
bloco_id: tese69-modulacao-acao-anterior
tipo: caso-especial
regras: [CR-07, CR-08, CR-09, CR-26]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: true
vigencia_inicio: "2021-05-13"
vigencia_fim: null
fundamentacao_legal:
  - "Acórdão de embargos declaratórios do RE 574.706 (julgado em 13/05/2021)"
  - "CTN, art. 168, I (prazo decadencial-prescricional para repetição/compensação)"
  - "IN RFB nº 2.055/2021 (procedimentos PER/DCOMP)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-fundamentacao
  - bloco_id: tese69-modulacao-modulacao-geral
---

# Cenário 2 — Cliente com ação judicial ajuizada antes de 15/03/2017

## Aplicabilidade

Este cenário se aplica quando o cliente **ajuizou ação judicial** sobre o Tema 69 (ou tese assemelhada — exclusão do ICMS da base de PIS/COFINS) antes de 15/03/2017, **e** essa ação transitou em julgado favoravelmente ao contribuinte. É situação minoritária em volume, mas de **alto valor financeiro** quando ocorre — porque amplia significativamente o horizonte temporal recuperável.

## Marco temporal e prescrição

O efeito da exclusão retroage **à data do ajuizamento da ação**, observado o prazo prescricional quinquenal contado da propositura. Como ações pré-modulação tipicamente foram ajuizadas em 2010-2016, o horizonte recuperável para esse perfil de cliente alcança rotineiramente fatos geradores de 2005-2011 — período em que a empresa ainda recolhia PIS/COFINS sobre base que já incluía ICMS indevido.

A vantagem comercial sobre o cenário 1 é direta: enquanto modulação geral oferece recuperação dos últimos 5 anos contados da análise, ação anterior pode oferecer 10-15 anos de recuperação acumulada. Em termos de ticket médio, isso costuma representar **2x a 4x o valor recuperável** do cenário modulação geral, para empresas de mesmo porte.

## Caminho processual

A formalização exige carrear ao pleito administrativo o **trânsito em julgado da ação judicial favorável**. Tipicamente:

- **Habilitação prévia do crédito** no e-CAC, conforme IN RFB 2.055/2021, art. 100 e seguintes — exige juntada de cópia autenticada do trânsito em julgado e da sentença/acórdão. O sistema valida o pedido em até 30 dias e habilita o crédito para uso em PER/DCOMP.
- **PER/DCOMP** subsequente referenciando o número da habilitação aprovada, com fundamento na sentença (não na decisão vinculante do STF).

A diferença operacional em relação ao cenário 1 é importante: mesmo com a tese consolidada pelo STF, **a RFB não aceita aplicar diretamente a sentença individual sem habilitação prévia** — ainda que a sentença tenha o mesmo conteúdo material da decisão vinculante. Pular essa etapa gera glosa por "ausência de habilitação" — armadilha frequente que está documentada no bloco `tese69-armadilhas`.

## Registro 1010 da EFD-Contribuições retificadora

Este cenário **exige** o preenchimento do registro 1010 (Detalhamento das Contribuições com Exigibilidade Suspensa) na EFD-Contribuições retificadora. O 1010 referencia o número do processo judicial, a vara, a data do trânsito em julgado e o tipo da ação (`IND_NAT_ACAO`). Sem o 1010 corretamente preenchido, a retificação fica formalmente válida mas sem ancoragem jurídica visível ao auditor RFB — fragilidade probatória crítica em eventual fiscalização.

---

---
bloco_id: tese69-modulacao-acao-pos-modulacao
tipo: caso-especial
regras: [CR-07, CR-08, CR-09, CR-26]
aplicavel_quando:
  cliente_tem_acao_judicial_pre_modulacao: false
  cliente_tem_acao_judicial_pos_modulacao: true
vigencia_inicio: "2021-05-13"
vigencia_fim: null
fundamentacao_legal:
  - "Acórdão de embargos declaratórios do RE 574.706 (julgado em 13/05/2021)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
---

# Cenário 3 — Cliente com ação judicial ajuizada após 15/03/2017

## Aplicabilidade

Este cenário se aplica quando o cliente ajuizou ação judicial sobre o Tema 69 **após 15/03/2017**. É frequente em empresas que tomaram conhecimento da tese tardiamente ou que litigam de forma defensiva mesmo após o julgamento.

## Marco temporal e prescrição

O efeito da exclusão é **idêntico ao do cenário 1** (modulação geral): retroage a 15/03/2017, observado o prazo prescricional quinquenal contado da entrega da escrituração ou do recolhimento.

Ações ajuizadas após 15/03/2017 **não conferem ampliação do horizonte recuperável** em relação à modulação geral, porque a modulação fixou o marco temporal independentemente da existência de ação. A ação posterior tem valor essencialmente declaratório e útil para casos de fiscalização contestada — não amplia direito.

## Caminho processual

Como o efeito é o mesmo da modulação geral, o caminho processual administrativo também é o mesmo: PER/DCOMP no e-CAC com fundamento na decisão vinculante do STF. A ação judicial **não precisa transitar em julgado** para que o pleito administrativo prossiga. O 1010 da EFD-Contribuições retificadora **não é obrigatório** para esse cenário (mas pode ser preenchido se a empresa preferir referenciar a ação por boa prática documental).

## Quando este cenário entra em pauta

Casos típicos onde o cenário 3 aparece e o auditor precisa reconhecê-lo: empresas que ajuizaram MS preventivo após o julgamento original mas antes da modulação; empresas com ação ajuizada por matriz que tem filiais com diferentes CNPJs; empresas que migraram de contadoria e descobriram a ação somente em revisão. Em todos os casos, o tratamento da retificação segue o cenário 1.
