import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from services.artifact_service import ArtifactService
import api.artifacts as artifacts_module


@pytest.fixture
def payload_limit_client(tmp_path):
    """Fixture providing isolated workspace with oversized and binary files."""
    files_dir = tmp_path / "files"
    files_dir.mkdir()

    # 1. Create an oversized text file (5.5 MB)
    large_file = files_dir / "large_execution.log"
    # Write 5.5 MB using sparse/quick write
    with open(large_file, "wb") as f:
        f.seek(5500000)
        f.write(b"\0")

    # 2. Create binary files
    bin_file = files_dir / "raw_recording.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\xFF\xFE")

    png_file = files_dir / "screenshot.png"
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    pdf_file = files_dir / "document.pdf"
    pdf_file.write_bytes(b"%PDF-1.4\n")

    # 3. Create regular valid Markdown file
    valid_file = files_dir / "normal.md"
    valid_file.write_text("# Normal Markdown Document", encoding="utf-8")

    service = ArtifactService(workspace_root=tmp_path)
    artifacts_module.artifact_service = service
    client = TestClient(app)
    return client, tmp_path


class TestPayloadLimitAndMediaType:
    """Tests for ADR-009 (5MB payload limit and unsupported binary media policy)."""

    def test_get_artifacts_content_with_oversized_file_returns_413_payload_too_large(self, payload_limit_client):
        client, _ = payload_limit_client

        response = client.get("/api/v1/artifacts/content?path=files/large_execution.log")

        assert response.status_code == 413
        data = response.json()
        assert data["error_code"] == "PAYLOAD_TOO_LARGE"
        assert "sobrepasa el límite máximo admitido de 5 MB" in data["detail"]

    def test_get_artifacts_content_with_bin_extension_returns_415_unsupported_media_type(self, payload_limit_client):
        client, _ = payload_limit_client

        response = client.get("/api/v1/artifacts/content?path=files/raw_recording.bin")

        assert response.status_code == 415
        data = response.json()
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"
        assert "formato binario" in data["detail"]

    def test_get_artifacts_content_with_png_extension_returns_415(self, payload_limit_client):
        client, _ = payload_limit_client

        response = client.get("/api/v1/artifacts/content?path=files/screenshot.png")

        assert response.status_code == 415
        data = response.json()
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_get_artifacts_content_with_pdf_extension_returns_415(self, payload_limit_client):
        client, _ = payload_limit_client

        response = client.get("/api/v1/artifacts/content?path=files/document.pdf")

        assert response.status_code == 415
        data = response.json()
        assert data["error_code"] == "UNSUPPORTED_MEDIA_TYPE"

    def test_get_artifacts_content_with_normal_size_succeeds(self, payload_limit_client):
        client, _ = payload_limit_client

        response = client.get("/api/v1/artifacts/content?path=files/normal.md")

        assert response.status_code == 200
        data = response.json()
        assert data["is_oversized"] is False
        assert data["is_unsupported_media"] is False
        assert "Normal Markdown Document" in data["raw_content"]
