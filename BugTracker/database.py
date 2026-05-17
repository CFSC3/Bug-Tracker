from sqlalchemy import create_engine, Column, Integer, String, Boolean # type: ignore # Import necessary SQLAlchemy components
from sqlalchemy.orm import declarative_base, sessionmaker # type: ignore # Import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./bugs.db" # Define a database URL

# Cria a o engine para conectar ao banco de dados SQLite 
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}) 
 
#Cria a Sessão Local para interagir com o banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define a base para os modelos do SQLAlchemy]
Base = declarative_base()

# Definindo a "Tabela" de Bugs no banco de dados
class BugDB(Base):
    __tablename__ = "bugs" # Nome da tabela no banco de dados

    id = Column(Integer, primary_key=True, index=True) # Coluna de ID
    titulo = Column(String, nullable=True) # Coluna de título
    descricao = Column(String, nullable=True) # Coluna de descrição
    prioridade = Column(String, nullable=True) # Coluna de prioridade
    resolvido = Column(Boolean, default=False) # Coluna de status de resolução