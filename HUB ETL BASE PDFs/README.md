# Hub de Aplicativos ETL

Este projeto é um lançador central ("Hub") com interface gráfica, construído em Python e Tkinter. Ele serve como um portal de acesso rápido para executar e gerenciar dois aplicativos de automação ETL distintos:

1.  **Parser de Monitoramentos Hospitalares**
2.  **Parser de Hospitais Municipais**

## Funcionalidades do Hub

* **Interface Gráfica Única:** Um painel de controle simples para iniciar qualquer um dos aplicativos.
* **Execução Direta:** Botões "EXECUTAR APLICAÇÃO" para iniciar cada parser em seu próprio processo.
* **Atalhos de Acesso:** Para cada projeto, o Hub fornece botões para abrir diretamente:
    * O arquivo `README` (documentação).
    * A pasta `PDFs`/`PDF` (pasta de entrada).
    * A pasta `Tabelas` (pasta de saída/relatórios).

## Estrutura de Pastas Esperada

Para que o Hub funcione, ele deve estar na pasta raiz, e os projetos devem estar em subpastas, da seguinte forma:

```
HUB ETL/
│
├── HUB.py                      <-- (O script deste lançador)
├── requirements.txt            <-- (Este arquivo de requisitos)
├── README.md                   <-- (Este arquivo de documentação)
│
├── Parser_PDF_Hospitais_Municipais/
│   ├── main.py
│   ├── PDF/
│   ├── Tabelas/
│   └── ...
│
└── Parser_PDF_Monitoramentos_Hospitalares/
    ├── src/
    │   └── app.py
    ├── PDFs/
    ├── Tabelas/
    └── ...
```

## Pré-requisitos

Antes de rodar o projeto, garanta que você tenha os seguintes softwares instalados:

1.  [cite_start]**Python 3.8** ou superior[cite: 6].
2.  [cite_start]**Java (JDK ou JRE) 8** ou superior.
    * A biblioteca `tabula-py`, usada por ambos os parsers, depende do Java para funcionar.

## Instalação

1.  Clique com botão direito na pasta inicial e abra um terminal (CMD ou PowerShell).
2.  Instale **todas** as bibliotecas Python necessárias (para o Hub e ambos os projetos) com um único comando:

    pip install -r requirements.txt


## Como Usar

1.  Certifique-se de que os pré-requisitos (Python e Java) e as bibliotecas estão instalados.
2.  Clique no HUB.py ou execute o script do Hub no terminal da pasta:

    python HUB.py

3.  A janela do "Hub de Aplicativos ETL" será aberta.
4.  Utilize os botões para executar o aplicativo desejado ou para abrir as pastas de trabalho (PDFs, Relatórios) e arquivos README.