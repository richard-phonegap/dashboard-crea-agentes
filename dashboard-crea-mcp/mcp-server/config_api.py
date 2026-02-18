from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml
import os
import uvicorn
import requests
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIG_PATH = os.getenv("MCP_CONFIG_PATH", "../shared/config.yaml")

class ConfigUpdate(BaseModel):
    config: dict

@app.get("/api/config")
def get_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {"error": "Config file not found", "path": CONFIG_PATH}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config")
def update_config(update: ConfigUpdate):
    try:
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(update.config, f)
        return {"status": "success", "message": "Config updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class OllamaRequest(BaseModel):
    api_base: str

@app.post("/api/ollama/models")
def get_ollama_models(req: OllamaRequest):
    try:
        # Ensure URL has scheme
        url = req.api_base.rstrip('/')
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        
        # Call Ollama tags endpoint
        resp = requests.get(f"{url}/api/tags", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        # Extract model names
        models = [m['name'] for m in data.get('models', [])]
        return {"models": models}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to Ollama: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
