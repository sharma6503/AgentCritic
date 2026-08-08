from fastapi import FastAPI
from code_reviewer.config import Config

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "model": Config().agent_settings.expert_model
    }