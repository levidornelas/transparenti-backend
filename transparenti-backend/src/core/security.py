from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from pwdlib import PasswordHash

from src.core.config import settings

password_hasher = PasswordHash.recommended()


def agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str) -> bool:
    return password_hasher.verify(password, encoded)


def create_access_token(usuario_id: str, perfil: str) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": usuario_id, "perfil": perfil, "iat": now, "exp": now + timedelta(minutes=settings.access_token_minutes), "iss": settings.jwt_issuer, "aud": settings.jwt_audience, "jti": str(uuid4())},
        settings.jwt_secret.get_secret_value(), algorithm="HS256"
    )


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret.get_secret_value(), algorithms=["HS256"], issuer=settings.jwt_issuer, audience=settings.jwt_audience)
    except jwt.PyJWTError as error:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido ou expirado.", headers={"WWW-Authenticate": "Bearer"}) from error
