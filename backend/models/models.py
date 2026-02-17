import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    crew_id = Column(String, ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(200), nullable=False)
    goal = Column(Text, nullable=False)
    backstory = Column(Text, default="")
    llm_model = Column(String(100), default="ollama/gemma3:latest")
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Float, default=4096)
    # Visual position on canvas
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    skills = Column(Text, default="[]")  # List of skills as JSON
    is_manager = Column(Boolean, default=False)
    # Integrated task fields
    task_description = Column(Text, nullable=True)
    task_expected_output = Column(Text, nullable=True)
    web_search_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    crew = relationship("Crew", back_populates="agents")
    tasks = relationship("Task", back_populates="agent", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    crew_id = Column(String, ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String, ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    expected_output = Column(Text, default="")
    order = Column(Float, default=0)
    # Visual position on canvas
    position_x = Column(Float, default=200)
    position_y = Column(Float, default=0)
    created_at = Column(DateTime, default=utcnow)

    crew = relationship("Crew", back_populates="tasks")
    agent = relationship("Agent", back_populates="tasks")


class Crew(Base):
    __tablename__ = "crews"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    process = Column(String(50), default="sequential")  # sequential | hierarchical
    # Scheduling fields
    schedule_type = Column(String(20), default="none")  # none | once | interval | cron
    schedule_value = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False)
    output_email = Column(String(200), nullable=True)
    # Canvas state stored as JSON (edges, viewport, etc.)
    canvas_state = Column(Text, default="{}")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    agents = relationship("Agent", back_populates="crew", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="crew", cascade="all, delete-orphan")
    runs = relationship("Run", back_populates="crew", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    crew_id = Column(String, ForeignKey("crews.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), default="pending")  # pending | running | completed | failed
    result = Column(Text, default="")
    logs = Column(Text, default="[]")
    tokens_used = Column(Float, default=0)
    cost = Column(Float, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    crew = relationship("Crew", back_populates="runs")

    def add_log(self, message: str, agent_name: str = "", level: str = "info"):
        current_logs = json.loads(self.logs or "[]")
        current_logs.append({
            "timestamp": utcnow().isoformat(),
            "agent": agent_name,
            "level": level,
            "message": message,
        })
        self.logs = json.dumps(current_logs)


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    model_id = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    base_url = Column(String(255), nullable=True)
    api_key = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    command = Column(String(255), nullable=False)
    args = Column(Text, default="[]")  # JSON list
    env = Column(Text, default="{}")   # JSON dict
    created_at = Column(DateTime, default=utcnow)
