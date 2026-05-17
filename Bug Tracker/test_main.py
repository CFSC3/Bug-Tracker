import pytest # type: ignore
from fastapi.testclient import TestClient # type: ignore
from sqlalchemy import create_engine # type: ignore
from sqlalchemy.orm import sessionmaker # type: ignore
from database import Base
from main import app, get_db

# Criando um banco de dados temporário para testes
SQLALCHEMY_DATABASE_URL = "sqlite:///./testes_qa.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db(): # Função para substituir a dependência do banco de dados durante os testes
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db # Substitui a dependência do banco de dados na aplicação

cliente = TestClient(app) # Cria um cliente de teste para a aplicação FastAPI

# Fixture para preparar o banco de dados antes dos testes e limpar após os testes
@pytest.fixture(autouse=True)
def preparar_banco_de_dados():
    Base.metadata.create_all(bind=engine) # Antes do teste rodar, cria as tabelas no banco de dados temporário
    yield 
    Base.metadata.drop_all(bind=engine) # Limpa as tabelas após os testes serem executados

def test_criar_bug():
    novo_bug = {
        "titulo": "Botão de login não funciona",
        "descricao": "Ao clicar no botão de login, a tela fica travada.",
        "prioridade": "Alta",
    }

    response = cliente.post("/bugs/", json=novo_bug) # Envia uma requisição POST para criar um novo bug na API

    assert response.status_code == 200 # Verifica se a resposta tem status code 200 (OK)
    dados = response.json() # Converte a resposta para JSON
    assert dados["titulo"] == "Botão de login não funciona" # Verifica se o título do bug criado é o esperado
    assert dados["resolvido"] == False  # Garante que o padrão é falso
    assert "id" in dados # Verifica se o ID do bug criado está presente na resposta

def test_listar_bugs():
    # Como o banco de dados é limpo antes de cada teste, a lista inicial deve estar vazia
    response = cliente.get("/bugs/") # Envia uma requisição GET para listar todos os bugs na API

    assert response.status_code == 200 # Verifica se a resposta tem status code 200 (OK)
    dados = response.json() # Converte a resposta para JSON

def test_nao_deve_criar_bug_sem_titulo():
    #Criando um dicionário sem o campo "titulo"
    bug_invalido = {
        "descricao": "O aplicativo fecha sozinho",
        "prioridade": "Alta"
    }
    
    # Tentamos enviar para a API
    response = cliente.post("/bugs/", json=bug_invalido)
    
    # A API DEVE recusar e retornar erro 422
    assert response.status_code == 422
    
    # Verifica se a API avisou onde está o erro
    detalhes_do_erro = response.json()
    # O Pydantic retorna uma lista de detalhes. O loc (location) aponta onde o erro ocorreu.
    assert detalhes_do_erro["detail"][0]["loc"] == ["body", "titulo"]
    assert detalhes_do_erro["detail"][0]["type"] == "missing"

def test_nao_deve_criar_bug_com_tipo_invalido():
    # O campo "resolvido" espera um Booleano (True/False). Vamos enviar um texto.
    bug_invalido = {
        "titulo": "Falha na exportação",
        "descricao": "PDF sai em branco",
        "prioridade": "Média",
        "resolvido": "não tenho certeza" # Isso é um texto, não um booleano!
    }
    
    # Act
    response = cliente.post("/bugs/", json=bug_invalido)
    
    # Assert: O Pydantic deve barrar e retornar 422
    assert response.status_code == 422
    
    # Validação Avançada: Confirma que o erro apontado foi no campo "resolvido"
    detalhes_do_erro = response.json()
    assert detalhes_do_erro["detail"][0]["loc"] == ["body", "resolvido"]

def test_atualizar_bug():
    # Primeiro, criamos um bug para atualizar
    bug_novo = {
        "titulo": "Erro na página de perfil",
        "descricao": "Foto de perfil não carrega",
        "prioridade": "Média"
    }

    resposta_criacao = cliente.post("/bugs/", json=bug_novo) # Envia uma requisição POST para criar um novo bug na API
    bug_id = resposta_criacao.json()["id"] # Pegamos o ID do bug criado para usar na atualização

    # Agora, preparamos os dados para atualizar o bug
    bug_atualizado = {
        "titulo": "Erro na página de perfil - atualizado",
        "descricao": "Foto de perfil não carrega, mesmo após limpar cache",
        "prioridade": "Alta",
        "resolvido": True
    }

    resposta_atualizacao = cliente.put(f"/bugs/{bug_id}", json=bug_atualizado) # Envia uma requisição PUT para atualizar o bug criado

    # Verificamos se a atualização foi bem-sucedida
    assert resposta_atualizacao.status_code == 200 # Verifica se a resposta tem status code 200 (OK)
    assert resposta_atualizacao.json()["resolvido"] == True # Verifica se o campo "resolvido" foi atualizado para True
    assert resposta_atualizacao.json()["titulo"] == "Erro na página de perfil - atualizado" # Verifica se o título foi atualizado corretamente

# Teste para deletar um bug
def test_deletar_bug():
    # Primeiro, criamos um bug para deletar
    bug_novo = {
        "titulo": "Bug tempórario",
        "descricao": "Vou ser deletado",
        "prioridade": "Média"
    }

    resposta_criacao = cliente.post("/bugs/", json=bug_novo) # Envia uma requisição POST para criar um novo bug na API
    bug_id = resposta_criacao.json()["id"] # Pegamos o ID do bug criado para usar na deleção

    resposta_deletar = cliente.delete(f"/bugs/{bug_id}") # Envia uma requisição DELETE para deletar o bug criad
    
    assert resposta_deletar.status_code == 200 # Verifica se a resposta tem status code 200 (OK)
    assert resposta_deletar.json()["mensagem"] == f"Bug {bug_id} deletado com sucesso!"


