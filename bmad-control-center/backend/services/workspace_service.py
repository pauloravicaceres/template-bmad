from services.artifact_service import ArtifactService

# WorkspaceService is an alias/subclass of ArtifactService for task naming compatibility
class WorkspaceService(ArtifactService):
    pass

__all__ = ["WorkspaceService", "ArtifactService"]
