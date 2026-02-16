import json
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional

from db.database import get_db
from models.models import Crew, Run
from models.schemas import RunResponse
from core.orchestrator import Orchestrator

router = APIRouter(prefix="/api/v1/services", tags=["External Services"])

async def get_public_crew(crew_id: str, db: AsyncSession):
    result = await db.execute(
        select(Crew)
        .options(selectinload(Crew.agents), selectinload(Crew.tasks))
        .where(Crew.id == crew_id)
    )
    crew = result.scalar_one_or_none()
    if not crew or not crew.is_public:
        raise HTTPException(status_code=404, detail="Public service not found")
    return crew

@router.get("/{crew_id}/latest")
async def get_latest_result(crew_id: str, db: AsyncSession = Depends(get_db)):
    """Get the latest completed run result for a public crew."""
    await get_public_crew(crew_id, db)
    
    result = await db.execute(
        select(Run).where(Run.crew_id == crew_id, Run.status == "completed")
        .order_by(Run.created_at.desc()).limit(1)
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="No completed runs found for this service")
    
    return {
        "crew_id": crew_id,
        "run_id": run.id,
        "status": run.status,
        "result": run.result,
        "completed_at": run.completed_at
    }

@router.api_route("/{crew_id}/run", methods=["GET", "POST"])
async def trigger_run(crew_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger a new run for a public crew and return the run ID."""
    crew = await get_public_crew(crew_id, db)
    
    orchestrator = Orchestrator(db)
    run = await orchestrator.execute_crew(crew)
    
    # Try to parse result as JSON for structured consumption
    parsed_result = run.result
    try:
        parsed_result = json.loads(run.result)
    except Exception:
        pass

    return {
        "message": "Run finished",
        "run_id": run.id,
        "status": run.status,
        "result": parsed_result,
        "tokens_used": run.tokens_used,
        "cost": run.cost
    }

@router.get("/{crew_id}/run/{run_id}")
async def get_run_status(crew_id: str, run_id: str, db: AsyncSession = Depends(get_db)):
    """Check the status of a specific run."""
    await get_public_crew(crew_id, db)
    
    run = await db.get(Run, run_id)
    if not run or run.crew_id != crew_id:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return RunResponse.from_orm(run)
