
from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.resumes import router as resumes_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.screening import router as screening_router


app = FastAPI(
    title="TalentFlow AI Recruiting Agent",
    description=(
        "AI-powered resume screening using "
        "FastAPI, LangChain, and LangGraph"
    ),
    version="1.2.0",
)


# Register application routers
app.include_router(health_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(screening_router)
