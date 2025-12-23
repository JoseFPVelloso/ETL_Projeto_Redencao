"""
Modelos SQLAlchemy para as tabelas do banco
"""
from sqlalchemy import Column, Integer, String, Date, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from config.database import Base


class ContagemDiaria(Base):
    __tablename__ = 'contagem_diaria'
    
    # Chave primária
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Campos originais da planilha
    equipe = Column(String(100), nullable=False)
    data = Column(Date, nullable=False)
    periodo = Column(String(20), nullable=False)
    qtd_pessoas = Column(Integer, nullable=False)
    
    # Endereço original
    logradouro_original = Column(Text, nullable=False)
    
    # Campos parseados
    tipo_logradouro = Column(String(50))
    nome_logradouro = Column(String(200))
    numero_logradouro = Column(String(20))
    complemento_logradouro = Column(Text)
    
    # Metadados
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("periodo IN ('Madrugada', 'Manhã', 'Tarde', 'Noite')", name='check_periodo'),
        CheckConstraint('qtd_pessoas >= 0', name='check_qtd_pessoas'),
    )
    
    def __repr__(self):
        return f"<ContagemDiaria(id={self.id}, data={self.data}, equipe={self.equipe})>"