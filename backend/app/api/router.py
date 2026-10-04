"""
ResQ-AI Master API Router.
Mounts all domain routers under `/api`.
"""

from fastapi import APIRouter
from app.api import (
    incidents,
    resources,
    agent,
    search,
    inference,
    csp,
    risk,
    planning,
    learning,
    decisions,
    lab,
)

api_router = APIRouter()
api_router.include_router(incidents.router, prefix="/incidents", tags=["Incidents"])
api_router.include_router(resources.router, prefix="", tags=["Resources"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(inference.router, prefix="/inference", tags=["Inference"])
api_router.include_router(csp.router, prefix="/csp", tags=["CSP"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk"])
api_router.include_router(planning.router, prefix="/planning", tags=["Planning"])
api_router.include_router(learning.router, prefix="/learning", tags=["Learning"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decisions"])
api_router.include_router(lab.router, prefix="/lab", tags=["Lab"])
