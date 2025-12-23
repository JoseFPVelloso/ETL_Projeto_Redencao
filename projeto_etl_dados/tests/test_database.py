"""
Script para testar conexão e operações básicas no PostgreSQL
"""

from sqlalchemy import text
from config.database import engine, test_connection

def test_basic_operations():
    """Testa operações básicas no banco"""
    
    # Testar conexão
    print("1. Testando conexão...")
    if not test_connection():
        return False
    
    # Criar tabela de teste
    print("\n2. Criando tabela de teste...")
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS teste_python (
                id SERIAL PRIMARY KEY,
                mensagem VARCHAR(200),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()
        print("✓ Tabela criada com sucesso!")
    
    # Inserir dados
    print("\n3. Inserindo dados...")
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO teste_python (mensagem) 
            VALUES ('Conexão Python + PostgreSQL funcionando!')
        """))
        conn.commit()
        print("✓ Dados inseridos com sucesso!")
    
    # Consultar dados
    print("\n4. Consultando dados...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM teste_python"))
        rows = result.fetchall()
        print(f"✓ {len(rows)} registro(s) encontrado(s):")
        for row in rows:
            print(f"  - ID: {row[0]}, Mensagem: {row[1]}, Criado em: {row[2]}")
    
    print("\n✅ Todos os testes passaram com sucesso!")
    return True

if __name__ == "__main__":
    test_basic_operations()