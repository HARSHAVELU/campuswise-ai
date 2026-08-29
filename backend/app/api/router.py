from fastapi import APIRouter

from app.api.routes import (
    ai,
    assessment,
    auth,
    chat,
    courses,
    degree,
    health,
    professors,
    rag,
    recommendations,
    schedule,
    sections,
    terms,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(professors.router)
api_router.include_router(sections.router)
api_router.include_router(terms.router)
api_router.include_router(ai.router)
api_router.include_router(chat.router)
api_router.include_router(recommendations.router)
api_router.include_router(rag.router)
api_router.include_router(assessment.router)
api_router.include_router(schedule.router)
api_router.include_router(degree.degrees_router)
api_router.include_router(degree.degree_router)
