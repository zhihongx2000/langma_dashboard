from fastapi import APIRouter

from backend.api.routes.persona_analysis import router as persona_analysis_router


api_router = APIRouter()
api_router.include_router(persona_analysis_router)
