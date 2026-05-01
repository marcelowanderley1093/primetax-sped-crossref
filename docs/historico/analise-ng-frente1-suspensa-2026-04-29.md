# Frente 1 — Análise fiscal Tema 779 da Norte Geradores

**Status:** SUSPENSA (aguardando Adaptação T9 versão completa)
**Data:** 2026-04-29
**Branch de trabalho:** `gui/sprint-1`
**Último commit relevante:** `b95985b`

---

## 1. Estado consolidado da v5 (pós-sessão NG)

- 8 commits empurrados na sessão Norte Geradores (branch `gui/sprint-1`)
- 425/425 testes passando
- 6 bugs descobertos:
  - 4 corrigidos (truncamento PVA, patterns mojibake, fixtures J150 CR-39, CLI cosmético)
  - 1 mitigado parcialmente (Bug-003 — apuração trimestral, Opção i aplicada)
  - 2 documentados como débito (Bug-001 Bloco 9 hard-coded; Bug-002 sem dedup em reimport)
- 4 bancos NG importados em `data/db/63876114000110/`:
  - `2021.sqlite` (34 MB)
  - `2022.sqlite` (38 MB)
  - `2023.sqlite` (40 MB)
  - `2024.sqlite` (35 MB)

## 2. Resultado da validação técnica

- **T9 reproduz Razão analítico com diff R$ 0,00 em 18/18 pares** (9 contas × 2 anos importados na fase intermediária)
- Bug-003 (cálculo de despesa em apuração trimestral) corrigido pela Opção (i): `SUM(vl_deb)` apenas, sem subtração de `vl_cred`
- L11 (Manutenção e Conservação) bate **conta-a-conta em 100%**: R$ 35.846,88 = R$ 35.846,88

## 3. Benchmark da consultoria

- **Total: R$ 4.797.126,82** (PIS+COFINS sobre BC R$ 51.860.830,52)
- Período declarado: 2021-2024
- Alíquota uniforme **9,25%** (não-cumulativo: PIS 1,65% + COFINS 7,6%)
- Sem Selic, sem juros (apenas principal)

**Fora do escopo T9:**
- R$ 985.731,45 imobilizado (vem de EFD ICMS/IPI das filiais)
- R$ 121.813,08 geradores não contabilizados na EFD-Contribuições

**Alvo realista T9: R$ 3.692.456** (subtraindo os dois itens acima do total da consultoria).

## 4. Reverse engineering — método da consultoria

Após análise das 9 contas mapeadas (3004, 3005, 3006, 3007, 3010, 3012, 3017, 3432, 3435), três padrões distintos emergem:

### Padrão A — Período generoso, sem filtro qualitativo forte
**Contas:** 3004 (Fretes), 3005 (Manut. Veículos), 3006 (Combustíveis), 3017 (Energia)
**Característica:** consultoria estendeu período além de dez/2022 com corte temporal *específico por conta*. Top 10 fornecedores são integralmente PJ (nenhuma PF detectada). Filtro qualitativo NÃO foi dominante.

### Padrão B — Filtro qualitativo restritivo, manual
**Contas:** 3007 (Locação Veíc/Maq), 3012 (Serviços PJ), 3435 (Locação Imóveis)
**Característica:** consultoria fez seleção individual de lançamentos. Em 3007: pegou 2 de 6 partidas pré-set/22 (R$ 6.000 + R$ 34.500 = R$ 40.500 exato). Em 3435: pegou 28% das partidas (separando aluguéis comerciais PJ de aluguéis residenciais PF). Em 3012: filtro PF + seleção parcial dos "indefinidos" — BC R$ 5,6M está entre os cenários "excluir PF" (R$ 6,2M) e "manter só PJ_sufixo" (R$ 4,4M).

### Padrão C — Match por coincidência temporal
**Conta:** 3432 (Manut. Móveis/Imóveis)
**Característica:** todos os 9 lançamentos da conta ocorreram em fev–abr/2022, naturalmente abaixo de qualquer corte 2022. Match 100% sem filtro adicional.

### Padrão D — Imaterialidade
**Conta:** 3010 (Manut. Equipamentos)
**Característica:** excluída pela consultoria por baixo valor (R$ 19K em 4 anos).

## 5. Datas efetivas de corte (Padrão A)

Acumulado D Normal cronológico atinge BC consultoria em:

