from fastapi import APIRouter, Query, HTTPException
from models.directory import ArtifactTreeResponse
from models.artifact import ArtifactContent
from services.artifact_service import ArtifactService

router = APIRouter(tags=["Artifact Explorer"])
artifact_service = ArtifactService()


@router.get("/artifacts/tree", response_model=ArtifactTreeResponse, summary="Escaneo recursivo del árbol de entregables")
async def get_artifact_tree(
    root: str = Query("all", description="Raíz a inspeccionar ('docs', 'specs', '.specify', 'all')")
) -> ArtifactTreeResponse:
    """
    Escanea recursivamente las raíces del workspace autorizadas ('docs/', 'specs/', '.specify/').
    Calcula el conteo de entregables directos y detecta directorios vacíos (Empty State).
    """
    return artifact_service.get_artifact_tree(root=root)


@router.get("/workspace/tree", response_model=ArtifactTreeResponse, summary="Alias interoperable para árbol de entregables")
async def get_workspace_tree(
    root: str = Query("all", description="Raíz a inspeccionar ('docs', 'specs', '.specify', 'all')")
) -> ArtifactTreeResponse:
    """Ruta de interoperabilidad alineada con contracts/api-contract.md."""
    return artifact_service.get_artifact_tree(root=root)


@router.get("/artifacts/content", response_model=ArtifactContent, summary="Lectura segura del contenido de un entregable")
async def get_artifact_content(
    path: str = Query(..., description="Ruta relativa del archivo dentro del sandbox autorizado")
) -> ArtifactContent:
    """
    Lectura segura del contenido UTF-8 de un archivo documental con guardas de sandbox (403),
    verificación de existencia (404), límite de tamaño de 5MB (413) y filtro de binarios (415).
    """
    return await artifact_service.get_artifact_content(relative_path=path)


@router.get("/workspace/file", response_model=ArtifactContent, summary="Alias interoperable para lectura de artefacto")
async def get_workspace_file(
    path: str = Query(..., description="Ruta relativa del archivo dentro del sandbox autorizado")
) -> ArtifactContent:
    """Ruta de interoperabilidad alineada con contracts/api-contract.md."""
    return await artifact_service.get_artifact_content(relative_path=path)
