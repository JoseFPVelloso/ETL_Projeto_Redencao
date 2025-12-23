-- ============================================================================
-- Schema do Banco de Dados - Projeto ETL
-- Tabela: contagem_diaria
-- Descrição: Contagens diárias nas ruas de Santa Cecília, Campos Elíseos e 
--            Santa Ifigênia com endereços parseados
-- ============================================================================

-- Criar tabela principal
CREATE TABLE IF NOT EXISTS contagem_diaria (
    -- Chave primária
    id SERIAL PRIMARY KEY,
    
    -- Campos originais da planilha
    equipe VARCHAR(100) NOT NULL,
    data DATE NOT NULL,
    periodo VARCHAR(20) NOT NULL CHECK (periodo IN ('05h - Madrugada', '10h - Manhã', '15h - Tarde', '20h - Noite')),
    qtd_pessoas INTEGER NOT NULL CHECK (qtd_pessoas >= 0),
    
    -- Endereço original (antes do parsing)
    logradouro_original TEXT NOT NULL,
    
    -- Campos de endereço parseados (4 campos)
    tipo_logradouro VARCHAR(50),
    nome_logradouro VARCHAR(200),
    numero_logradouro VARCHAR(20),
    complemento_logradouro TEXT,
    
    -- Metadados
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para melhorar performance das consultas
CREATE INDEX IF NOT EXISTS idx_contagem_data ON contagem_diaria(data);
CREATE INDEX IF NOT EXISTS idx_contagem_equipe ON contagem_diaria(equipe);
CREATE INDEX IF NOT EXISTS idx_contagem_periodo ON contagem_diaria(periodo);
CREATE INDEX IF NOT EXISTS idx_contagem_tipo_logradouro ON contagem_diaria(tipo_logradouro);
CREATE INDEX IF NOT EXISTS idx_contagem_nome_logradouro ON contagem_diaria(nome_logradouro);

-- Criar índice composto para consultas comuns
CREATE INDEX IF NOT EXISTS idx_contagem_data_periodo ON contagem_diaria(data, periodo);

-- Comentários nas colunas (documentação)
COMMENT ON TABLE contagem_diaria IS 'Contagens diárias de pessoas nas ruas de Santa Cecília, Campos Elíseos e Santa Ifigênia';
COMMENT ON COLUMN contagem_diaria.id IS 'Identificador único do registro';
COMMENT ON COLUMN contagem_diaria.equipe IS 'Nome da equipe que realizou a contagem';
COMMENT ON COLUMN contagem_diaria.data IS 'Data em que a contagem foi realizada';
COMMENT ON COLUMN contagem_diaria.periodo IS 'Período do dia: Madrugada, Manhã, Tarde ou Noite';
COMMENT ON COLUMN contagem_diaria.qtd_pessoas IS 'Quantidade de pessoas contadas no local';
COMMENT ON COLUMN contagem_diaria.logradouro_original IS 'Endereço original conforme registrado na planilha';
COMMENT ON COLUMN contagem_diaria.tipo_logradouro IS 'Tipo do logradouro (Rua, Avenida, Alameda, etc)';
COMMENT ON COLUMN contagem_diaria.nome_logradouro IS 'Nome do logradouro sem o tipo';
COMMENT ON COLUMN contagem_diaria.numero_logradouro IS 'Número do logradouro';
COMMENT ON COLUMN contagem_diaria.complemento_logradouro IS 'Complemento do endereço (quando houver)';
COMMENT ON COLUMN contagem_diaria.created_at IS 'Data e hora de criação do registro';
COMMENT ON COLUMN contagem_diaria.updated_at IS 'Data e hora da última atualização';

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_contagem_diaria_updated_at 
    BEFORE UPDATE ON contagem_diaria 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- View para consultas simplificadas (endereço completo montado)
CREATE OR REPLACE VIEW vw_contagem_completa AS
SELECT 
    id,
    equipe,
    data,
    periodo,
    qtd_pessoas,
    logradouro_original,
    CONCAT_WS(' ', tipo_logradouro, nome_logradouro, numero_logradouro, complemento_logradouro) AS endereco_parseado,
    tipo_logradouro,
    nome_logradouro,
    numero_logradouro,
    complemento_logradouro,
    created_at,
    updated_at
FROM contagem_diaria;

COMMENT ON VIEW vw_contagem_completa IS 'View com endereço parseado montado em um único campo';

-- ============================================================================
-- Queries úteis para análises
-- ============================================================================

-- Total de pessoas por logradouro (top 10)
-- SELECT 
--     tipo_logradouro,
--     nome_logradouro,
--     numero_logradouro,
--     SUM(qtd_pessoas) as total_pessoas,
--     COUNT(*) as total_contagens
-- FROM contagem_diaria
-- GROUP BY tipo_logradouro, nome_logradouro, numero_logradouro
-- ORDER BY total_pessoas DESC
-- LIMIT 10;

-- Total de pessoas por período
-- SELECT 
--     periodo,
--     SUM(qtd_pessoas) as total_pessoas,
--     COUNT(*) as total_contagens,
--     ROUND(AVG(qtd_pessoas), 2) as media_pessoas
-- FROM contagem_diaria
-- GROUP BY periodo
-- ORDER BY total_pessoas DESC;

-- Total de pessoas por equipe
-- SELECT 
--     equipe,
--     SUM(qtd_pessoas) as total_pessoas,
--     COUNT(*) as total_contagens
-- FROM contagem_diaria
-- GROUP BY equipe
-- ORDER BY total_pessoas DESC;

-- Evolução diária das contagens
-- SELECT 
--     data,
--     SUM(qtd_pessoas) as total_pessoas,
--     COUNT(*) as total_contagens
-- FROM contagem_diaria
-- GROUP BY data
-- ORDER BY data;