from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.core.security import hash_password
from src.db.session import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.usuarios.models import Usuario
from src.modules.usuarios.schemas import UsuarioCreate, UsuarioOutput

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

@router.post("", response_model=UsuarioOutput, status_code=status.HTTP_201_CREATED)
def create_usuario(dados: UsuarioCreate, db: Session = Depends(get_db), _gestor: Usuario = Depends(require_roles("GESTOR"))):
    email = str(dados.email).lower()
    if db.scalar(select(Usuario).where(Usuario.email == email)):
        raise HTTPException(409, "E-mail já cadastrado.")
    usuario = Usuario(nome=dados.nome.strip(), email=email, senha_hash=hash_password(dados.senha), perfil=dados.perfil)
    db.add(usuario); db.commit(); db.refresh(usuario)
    return usuario

@router.get("", response_model=list[UsuarioOutput])
def list_usuarios(db: Session = Depends(get_db), _gestor: Usuario = Depends(require_roles("GESTOR"))):
    return list(db.scalars(select(Usuario).order_by(Usuario.nome)))
