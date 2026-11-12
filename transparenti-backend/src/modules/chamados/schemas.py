from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Categoria = Literal["COMPUTADOR", "SISTEMAS", "INTERNET", "CONTA_INSTITUCIONAL"]
ImpactoUrgencia = Literal["ALTO", "BAIXO"]
Prioridade = Literal["CRITICA", "ALTA", "MEDIA", "BAIXA"]
StatusChamado = Literal["ABERTO", "EM_TRIAGEM", "EM_ATENDIMENTO", "RESOLVIDO", "FECHADO", "REABERTO"]

class ChamadoCreate(BaseModel):
    titulo: str = Field(min_length=4, max_length=160)
    descricao: str = Field(min_length=10, max_length=5000)
    categoria: Categoria
    setor: str = Field(min_length=2, max_length=160)
    impacto: ImpactoUrgencia
    urgencia: ImpactoUrgencia

class ComentarioCreate(BaseModel):
    texto: str = Field(min_length=1, max_length=3000)

class PrioridadeUpdate(BaseModel):
    prioridade: Prioridade
    justificativa: str = Field(min_length=5, max_length=1000)

class AtribuicaoUpdate(BaseModel):
    responsavel_id: str

class StatusUpdate(BaseModel):
    status: StatusChamado
    solucao: str | None = Field(None, max_length=5000)

class AvaliacaoCreate(BaseModel):
    nota: int = Field(ge=1, le=5)
    comentario: str | None = Field(None, max_length=2000)
    problema_persiste: bool = False

class UsuarioResumo(BaseModel):
    id: str
    nome: str
    perfil: str
    model_config = ConfigDict(from_attributes=True)

class HistoricoOutput(BaseModel):
    id: str
    tipo: str
    descricao: str
    de_valor: str | None
    para_valor: str | None
    criado_em: datetime
    autor: UsuarioResumo | None
    model_config = ConfigDict(from_attributes=True)

class AvaliacaoOutput(BaseModel):
    nota: int
    comentario: str | None
    criado_em: datetime
    model_config = ConfigDict(from_attributes=True)

class ChamadoOutput(BaseModel):
    id: str
    protocolo: str
    titulo: str
    descricao: str
    categoria: str
    setor: str
    impacto: str
    urgencia: str
    prioridade: str
    status: str
    aberto_em: datetime
    prazo_em: datetime
    resolvido_em: datetime | None
    solucao: str | None
    solicitante: UsuarioResumo
    responsavel: UsuarioResumo | None
    historico: list[HistoricoOutput] = []
    avaliacao: AvaliacaoOutput | None = None
    model_config = ConfigDict(from_attributes=True)

class ChamadoListItem(BaseModel):
    id: str
    protocolo: str
    titulo: str
    categoria: str
    prioridade: str
    status: str
    prazo_em: datetime
    aberto_em: datetime
    responsavel: UsuarioResumo | None
    model_config = ConfigDict(from_attributes=True)
