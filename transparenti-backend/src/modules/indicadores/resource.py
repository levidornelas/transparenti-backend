from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from src.db.session import get_db
from src.modules.auth.dependencies import require_roles
from src.modules.chamados.models import Avaliacao, Chamado
from src.modules.usuarios.models import Usuario

router = APIRouter(prefix="/indicadores", tags=["Indicadores"])

@router.get("")
def indicadores(inicio: datetime | None = Query(None), fim: datetime | None = Query(None), db: Session = Depends(get_db), _gestor: Usuario = Depends(require_roles("GESTOR"))):
    base = select(Chamado)
    if inicio: base = base.where(Chamado.aberto_em >= inicio)
    if fim: base = base.where(Chamado.aberto_em <= fim)
    sub = base.subquery()
    por_status = dict(db.execute(select(sub.c.status, func.count()).group_by(sub.c.status)).all())
    por_categoria = dict(db.execute(select(sub.c.categoria, func.count()).group_by(sub.c.categoria)).all())
    resolvidos = select(Chamado).where(Chamado.resolvido_em.is_not(None))
    if inicio: resolvidos = resolvidos.where(Chamado.aberto_em >= inicio)
    if fim: resolvidos = resolvidos.where(Chamado.aberto_em <= fim)
    res = resolvidos.subquery()
    total_resolvidos, no_sla = db.execute(select(func.count(), func.coalesce(func.sum(case((res.c.resolvido_em <= res.c.prazo_em, 1), else_=0)), 0)).select_from(res)).one()
    resolucoes = db.execute(select(res.c.prioridade, res.c.aberto_em, res.c.resolvido_em)).all()
    tempos_acumulados: dict[str, list[float]] = {}
    for prioridade, aberto_em, resolvido_em in resolucoes:
        tempos_acumulados.setdefault(prioridade, []).append((resolvido_em - aberto_em).total_seconds() / 3600)
    satisfacao = db.scalar(select(func.avg(Avaliacao.nota)))
    return {"chamados_por_status": por_status, "percentual_dentro_sla": round((no_sla / total_resolvidos * 100), 2) if total_resolvidos else None, "tempo_medio_resolucao_horas_por_prioridade": {p: round(sum(valores) / len(valores), 2) for p, valores in tempos_acumulados.items()}, "chamados_por_categoria": por_categoria, "satisfacao_media": round(float(satisfacao), 2) if satisfacao is not None else None}
