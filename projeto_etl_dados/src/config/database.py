"""
Configuração de conexão com PostgreSQL
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do banco
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'etl_dados')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')

# String de conexão
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Engine do SQLAlchemy
engine = create_engine(DATABASE_URL)

# Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

def get_db():
    """Retorna uma sessão do banco"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def test_connection():
    """Testa a conexão com o banco"""
    try:
        connection = engine.connect()
        print("✓ Conexão com PostgreSQL estabelecida com sucesso!")
        connection.close()
        return True
    except Exception as e:
        print(f"✗ Erro ao conectar com PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    test_connection()