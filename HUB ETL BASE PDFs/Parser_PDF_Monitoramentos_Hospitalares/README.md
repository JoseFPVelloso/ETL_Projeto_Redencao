# Parser de Monitoramentos (v2.3)

Este projeto é um aplicativo de automação ETL (Extração, Transformação e Carga) com interface gráfica, construído em Python. Sua principal função é ler três relatórios PDF distintos sobre monitoramento de leitos, extrair os dados, padronizá-los e consolidá-los em um único arquivo Excel.

##  Recursos Principais

* **Interface Gráfica:** Aplicativo de desktop amigável construído com Tkinter.
* **Extração de PDFs:** Lê tabelas de PDFs complexos usando `tabula-py`.
* **Múltiplos Parsers:** Possui módulos de parser especializados para cada tipo de relatório:
    1.  Leitos de Saúde Mental (Hospitais)
    2.  Acolhimento Terapêutico
    3.  Secretaria do Desenvolvimento Social (SEDS)
* **Seleção de Data:** Permite ao usuário selecionar a data do relatório (`dd/MM/yyyy`) através de um calendário (`tkcalendar`).
* **Padronização e Limpeza:**
    * Adiciona a coluna "Tipologia" ("Hospitais", "Acolhimento Terapêutico", "SEDS").
    * Padroniza os nomes dos equipamentos (ex: "HOSP LACAN" -> "Lacan (Grande ABC)").
    * Converte e arredonda taxas de ocupação (ex: "63,5%" -> `64`).
    * Renomeia colunas para um formato unificado (`Unidade` -> `Equipamento`).
* **Consolidação:** Junta os três relatórios em uma única tabela Excel.
* **Saída Nomenclada:** Salva o arquivo final com a data selecionada (ex: `Tabela_Combinada_Monitoramento_2025-11-03.xlsx`).

---

##  Estrutura de Pastas
Parser_PDF_Monitoramentos_Hospitalares/
│
├── PDFS/
│   └── (Coloque seus PDFs de entrada aqui)
│
├── Tabelas/
│   └── (O relatório final em Excel será salvo aqui)
│
├── src/
│   │
│   ├── parsers/
│   │   ├── parser_Leitos_saude_mental.py
│   │   ├── parser_Acolhimento_terapeutico.py
│   │   ├── parser_Secretaria_do_desenvolvimento_social.py
│   │   └── __init__.py
│   │
│   ├── app.py                     (Arquivo principal, executa a UI)
│   ├── gerador_relatorio.py       (Padroniza e consolida os dados)
│   └── __init__.py
│
└── README.md                    (Este arquivo)


### Descrição dos Componentes

#### Pastas

* `/PDFS`: Pasta de **entrada**. Você deve colocar os 3 arquivos PDF a serem processados aqui.
* `/Tabelas`: Pasta de **saída**. O relatório Excel consolidado será salvo aqui.

#### Arquivos Python (`src/`)

* `app.py`: **(O Orquestrador)**
    * Cria e gerencia toda a interface gráfica (GUI) usando Tkinter.
    * Contém o seletor de data (`tkcalendar`).
    * Orquestra o processo: recebe os caminhos dos arquivos, chama os parsers e, em seguida, chama o `gerador_relatorio`.
    * Salva o arquivo Excel final na pasta `/Tabelas`.

* `pardonizador.py`: **(O Cérebro da Transformação)**
    * Recebe os dados brutos (DataFrames) de todos os parsers.
    * **Padroniza** os dados:
        * Adiciona a coluna "Tipologia" ("Hospitais", "Acolhimento Terapêutico", "SEDS").
        * Adiciona a coluna "Data" (recebida do `app.py`).
        * Limpa e formata a "Taxa de ocupação" (arredonda para inteiro).
        * Renomeia colunas para o formato final (`Unidade` -> `Equipamento`).
        * Aplica o mapeamento de nomes (DE-PARA) para padronizar os nomes dos equipamentos.
    * Consolida os 3 DataFrames transformados em um único DataFrame final.

* `parsers/parser_...py`:
    * Cada parser é especializado em extrair dados de um tipo de PDF.
    * Eles filtram os dados brutos (ex: "HUB" ou "FASE COMUNITARIA") e os retornam ao `app.py`.

---

## Instalação e Requisitos

Este projeto requer Python 3 e algumas bibliotecas.

### 1. Pré-requisito: Python
* Você pode baixar o Python [aqui](https://www.python.org/).

### 2. Pré-requisito: Java

A biblioteca `tabula-py` (que lê os PDFs) é um *wrapper* para uma ferramenta em Java. Você **precisa ter o Java instalado** no seu computador para que ela funcione.

* Você pode baixar o Java [aqui](https://www.java.com/pt-BR/download/).

### 3. Bibliotecas Python 

Clique com botão direito na pasta do projeto, selecione "Abrir no terminal", ao abrir o terminal digite:
pip install -r requirements.txt

ou apenas digite/cole no terminal:

pip install pandas tabula-py openpyxl tkcalendar tkinter

---

### COMO USAR ###

Prepare os Arquivos: Coloque os 3 arquivos PDF (Leitos, Acolhimento e SEDS) dentro da pasta /PDFS/.
*ELE SÓ RODA SE TIVER OS 3 ARQUIVOS*

Execute a Aplicação: Clique no atalho conversor na primeira pasta, ou abra o /src e clique em app.py.
você tambem pode abrir seu terminal na pasta /src com botão direito e execute o comando "python app.py".


Na Interface:

Clique em "Carregar..." para cada um dos 3 tipos de relatório.

Selecione a data correta do relatório no calendário.

Clique no botão "Processar e Juntar (3 Arquivos)".

Pronto! O log de processamento será exibido na janela. Ao final, o arquivo Tabela_Combinada_Monitoramento_AAAA-MM-DD.xlsx aparecerá na pasta Tabelas.