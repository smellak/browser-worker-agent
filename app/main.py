import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl

from .agent import run_agent


app = FastAPI(
    title="Browser Worker Agent",
    description="Microservicio Playwright + OpenAI para exploración web autónoma",
    version="0.1.0",
)


class RunAgentRequest(BaseModel):
    url: HttpUrl
    goal: str
    max_steps: int = 20


class RunAgentResponse(BaseModel):
    start_url: HttpUrl
    goal: str
    max_steps: int
    steps: list
    aggregated_content: str
    finished_reason: str


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Browser Worker Agent vivo",
    }


@app.post("/run-agent", response_model=RunAgentResponse)
def run_agent_endpoint(payload: RunAgentRequest):
    """
    Endpoint principal: recibe una URL, un objetivo y un máximo de pasos,
    ejecuta el agente y devuelve el resultado.
    """
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY no está configurado en el entorno",
        )

    try:
        result = run_agent(
            start_url=str(payload.url),
            goal=payload.goal,
            max_steps=payload.max_steps,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
