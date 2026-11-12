from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from src.db.session import get_db
from src.modules.auth.dependencies import current_user, require_roles
from src.modules.chamados.models import Avaliacao, Chamado
from src.modules.chamados.schemas import (AtribuicaoUpdate, AvaliacaoCreate, ChamadoCreate, ChamadoListItem, ChamadoOutput, ComentarioCreate, PrioridadeUpdate, StatusUpdate)
from src.modules.chamados.service import ChamadoService, SLA_HORAS
from src.modules.usuarios.models import Usuario

router = APIRouter(prefix="/chamados", tags=["Chamados"])

def detail(chamado: Chamado) -> Chamado:
    return chamado

@router.post("", response_model=ChamadoOutput, status_code=status.HTTP_201_CREATED)
def create_chamado(dados: ChamadoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("SERVIDOR"))):
    return ChamadoService(db).create(dados, usuario)

@router.get("", response_model=list[ChamadoListItem])
def list_chamados(status_filter: str | None = Query(None, alias="status"), prioridade: str | None = None, categoria: str | None = None, responsavel_id: str | None = None, db: Session = Depends(get_db), usuario: Usuario = Depends(current_user)):
    ChamadoService(db).fechar_resolvidos_sem_avaliacao()
    stmt = select(Chamado).options(joinedload(Chamado.responsavel)).order_by(Chamado.prazo_em)
    if usuario.perfil == "SERVIDOR": stmt = stmt.where(Chamado.solicitante_id == usuario.id)
    if status_filter: stmt = stmt.where(Chamado.status == status_filter)
    if prioridade: stmt = stmt.where(Chamado.prioridade == prioridade)
    if categoria: stmt = stmt.where(Chamado.categoria == categoria)
    if responsavel_id: stmt = stmt.where(Chamado.responsavel_id == responsavel_id)
    return list(db.scalars(stmt).unique())

@router.get("/{chamado_id}", response_model=ChamadoOutput)
def get_chamado(chamado_id: str, db: Session = Depends(get_db), usuario: Usuario = Depends(current_user)):
    service = ChamadoService(db); chamado = service.get(chamado_id); service.check_access(chamado, usuario); return detail(chamado)

@router.post("/{chamado_id}/comentarios", response_model=ChamadoOutput)
def add_comentario(chamado_id: str, dados: ComentarioCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(current_user)):
    service = ChamadoService(db); chamado = service.get(chamado_id); service.check_access(chamado, usuario)
    service._log(chamado, usuario, "COMENTARIO", dados.texto.strip()); db.commit(); return service.get(chamado_id)

@router.patch("/{chamado_id}/prioridade", response_model=ChamadoOutput)
def update_prioridade(chamado_id: str, dados: PrioridadeUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("TECNICO", "GESTOR"))):
    service = ChamadoService(db); chamado = service.get(chamado_id); anterior = chamado.prioridade
    chamado.prioridade = dados.prioridade; chamado.prazo_em = chamado.aberto_em + __import__('datetime').timedelta(hours=SLA_HORAS[dados.prioridade])
    service._log(chamado, usuario, "PRIORIDADE", dados.justificativa.strip(), anterior, dados.prioridade); db.commit(); return service.get(chamado_id)

@router.patch("/{chamado_id}/responsavel", response_model=ChamadoOutput)
def atribuir_responsavel(chamado_id: str, dados: AtribuicaoUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("TECNICO", "GESTOR"))):
    service = ChamadoService(db); chamado = service.get(chamado_id); responsavel = db.get(Usuario, dados.responsavel_id)
    if not responsavel or not responsavel.ativo or responsavel.perfil not in {"TECNICO", "GESTOR"}: raise HTTPException(422, "Responsável deve ser um técnico ou gestor ativo.")
    if usuario.perfil == "TECNICO" and responsavel.id != usuario.id: raise HTTPException(403, "Técnicos só podem assumir o próprio chamado.")
    anterior = chamado.responsavel.nome if chamado.responsavel else None; chamado.responsavel_id = responsavel.id
    service._log(chamado, usuario, "ATRIBUICAO", f"Responsável definido como {responsavel.nome}.", anterior, responsavel.nome); db.commit(); return service.get(chamado_id)

@router.patch("/{chamado_id}/status", response_model=ChamadoOutput)
def update_status(chamado_id: str, dados: StatusUpdate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("TECNICO", "GESTOR"))):
    service = ChamadoService(db); chamado = service.get(chamado_id); return service.change_status(chamado, usuario, dados.status, dados.solucao)

@router.post("/{chamado_id}/avaliacao", response_model=ChamadoOutput)
def avaliar(chamado_id: str, dados: AvaliacaoCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_roles("SERVIDOR"))):
    service = ChamadoService(db); chamado = service.get(chamado_id); service.check_access(chamado, usuario)
    if chamado.status != "RESOLVIDO": raise HTTPException(422, "A avaliação só está disponível para chamados resolvidos.")
    if chamado.avaliacao: raise HTTPException(409, "Este chamado já foi avaliado.")
    db.add(Avaliacao(chamado_id=chamado.id, nota=dados.nota, comentario=dados.comentario.strip() if dados.comentario else None))
    if dados.problema_persiste:
        anterior = chamado.status; chamado.status = "REABERTO"; service._log(chamado, usuario, "STATUS", "Chamado reaberto pelo solicitante.", anterior, "REABERTO")
    else:
        anterior = chamado.status; chamado.status = "FECHADO"; service._log(chamado, usuario, "STATUS", "Chamado fechado após avaliação.", anterior, "FECHADO")
    db.commit(); return service.get(chamado_id)
