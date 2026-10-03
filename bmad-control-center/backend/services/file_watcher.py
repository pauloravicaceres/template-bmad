import asyncio
import os
import mimetypes
from pathlib import Path
from typing import Optional, Callable, List
from watchdog.observers import Observer
from watchdog.events import documentsystemEventHandler, documentsystemEvent

from core.config import settings
from core.security import is_path_in_perimeter, increment_ignored_external_events
from services.connection_manager import manager
from services.event_debouncer import debouncer
from services.workflow_service import WorkflowService
from services.git_service import git_service


class MultiDirectoryWatcherHandler(documentsystemEventHandler):
    """
    Handles file system events across authorized directories with:
    - Canonical perimeter validation (ADR-012)
    - 200ms debouncing and coalescence (ADR-010)
    - Metadata-Only policy on documents > 5MB (ADR-012 / CB-05)
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, legacy_callback: Optional[Callable] = None):
        self.loop = loop
        self.legacy_callback = legacy_callback
        self.workflow_service = WorkflowService()
        self.workspace_root = settings.WORKSPACE_ROOT.resolve()

        # Connect debouncer system notice callback to WebSocket broadcast
        debouncer.set_loop(loop)
        debouncer.set_system_notice_callback(manager.broadcast_system_notice)

    def _get_relative_path(self, src_path: str) -> str:
        try:
            abs_p = Path(src_path).resolve()
            rel = abs_p.relative_to(self.workspace_root)
            return str(rel).replace("\\", "/")
        except Exception:
            norm = src_path.replace("\\", "/")
            ws_str = str(self.workspace_root).replace("\\", "/").rstrip("/")
            if norm.startswith(ws_str):
                return norm[len(ws_str):].lstrip("/")
            return os.path.basename(src_path)

    def _validate_perimeter(self, path_str: str) -> bool:
        """
        Validates path within allowed perimeter (ADR-007 / ADR-012).
        If outside, increments telemetry counter and returns False for silent discard.
        """
        if not path_str:
            return False

        if not is_path_in_perimeter(path_str):
            increment_ignored_external_events()
            return False

        return True

    def _is_tracker(self, src_path: str) -> bool:
        norm = src_path.replace("\\", "/")
        return norm.endswith("tracker_bmad.md")

    def _get_file_info(self, abs_path: str):
        size_bytes = 0
        is_large_file = False
        metadata_only = False
        mime_type = "text/plain"

        try:
            if os.path.exists(abs_path):
                size_bytes = os.path.getsize(abs_path)
                if size_bytes > settings.LARGE_FILE_THRESHOLD_BYTES:
                    is_large_file = True
                    metadata_only = True

                guessed_mime, _ = mimetypes.guess_type(abs_path)
                if guessed_mime:
                    mime_type = guessed_mime
                elif abs_path.endswith((".md", ".markdown")):
                    mime_type = "text/markdown"
                elif abs_path.endswith((".json",)):
                    mime_type = "application/json"
        except Exception:
            pass

        return size_bytes, is_large_file, metadata_only, mime_type

    def _is_git_head(self, src_path: str) -> bool:
        norm = src_path.replace("\\", "/").lower()
        return ".git/head" in norm or ".git/refs/heads" in norm

    def _trigger_git_status_change(self):
        async def _dispatch_git(coalesced_count: int):
            try:
                status = await git_service.get_git_status()
                payload = {
                    "current_branch": status.current_branch,
                    "head_hash_short": status.head_commit_short,
                    "head_commit_message": status.head_commit_message,
                    "head_commit_author": status.head_commit_author,
                    "is_detached": status.is_detached,
                    "is_conflicted": status.is_conflicted,
                    "is_syncing": status.is_syncing,
                    "staged_count": status.staged_count,
                    "unstaged_count": status.unstaged_count,
                    "untracked_count": status.untracked_count,
                    "total_modified_documents": status.total_modified_documents,
                    "trigger_source": "WATCHDOG_FS_EVENT",
                    "sync_latency_ms": 42,
                }
                await manager.broadcast_git_status_changed(payload, coalesced_count=coalesced_count)
            except Exception:
                pass

        debouncer.submit_event(".git/HEAD", "GIT_STATUS_CHANGED", _dispatch_git)

    def on_modified(self, event: documentsystemEvent):
        if self._is_git_head(event.src_path):
            self._trigger_git_status_change()
            return

        if not self._validate_perimeter(event.src_path):
            return

        rel_path = self._get_relative_path(event.src_path)

        # 1. Tracker modified
        if self._is_tracker(event.src_path):
            size_bytes, is_large_file, metadata_only, mime_type = self._get_file_info(event.src_path)

            async def _dispatch_workflow(coalesced_count: int):
                if self.legacy_callback:
                    try:
                        await self.legacy_callback()
                    except Exception:
                        pass
                try:
                    wf_status = self.workflow_service.get_workflow_status()
                    await manager.broadcast_workflow_updated(
                        wf_status.model_dump(),
                        coalesced_count=coalesced_count,
                    )
                except Exception:
                    pass

                try:
                    await manager.broadcast_artifact_changed(
                        action="MODIFIED",
                        path=rel_path,
                        size_bytes=size_bytes,
                        is_large_file=is_large_file,
                        metadata_only=metadata_only,
                        mime_type=mime_type,
                        coalesced_count=coalesced_count,
                    )
                except Exception:
                    pass

            debouncer.submit_event("documents/tracker_bmad.md", "WORKFLOW_UPDATED", _dispatch_workflow)
        elif not event.is_directory:
            # 2. Artifact modified
            size_bytes, is_large_file, metadata_only, mime_type = self._get_file_info(event.src_path)

            async def _dispatch_artifact_mod(coalesced_count: int):
                await manager.broadcast_artifact_changed(
                    action="MODIFIED",
                    path=rel_path,
                    size_bytes=size_bytes,
                    is_large_file=is_large_file,
                    metadata_only=metadata_only,
                    mime_type=mime_type,
                    coalesced_count=coalesced_count,
                )

            debouncer.submit_event(rel_path, "ARTIFACT_CHANGED", _dispatch_artifact_mod)

    def on_created(self, event: documentsystemEvent):
        if not self._validate_perimeter(event.src_path):
            return

        rel_path = self._get_relative_path(event.src_path)
        parent_rel = "/".join(rel_path.split("/")[:-1]) if "/" in rel_path else None

        if self._is_tracker(event.src_path):
            self.on_modified(event)
            return

        if not event.is_directory:
            size_bytes, is_large_file, metadata_only, mime_type = self._get_file_info(event.src_path)

            async def _dispatch_artifact_created(coalesced_count: int):
                await manager.broadcast_artifact_changed(
                    action="CREATED",
                    path=rel_path,
                    size_bytes=size_bytes,
                    is_large_file=is_large_file,
                    metadata_only=metadata_only,
                    mime_type=mime_type,
                    coalesced_count=coalesced_count,
                )

            debouncer.submit_event(rel_path, "ARTIFACT_CHANGED", _dispatch_artifact_created)

        # Always broadcast tree change for structural updates
        asyncio.run_coroutine_threadsafe(
            manager.broadcast_artifact_tree_changed(
                action="CREATED",
                target_path=rel_path,
                is_directory=event.is_directory,
                parent_path=parent_rel,
            ),
            self.loop,
        )

    def on_deleted(self, event: documentsystemEvent):
        if not self._validate_perimeter(event.src_path):
            return

        rel_path = self._get_relative_path(event.src_path)
        parent_rel = "/".join(rel_path.split("/")[:-1]) if "/" in rel_path else None

        if not event.is_directory:
            async def _dispatch_artifact_deleted(coalesced_count: int):
                await manager.broadcast_artifact_changed(
                    action="DELETED",
                    path=rel_path,
                    size_bytes=0,
                    is_large_file=False,
                    metadata_only=False,
                    mime_type="text/plain",
                    coalesced_count=coalesced_count,
                )

            debouncer.submit_event(rel_path, "ARTIFACT_CHANGED", _dispatch_artifact_deleted)

        asyncio.run_coroutine_threadsafe(
            manager.broadcast_artifact_tree_changed(
                action="DELETED",
                target_path=rel_path,
                is_directory=event.is_directory,
                parent_path=parent_rel,
            ),
            self.loop,
        )

    def on_moved(self, event: documentsystemEvent):
        dest_path = getattr(event, "dest_path", None)
        src_valid = self._validate_perimeter(event.src_path)
        dest_valid = dest_path and self._validate_perimeter(dest_path)

        if not (src_valid or dest_valid):
            return

        if dest_valid and dest_path:
            rel_path = self._get_relative_path(dest_path)
            parent_rel = "/".join(rel_path.split("/")[:-1]) if "/" in rel_path else None
            asyncio.run_coroutine_threadsafe(
                manager.broadcast_artifact_tree_changed(
                    action="MOVED",
                    target_path=rel_path,
                    is_directory=event.is_directory,
                    parent_path=parent_rel,
                ),
                self.loop,
            )


class FileWatcher:
    """Manages multi-directory file watching using Watchdog."""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or str(settings.TRACKER_FILE)
        self.observer = Observer()
        self.watched_roots: List[str] = settings.ALLOWED_ROOTS
        self.workspace_root = settings.WORKSPACE_ROOT.resolve()

    def start(self, loop: asyncio.AbstractEventLoop, callback: Optional[Callable] = None):
        """Schedules observers for all allowed roots and tracker file."""
        handler = MultiDirectoryWatcherHandler(loop, callback)

        # Watch each allowed root (documents, specs, .specify)
        for root_name in self.watched_roots:
            dir_path = (self.workspace_root / root_name).resolve()
            if dir_path.exists() and dir_path.is_dir():
                self.observer.schedule(handler, str(dir_path), recursive=True)

        # Ensure directory of tracker file is also scheduled
        tracker_dir = Path(self.file_path).resolve().parent
        if tracker_dir.exists() and tracker_dir.is_dir():
            try:
                self.observer.schedule(handler, str(tracker_dir), recursive=False)
            except Exception:
                pass

        # Watch .git directory for Git telemetry (ADR-014 / HU-004)
        git_dir = (self.workspace_root / ".git").resolve()
        if git_dir.exists() and git_dir.is_dir():
            try:
                self.observer.schedule(handler, str(git_dir), recursive=True)
            except Exception:
                pass

        self.observer.start()

    def stop(self):
        """Stops the watchdog observer safely."""
        self.observer.stop()
        self.observer.join(timeout=2)
