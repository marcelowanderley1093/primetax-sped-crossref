---
bloco_id: tese69-per-dcomp
tipo: procedimento
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "IN RFB nº 2.055/2021 (procedimentos PER/DCOMP)"
  - "CTN, art. 168, I (prazo para pleito de restituição/compensação)"
  - "Lei nº 9.430/1996, art. 74 (compensação tributária federal)"
  - "Parecer SEI nº 7698/2021/ME"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-retificacao-sped
  - bloco_id: tese69-armadilha-cenario2-sem-habilitacao
  - bloco_id: tese69-armadilha-selic-erro-aritmetico

operacao_estruturada:
  decisao_humana_necessaria: true
  motivo_decisao_humana: "A escolha entre PER (restituição) e DCOMP (compensação), bem como a vinculação a débitos específicos, depende de análise do horizonte de débitos do cliente nos 12-24 meses subsequentes. Esta análise envolve decisões comerciais e estratégicas que não cabem em automação direta na Etapa 1."
  campos_relevantes_quando_etapa_4:
    - tipo_credito_per_dcomp: "Pagamento Indevido ou a Maior - Tributos Federais"
    - codigo_receita_pis: "Conforme tabela RFB para o regime do cliente"
    - codigo_receita_cofins: "Conforme tabela RFB para o regime do cliente"
---

# Procedimento — Formalização do PER/DCOMP via e-CAC

Após a retificação dos arquivos SPED conforme `tese69-retificacao-sped`, o crédito identificado precisa ser formalizado no e-CAC para compensação ou restituição. Este procedimento orienta esse passo.

## Pré-condições

1. **Retificação SPED concluída e transmitida** com sucesso para todas as competências envolvidas.
2. **Crédito calculado e atualizado pela SELIC** até o mês previsto para a transmissão do PER/DCOMP (ver bloco `tese69-quantificacao`).
3. **Cenário de modulação confirmado** — a habilitação prévia é necessária no cenário 2 (ação anterior), dispensável nos cenários 1 e 3.
4. **Certificado digital A1 válido** da empresa (ou e-CAC habilitado para o representante legal).
5. **Decisão tomada sobre PER vs. DCOMP** — restituição em dinheiro vs. compensação com débitos a pagar (ver seção "Escolha entre PER e DCOMP" abaixo).

## Escolha entre PER e DCOMP

Esta é a decisão estratégica central do procedimento e **exige análise humana** — não há automação direta possível.

**PER (Pedido Eletrônico de Restituição)** — pleito de devolução em dinheiro. Caminho mais lento (12-36 meses até o efetivo crédito em conta), com mais atrito administrativo (RFB pode exigir habilitação, perícia, complementações). Faz sentido quando o cliente **não tem débitos federais a pagar** no horizonte recuperável, ou quando o crédito é muito superior aos débitos disponíveis.

**DCOMP (Declaração de Compensação)** — uso do crédito para extinguir débitos federais já vencidos ou vincendos. Caminho mais rápido (compensação em D+0 a D+30 dependendo da modalidade), com menor atrito (a RFB tem 5 anos para homologar tacitamente, conforme art. 74 da Lei 9.430/1996). Faz sentido quando o cliente tem **débitos federais a pagar** no horizonte de 12-24 meses subsequentes — IRPJ estimado, CSLL estimado, PIS/COFINS de competências futuras, contribuições previdenciárias, IPI, IRRF de pagamentos a colaboradores ou fornecedores.

A regra prática Primetax: **se o cliente tem débitos federais regulares no horizonte de 24 meses ≥ 70% do crédito a recuperar, fazer DCOMP**. Caso contrário, fazer PER pelo excedente. Em muitos casos, a melhor estratégia é **mista** — DCOMP para a parcela compensável e PER para o saldo que não cabe na janela de compensação.

## Sequência de passos

### Passo 1 — Cenário 2 apenas: habilitar previamente o crédito

Se o cliente está no cenário 2 (ação judicial pré-modulação), antes de qualquer PER/DCOMP é necessário **habilitar o crédito** no e-CAC, conforme IN RFB 2.055/2021, art. 100 e seguintes.

Acesse e-CAC → Compensação e Restituição → Habilitação de Crédito → Novo Pedido. Anexar:
- Cópia autenticada do trânsito em julgado da ação.
- Cópia da sentença/acórdão favorável.
- Procuração se for o caso.

A RFB tem 30 dias para validar e habilitar (ou indeferir e indicar exigências). Habilitação aprovada gera número de habilitação que será referenciado nos PER/DCOMP subsequentes.

Cenários 1 e 3 **não exigem habilitação prévia** — pular este passo.

### Passo 2 — Acessar o e-CAC e iniciar o PER/DCOMP

