from fastapi import FastAPI, Depends, HTTPException  # type: ignore
from pydantic import BaseModel, ConfigDict  # type: ignore
from sqlalchemy.orm import Session # type: ignore
from database import BugDB, SessionLocal, Base, engine # type: ignore

# Cria a tabela no banco de dados assim que o código é executado
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bug Tracker API")

# Modelo de como os dados do bug devem chegar
class Bug(BaseModel):
    titulo: str #titulo do bug
    descricao: str #descrição do bug
    prioridade: str #baixa, média ou alta
    resolvido: bool = False #status do bug, se foi resolvido ou não

class BugResponse(Bug):
    id: int #id do bug, gerado automaticamente pelo banco de dados

    model_config = ConfigDict(from_attributes=True) # Configuração para permitir a conversão de objetos ORM para modelos Pydantic

def get_db(): # Função para garantir que a sessão do banco de dados seja fechada após o uso
    db = SessionLocal() # Cria uma sessão de banco de dados
    try:
        yield db # Fornece a sessão para as operações do banco de dados
    finally:
        db.close() # Garante que a sessão seja fechada após o uso


@app.get("/")
def home():
    return {"mensagem": "API de Bug Tracker ativa!"}

# Endpoint para criar um novo bug, recebe os dados do bug e a sessão do banco de dados como dependência, e retorna o bug criado.
@app.post("/bugs/", response_model=BugResponse)
def criar_bug(bug: Bug, db: Session = Depends(get_db)): # Função para criar um novo bug no banco de dados
    # Cria uma nova instância do modelo BugDB com os dados fornecidos
    novo_bug = BugDB( 
        titulo=bug.titulo,
        descricao=bug.descricao,
        prioridade=bug.prioridade,
        resolvido=bug.resolvido
    )

    db.add(novo_bug) # Adiciona o novo bug à sessão do banco de dados
    db.commit() # Salva as alterações no banco de dados
    db.refresh(novo_bug) # Atualiza a instância do bug com os dados do banco de dados (como o ID gerado)
    return novo_bug # Retorna o bug criado

# Endpoint para listar todos os bugs, recebe a sessão do banco de dados como dependência, e retorna uma lista de bugs.
@app.get("/bugs/", response_model=list[BugResponse])
def listar_bugs(db: Session = Depends(get_db)):
    # Consulta todos os bugs no banco de dados e retorna como uma lista
    return db.query(BugDB).all()

# Endpoint para atualizar um bug existente, recebe o ID do bug, os dados atualizados e a sessão do banco de dados como dependência, e retorna o bug atualizado.
@app.put("/bugs/{bug_id}", response_model=BugResponse)
def atualizar_bug(bug_id: int, bugAtualizado: Bug, db: Session = Depends(get_db)):
    # Consulta o bug pelo ID
    bug = db.query(BugDB).filter(BugDB.id == bug_id).first()

    if not bug: # Se o bug não for encontrado, retorna um erro 404
        raise HTTPException(status_code=404, detail="Bug não encontrado")
    
    # Atualiza os campos do bug com os novos dados
    bug.titulo = bugAtualizado.titulo
    bug.descricao = bugAtualizado.descricao
    bug.prioridade = bugAtualizado.prioridade
    bug.resolvido = bugAtualizado.resolvido

    db.commit() # Salva as alterações no banco de dados
    db.refresh(bug) # Atualiza a instância do bug com os dados do banco
    return bug # Retorna o bug atualizado

# Endpoint para deletar um bug, recebe o ID do bug e a sessão do banco de dados como dependência, e retorna uma mensagem de sucesso.
@app.delete("/bugs/{bug_id}")
def deletar_bug(bug_id: int, db: Session = Depends(get_db)):
    # Consulta o bug pelo ID
    bug = db.query(BugDB).filter(BugDB.id == bug_id).first()

    if not bug: # Se o bug não for encontrado, retorna um erro 404
        raise HTTPException(status_code=404, detail="Bug não encontrado")
    
    db.delete(bug) # Deleta o bug do banco de dados
    db.commit() # Salva as alterações no banco de dados
    return {"mensagem": f"Bug {bug_id} deletado com sucesso!"} # Retorna uma mensagem de sucesso