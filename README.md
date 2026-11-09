# Painel de duplicidades de descontos

Painel em HTML que lê a exportação de descontos e identifica os descontos registrados mais de uma vez na mesma matrícula, nas superintendências Interior e Leste.

## Como usar

1. Abra o painel no navegador (no Chrome ou no Edge a pasta fica memorizada).
2. Clique em **📁 Conectar pasta** e escolha a pasta **Painel Análise de Descontos**, a cópia do OneDrive sincronizada no seu computador.
3. Aguarde a leitura. A base fica guardada no navegador e abre sozinha nas próximas vezes.
4. Para atualizar, troque o arquivo na pasta e clique em **↻ Atualizar**. Em outros navegadores, escolha a pasta de novo.

## Estrutura da pasta

```
Painel Análise de Descontos/
  Descontos/   exportação de descontos (.xlsx); vale só o arquivo mais recente
  Cadastro/    um arquivo por superintendência (.xlsx); todos são lidos
```

**Descontos:** colunas EMP_CODIGO, DAT_ACESSO, DAT_ACESSO_HORA, REFERENCIA, ANO_LOG, NUM_LOG, ZONA_LIGACAO, NUM_LIGACAO, COD_USUARIO, VALOR_A_VISTA, DESCONTO, VALOR_TOTAL e PCT_DESCONTO.

**Cadastro:** precisa de NUM_LIGACAO e SUPERINTENDENCIA. Usa também CHAVE_LIGACAO, CIDADE e NOM_CLIENTE. LAGOS aparece no painel como **Interior**.

## Regras, em resumo

- **Duplicidade:** mesma matrícula, mesmo mês de referência e mesmo valor de desconto, lançado duas ou mais vezes.
- **Nível 1:** o valor total também é igual em todos os lançamentos. **Nível 2:** o valor total muda.
- **Lançamento válido:** o mais recente. Os anteriores são repetições.
- **Alerta entre meses:** mesmo desconto na mesma matrícula em meses diferentes.
- **A verificar:** descontos diferentes na mesma matrícula e mês.

As regras completas ficam na aba **Dados** do painel.

## Privacidade

Os arquivos são lidos só no seu computador. Nenhum dado é enviado para a internet nem para este repositório. Nunca suba arquivos .xlsx ou .csv para cá (o `.gitignore` já bloqueia).

## Conferência dos números

```bash
python tests/conferir_totais.py "Painel Análise de Descontos"          # mesmos números do Resumo
python tests/conferir_totais.py "Painel Análise de Descontos" --sup Interior
```
