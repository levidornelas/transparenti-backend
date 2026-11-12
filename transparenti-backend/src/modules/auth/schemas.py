from pydantic import BaseModel, EmailStr, Field
from src.modules.usuarios.schemas import UsuarioOutput

class LoginInput(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=128)

class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOutput
