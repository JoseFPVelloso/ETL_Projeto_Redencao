# Automações e ETL - Programa Redenção

Este repositório centraliza rotinas de automação, scripts de ETL (Extract, Transform, Load) e ferramentas de análise de dados desenvolvidas para o Programa Redenção.

> **Nota:** Cada subdiretório contém seu próprio README com instruções específicas de execução.

## Estrutura do Projeto

### 📂 HUB ETL BASE PDFs
**Função:** Extração de dados de relatórios diários (PDF).
**Descrição:** Automatiza a leitura de PDFs contendo "Dados Estaduais" e "Leitos Hospitalares". O script converte estes dados não estruturados em planilhas formatadas, otimizando a inserção posterior no banco de dados.


### 📂 Controle_de_Aglomeracoes
**Função:** Gestão de relatórios de contagem e geolocalização.
**Descrição:** Automatiza a criação de relatórios diários e planilhas de aglomerações.
* Processa planilhas de contagem padronizadas.
* Realiza a divisão de dados por quadras e logradouros.
* Gera outputs prontos para análise.


### 📂 Parser_EXCEL_EquipamentosdeAcolhimento
**Função:** Tratamento de dados semanais.
**Descrição:** Script parser dedicado à extração e normalização de dados recebidos semanalmente via tabelas estaduais referentes aos equipamentos de acolhimento.


### 📂 GTSEGURANCA_gerador_graficos
**Função:** Rotinas de criação de gráficos para o evento semanal do GT de Segurança.
**Descrição:** Script para gerar relatórios padronizados em Excel de forma automatizada. Utiliza como base as planilhas:
* "CONTAGEM 2026 - CnR" (aba "Base de Contagem")
* "Contagem SMS - Compilado_2026" (versão padronizada da "Contagem SMS_2026")

> **OBS:** Utilize como referência alguns relatórios antigos do GT para confecção de certos gráficos.
> **OBS²:** Para mais informações, acesse o arquivo `README.txt` presente nesta pasta.


### 📂 Projetos do Time
**Descrição:** Pasta contendo scripts focalizados em rotinas específicas de integrantes do time.

* **📂 Luiz**
    * **Função:** Leitura de PDFs de altas hospitalares (Instituto Bairral e Bezerra de Menezes).
    * **Descrição:** Script com interface gráfica (UI) simples e intuitiva, que converte os valores presentes nos PDFs em planilhas estruturadas para agregação.


## 🛠 Tecnologias Utilizadas
* **Linguagem:** Python 3.x
* **Bibliotecas Principais:** Pandas, Tabula-py, Tkinter (UI), OpenPyXL.
* **Formatos:** Excel (.xlsx), CSV, PDF.