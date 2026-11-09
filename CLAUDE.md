# Painel de duplicidades de descontos

Contexto para continuar o desenvolvimento no Claude Code. Este arquivo resume tudo o que foi decidido até agora.

## Regras de trabalho

- **Pergunte antes de executar.** Quando houver dúvida sobre regra de negócio, layout ou formato, faça as perguntas necessárias antes de mudar o código. O dono do painel prefere responder perguntas a receber algo diferente do que pediu.
- **Valide os números.** Confira toda mudança de cálculo com `tests/conferir_totais.py`, que recalcula tudo em Python de forma independente.
- **Mantenha um arquivo só.** O painel é um único `index.html`, sem build e sem dependências além das Google Fonts.
- **Escreva em português do Brasil.** Os textos da interface e os comentários do código ficam em português.
- **Mantenha a aba Dados em dia.** Toda mudança de regra atualiza `renderDados()` na mesma versão.
- **Aumente a versão a cada atualização.** A constante `VERSAO_SITE` aparece no cabeçalho.
- **Mesmo padrão visual do painel de economias de esgoto** (repositório economias), que copia o painel de faturamento: cores, fontes, cabeçalho, filtros, faixa de 8 indicadores, gráfico com tabela alinhada, CSV com `;`.

## Objetivo

Identificar descontos registrados mais de uma vez na mesma matrícula. Cada linha do arquivo é um registro de negociação/desconto (um NUM_LOG); o painel mostra o que foi registrado mais de uma vez, mas se refere ao mesmo desconto. Há casos com dezenas de repetições do mesmo desconto, em poucos minutos.

Publicação: GitHub Pages, repositório novo, branch `main`, pasta raiz.

## Dados de entrada

Pasta **Painel Análise de Descontos** no OneDrive, com as subpastas **Descontos** e **Cadastro**. A pasta é escolhida no painel; ela não vai para o repositório.

- **Descontos:** o painel usa só o .xlsx mais recente (`lastModified`) que tenha as colunas obrigatórias (`OBRIG_DESC`). Um mais recente com outro layout é pulado e listado na aba Dados. O arquivo real (`desconto (23).xlsx`, aba Query1) tem 43.683 linhas, de out/24 a nov/26, da empresa toda.
- **Cadastro:** todos os .xlsx são lidos. `Cadastro_Interior.xlsx` (aba Planilha1, 83.984 matrículas, SUPERINTENDENCIA = LAGOS) e `Cadastro_Leste.xlsx` (aba Query1, 241.541 matrículas, LESTE). 24 colunas, uma linha por matrícula. A superintendência vem da coluna, não do nome do arquivo. **LAGOS = Interior** (pedido do usuário: chamar sempre de Interior).
- **Cruzamento:** CHAVE_LIGACAO do cadastro (`56-100607450`) = `EMP_CODIGO-NUM_LIGACAO` dos descontos. Os prefixos 56 e 57 são da matrícula (57 = "RIO DE JANEIRO - A", no Leste). O worker guarda do cadastro só as matrículas que aparecem nos descontos.
- **Fora das superintendências:** 84% dos lançamentos (36.097, R$ 150,9 mi) são de outras superintendências. Decisão do usuário: continuam lidos, mas ignorados por enquanto; só aparecem na aba Dados (quantidade e o que dariam pelas mesmas regras).
- **Empresa (EMP_CODIGO):** o usuário não sabe o nome dos códigos 3, 56 e 57; fica só no CSV.

## Regras de negócio (definidas com o usuário)

