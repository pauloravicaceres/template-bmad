import os
import tempfile
import pytest
from core.config import settings
from services.file_watcher import MultiDirectoryWatcherHandler
from services.connection_manager import ConnectionManager
from models.observability import FileMetadataRecord


class TestLargeFileMetadataPolicy:
    """Tests for Metadata-Only policy on files > 5MB (T028 / CB-05 / ADR-012)."""

    def test_file_watcher_flags_large_file_as_metadata_only(self, tmp_path):
        import asyncio
        loop = asyncio.new_event_loop()
        handler = MultiDirectoryWatcherHandler(loop=loop)

        # Create a mock large file (> 5MB threshold)
        large_file = tmp_path / "large_dataset.bin"
        target_size = settings.LARGE_FILE_THRESHOLD_BYTES + 1024  # 5MB + 1KB
        
        # Write sparse file or seek to create target size without wasting disk IO
        with open(large_file, "wb") as f:
            f.seek(target_size - 1)
            f.write(b"\0")

        assert os.path.getsize(large_file) == target_size

        size_bytes, is_large_file, metadata_only, mime_type = handler._get_file_info(str(large_file))

        assert size_bytes == target_size
        assert is_large_file is True
        assert metadata_only is True

        loop.close()

    def test_small_file_is_not_flagged_as_large(self, tmp_path):
        import asyncio
        loop = asyncio.new_event_loop()
        handler = MultiDirectoryWatcherHandler(loop=loop)

        small_file = tmp_path / "normal_doc.md"
        small_file.write_text("# Normal Title\nContent here", encoding="utf-8")

        size_bytes, is_large_file, metadata_only, mime_type = handler._get_file_info(str(small_file))

        assert size_bytes < settings.LARGE_FILE_THRESHOLD_BYTES
        assert is_large_file is False
        assert metadata_only is False
        assert mime_type == "text/markdown"

        loop.close()

    @pytest.mark.anyio
    async def test_broadcast_artifact_changed_enforces_metadata_only(self):
        cm = ConnectionManager()
        dispatched_messages = []

        # Mock broadcast to inspect payload
        async def mock_broadcast(msg):
            dispatched_messages.append(msg)

        cm.broadcast = mock_broadcast

        await cm.broadcast_artifact_changed(
            action="CREATED",
            path="docs/exports/huge_dump.tar.gz",
            size_bytes=20_000_000,
            is_large_file=True,
            metadata_only=True,
            mime_type="application/gzip",
            coalesced_count=1
        )

        assert len(dispatched_messages) == 1
        event = dispatched_messages[0]
        assert event["event_type"] == "ARTIFACT_CHANGED"
        assert event["payload"]["file_metadata"]["is_large_file"] is True
        assert event["payload"]["file_metadata"]["metadata_only"] is True
        assert event["payload"]["file_metadata"]["size_bytes"] == 20_000_000
        # Verify no raw payload of content exists
        assert "content" not in event["payload"]
        assert "raw_content" not in event["payload"]
