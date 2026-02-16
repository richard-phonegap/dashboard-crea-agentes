from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from db.database import init_db
from api.routes.crews import router as crews_router
from api.routes.runs import router as runs_router
from api.routes.services import router as services_router
from core.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Start background scheduler
    scheduler.start()
    await scheduler.load_all_schedules()
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Plataforma visual de orquestación multi-agente",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crews_router)
app.include_router(runs_router)
app.include_router(services_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/api/llm-models")
async def list_llm_models():
    return settings.AVAILABLE_MODELS