Login com certificado digital A1 da empresa (ou e-CAC habilitado para procurador). Navegar até **Compensação e Restituição → PER/DCOMP Web → Novo Documento**.

Selecionar o tipo de documento:
- **PER** (Pedido de Restituição) — para restituir em dinheiro.
- **DCOMP** (Declaração de Compensação) — para compensar com débitos.

### Passo 3 — Preencher os dados do crédito

Identificar a natureza do crédito como **"Pagamento Indevido ou a Maior - Tributos Federais"**. Para cada competência retificada, informar:

- **Código de receita** — códigos da PIS/COFINS conforme regime do cliente (tabela vigente da RFB; consultar `src/tables/codigos_receita_pis_cofins.py`).
- **Período de apuração** — competência (MM/AAAA).
- **Data do recolhimento** — data efetiva do pagamento original do DARF que se está restituindo/compensando.
- **Valor original do recolhimento** — valor do DARF originalmente pago.
- **Valor a recuperar** — diferença entre o valor pago e o valor que seria devido pela base correta (ICMS excluído).
- **Valor atualizado pela SELIC** — recalcular com a SELIC acumulada do mês seguinte ao recolhimento até o mês da transmissão.

Para o cenário 2, no campo "Origem do Crédito" referenciar o número da habilitação aprovada no Passo 1.

### Passo 4 — Para DCOMP: vincular aos débitos a compensar

Em DCOMP, após informar o crédito, listar os débitos que serão compensados. Cada débito é identificado por:

- Código de receita.
- Período de apuração.
- Vencimento.
- Valor.

A compensação é feita débito a débito, na ordem cronológica. Se o crédito não cobre todos os débitos vinculados, o sistema rejeita parcialmente — refazer com vinculação ajustada.

### Passo 5 — Anexar documentação probatória

A IN RFB 2.055/2021 exige anexação de documentos comprobatórios mínimos. Para Tese 69:

1. **Demonstrativo de cálculo** detalhado por competência — pode ser exportado pelo `primetax-sped manuais render --formato=pdf` (versão futura) ou por planilha gerada manualmente.
2. **Cópia das DCTF/DCTFWeb** das competências retificadas — comprovam o débito originalmente declarado.
3. **Cópia dos DARFs de recolhimento** — comprovam o pagamento efetivo.
4. **Cópia dos recibos das EFD-Contribuições retificadoras** — comprovam que a base de cálculo foi corrigida formalmente.
5. **Para cenário 2**: cópia da habilitação aprovada no Passo 1.

A ausência de qualquer desses documentos é causa frequente de exigência de complementação pela RFB, atrasando o processo em 60-90 dias.

### Passo 6 — Transmitir e acompanhar

Transmitir o PER/DCOMP. O sistema gera comprovante com número de protocolo. Salvar em `data/output/{cnpj}/{ano}/per-dcomp-protocolo-{numero}.pdf`.

Acompanhar pelo e-CAC mensalmente:
- **DCOMP** — homologação tácita em 5 anos contados da transmissão (Lei 9.430/1996, art. 74); homologação expressa pode ocorrer antes.
- **PER** — análise pela RFB pode demorar 12-36 meses; resposta vem como deferimento total, parcial ou indeferimento.

Em caso de exigência ou indeferimento, o cliente tem 30 dias para apresentar **Manifestação de Inconformidade** — caminho recursal próprio dos PER/DCOMP, que pode ir até a 3ª instância (CARF). A Primetax acompanha esse contencioso quando contratado para a fase pós-protocolo.

## Pós-condições

1. PER/DCOMP transmitido e protocolo salvo em `data/output/`.
2. Para DCOMP — débitos compensados extintos no e-CAC dentro de D+30.
3. Para PER — pedido em análise pela RFB, com prazo de resposta esperado registrado no controle interno do cliente.
4. Cliente informado por relatório formal sobre o status, valor protocolado e prazos esperados.

## Decisão estruturada na Etapa 4

A camada `operacao_estruturada` deste bloco está marcada como `decisao_humana_necessaria: true`. A razão é que a escolha PER vs. DCOMP, a vinculação a débitos específicos, e a estratégia de timing dependem de análise do contexto comercial e estratégico do cliente — não de regra mecânica.

Quando a Etapa 4 chegar, o gerador automático poderá:
- Pré-preencher os dados do crédito por competência, valor e SELIC atualizada.
- Sugerir débitos disponíveis para compensação a partir das obrigações declaradas em DCTF/DCTFWeb do cliente.
- Gerar o demonstrativo de cálculo em PDF formatado.

Mas a decisão final sobre **fazer PER ou DCOMP**, e **quais débitos vincular**, permanecerá humana — assistida pelo sistema, não substituída por ele.
