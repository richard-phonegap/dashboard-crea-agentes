import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from datetime import datetime, timezone
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
async def start_run(crew_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
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
    
    # Check if there are either manual tasks OR integrated tasks in agents
    has_integrated_tasks = any(a.task_description for a in crew.agents)
    if not crew.tasks and not has_integrated_tasks:
        raise HTTPException(400, "El equipo debe tener al menos una tarea (ya sea como nodo independiente o integrada en un agente)")

    # Create run object immediately
    run = Run(
        crew_id=crew.id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    orchestrator = Orchestrator(db)
    
    # Dispatch execution to background task
    background_tasks.add_task(orchestrator.process_run, run.id, crew.id)
    
    return run

@router.post("/{run_id}/stop")
async def stop_run(crew_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    success = Orchestrator.stop_run(run_id)
    if not success:
        # Check if run exists but isn't active
        result = await db.execute(select(Run).where(Run.id == run_id))
        run = result.scalar_one_or_none()
        if not run:
            raise HTTPException(404, "Run not found")
        return {"status": "ignored", "message": "Run is not active"}
    
    return {"status": "success", "message": "Run cancellation requested"}


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(crew_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Run).where(Run.id == run_id, Run.crew_id == crew_id)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(404, "Run not found")
    return run
