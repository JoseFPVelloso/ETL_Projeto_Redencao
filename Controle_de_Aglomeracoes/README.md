# 🤖 Automatizador de Relatórios SEPE

Este aplicativo automatiza a criação do Relatório Diário Consolidado e a análise territorial por Quadras. Ele lê a base de dados padronizada, processa as informações e gera planilhas formatadas (`.xlsx`) e textos de análise (`.txt`).

---

## 📦 Instalação e Configuração Inicial
*(Faça isso apenas na primeira vez que usar o programa neste computador)*

1.  **Tenha o Python Instalado:** Certifique-se de que o Python está instalado no computador. (https://www.python.org/)
2.  **Abra o Programa:** Dê dois cliques no arquivo `EXECUTAR_RELATORIO.bat`.
3.  **Instale as Dependências:**
    * **Importante:** Conecte-se no Wi-Fi (a internet a cabo da PMSP pode bloquear instalações do Python).
    * Na interface do programa, procure a seção "Utilitários e Ajuda".
    * Clique no botão **"Instalar Dependências"**.
    * Aguarde a mensagem de sucesso no log: `✓ Sucesso!`.

Pronto! Agora o computador está preparado para gerar relatórios todos os dias.

---

## 🚀 Como Usar (Fluxo Diário)

Siga este passo a passo para garantir que os dados estejam corretos.

### 0. Preparação (Antes de abrir o programa)
1.  Abra a planilha no Google Drive chamada **"Contagem diária - Compilado"**.
2.  Copie as datas novas (que ainda não foram processadas).
3.  Cole esses dados no seu arquivo Excel local chamado **`Contagem_diaria_centro - Padronizada.xlsx`**.
4.  Salve e feche o Excel.

### 1. Passo 1: Processar a Base de Dados
1.  Abra o programa pelo `EXECUTAR_RELATORIO.bat`.
2.  Clique em **"Selecionar... (Planilha Raw)"**.
3.  Selecione o arquivo que você acabou de atualizar: **`Contagem_diaria_centro - Padronizada.xlsx`**.
4.  Clique em **"Executar Parser"**.
5.  Aguarde o log mostrar `✓ Parser concluído.`.

### 2. Passo 2: Gerar o Relatório Diário
1.  O campo "Arq. Processado" será preenchido automaticamente.
2.  **Confira as Datas:** Verifique se "Data Início" e "Data Fim" correspondem ao intervalo desejado (Padrão: últimos 4 dias).
3.  Clique em **"Gerar Relatório"**.
4.  Aguarde o log mostrar `✓ Relatório Diário concluído.`.

### 🆕 3. Passo 3: Relatório de Quadras
*Este passo é opcional, mas recomendado para análise territorial.*
1.  Após concluir o Passo 2, o botão **"Gerar Relatório por Quadras"** ficará ativo.
2.  Clique nele. O sistema irá cruzar os endereços do relatório diário com a base de mapeamento.
3.  Aguarde a mensagem `✓ Relatório de Quadras gerado com sucesso!`.

### 4. Passo 4: Resultados (Pasta "docs")
Seus relatórios foram criados na pasta `docs`. O programa gera:

* 📊 **Relatório Diário (`.xlsx`)**: Planilha formatada com contagens gerais e aglomerações destacadas.
* 🗺️ **Relatório de Quadras (`relatorio_quadras...xlsx`)**: Planilha agrupada por micro-regiões (quadras), com subtotais automáticos e filtragem de ruas sem movimento.
* 📝 **Análise Textual (`.txt`)**: Texto pronto (médias e variações) para boletins.
* ⚙️ **Logs (`.txt`)**: Arquivos técnicos para verificação de erros.

> **Dica:** Use os botões na parte inferior do programa ("Abrir Diário", "Abrir Quadras") para acessar os arquivos rapidamente.

---

## 🗺️ Sobre a Metodologia de Mapeamento

A inteligência por trás do **Passo 3 (Quadras)** reside no arquivo `Mapeamento_FINAL_editado.xlsx`. Este arquivo atua como uma matriz que converte endereços comuns em setores operacionais do Programa Redenção.

**Características Técnicas:**
* **Base GeoSampa:** A estrutura dos logradouros foi extraída e normalizada a partir da base oficial do **GeoSampa** (Mapa Digital da Cidade de São Paulo), garantindo que a nomenclatura das ruas esteja alinhada com os dados oficiais da prefeitura.
* **Intervalos Numéricos:** O mapeamento utiliza intervalos (`Num Min` e `Num Max`). Isso permite que uma mesma rua extensa (ex: Av. do Estado) seja dividida em múltiplas quadras diferentes dependendo da altura da numeração.
* **Tratamento para o Redenção:** A base passou por uma curadoria para atender à realidade do território:
    * Inclusão de nomes populares/informais usados pelas equipes de campo.
    * Ajuste de perímetros para refletir a dinâmica real de ocupação, superando divisões geográficas frias quando necessário.

---

## 🔧 Solução de Problemas

* **Erro: "Python não encontrado" ao abrir o .bat:**
    * O Python não está instalado ou não foi adicionado ao "Path" do Windows. Contate o suporte de TI ou instale via Microsoft Store.
* **Erro: "Módulo 'pandas'/'openpyxl' não encontrado":**
    * Você esqueceu de clicar em **"Instalar Dependências"** na configuração inicial.
* **Erro: "Arquivo de mapeamento não encontrado":**
    * Certifique-se de que o arquivo `Mapeamento_FINAL_editado.xlsx` está na mesma pasta do programa.

---

## ⚙️ Estrutura do Projeto (Técnico)

* `EXECUTAR_RELATORIO.bat`: Atalho para iniciar o programa.
* `main_app.py`: Interface gráfica principal.
* `logic_parser.py`: Motor de padronização de dados.
* `logic_report.py`: Motor de cálculo estatístico e geração do diário.
* `quadras_report.py`: **[NOVO]** Motor de processamento territorial e geração do relatório de quadras.
* `Mapeamento_FINAL_editado.xlsx`: Base de conhecimento de logradouros (GeoSampa + Tratamento).
* `requirements.txt`: Lista de bibliotecas Python necessárias.