| Conta | BC consultoria | Data em que acumulado atinge BC |
|------:|---------------:|--------------------------------:|
| 3005 Manut. Veículos | R$ 30.039.901,32 | **31/ago/2023** (R$ 30.221.878,18) |
| 3006 Combustíveis | R$ 3.171.953,48 | **20/jun/2023** (R$ 3.172.418,54) |
| 3017 Energia | R$ 285.457,18 | **18/jul/2024** (R$ 285.761,26) |

**Implicação:** a nota L16 da planilha-consultoria ("OUTUBRO/2022 EM DIANTE SEM MOVIMENTO") era simplificação narrativa, não regra de filtragem aplicada. Cada conta teve período próprio definido caso a caso.

## 6. Gap descoberto na T9 atual

- T9 atual marca conta inteira via `ContabilController.marcar_oportunidade` (uma marcação por `cod_cta`)
- Análise fiscal real exige **marcação por lançamento individual** — Padrão B é irredutivelmente granular: em 3007, das 6 partidas pré-set/22 só 2 são elegíveis; em 3435 só 28%
- Filtros simples (período, PF/PJ) cobrem ~80% dos casos; os 20% restantes (3007, 3435) exigem julgamento de essencialidade lançamento-a-lançamento
- **Decisão:** Adaptação T9 versão completa antes de retomada da análise NG

## 7. Especificação derivada para Adaptação T9 (versão completa)

### Capacidades essenciais (universais — todos clientes Lucro Real)

| Capacidade | Padrão que motiva |
|------------|-------------------|
| Marcação por lançamento individual (substitui marcação por conta) | B (3007, 3435) |
| Detector heurístico PF/PJ (regex CPF/CNPJ + sufixos LTDA/EIRELI/EPP/MEI/SA) | B (3012 com 10,5% PF identificável) |
| Filtro de período variável por conta (não global) | A (3005 ago/23, 3006 jun/23, 3017 jul/24 — cada um diferente) |
| Filtros compostos para marcação em massa (data + classe + valor + texto + fornecedor) | B (3012 com 2.678 partidas) |
| Marcação por participante/fornecedor recorrente | A/B (DELTA CARGO 6× em 3004; ALELO 8× em 3012) |
| Visualização "elegível vs total" agregado em tempo real | B onde % é variável |
| Persistência granular auditável (decisão por lançamento + justificativa) | Defesa em fiscalização |
| Histórico de decisões por conta | Conformidade fiscal |

### Específicos NG (não generalizáveis — viram regras manuais por cliente)

- Critério "atividade-fim navegação ≠ locação de geradores" → exclui RNM BARBOSA em 3007
- Critério "apartamento residencial ≠ imóvel comercial" → exclui locações residenciais em 3435
- Estes dependem da atividade-fim e da nomenclatura do plano de contas de cada cliente

## 8. Alternativas de UI mapeadas (decisão pendente)

### Alternativa A — Checkbox por linha + filtros progressivos
Tabela de razão analítico com coluna "Elegível" (checkbox) por linha. Painel lateral de filtros (data range, valor range, classe PF/PJ, texto contém, fornecedor). Botões de marcação em massa. Total agregado no rodapé.
**Prós:** familiar, simples. **Contras:** tedioso em contas com 2.000+ partidas.

### Alternativa B — Regras de marcação empilháveis
Lista ordenada de regras (filtro + ação incluir/excluir). Resultado calculado em tempo real. Cada regra revisável.
**Prós:** auditável, regras viram template entre clientes. **Contras:** mais complexa de implementar.

### Alternativa C — Workflow guiado por conta (wizard)
Sequência de perguntas por conta: "Candidata Tema 779? Período? Filtros automáticos? Revisar restantes?".
**Prós:** guia auditor iniciante. **Contras:** rígido para casos complexos.

## 9. Alternativas de persistência mapeadas (decisão pendente)

### P1 — Nova tabela `essencialidade_lancamento`
Granular: `(cnpj × ano × cod_cta × linha_arquivo) → elegivel: bool, regra_aplicada: TEXT, justificativa: TEXT, decidido_por, decidido_em`. Complementa `contabil_oportunidades_essencialidade` atual (marcação por conta inteira fica como modo simplificado).

### P2 — Tabelas `regras_essencialidade` + `regras_aplicadas_lancamento`
Mais flexível para Alternativa B (regras stackable, reutilizáveis entre clientes).

### P3 — Coluna `elegivel_essencialidade` em `ecd_i250`
Mais simples, mas mistura semântica fiscal com schema contábil (não recomendado).

### Implicação do Bug-002 (resolução técnica) sobre P1/P2/P3

