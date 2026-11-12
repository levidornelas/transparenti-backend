from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.security import create_access_token, verify_password
from src.db.session import get_db
from src.modules.auth.dependencies import current_user
from src.modules.auth.schemas import LoginInput, TokenOutput
from src.modules.usuarios.models import Usuario
from src.modules.usuarios.schemas import UsuarioOutput

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=TokenOutput)
def login(dados: LoginInput, db: Session = Depends(get_db)):
    usuario = db.scalar(select(Usuario).where(Usuario.email == str(dados.email).lower()))
    if not usuario or not usuario.ativo or not verify_password(dados.senha, usuario.senha_hash):
        raise HTTPException(401, "E-mail ou senha inválidos.")
    return TokenOutput(access_token=create_access_token(usuario.id, usuario.perfil), usuario=usuario)

@router.get("/me", response_model=UsuarioOutput)
def me(usuario: Usuario = Depends(current_user)):
    return usuario
