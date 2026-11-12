# TransparenTI Backend

API FastAPI da central de chamados de TI. Inclui autenticação por perfil, SLA, histórico imutável, avaliação e indicadores.

## Executar

```powershell
uv sync --all-groups
Copy-Item .env.example .env
uv run uvicorn src.main:app --reload
```

Na primeira inicialização, o gestor definido no `.env` é criado. A documentação interativa fica em `http://localhost:8000/docs`.
