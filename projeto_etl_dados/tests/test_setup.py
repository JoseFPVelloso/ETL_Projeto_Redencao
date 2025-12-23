"""
Script para testar se o ambiente está configurado corretamente
"""

def test_imports():
    """Testa se todas as bibliotecas foram instaladas"""
    try:
        import pandas as pd
        print("✓ pandas instalado com sucesso")
        
        import openpyxl
        print("✓ openpyxl instalado com sucesso")
        
        import sqlalchemy
        print("✓ sqlalchemy instalado com sucesso")
        
        import pydantic
        print("✓ pydantic instalado com sucesso")
        
        import psycopg2
        print("✓ psycopg2 instalado com sucesso")
        
        import geopy
        print("✓ geopy instalado com sucesso")
        
        from dotenv import load_dotenv
        print("✓ python-dotenv instalado com sucesso")
        
        import pytest
        print("✓ pytest instalado com sucesso")
        
        print("\n✅ Todas as bibliotecas foram instaladas corretamente!")
        print(f"✅ Versão do pandas: {pd.__version__}")
        print(f"✅ Versão do sqlalchemy: {sqlalchemy.__version__}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Erro ao importar biblioteca: {e}")
        return False

if __name__ == "__main__":
    test_imports()