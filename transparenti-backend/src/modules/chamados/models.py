from __future__ import annotations

from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.security import agora
from src.db.base import Base


class Chamado(Base):
    __tablename__ = "chamados"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    protocolo: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(160))
    descricao: Mapped[str] = mapped_column(Text)
    categoria: Mapped[str] = mapped_column(String(30), index=True)
    setor: Mapped[str] = mapped_column(String(160))
    impacto: Mapped[str] = mapped_column(String(10))
    urgencia: Mapped[str] = mapped_column(String(10))
    prioridade: Mapped[str] = mapped_column(String(10), index=True)
    status: Mapped[str] = mapped_column(String(16), default="ABERTO", index=True)
    solicitante_id: Mapped[str] = mapped_column(ForeignKey("usuarios.id"), index=True)
    responsavel_id: Mapped[str | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True, index=True)
    aberto_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    prazo_em: Mapped[datetime] = mapped_column(DateTime, index=True)
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    solucao: Mapped[str | None] = mapped_column(Text, nullable=True)
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    responsavel = relationship("Usuario", foreign_keys=[responsavel_id])
    historico: Mapped[list[HistoricoChamado]] = relationship(back_populates="chamado", cascade="all, delete-orphan", order_by="HistoricoChamado.criado_em")
    avaliacao: Mapped[Avaliacao | None] = relationship(back_populates="chamado", cascade="all, delete-orphan", uselist=False)


class HistoricoChamado(Base):
    __tablename__ = "historico_chamados"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    chamado_id: Mapped[str] = mapped_column(ForeignKey("chamados.id", ondelete="CASCADE"), index=True)
    autor_id: Mapped[str | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20))  # CRIACAO, STATUS, ATRIBUICAO, PRIORIDADE, COMENTARIO
    descricao: Mapped[str] = mapped_column(Text)
    de_valor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    para_valor: Mapped[str | None] = mapped_column(String(60), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    chamado: Mapped[Chamado] = relationship(back_populates="historico")
    autor = relationship("Usuario")


class Avaliacao(Base):
    __tablename__ = "avaliacoes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    chamado_id: Mapped[str] = mapped_column(ForeignKey("chamados.id", ondelete="CASCADE"), unique=True)
    nota: Mapped[int] = mapped_column(Integer)
    comentario: Mapped[str | None] = mapped_column(Text, nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=agora)
    chamado: Mapped[Chamado] = relationship(back_populates="avaliacao")
