from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from src.core.config import settings
from src.core.security import hash_password
from src.db.base import Base
from src.db.session import SessionLocal, engine
from src.modules.usuarios.models import Usuario
from src.modules.chamados.models import Chamado, HistoricoChamado, Avaliacao
from src.modules.auth.resource import router as auth_router
from src.modules.usuarios.resource import router as usuarios_router
from src.modules.chamados.resource import router as chamados_router
from src.modules.indicadores.resource import router as indicadores_router

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        email = settings.bootstrap_admin_email.lower()
        if not db.scalar(select(Usuario).where(Usuario.email == email)):
            db.add(Usuario(nome="Gestor inicial", email=email, senha_hash=hash_password(settings.bootstrap_admin_password), perfil="GESTOR")); db.commit()
    yield

app = FastAPI(title="TransparenTI API", version="1.0.0", openapi_url="/api/v1/openapi.json", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router, prefix="/api/v1")
app.include_router(usuarios_router, prefix="/api/v1")
app.include_router(chamados_router, prefix="/api/v1")
app.include_router(indicadores_router, prefix="/api/v1")

@app.get("/health", tags=["Sistema"])
def health(): return {"status": "ok"}
