import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "AgentForge"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/agentforge.db")
    
    # LLM Provider Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Ollama (internal Docker service)
    OLLAMA_API_BASE: str = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    
    # Available LLM models (Ollama local models first)
    AVAILABLE_MODELS: list = [
        {"id": "ollama/gemma3:latest", "name": "Gemma 3 (Local)", "provider": "ollama"},
        {"id": "ollama/qwen2.5-coder:7b", "name": "Qwen 2.5 Coder 7B (Local)", "provider": "ollama"},
        {"id": "ollama/qwen2.5-coder:3b", "name": "Qwen 2.5 Coder 3B (Local)", "provider": "ollama"},
        {"id": "ollama/deepseek-coder:6.7b-instruct", "name": "DeepSeek Coder 6.7B (Local)", "provider": "ollama"},
        {"id": "ollama/llama3.2:latest", "name": "Llama 3.2 (Local)", "provider": "ollama"},
        {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
        {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "provider": "anthropic"},
        {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
        {"id": "gemini/gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "google"},
    ]
    
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
    ]


settings = Settings()
