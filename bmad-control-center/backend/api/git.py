from typing import Optional
from fastapi import APIRouter, Query, HTTPException

from models.git import (
    GitStatusResponse,
    GitCommitListResponse,
    GitBranchListResponse,
    GitErrorResponse,
)
from services.git_service import (
    git_service,
    GitRepoNotFoundError,
    GitCommandError,
)

router = APIRouter(prefix="/git", tags=["Git Telemetry"])


@router.get(
    "/status",
    response_model=GitStatusResponse,
    responses={
        404: {"model": GitErrorResponse, "description": "Repositorio Git no encontrado"},
        500: {"model": GitErrorResponse, "description": "Error al ejecutar comando Git"},
    },
)
async def get_git_status() -> GitStatusResponse:
    """
    Returns live or cached Git telemetry (branch, HEAD, working tree, resilience flags) (ADR-013, ADR-014, ADR-015).
    """
    return await git_service.get_git_status()


@router.get(
    "/commits",
    response_model=GitCommitListResponse,
    responses={
        400: {"model": GitErrorResponse, "description": "Parámetros de paginación inválidos"},
        404: {"model": GitErrorResponse, "description": "Repositorio Git no encontrado"},
    },
)
async def get_git_commits(
    limit: int = Query(50, ge=1, le=500, description="Cantidad máxima de commits a retornar"),
    offset: int = Query(0, ge=0, description="Desplazamiento para paginación"),
    branch: Optional[str] = Query(None, description="Rama objetivo opcional"),
) -> GitCommitListResponse:
    """
    Returns chronological commit history with pagination (< 300ms SLA) and diff elision (ADR-014).
    """
    return await git_service.get_commits(limit=limit, offset=offset, branch=branch)


@router.get(
    "/branches",
    response_model=GitBranchListResponse,
    responses={
        404: {"model": GitErrorResponse, "description": "Repositorio Git no encontrado"},
    },
)
async def get_git_branches() -> GitBranchListResponse:
    """
    Returns active local branches and upstream correlation (ADR-014).
    """
    return await git_service.get_branches()
