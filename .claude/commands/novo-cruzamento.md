---
description: Gerar esqueleto de um novo cruzamento (módulo + testes + fixtures).
---

O usuário pede um novo cruzamento. Antes de escrever código, confirme:

1. **Código da regra** (ex: `CR-48`) e uma descrição curta de uma linha.
2. **SPEDs envolvidos** — deve casar com os prefixos já usados em `src/crossref/`:
   `efd_contribuicoes`, `efd_icms`, `ecd`, `ecf`.
3. **Base legal** — lei, IN ou precedente que sustenta a regra. Sem isso, **pare**
   e peça explicitamente. O princípio 4 do CLAUDE.md (§4) proíbe regras sem
   âncora normativa.
4. **Lógica de disparo** — que condição SQL/Python torna a regra positiva?
5. **Severidade** (`alto`/`medio`/`baixo`) e o que cai em `valor_impacto_conservador` /
   `valor_impacto_maximo`.
6. **Depende de reconciliação de plano de contas?** Se for COD_CTA-dependente,
   precisa declarar `MODO_DEGRADADO_SUPORTADO` e implementar o fallback
   agregado (CLAUDE.md §16.3).

Com essas respostas:

1. **Crie o módulo** em `src/crossref/camada_2_oportunidades/cruzamento_NN_nome.py`
   (ou `camada_3_consistencia/` se for intra-SPED puro). Siga o padrão:
   - Docstring começando com `"""CR-NN — título."""`
   - Bloco `Base legal:` citando dispositivo exato e `Vigência:`.
   - `CODIGO_REGRA = "CR-NN"`, `DEPENDENCIAS_SPED = [...]`.
   - Função `executar(repo, conn, cnpj, ano_mes, ano_calendario) -> (ops, divs)`.

2. **Registre no engine** em `src/crossref/engine.py`: import + append na lista
   da camada correspondente.

3. **Adicione metadata ao relatório** em `src/reports/excel_diagnostico.py`
   (tupla em `_METADATA_REGRAS` com deps e descrição curta).

4. **Se for parte de uma tese**, adicione o CR-NN a `codigos_regras` da tese
   apropriada em `src/reports/word_parecer.py` (`_TESES`).

5. **Crie o par de testes** em `tests/crossref/test_cruzamento_NN_*.py`:
   - `test_*_dispara`: fixture com anomalia → cruzamento detecta.
   - `test_*_nao_dispara`: fixture sem anomalia → cruzamento silente.
   - Para cruzamentos COD_CTA-dependentes, inclua os 4 testes exigidos em §16.7
     (positivo/negativo granular + positivo/negativo degradado).

6. **Crie a(s) fixture(s)** em `tests/fixtures/` — SPEDs mínimos sintéticos.
   Nunca use dados reais de cliente (§10). Para reduzir um SPED real a fixture,
   use `python -m scripts.anonimizar_sped`.

7. **Rode `pytest tests/crossref/test_cruzamento_NN_*.py -v`** até verde.

Não refatore código existente durante a adição. Correções pontuais apenas (§11).
Se notar oportunidade de melhoria adjacente, sugira separadamente ao usuário.
