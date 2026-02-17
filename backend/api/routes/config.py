from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.models import LLMConfig, MCPServer
from models.schemas import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse,
    MCPServerCreate, MCPServerUpdate, MCPServerResponse
)

router = APIRouter(prefix="/api/config", tags=["config"])


# ─── LLM Models ───

@router.get("/llms", response_model=list[LLMConfigResponse])
async def list_llms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfig).order_by(LLMConfig.created_at.desc()))
    return result.scalars().all()


@router.post("/llms", response_model=LLMConfigResponse, status_code=201)
async def create_llm(data: LLMConfigCreate, db: AsyncSession = Depends(get_db)):
    llm = LLMConfig(**data.model_dump())
    db.add(llm)
    await db.commit()
    await db.refresh(llm)
    return llm


@router.put("/llms/{llm_id}", response_model=LLMConfigResponse)
async def update_llm(llm_id: str, data: LLMConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == llm_id))
    llm = result.scalar_one_or_none()
    if not llm:
        raise HTTPException(404, "LLM config not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(llm, key, value)
    
    await db.commit()
    await db.refresh(llm)
    return llm


@router.delete("/llms/{llm_id}", status_code=204)
async def delete_llm(llm_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == llm_id))
    llm = result.scalar_one_or_none()
    if not llm:
        raise HTTPException(404, "LLM config not found")
    
    await db.delete(llm)
    await db.commit()


# ─── MCP Servers ───

@router.get("/mcp", response_model=list[MCPServerResponse])
async def list_mcp_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MCPServer).order_by(MCPServer.created_at.desc()))
    return result.scalars().all()


@router.post("/mcp", response_model=MCPServerResponse, status_code=201)
async def create_mcp_server(data: MCPServerCreate, db: AsyncSession = Depends(get_db)):
    server = MCPServer(**data.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return server


@router.put("/mcp/{server_id}", response_model=MCPServerResponse)
async def update_mcp_server(server_id: str, data: MCPServerUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "MCP server not found")
    
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(server, key, value)
    
    await db.commit()
    await db.refresh(server)
    return server


@router.delete("/mcp/{server_id}", status_code=204)
async def delete_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MCPServer).where(MCPServer.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(404, "MCP server not found")
    
    await db.delete(server)
    await db.commit()
