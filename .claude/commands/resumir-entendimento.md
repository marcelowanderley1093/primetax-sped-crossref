---
description: Kick-off de sessão — resumir o que foi pedido e as restrições aplicáveis antes de escrever código.
---

O CLAUDE.md §11 exige que, em qualquer sessão nova ou pedido ambíguo, a
primeira resposta seja **um resumo do entendimento**, não código. Use este
comando para forçar explicitamente esse rito.

Estrutura da resposta (nessa ordem, sem introdução):

1. **O que entendi do pedido** — uma a três frases objetivas reformulando o
   que o operador quer. Sem perguntas retóricas ou paráfrases.

2. **Princípios não-negociáveis aplicáveis** (§4) — liste apenas os princípios
   que o pedido toca, justificando por quê. Exemplos:
   - Princípio 1 (rastreabilidade absoluta) se o pedido gera saída para o cliente.
   - Princípio 2 (não alterar SPED original) se toca arquivos em `data/input/`.
   - Princípio 3 (par positivo + negativo) se adiciona/modifica cruzamento.
   - Princípio 4 (base legal citada) se adiciona/modifica regra em `src/rules/`.
   - Princípio 5 (português em nomes fiscais) se cria campo ou função fiscal.
   - Princípio 6 (proibido hardcoding de alíquota/tabela) se toca cálculo.
   - Princípio 7 (privacidade) se toca `data/`.

3. **Decisões arquiteturais relevantes** — cite, se aplicáveis:
   - §15: persistência longitudinal por CNPJ × AC.
   - §16: reconciliação de plano de contas (modos integra/suspeita/ausente).
   - §18: disponibilidade de SPEDs (importada/pendente/estruturalmente_ausente).

4. **Fora do escopo da v1** (§13) — se o pedido sugerir um item da lista
   (Bloco I, CR-24 e-CAC, Bloco K/W ECF, DEREX, Razão Auxiliar ECD),
   pare e peça confirmação explícita de reversão da decisão, antes de
   qualquer código.

5. **Ambiguidades ou riscos** — se algo não está claro ou pode ter múltiplas
   interpretações, liste como pergunta fechada (sim/não, A/B). Não invente
   a resposta.

6. **Próximo passo proposto** — uma frase com o primeiro passo concreto que
   você executaria após aprovação. Sem escrever código ainda.

Termine a resposta esperando confirmação. Só escreva código após o operador
aprovar ou refinar o entendimento.
