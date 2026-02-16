from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db.database import get_db
from models.models import Crew, Run
from models.schemas import RunResponse
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/api/crews/{crew_id}/runs", tags=["runs"])


@router.get("", response_model=list[RunResponse])
async def list_runs(crew_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run).where(Run.crew_id == crew_id).order_by(Run.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=RunResponse, status_code=201)
async def start_run(crew_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Crew)
        .options(selectinload(Crew.agents), selectinload(Crew.tasks))
        .where(Crew.id == crew_id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(404, "Crew not found")

    if not crew.agents:
        raise HTTPException(400, "El equipo debe tener al menos un agente")
    if not crew.tasks:
        raise HTTPException(400, "El equipo debe tener al menos una tarea")

    orchestrator = Orchestrator(db)
    run = await orchestrator.execute_crew(crew)
    return run


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(crew_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.crew_id == crew_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")
    return run
