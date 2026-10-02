import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.backend.main import app
from app.backend.services.artifact_service import ArtifactService
import app.backend.api.artifacts as artifacts_module


@pytest.fixture
def isolated_workspace(tmp_path):
    """Fixture creating an isolated workspace structure with files, specs and .specify."""
    files_dir = tmp_path / "files"
    specs_dir = tmp_path / "specs"
    specify_dir = tmp_path / ".specify"

    files_dir.mkdir()
    specs_dir.mkdir()
    specify_dir.mkdir()

    # Create dummy files
    ba_dir = files_dir / "business-analyst"
    ba_dir.mkdir()
    hu_file = ba_dir / "002-HU.md"
    hu_file.write_text("# Feature BDD\n\n```mermaid\ngraph TD\nA-->B\n```", encoding="utf-8")

    # Empty directory (US2 / T023)
    empty_sa_dir = files_dir / "solutions-architect"
    empty_sa_dir.mkdir()

    # Spec file
    readme_spec = specs_dir / "README.md"
    readme_spec.write_text("# Product State Ledger", encoding="utf-8")

    # Wire up isolated service
    isolated_service = ArtifactService(workspace_root=tmp_path)
    artifacts_module.artifact_service = isolated_service

    client = TestClient(app)
    return client, isolated_service, tmp_path


class TestArtifactsApi:
    """Tests for GET /api/v1/artifacts/tree and /api/v1/artifacts/content."""

    def test_get_artifacts_tree_with_all_roots_returns_hierarchical_tree(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/artifacts/tree")

        assert response.status_code == 200
        data = response.json()
        assert "root_node" in data
        assert data["root_node"]["name"] == "Dashboard BMAD Workspace"
        assert len(data["root_node"]["children"]) >= 3

        # Interoperability fields for api-contract.md
        assert data["type"] == "DIRECTORY"
        assert data["name"] == "root"
        assert data["path"] == "/"

    def test_get_artifacts_tree_with_invalid_root_returns_400_invalid_parameter(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/artifacts/tree?root=app")

        assert response.status_code == 400
        error_data = response.json()
        assert error_data["error_code"] == "INVALID_PARAMETER"
        assert "no es una raíz autorizada" in error_data["detail"]

    def test_get_artifacts_tree_detects_empty_directories_without_failing(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/artifacts/tree?root=files")

        assert response.status_code == 200
        data = response.json()
        files_node = next(c for c in data["root_node"]["children"] if c["name"] == "files")
        
        # Check solutions-architect directory is marked is_empty=True and child_file_count=0
        sa_node = next(c for c in files_node["children"] if c["name"] == "solutions-architect")
        assert sa_node["is_empty"] is True
        assert sa_node["child_file_count"] == 0

        # Check business-analyst directory has child_file_count=1
        ba_node = next(c for c in files_node["children"] if c["name"] == "business-analyst")
        assert ba_node["child_file_count"] == 1
        assert ba_node["is_empty"] is False

    def test_get_artifacts_content_with_valid_markdown_file_returns_200_and_payload(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/artifacts/content?path=files/business-analyst/002-HU.md")

        assert response.status_code == 200
        data = response.json()
        assert data["relative_path"] == "files/business-analyst/002-HU.md"
        assert data["filename"] == "002-HU.md"
        assert data["detected_format"] == "MARKDOWN"
        assert data["encoding"] == "utf-8"
        assert "Feature BDD" in data["raw_content"]
        assert data["is_oversized"] is False
        assert data["is_unsupported_media"] is False
        assert data["content"] == data["raw_content"]
        assert data["format"] == "MARKDOWN"

    def test_get_workspace_file_alias_returns_same_content(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/workspace/file?path=specs/README.md")

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "README.md"
        assert "Product State Ledger" in data["raw_content"]

    def test_get_artifacts_content_with_non_existent_file_returns_404_not_found(self, isolated_workspace):
        client, _, _ = isolated_workspace

        response = client.get("/api/v1/artifacts/content?path=files/inexistente.md")

        assert response.status_code == 404
        error_data = response.json()
        assert error_data["error_code"] == "ARTIFACT_NOT_FOUND"
        assert "no existe en el sistema de archivos local" in error_data["detail"]
