from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from src.core.security import agora
from src.modules.chamados.models import Avaliacao, Chamado, HistoricoChamado
from src.modules.chamados.schemas import ChamadoCreate
from src.modules.usuarios.models import Usuario

SLA_HORAS = {"CRITICA": 4, "ALTA": 8, "MEDIA": 24, "BAIXA": 72}
TRANSICOES = {"ABERTO": {"EM_TRIAGEM", "EM_ATENDIMENTO"}, "EM_TRIAGEM": {"EM_ATENDIMENTO"}, "EM_ATENDIMENTO": {"RESOLVIDO"}, "RESOLVIDO": {"FECHADO", "REABERTO"}, "REABERTO": {"EM_ATENDIMENTO"}}

def prioridade_por_matriz(impacto: str, urgencia: str) -> str:
    return {("ALTO", "ALTO"): "CRITICA", ("ALTO", "BAIXO"): "ALTA", ("BAIXO", "ALTO"): "MEDIA", ("BAIXO", "BAIXO"): "BAIXA"}[(impacto, urgencia)]

class ChamadoService:
    def __init__(self, db: Session): self.db = db

    def fechar_resolvidos_sem_avaliacao(self) -> None:
        """Aplica a regra do MVP de fechamento automático após 72 horas."""
        limite = agora() - timedelta(hours=72)
        pendentes = self.db.scalars(
            select(Chamado)
            .outerjoin(Avaliacao)
            .where(Chamado.status == "RESOLVIDO", Chamado.resolvido_em <= limite, Avaliacao.id.is_(None))
        ).all()
        for chamado in pendentes:
            chamado.status = "FECHADO"
            self._log(chamado, None, "STATUS", "Chamado fechado automaticamente após 72 horas sem avaliação.", "RESOLVIDO", "FECHADO")
        if pendentes:
            self.db.commit()

    def get(self, chamado_id: str) -> Chamado:
        self.fechar_resolvidos_sem_avaliacao()
        stmt = select(Chamado).where(Chamado.id == chamado_id).options(joinedload(Chamado.solicitante), joinedload(Chamado.responsavel), joinedload(Chamado.historico).joinedload(HistoricoChamado.autor), joinedload(Chamado.avaliacao))
        chamado = self.db.execute(stmt).unique().scalar_one_or_none()
        if not chamado: raise HTTPException(404, "Chamado não encontrado.")
        return chamado

    def _log(self, chamado: Chamado, autor: Usuario | None, tipo: str, descricao: str, de: str | None = None, para: str | None = None):
        self.db.add(HistoricoChamado(chamado_id=chamado.id, autor_id=autor.id if autor else None, tipo=tipo, descricao=descricao, de_valor=de, para_valor=para))

    def create(self, dados: ChamadoCreate, usuario: Usuario) -> Chamado:
        prioridade = prioridade_por_matriz(dados.impacto, dados.urgencia); aberto = agora()
        chamado = Chamado(protocolo=f"TI-{aberto:%Y%m%d}-{str(__import__('uuid').uuid4())[:6].upper()}", titulo=dados.titulo.strip(), descricao=dados.descricao.strip(), categoria=dados.categoria, setor=dados.setor.strip(), impacto=dados.impacto, urgencia=dados.urgencia, prioridade=prioridade, solicitante_id=usuario.id, aberto_em=aberto, prazo_em=aberto + timedelta(hours=SLA_HORAS[prioridade]))
        self.db.add(chamado); self.db.flush(); self._log(chamado, usuario, "CRIACAO", "Chamado aberto.", None, "ABERTO"); self.db.commit()
        return self.get(chamado.id)

    def check_access(self, chamado: Chamado, usuario: Usuario):
        if usuario.perfil == "SERVIDOR" and chamado.solicitante_id != usuario.id: raise HTTPException(403, "Você só pode acessar seus próprios chamados.")

    def change_status(self, chamado: Chamado, usuario: Usuario, novo: str, solucao: str | None):
        if novo not in TRANSICOES.get(chamado.status, set()): raise HTTPException(422, f"Transição inválida: {chamado.status} para {novo}.")
        if novo == "EM_ATENDIMENTO" and not chamado.responsavel_id: raise HTTPException(422, "Atribua um responsável antes de iniciar o atendimento.")
        if novo == "RESOLVIDO" and not (solucao or "").strip(): raise HTTPException(422, "Informe a solução aplicada.")
        anterior = chamado.status; chamado.status = novo
        if novo == "RESOLVIDO": chamado.solucao = solucao.strip(); chamado.resolvido_em = agora()
        self._log(chamado, usuario, "STATUS", f"Status alterado de {anterior} para {novo}.", anterior, novo); self.db.commit(); return self.get(chamado.id)
