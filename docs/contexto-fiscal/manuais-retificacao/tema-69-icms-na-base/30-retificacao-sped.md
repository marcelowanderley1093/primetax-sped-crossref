---
bloco_id: tese69-retificacao-sped
tipo: procedimento
regras: [CR-07, CR-08, CR-09]
vigencia_inicio: "2017-03-15"
vigencia_fim: null
fundamentacao_legal:
  - "IN RFB nº 1.252/2012 (institui a EFD-Contribuições)"
  - "IN RFB nº 1.387/2013 (prazo para retificação)"
  - "Guia Prático EFD-Contribuições versão 1.35 (jun/2021)"
ultima_revisao: "2026-04-15"
revisor: "Marcelo Wanderley"
referencias_cruzadas:
  - bloco_id: tese69-quantificacao
  - bloco_id: tese69-per-dcomp
  - bloco_id: tese69-armadilha-1010-ausente
  - bloco_id: tese69-armadilha-ordem-cronologica
  - bloco_id: tese69-armadilha-cst-fora-do-conjunto
  - bloco_id: tese69-armadilha-esquecer-recalcular-totalizadores

operacao_estruturada:
  registros_alvo: [C170]
  alteracoes:
    - campo: VL_BC_PIS
      formula: "VL_ITEM - VL_DESC - VL_ICMS"
      condicao: "CST_PIS in [01, 02, 03, 05] and VL_ICMS > 0"
    - campo: VL_BC_COFINS
      formula: "VL_ITEM - VL_DESC - VL_ICMS"
      condicao: "CST_COFINS in [01, 02, 03, 05] and VL_ICMS > 0"
    - campo: VL_PIS
      formula: "round(VL_BC_PIS * ALIQ_PIS / 100, 2)"
      condicao: "CST_PIS in [01, 02, 03, 05] and VL_ICMS > 0"
    - campo: VL_COFINS
      formula: "round(VL_BC_COFINS * ALIQ_COFINS / 100, 2)"
      condicao: "CST_COFINS in [01, 02, 03, 05] and VL_ICMS > 0"
  registros_dependentes: [C190, M210, M610, M200, M600, 1100, 1500]
  validacao_pos_alteracao:
    - "VL_BC_PIS >= 0"
    - "VL_BC_PIS <= VL_ITEM"
    - "VL_BC_COFINS >= 0"
    - "VL_BC_COFINS <= VL_ITEM"
  efeitos_apuracao:
    - reducao_base_pis_nao_cumulativo
    - reducao_base_cofins_nao_cumulativo
    - reducao_imposto_devido
    - eventual_geracao_saldo_credor
---

# Procedimento — Retificação da EFD-Contribuições para Tese 69

Este procedimento orienta a geração e transmissão dos arquivos retificadores da EFD-Contribuições para incorporar a exclusão do ICMS da base de cálculo do PIS/COFINS, conforme Tema 69 do STF.

## Pré-condições

Antes de iniciar, o auditor Primetax deve ter:

1. **Diagnóstico do sistema** confirmando oportunidade — relatório do `primetax-sped diagnose` com cruzamento CR-07 ativo e valores quantificados por competência.
2. **Cenário de modulação identificado** — modulação geral, ação anterior ou ação posterior à modulação (consultar blocos `tese69-modulacao-*`). Para ação anterior, ter em mãos o número do processo, vara, data do ajuizamento e cópia do trânsito em julgado.
3. **Acesso ao PVA da EFD-Contribuições** instalado e atualizado para a versão do leiaute compatível com a competência a retificar (vigente versão 1.35 para fatos pós-jul/2021).
4. **Arquivos SPED originais** das competências a retificar, em `data/input/{cnpj}/{competencia}/`. O sistema Primetax mantém esses arquivos imutáveis (princípio 2 da seção 4 do CLAUDE.md); a retificação é arquivo novo.
5. **Confirmação do prazo prescricional** — a competência ainda está dentro do quinquênio contado da data atual, pelos critérios da seção 18.5 do CLAUDE.md (data de entrega da escrituração + 5 anos).

## Sequência de passos

### Passo 1 — Determinar a ordem cronológica das competências a retificar

Retificar **da mais antiga para a mais recente**. A razão é técnica: alterações no saldo credor de uma competência (campo `1100.SLD_CRED_FIM` no PIS, `1500` no COFINS) afetam diretamente a competência seguinte (campo `1100.VL_SLD_CRED_INI` da subsequente). Retificar fora de ordem cronológica gera quebras de continuidade no carry-forward.

Ação concreta: ordenar as competências candidatas em ordem ascendente; processar uma de cada vez; só passar para a seguinte após validar o PVA da anterior.

### Passo 2 — Marcar o registro 0000 como retificadora

Abrir o arquivo SPED original em editor de texto (ou ferramenta de geração interna), localizar o registro 0000 e alterar o campo `IND_FIN_ESC` (campo 14) de "0" (original) para "1" (retificadora).

Adicionar no campo `COD_HASH_SUB` (campo 15) o hash da escrituração substituída — disponível no recibo de transmissão da escrituração original. Sem o hash correto, o PVA rejeita a retificadora.

