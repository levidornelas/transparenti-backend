from datetime import datetime
from uuid import uuid4
from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from src.core.security import agora
from src.db.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nome: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    perfil: Mapped[str] = mapped_column(String(20), index=True)  # SERVIDOR, TECNICO, GESTOR
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=agora, onupdate=agora)
