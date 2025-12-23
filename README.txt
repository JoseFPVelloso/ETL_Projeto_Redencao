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

### 📂 projeto_etl_dados (Legado)
**Função:** Biblioteca de rotinas antigas e referência.
**Descrição:** Contém o código-fonte desenvolvido pela gestão técnica anterior. Inclui diversos parsers e scripts de geração de gráficos.
* *Obs:* Este diretório serve como base de conhecimento. O projeto `Controle_de_Aglomeracoes`, por exemplo, é uma versão refatorada e aprimorada (com correção de casas decimais e lógica de logradouros) de scripts presentes aqui.

---
## Tecnologias Utilizadas
* Python (Pandas, Tabula, etc.)
* Excel / CSV