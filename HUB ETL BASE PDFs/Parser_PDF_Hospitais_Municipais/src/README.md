# Conversor de Leitos Hospitalares

Este projeto é um script em Python para automatizar a extração de dados tabulados de relatórios em PDF sobre leitos hospitalares e consolidá-los em um único arquivo Excel, utilizando uma interface gráfica amigável.

## Funcionalidades

* Interface Gráfica Possui uma interface fácil de usar para selecionar arquivos e iniciar o processamento.
* Lê arquivos `.pdf` de uma pasta de entrada.
* Extrai tabelas de páginas específicas (configurável).
* Limpa e renomeia colunas.
* Mapeia e corrige nomes de estabelecimentos.
* Salva o resultado consolidado em um arquivo `.xlsx` em uma pasta de saída.

---

## Pré-requisitos

Antes de rodar o projeto, garanta que você tenha os seguintes softwares instalados:

1.  **Python 3.8** ou superior.
    * [baixe em https://www.python.org/]
2.  **Java (JDK ou JRE)** 8 ou superior.
    * A biblioteca `tabula-py` depende do Java para funcionar.
    * Você pode baixá-lo em [java.com](https://www.java.com/pt-BR/download/).
    * Para verificar se o Java está instalado, abra seu terminal (CMD) e digite: `java -version`.

---

## Instalação

1.  Baixe (ou clone) os arquivos para uma pasta no seu computador.
2.  Abra um terminal (CMD ou PowerShell) *DENTRO* da pasta do projeto. (Clique direito na pasta > Abrir no terminal)
3.  Instale as bibliotecas Python necessárias colando o seguinte comando:
    pip install -r requirements.txt


---

## Como Usar (Com Interface Gráfica)

1.  Coloque o(s) PDF(s) que deseja transformar na pasta `PDF/`.
2.  Execute o programa principal: main.py
3.  Uma janela será aberta:
    * **Passo 1:** Selecione o PDF de entrada no menu "Arquivo PDF de Entrada:". (Se você adicionar um novo PDF na pasta, clique em "Atualizar Lista").
    * **Passo 2:** O nome de saída e a data serão preenchidos automaticamente. Ajuste se necessário.
    * **Passo 3:** Clique no botão "Processar Arquivo".
4.  Aguarde o processamento.
5.  Ao final, uma mensagem de "Sucesso" aparecerá, e o seu arquivo Excel estará na pasta `Tabelas/`.

---

## Estrutura do Projeto

    PARSER_PDF_LEITOSHOSPITALARES/
    ├── PDF/
    │   └── (Aqui é onde os PDFs serão recebidos)
    │
    ├── Tabelas/
    │   └── (Aqui é onde os Excels serão salvos)
    │
    ├── config.py             # Arquivo 1: Constantes e Mapeamentos
    ├── etl_core.py           # Arquivo 2: Lógica de Processamento (Pandas)
    ├── main.py                # Arquivo 3: Programa base (Interface Gráfica)
    ├── requirements.txt      # Lista de dependências
    └── README.txt            # Este arquivo

---

## Estrutura de Dados do PDF

O script foi desenvolvido para extrair tabelas de PDFs que sigam a estrutura mostrada abaixo. Se o layout do PDF for muito diferente, podem ser necessários ajustes no código (principalmente no `etl_core.py`).
pdf de exemplo se encontra na pasta do programa com nome de "image_8aea22.png"
