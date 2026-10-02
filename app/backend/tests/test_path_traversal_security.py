import pytest
from fastapi.testclient import TestClient
from app.backend.main import app
from app.backend.core.security import validate_sandbox_path, PathTraversalError
from app.backend.services.artifact_service import ArtifactService
import app.backend.api.artifacts as artifacts_module


@pytest.fixture
def sandbox_client(tmp_path):
    """Fixture providing isolated workspace and client for security audit."""
    files_dir = tmp_path / "files"
    specs_dir = tmp_path / "specs"
    specify_dir = tmp_path / ".specify"
    files_dir.mkdir()
    specs_dir.mkdir()
    specify_dir.mkdir()

    # Secret file outside sandbox
    secret_env = tmp_path / ".env"
    secret_env.write_text("SUPER_SECRET_KEY=12345", encoding="utf-8")

    # Valid file inside sandbox
    valid_file = files_dir / "valid.md"
    valid_file.write_text("# Valid File", encoding="utf-8")

    service = ArtifactService(workspace_root=tmp_path)
    artifacts_module.artifact_service = service
    client = TestClient(app)
    return client, tmp_path


class TestPathTraversalSecurity:
    """Security tests for ADR-007 Sandboxing Path Traversal Guard."""

    def test_validate_sandbox_path_direct_unit_rejects_parent_escape(self, sandbox_client):
        _, ws_root = sandbox_client
        allowed = ["files", "specs", ".specify"]

        with pytest.raises(PathTraversalError):
            validate_sandbox_path("../.env", allowed_roots=allowed, workspace_root=ws_root)

        with pytest.raises(PathTraversalError):
            validate_sandbox_path("../../etc/passwd", allowed_roots=allowed, workspace_root=ws_root)

        with pytest.raises(PathTraversalError):
            validate_sandbox_path("..\\..\\Windows\\System32", allowed_roots=allowed, workspace_root=ws_root)

    def test_validate_sandbox_path_direct_unit_rejects_double_url_encoding(self, sandbox_client):
        _, ws_root = sandbox_client
        allowed = ["files", "specs", ".specify"]

        # Double URL encoded ../
        double_encoded = "%252e%252e%252f.env"
        with pytest.raises(PathTraversalError):
            validate_sandbox_path(double_encoded, allowed_roots=allowed, workspace_root=ws_root)

    def test_validate_sandbox_path_direct_unit_rejects_null_bytes(self, sandbox_client):
        _, ws_root = sandbox_client
        allowed = ["files", "specs", ".specify"]

        with pytest.raises(PathTraversalError):
            validate_sandbox_path("files/valid.md\x00.exe", allowed_roots=allowed, workspace_root=ws_root)

    def test_get_artifacts_content_with_relative_escape_returns_403_path_traversal(self, sandbox_client):
        client, _ = sandbox_client

        response = client.get("/api/v1/artifacts/content?path=../.env")

        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PATH_TRAVERSAL_DETECTED"
        assert "fuera de los límites autorizados del sandbox" in data["detail"]

    def test_get_artifacts_content_with_deep_escape_returns_403(self, sandbox_client):
        client, _ = sandbox_client

        response = client.get("/api/v1/artifacts/content?path=files/../../../../etc/shadow")

        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_get_artifacts_content_with_windows_backslash_escape_returns_403(self, sandbox_client):
        client, _ = sandbox_client

        response = client.get(r"/api/v1/artifacts/content?path=..\..\boot.ini")

        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PATH_TRAVERSAL_DETECTED"

    def test_get_workspace_file_alias_also_blocks_path_traversal(self, sandbox_client):
        client, _ = sandbox_client

        response = client.get("/api/v1/workspace/file?path=../config_bmad.json")

        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "PATH_TRAVERSAL_DETECTED"
