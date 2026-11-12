import os
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///./data/test_suite.db"
os.environ["JWT_SECRET"] = "12345678901234567890123456789012"
os.environ["BOOTSTRAP_ADMIN_EMAIL"] = "gestor@prefeitura.gov.br"
os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "senha-segura-123"

DATABASE = Path("data/test_suite.db")
if DATABASE.exists():
    DATABASE.unlink()

from fastapi.testclient import TestClient

from src.db.session import engine
from src.main import app


def test_fluxo_principal_de_chamado():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/login", json={"email": "gestor@prefeitura.gov.br", "senha": "senha-segura-123"})
        assert login.status_code == 200
        gestor_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        tecnico = client.post("/api/v1/usuarios", json={"nome": "Técnica", "email": "tecnica@prefeitura.gov.br", "senha": "senha-tecnica-123", "perfil": "TECNICO"}, headers=gestor_headers)
        assert tecnico.status_code == 201
        servidor = client.post("/api/v1/usuarios", json={"nome": "Servidor", "email": "servidor@prefeitura.gov.br", "senha": "senha-servidor-123", "perfil": "SERVIDOR"}, headers=gestor_headers)
        assert servidor.status_code == 201

        login_servidor = client.post("/api/v1/auth/login", json={"email": "servidor@prefeitura.gov.br", "senha": "senha-servidor-123"})
        servidor_headers = {"Authorization": f"Bearer {login_servidor.json()['access_token']}"}
        chamado = client.post("/api/v1/chamados", json={"titulo": "Internet indisponível", "descricao": "A internet do setor inteiro está indisponível.", "categoria": "INTERNET", "setor": "Finanças", "impacto": "ALTO", "urgencia": "ALTO"}, headers=servidor_headers)
        assert chamado.status_code == 201
        assert chamado.json()["prioridade"] == "CRITICA"
        chamado_id = chamado.json()["id"]

        assert client.patch(f"/api/v1/chamados/{chamado_id}/responsavel", json={"responsavel_id": tecnico.json()["id"]}, headers=gestor_headers).status_code == 200
        assert client.patch(f"/api/v1/chamados/{chamado_id}/status", json={"status": "EM_ATENDIMENTO"}, headers=gestor_headers).status_code == 200
        assert client.patch(f"/api/v1/chamados/{chamado_id}/status", json={"status": "RESOLVIDO", "solucao": "Roteador reiniciado."}, headers=gestor_headers).status_code == 200
        assert client.post(f"/api/v1/chamados/{chamado_id}/avaliacao", json={"nota": 5}, headers=servidor_headers).status_code == 200
        indicadores = client.get("/api/v1/indicadores", headers=gestor_headers)
        assert indicadores.status_code == 200
        assert indicadores.json()["satisfacao_media"] == 5.0

    engine.dispose()
    if DATABASE.exists():
        DATABASE.unlink()