1. Fora da análise: DESCONTO ou VALOR_TOTAL sem número (no arquivo real vêm como texto "NULL"), sem REFERENCIA, NUM_LIGACAO 0, desconto = 0.
2. **Grupo de duplicidade:** mesma NUM_LIGACAO + REFERENCIA + DESCONTO (ao centavo), 2+ lançamentos.
3. **Nível 1:** mesmo VALOR_TOTAL em todos. **Nível 2:** totais diferentes; grupo com totais misturados fica inteiro no nível 2. O usuário pediu os dois níveis separados.
4. **Válido = mais recente** (DAT_ACESSO + DAT_ACESSO_HORA; empate → maior NUM_LOG). Os outros são repetições. Valor em duplicidade = (vezes − 1) × desconto.
5. **Alerta entre meses** (separado, não soma): mesma matrícula + mesmo DESCONTO em 2+ referências, sem olhar o total (decisão do usuário).
6. **A verificar:** mesma matrícula + referência com 2+ descontos diferentes (um desconto por fatura em vez de somar). Não é duplicidade; só se confirma entrando na matrícula.
7. **Filtros** (todos com seleção múltipla): Superintendência, Cidade (lista depende das superintendências marcadas), Zona, Usuário, Mês de referência. Local pela matrícula; mês pela referência do grupo; usuário: grupo entra inteiro se tiver algum lançamento do usuário.
8. **Por usuário:** repetições e valor ficam com o usuário do lançamento que é repetição.

## Arquitetura (index.html)

- **Worker inline** (`<script type="text/plain" id="worker-src">`): leitor de .xlsx próprio, copiado do painel de economias (zip com zip64, `DecompressionStream`, XML em fluxo por `</row>`). `lerDescontos()` devolve typed arrays por lançamento (`emp, mat, zona, ref, dt, log, ano, usr, vav, desc, tot, pct, ok`); `dt` em ms com o horário "de parede" (UTC, sem fuso). `lerCadastro()` devolve `keys, nomes, sup, cid` só das matrículas com desconto.
- **Página:** `separa()` divide os arquivos pelas subpastas; `derive()` calcula uma vez os grupos sobre a base inteira (`dups`, `al`, `ver`, `recRep`, `recG`); os filtros só selecionam grupos (`okDup`, `okAl`, `okVer`, `okRec`). `calcula()` monta o Resumo.
- **Armazenamento:** IndexedDB `painel-duplicidade-descontos`, store `dados`, chaves `atual` (resultado do worker, `formato: 1`) e `pasta` (handle da File System Access API). Sem `showDirectoryPicker` (Firefox/Safari), usa `<input webkitdirectory>`.

## Layout

- **Resumo:** 8 indicadores (lançamentos analisados, matrículas com duplicidade, lançamentos repetidos, valor em duplicidade, nível 1, nível 2, alerta entre meses, a verificar); gráfico por mês de referência com nível 1 (marinho) e nível 2 (azul) empilhados, seletor Lançamentos / Matrículas / Valor, valores exatos em cima, tabela alinhada embaixo com a coluna de rótulos fixa e rolagem que abre nos meses mais recentes; tabela por usuário (pedido do usuário), ordenável, com o número de repetições levando para a lista filtrada.
- **Duplicidades:** seletor Duplicidades / Alerta entre meses / A verificar; busca, nível, ordenação; uma linha por grupo, que abre os lançamentos; 100 por página; CSV com uma linha por lançamento.
- **Dados:** arquivos lidos, lançamentos considerados e as regras numeradas.

## Valores de referência (arquivos reais de 09/11/2026)

Base: 6.932 lançamentos, R$ 16.071.966,08, 5.304 matrículas. 378 matrículas com duplicidade; 594 lançamentos repetidos em 405 grupos; R$ 2.253.788,39. Nível 1: 311 grupos, 446 repetições, R$ 1.853.745,68. Nível 2: 94, 148, R$ 400.042,71. Alerta: 47 grupos, 46 matrículas. A verificar: 464 matrículas, 474 casos. Interior: 112 matrículas, 122 grupos (92 + 30), R$ 558.740,84, alerta 10, a verificar 130.

## Como validar uma mudança

```bash
python tests/conferir_totais.py "Painel Análise de Descontos"
python tests/conferir_totais.py "Painel Análise de Descontos" --sup Interior
# abra o index.html, conecte a mesma pasta e compare com o Resumo
```

Nunca suba arquivos `.xlsx` ou `.csv` para o repositório: os dados têm nomes de clientes.
