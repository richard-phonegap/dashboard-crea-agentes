from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Agent Schemas ───

class AgentCreate(BaseModel):
    name: str
    role: str
    goal: str
    backstory: str = ""
    llm_model: str = "ollama/gemma3:latest"
    temperature: float = 0.7
    max_tokens: int = 4096
    position_x: float = 0
    position_y: float = 0
    skills: str = "[]"
    is_manager: bool = False
    task_description: Optional[str] = None
    task_expected_output: Optional[str] = None


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    goal: Optional[str] = None
    backstory: Optional[str] = None
    llm_model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    skills: Optional[str] = None
    is_manager: Optional[bool] = None
    task_description: Optional[str] = None
    task_expected_output: Optional[str] = None


class AgentResponse(BaseModel):
    id: str
    crew_id: str
    name: str
    role: str
    goal: str
    backstory: str
    llm_model: str
    temperature: float
    max_tokens: float
    position_x: float
    position_y: float
    skills: str
    is_manager: bool
    task_description: Optional[str]
    task_expected_output: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Task Schemas ───

class TaskCreate(BaseModel):
    name: str
    description: str
    expected_output: str = ""
    agent_id: Optional[str] = None
    order: int = 0
    position_x: float = 200
    position_y: float = 0


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    expected_output: Optional[str] = None
    agent_id: Optional[str] = None
    order: Optional[int] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None


class TaskResponse(BaseModel):
    id: str
    crew_id: str
    agent_id: Optional[str]
    name: str
    description: str
    expected_output: str
    order: float
    position_x: float
    position_y: float
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Crew Schemas ───

class CrewCreate(BaseModel):
    name: str
    description: str = ""
    process: str = "sequential"
    schedule_type: str = "none"
    schedule_value: Optional[str] = None
    is_public: bool = False
    output_email: Optional[str] = None


class CrewUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    process: Optional[str] = None
    schedule_type: Optional[str] = None
    schedule_value: Optional[str] = None
    is_public: Optional[bool] = None
    output_email: Optional[str] = None
    canvas_state: Optional[str] = None


class CrewResponse(BaseModel):
    id: str
    name: str
    description: str
    process: str
    schedule_type: str
    schedule_value: Optional[str]
    is_public: bool
    output_email: Optional[str]
    canvas_state: str
    agents: List[AgentResponse] = []
    tasks: List[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CrewListResponse(BaseModel):
    id: str
    name: str
    description: str
    process: str
    agent_count: int = 0
    task_count: int = 0
    created_at: datetime
    updated_at: datetime


# ─── Run Schemas ───

class RunResponse(BaseModel):
    id: str
    crew_id: str
    status: str
    result: str
    logs: str
    tokens_used: float
    cost: float
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Config Schemas ───

class LLMConfigBase(BaseModel):
    name: str
    model_id: str
    provider: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(BaseModel):
    name: Optional[str] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None

class LLMConfigResponse(LLMConfigBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class MCPServerBase(BaseModel):
    name: str
    command: str
    args: str = "[]"
    env: str = "{}"

class MCPServerCreate(MCPServerBase):
    pass

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    command: Optional[str] = None
    args: Optional[str] = None
    env: Optional[str] = None

class MCPServerResponse(MCPServerBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
