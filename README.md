# ⚡ AgentForge

**Plataforma visual de orquestación multi-agente** — Diseña, configura y ejecuta equipos de agentes IA mediante una interfaz drag-and-drop, sin escribir código.

![Vue.js](https://img.shields.io/badge/Vue.js-3-42b883) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![License](https://img.shields.io/badge/License-MIT-purple)

## 🚀 Inicio Rápido

### Con Docker Compose (recomendado)
```bash
# 1. Configurar API keys
cp backend/.env.example backend/.env
# Edita backend/.env con tus API keys

# 2. Levantar todo
docker compose up --build
```

### Desarrollo local
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (otra terminal)
cd frontend
npm install
npm run dev
```

Abre **http://localhost:3000** 🎉

## 📖 Cómo Usar

1. **Crear un Equipo** — Desde el Dashboard, crea un nuevo equipo
2. **Agregar Agentes** — Arrastra nodos "Agente" al canvas y configura su rol, objetivo y LLM
3. **Agregar Tareas** — Arrastra nodos "Tarea" y describe qué deben hacer
4. **Conectar** — Arrastra cables de agentes a tareas para asignarlos
5. **Ejecutar** — Presiona ▶️ para ejecutar y ver los resultados en tiempo real

## 🏗️ Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Vue.js 3 + Vite + TypeScript |
| Canvas | Vue Flow |
| Backend | FastAPI + Python 3.12 |
| Base de Datos | SQLite (SQLAlchemy async) |
| LLM | LiteLLM (OpenAI, Anthropic, Gemini, Ollama) |
| Deploy | Docker Compose |

## 🔑 Configuración de LLM

Edita `backend/.env` con al menos una API key:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
```

Para modelos locales, instala [Ollama](https://ollama.com) y los modelos estarán disponibles automáticamente.

## 📁 Estructura

```
├── frontend/          # Vue.js 3 + Vite
│   ├── src/
│   │   ├── views/     # Dashboard, Editor, Monitor
│   │   ├── styles/    # Design system CSS
│   │   └── api.ts     # API client tipado
├── backend/           # FastAPI
│   ├── api/routes/    # Endpoints REST
│   ├── core/          # Motor de orquestación
│   ├── models/        # SQLAlchemy + Pydantic
│   └── db/            # Database setup
└── docker-compose.yml
```

## 📜 Licencia

MIT
