import pytest
from pathlib import Path
from utils.fs_utils import validate_sandbox_path, PathTraversalError


class TestFsUtilsUnit:
    """Unit tests for fs_utils validate_sandbox_path (T026)."""

    def test_validate_sandbox_path_allows_path_inside_allowed_root(self, tmp_path):
        documents_dir = tmp_path / "documents"
        documents_dir.mkdir()
        test_file = documents_dir / "doc.md"
        test_file.write_text("Hello", encoding="utf-8")

        resolved = validate_sandbox_path(
            "documents/doc.md",
            allowed_roots=["documents"],
            workspace_root=tmp_path
        )
        assert resolved == test_file.resolve()

    def test_validate_sandbox_path_blocks_parent_directory_navigation(self, tmp_path):
        documents_dir = tmp_path / "documents"
        documents_dir.mkdir()

        with pytest.raises(PathTraversalError):
            validate_sandbox_path(
                "documents/../../etc/passwd",
                allowed_roots=["documents"],
                workspace_root=tmp_path
            )

    def test_validate_sandbox_path_blocks_encoded_traversal(self, tmp_path):
        documents_dir = tmp_path / "documents"
        documents_dir.mkdir()

        with pytest.raises(PathTraversalError):
            validate_sandbox_path(
                "documents/%2e%2e/%2e%2e/secret.txt",
                allowed_roots=["documents"],
                workspace_root=tmp_path
            )