Após resolução do Bug-002 via Opção 2 (DELETE prévio em
reimport — todas as tabelas SPED do tipo × período × CNPJ
são recriadas em cada import; commits `fd2a63f` + `af3b55f` +
`c8d6379` da Sprint Hardening 2026-05-01), persistência granular
T9 deve **referenciar lançamentos por chave de negócio**, não
por `linha_arquivo` física. Em retificação, `linha_arquivo` muda
(arquivo novo, ordem nova); chaves de negócio (ex.: `num_lcto +
cod_cta + dt_lcto + vl_deb_cred` em I250) sobrevivem.

Ajustes às alternativas:

- **P1 ajustado**: chave `(cnpj × ano × cod_cta × num_lcto ×
  dt_lcto)` em vez de `(... × linha_arquivo)`. Marcação resiste
  a retificação.
- **P2 ajustado**: regras stackable aplicam a chaves de negócio
  (mesmo princípio).
- **P3 desaconselhado**: coluna em `ecd_i250` perde anotação no
  DELETE prévio do reimport. P1 ou P2 são preferíveis.

Esta nota decorre da decisão técnica do Bug-002 e preserva
aprendizado para a próxima sprint da Adaptação T9.

## 10. Sequência planejada para retomada

| Etapa | Status | Conteúdo |
|-------|--------|----------|
| 1 | concluída | Este documento de encerramento |
| 2 | pendente | Sprint Hardening (Bug-001 Bloco 9 + Bug-002 dedup reimport) |
| 3 | pendente | Adaptação T9 versão completa (capacidades da seção 7) |
| 4 | pendente | Análise NG retomada com T9 madura |
| 5 | pendente | CLAUDE.md consolidando aprendizados |

## 11. Dados de retomada

### Bancos
- `data/db/63876114000110/2021.sqlite`
- `data/db/63876114000110/2022.sqlite`
- `data/db/63876114000110/2023.sqlite`
- `data/db/63876114000110/2024.sqlite`

### Scripts ad-hoc preservados em `temp/` (gitignored)
- `temp/validacao_t9_2021.py` — validação inicial T9 contra 2021
- `temp/triangulacao_razao_t9.py` — triangulação T9 vs Razão (18/18 zero diff)
- `temp/analise_t9_ng_completa.py` — extração consolidada 4 anos
- `temp/reverse_eng_consultoria.py` — análise quantitativa Padrões A/B/C/D
- `temp/reverse_eng_padroes.py` — análise textual com histórico real (col 13)
- `temp/reverse_eng_padroes_b.py` — agregação PF/PJ + busca data corte Padrão A

### Fontes externas em `temp/norte-geradores/` (gitignored)
- `planilha-consultoria.xlsx` — aba relevante: **"Levantamento Completo"** (10 pontos L06-L15)
- `Razão - 3xxx.csv` — 9 razões analíticos (3004, 3005, 3006, 3007, 3010, 3012, 3017, 3432, 3435)
- `ECD - I050, I155 - Balancete...xlsx` — balancete completo
- `EFD-Contribuições - 037 / F100`, `PIS-Cofins - 063 / 087 / 865` — extrações da consultoria
- `PIS.csv`, `COFINS.csv`, `IRPJ.csv`, `CSLL.csv` — apurações mensais 2021-2024

## 12. Referências cruzadas

### Débitos documentados
- `docs/debitos-conhecidos.md`:
  - Bug-001 — Validação de Bloco 9 hard-coded vazia em ECD/EFD ICMS/IPI/ECF
  - Bug-002 — Ausência de dedup/upsert em reimport de SPED
  - Bug-003 — Despesa em apuração trimestral (mitigado por Opção i; refinamentos ii/iii pendentes)

### Commits da sessão NG (branch `gui/sprint-1`)
| Hash | Mensagem |
|------|----------|
| `04aed11` | fix(parsers): trunca conteúdo em \|9999\| antes de validar encoding |
| `c6bf3f2` | fix(encoding): alinha patterns de mojibake com v6 arquivada |
| `9141862` | fix(fixtures): atualiza J150 do CR-39 para Leiaute 9 real |
| `73811d5` | refactor(parsers): truncamento PKCS#7 PVA simétrico em todos os parsers SPED |
| `b5d17c8` | fix(cli): substitui '→' por '->' em mensagem de OK do import |
| `d12341c` | docs(debitos): registra Bug-001 (Bloco 9 hard-coded) e Bug-002 (sem dedup em reimport) |
| `1f4dd31` | fix(contabil): corrige cálculo de despesa em apuração trimestral (Bug-003) |
| `b95985b` | docs(debitos): registra Bug-003 como mitigado por correção parcial |
