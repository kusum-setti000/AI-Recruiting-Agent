
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/")
def home():
    return {
        "message": "TalentFlow AI Recruiting Agent is running",
        "version": "1.2.0",
        "frameworks": [
            "FastAPI",
            "LangChain",
            "LangGraph",
        ],
    }
