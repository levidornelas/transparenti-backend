from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field

Perfil = Literal["SERVIDOR", "TECNICO", "GESTOR"]

class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    perfil: Perfil = "SERVIDOR"

class UsuarioOutput(BaseModel):
    id: str
    nome: str
    email: EmailStr
    perfil: Perfil
    ativo: bool
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)