### Passo 3 — Aplicar a exclusão do ICMS nos registros C170

Para cada item de C170 onde:
- `CST_PIS` ∈ {01, 02, 03, 05} (CST de débito);
- `CST_COFINS` ∈ {01, 02, 03, 05};
- `VL_ICMS` > 0;

executar:

```
Novo VL_BC_PIS    = VL_ITEM - VL_DESC - VL_ICMS
Novo VL_BC_COFINS = VL_ITEM - VL_DESC - VL_ICMS
Novo VL_PIS       = round(Novo VL_BC_PIS × ALIQ_PIS / 100, 2)
Novo VL_COFINS    = round(Novo VL_BC_COFINS × ALIQ_COFINS / 100, 2)
```

Itens com CST fora do conjunto acima ou com VL_ICMS = 0 **não são tocados**.

### Passo 4 — Recalcular registros C190 (analítico do documento)

O C190 agrega C170 por combinação de `CST_ICMS + CFOP + ALIQ_ICMS`. Após alterar o C170, recalcular os campos somatórios do C190 — sobretudo `VL_BC_PIS` e `VL_COFINS` se presentes (a depender da versão do leiaute).

### Passo 5 — Recalcular registros M210 e M610 (apuração)

O M210 é a apuração de PIS por código de receita (`COD_CONT`); o M610 é o equivalente para COFINS. Após alterar o C170/C190, recalcular para cada combinação de `COD_CONT + ALIQ`:

- `VL_BC_CONT` = soma das bases dos itens correspondentes.
- `VL_CONT_APUR` = VL_BC_CONT × alíquota.

Manter os ajustes em M215/M615 que já existiam no original (a menos que a tese envolva ajuste de base via 1050, caso especial tratado em outro bloco).

### Passo 6 — Recalcular registros M200 e M600 (totalizador)

M200 totaliza o PIS do período; M600 a COFINS. Recalcular:

- `VL_TOT_CONT_NC_PER` = soma de `VL_CONT_APUR` dos M210 não-cumulativos.
- `VL_TOT_CRED_DESC` (mantém crédito do período).
- `VL_CONT_DEV` = `VL_TOT_CONT_NC_PER + VL_TOT_CONT_CUM_PER - VL_TOT_CRED_DESC`.

Se VL_CONT_DEV ficar negativo, o saldo é credor — segue para 1100/1500 do período seguinte.

### Passo 7 — Recalcular registros 1100 e 1500 (saldos)

Atualizar `VL_SLD_CRED_FIM` do M200/M600 para refletir o saldo credor gerado pela retificação. Esse saldo será o `VL_SLD_CRED_INI` da competência seguinte — por isso a importância da ordem cronológica do Passo 1.

### Passo 8 — Para cenário "ação anterior", preencher o registro 1010

Se o cliente está no cenário 2 (ação judicial pré-modulação com trânsito em julgado), preencher um registro 1010 referenciando:

- `IND_NAT_ACAO` = "01" (ação judicial transitada em julgado favorável ao contribuinte).
- `NUM_PROC` = número completo do processo.
- `IND_PROC` = "1" (Justiça Federal) ou "2" (Justiça Estadual), conforme o caso.
- `VARA` = identificação da vara.
- `DT_DEC` = data do trânsito em julgado.

Sem o 1010 nesse cenário, a retificação fica sem ancoragem visível à RFB — fragilidade probatória crítica (ver `tese69-armadilhas`).

### Passo 9 — Validar no PVA antes de transmitir

Carregar o arquivo retificador no PVA da EFD-Contribuições e executar **validação completa**. O PVA aplica regras de consistência interna que detectam erros aritméticos de retificação (ex.: M210 que não bate com somatório de C170; saldo credor que não bate com fluxo do período). Erros do PVA bloqueiam a transmissão e devem ser todos resolvidos antes de prosseguir.

### Passo 10 — Transmitir e arquivar o recibo

Transmitir via Receitanet. Salvar o recibo de transmissão em `data/output/{cnpj}/{competencia}/recibo-retificadora.pdf`. O hash do recibo será necessário se houver retificação posterior dessa retificadora (raro, mas possível).

## Pós-condições

Após o procedimento completo, devem ser verdadeiros:

1. Arquivo retificador transmitido com sucesso ao Receitanet.
2. Recibo arquivado em `data/output/`.
3. Para todas as competências retificadas, o sistema do auditor mostra `IND_FIN_ESC = 1` na consulta da escrituração via Sefaz.
4. Os valores de saldo credor projetados pelo motor de cruzamentos coincidem com os valores efetivamente registrados em 1100/1500 da retificadora — divergência aqui indica erro aritmético que precisa ser revisado antes de prosseguir para o PER/DCOMP.
5. Snapshot da versão do manual consultada salvo em `data/output/{cnpj}/{ano}/snapshot-manuais.json` (geração automática pelo sistema, princípio de rastreabilidade).

Concluído este procedimento, prosseguir para o bloco `tese69-per-dcomp` para formalização do pleito administrativo de compensação ou restituição.
