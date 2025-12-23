# ⚙️ Processador de Relatórios - Equipamentos Estaduais

Este é um aplicativo de automação com interface gráfica (GUI) desenvolvido em Python e Tkinter.

## 🎯 Objetivo

O objetivo principal deste aplicativo é **converter o relatório mensal bruto da "Ocupação das Vagas em Equipamentos de Acolhimento Estaduais"** em uma tabela de dados tratada, limpa e padronizada.

O arquivo final gerado por este parser é formatado especificamente para ser **copiado e colado** diretamente na planilha principal de **"Dados Estaduais"** utilizada pela equipe do **Projeto Redenção**.

## 🏗️ Estrutura do Projeto

O projeto é dividido em dois arquivos principais para separar a lógica da interface:

1.  **`parser_equipamentosEstaduais.py` (O "Motor")**
    * Contém toda a lógica de processamento de dados.
    * Utiliza a biblioteca `pandas` para ler, limpar e transformar a tabela.
    * É importado pelo `app.py`.

2.  **`app.py` (A Interface Gráfica)**
    * Contém todo o código da interface `tkinter`.
    * Permite que o usuário selecione o arquivo de entrada, defina o nome do arquivo de saída e inicie o processamento.
    * Chama a função "motor" do outro arquivo para fazer o trabalho.

3.  **Pasta `Tabelas Tratadas/`**
    * Esta pasta é **criada automaticamente** pelo `app.py` quando você processa um arquivo pela primeira vez.
    * Todos os relatórios tratados são salvos dentro dela.

## 🚀 Instalação

Siga estes passos para configurar e executar o aplicativo no seu computador.

**Pré-requisito:** Você precisa ter o [Python 3](https://www.python.org/downloads/) instalado.

### Passo 1: Obter os arquivos
Certifique-se de que os arquivos `app.py`, `parser_equipamentosEstaduais.py` e `requirements.txt` estejam na mesma pasta.

### Passo 2: (Opcional) Clique com botão direito na PASTA DO PROJETO e selecione "Abrir com terminal"


### Passo 3: Instalar as Dependências
Dentro do terminal cole o comando abaixo para instalar as bibliotecas necessárias:

pip install -r requirements.txt

Isso instalará o `pandas` e o `openpyxl`.

## 📈 Como Usar

Depois de instalar, usar o aplicativo é simples:

1.  Certifique-se de que seu ambiente virtual esteja ativado (se você criou um).
2.  Execute o arquivo `app.py` com comando do terminal ou clicando nele:
   
    python app.py
    

3.  A interface gráfica do aplicativo será aberta.

4.  **Selecionar Arquivo:** Clique no botão **"Selecionar..."** e navegue até o arquivo Excel (`.xlsx`) do relatório estadual que você deseja processar.
    * **IMPORTANTE:** O script espera que o seu arquivo Excel tenha os dados do resumo na **segunda aba (planilha)**.

5.  **Renomear Saída:** No campo **"Nome da Saída"**, digite o nome que você deseja para o arquivo final (ex: `Resumo_Novembro_2025.xlsx`).

6.  **Processar:** Clique no botão **"Processar Arquivo"**.

7.  **Pronto!** O aplicativo irá ler a segunda aba do arquivo, limpá-la, e salvar o resultado na pasta `Tabelas Tratadas/`. Uma mensagem de sucesso aparecerá informando o local exato do arquivo.

## 🤖 O que o Parser Faz Automaticamente

Este "motor" foi programado para realizar as seguintes tarefas de limpeza e formatação:

* Lê a **segunda aba** do arquivo Excel.
* Remove linhas de `TOTAL GERAL` e linhas completamente em branco.
* Preenche a data de referência para todas as linhas.
* Converte os nomes das tipologias para o formato normal (ex: "CASAS DE PASSAGEM" vira "Casas de passagem").
* Formata a data para o padrão `DD/MM/YYYY`.
* Calcula a **Taxa de Ocupação** e arredonda para o número inteiro mais próximo (sem casas decimais).
* Reorganiza as colunas para a ordem correta de colagem:
    1.  `Tipologia`
    2.  `Equipamento`
    3.  `Data`
    4.  `Leitos Instalados`
    5.  `Leitos Operacionais`
    6.  `Ocupação Atual`
    7.  `Taxa de ocupação`
    8.  `Leitos Disponiveis`