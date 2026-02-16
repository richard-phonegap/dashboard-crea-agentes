from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.scheduler import scheduler
from db.database import get_db
from models.models import Crew, Agent, Task
from models.schemas import (
    CrewCreate, CrewUpdate, CrewResponse, CrewListResponse,
    AgentCreate, AgentUpdate, AgentResponse,
    TaskCreate, TaskUpdate, TaskResponse,
)

router = APIRouter(prefix="/api/crews", tags=["crews"])


@router.get("", response_model=list[CrewListResponse])
async def list_crews(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Crew).options(selectinload(Crew.agents), selectinload(Crew.tasks))
        .order_by(Crew.updated_at.desc())
    )
    crews = result.scalars().all()
    return [
        CrewListResponse(
            id=c.id, name=c.name, description=c.description,
            process=c.process, agent_count=len(c.agents),
            task_count=len(c.tasks), created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in crews
    ]


@router.post("", response_model=CrewResponse, status_code=201)
async def create_crew(data: CrewCreate, db: AsyncSession = Depends(get_db)):
    crew = Crew(name=data.name, description=data.description, process=data.process)
    db.add(crew)
    await db.commit()
    await db.refresh(crew)
    
    # Update scheduler if needed
    scheduler.schedule_crew(crew)
    
    return await _get_crew(crew.id, db)


@router.get("/{crew_id}", response_model=CrewResponse)
async def get_crew(crew_id: str, db: AsyncSession = Depends(get_db)):
    return await _get_crew(crew_id, db)


@router.put("/{crew_id}", response_model=CrewResponse)
async def update_crew(crew_id: str, data: CrewUpdate, db: AsyncSession = Depends(get_db)):
    crew = await _get_crew_model(crew_id, db)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(crew, key, value)
    await db.commit()
    return await _get_crew(crew_id, db)


@router.delete("/{crew_id}", status_code=204)
async def delete_crew(crew_id: str, db: AsyncSession = Depends(get_db)):
    crew = await _get_crew_model(crew_id, db)
    await db.delete(crew)
    await db.commit()


# ─── Agents within Crew ───

@router.post("/{crew_id}/agents", response_model=AgentResponse, status_code=201)
async def create_agent(crew_id: str, data: AgentCreate, db: AsyncSession = Depends(get_db)):
    await _get_crew_model(crew_id, db)
    agent = Agent(crew_id=crew_id, **data.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.put("/{crew_id}/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(crew_id: str, agent_id: str, data: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_model(agent_id, db)
    if agent.crew_id != crew_id:
        raise HTTPException(404, "Agent not found in this crew")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(agent, key, value)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{crew_id}/agents/{agent_id}", status_code=204)
async def delete_agent(crew_id: str, agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await _get_agent_model(agent_id, db)
    if agent.crew_id != crew_id:
        raise HTTPException(404, "Agent not found in this crew")
    await db.delete(agent)
    await db.commit()


# ─── Tasks within Crew ───

@router.post("/{crew_id}/tasks", response_model=TaskResponse, status_code=201)
async def create_task(crew_id: str, data: TaskCreate, db: AsyncSession = Depends(get_db)):
    await _get_crew_model(crew_id, db)
    task = Task(crew_id=crew_id, **data.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.put("/{crew_id}/tasks/{task_id}", response_model=TaskResponse)
async def update_task(crew_id: str, task_id: str, data: TaskUpdate, db: AsyncSession = Depends(get_db)):
    task = await _get_task_model(task_id, db)
    if task.crew_id != crew_id:
        raise HTTPException(404, "Task not found in this crew")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{crew_id}/tasks/{task_id}", status_code=204)
async def delete_task(crew_id: str, task_id: str, db: AsyncSession = Depends(get_db)):
    task = await _get_task_model(task_id, db)
    if task.crew_id != crew_id:
        raise HTTPException(404, "Task not found in this crew")
    await db.delete(task)
    await db.commit()


# ─── Helpers ───

async def _get_crew(crew_id: str, db: AsyncSession) -> Crew:
    result = await db.execute(
        select(Crew)
        .options(selectinload(Crew.agents), selectinload(Crew.tasks))
        .where(Crew.id == crew_id)
    )
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(404, "Crew not found")
    return crew


async def _get_crew_model(crew_id: str, db: AsyncSession) -> Crew:
    result = await db.execute(select(Crew).where(Crew.id == crew_id))
    crew = result.scalar_one_or_none()
    if not crew:
        raise HTTPException(404, "Crew not found")
    return crew


async def _get_agent_model(agent_id: str, db: AsyncSession) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


async def _get_task_model(task_id: str, db: AsyncSession) -> Task:
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    return task
