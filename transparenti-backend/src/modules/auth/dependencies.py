from collections.abc import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from src.core.security import decode_access_token
from src.db.session import get_db
from src.modules.usuarios.models import Usuario

bearer = HTTPBearer()

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> Usuario:
    payload = decode_access_token(credentials.credentials)
    usuario = db.get(Usuario, payload["sub"])
    if not usuario or not usuario.ativo:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuário não autorizado.")
    return usuario

def require_roles(*roles: str) -> Callable:
    def dependency(usuario: Usuario = Depends(current_user)) -> Usuario:
        if usuario.perfil not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Seu perfil não tem permissão para esta ação.")
        return usuario
    return dependency
