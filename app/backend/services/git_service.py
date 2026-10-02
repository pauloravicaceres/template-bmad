import asyncio
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException

from app.backend.core.config import settings
from app.backend.models.git import (
    GitStatusResponse,
    GitWorkingTree,
    GitFileEntry,
    GitFileCategory,
    GitCommitListResponse,
    GitCommitItem,
    GitCommitFileChange,
    GitBranchListResponse,
    GitBranchItem,
)


class GitRepoNotFoundError(HTTPException):
    """Exception raised when .git directory is missing in workspace (ADR-015 / CB-02)."""
    def __init__(
        self,
        detail: str = "No se detectó un repositorio Git inicializado en el espacio de trabajo actual. Ejecute 'git init' para habilitar la telemetría.",
    ):
        super().__init__(status_code=404, detail=detail)
        self.error_code = "GIT_REPO_NOT_FOUND"


class GitCommandError(HTTPException):
    """Exception raised when a git CLI command fails."""
    def __init__(self, detail: str = "Error al ejecutar el comando Git."):
        super().__init__(status_code=500, detail=detail)
        self.error_code = "GIT_COMMAND_ERROR"


class GitService:
    """
    Service for inspecting Git repository status, commits and branches
    under strict read-only operation (ADR-013, ADR-014, ADR-015).
    """

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or settings.WORKSPACE_ROOT).resolve()
        self._last_snapshot: Optional[GitStatusResponse] = None
        self._cached_total_count: Optional[int] = None

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _is_git_repo(self) -> bool:
        """Checks if .git directory or file exists in workspace root."""
        git_dir = self.workspace_root / ".git"
        if not git_dir.exists():
            raise GitRepoNotFoundError()
        return True

    def _sanitize_string(self, text: Optional[str]) -> str:
        """Removes null bytes and cleans up output."""
        if not text:
            return ""
        return text.replace("\x00", "").strip()

    def _infer_agent_role(self, author_name: str, message: str) -> Optional[str]:
        """Infers agent role from commit author or conventional commit message."""
        combined = f"{author_name} {message}".lower()
        if "product manager" in combined or "pm:" in combined:
            return "Product Manager"
        if "business analyst" in combined or "ba:" in combined:
            return "Business Analyst"
        if "qa documental" in combined:
            return "QA Documental"
        if "designer ux" in combined or "ux:" in combined:
            return "Designer UX"
        if "solutions architect" in combined or "sa:" in combined:
            return "Solutions Architect"
        if "data architect" in combined or "da:" in combined:
            return "Data Architect"
        if "api architect" in combined or "api:" in combined:
            return "API Architect"
        if "qa-tech" in combined or "qa tech" in combined or "qt:" in combined:
            return "QA-Tech"
        if "backend" in combined or "dev-backend" in combined or "task-" in combined and "-be-" in combined:
            return "Senior Backend Developer"
        if "frontend" in combined or "dev-front" in combined or "task-" in combined and "-fe-" in combined:
            return "Senior Frontend Developer"
        if "qa automation" in combined or "qa-auto" in combined or "task-" in combined and "-qa-" in combined:
            return "QA Automation"
        if "watcher" in combined:
            return "Watcher BMAD"
        return author_name if author_name and author_name != "Desconocido" else None

    async def _run_git_command(self, *args: str, timeout: float = 5.0) -> Tuple[str, str, int]:
        """
        Executes native Git CLI via subprocess without shell interpolation (ADR-014).
        """
        self._is_git_repo()

        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                *args,
                cwd=str(self.workspace_root),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout_b, stderr_b = await asyncio.wait_for(process.communicate(), timeout=timeout)
            stdout = self._sanitize_string(stdout_b.decode("utf-8", errors="replace"))
            stderr = self._sanitize_string(stderr_b.decode("utf-8", errors="replace"))
            return stdout, stderr, process.returncode or 0
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            raise GitCommandError(f"El comando Git expiró tras {timeout}s.")
        except FileNotFoundError:
            raise GitCommandError("El binario de 'git' no se encuentra en el PATH del sistema.")
        except GitRepoNotFoundError:
            raise
        except Exception as e:
            raise GitCommandError(f"Error inesperado al ejecutar git: {str(e)}")

    async def _check_and_handle_lock(self) -> bool:
        """
        Detects .git/index.lock and retries up to 3 times (50ms, 100ms, 200ms).
        Returns True if lock persists (contention), False if clear (ADR-015).
        """
        lock_file = self.workspace_root / ".git" / "index.lock"
        if not lock_file.exists():
            return False

        retries = [0.05, 0.10, 0.20]
        for delay in retries:
            await asyncio.sleep(delay)
            if not lock_file.exists():
                return False

        return True

    async def get_git_status(self) -> GitStatusResponse:
        """
        Returns full Git status telemetry (US1, US3 / ADR-014, ADR-015).
        """
        self._is_git_repo()

        # 1. Check lock contention before command execution
        is_locked = await self._check_and_handle_lock()
        if is_locked and self._last_snapshot:
            cached = self._last_snapshot.model_copy()
            cached.is_syncing = True
            cached.captured_at_utc = self._now_iso()
            return cached

        # 2. Run git status --porcelain=v2 --branch
        stdout, stderr, code = await self._run_git_command("status", "--porcelain=v2", "--branch")
        if code != 0:
            if "index.lock" in stderr and self._last_snapshot:
                cached = self._last_snapshot.model_copy()
                cached.is_syncing = True
                cached.captured_at_utc = self._now_iso()
                return cached
            raise GitCommandError(f"git status falló: {stderr}")

        # 3. Parse porcelain v2 output
        current_branch: Optional[str] = None
        upstream_branch: Optional[str] = None
        is_detached = False
        is_conflicted = False

        staged_files: List[GitFileEntry] = []
        unstaged_files: List[GitFileEntry] = []
        untracked_files: List[GitFileEntry] = []
        conflict_files: List[GitFileEntry] = []

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith("# branch.head "):
                branch_val = line[len("# branch.head "):].strip()
                if branch_val == "(detached)":
                    is_detached = True
                    current_branch = None
                else:
                    current_branch = branch_val
            elif line.startswith("# branch.upstream "):
                upstream_branch = line[len("# branch.upstream "):].strip()
            elif line.startswith("? "):
                path = line[2:].strip().replace("\\", "/")
                abs_path = self.workspace_root / path
                size_bytes = os.path.getsize(abs_path) if abs_path.exists() else 0
                is_binary = any(path.endswith(ext) for ext in [".png", ".jpg", ".bin", ".tar", ".gz", ".zip"])
                untracked_files.append(
                    GitFileEntry(
                        path=path,
                        status_code="??",
                        category=GitFileCategory.UNTRACKED.value,
                        is_binary=is_binary,
                        size_bytes=size_bytes,
                    )
                )
            elif line.startswith("u "):
                is_conflicted = True
                parts = line.split(" ")
                xy = parts[1] if len(parts) > 1 else "UU"
                path = parts[-1].strip().replace("\\", "/")
                abs_path = self.workspace_root / path
                size_bytes = os.path.getsize(abs_path) if abs_path.exists() else 0
                conflict_files.append(
                    GitFileEntry(
                        path=path,
                        status_code=xy,
                        category=GitFileCategory.CONFLICT.value,
                        size_bytes=size_bytes,
                    )
                )
            elif line.startswith("1 ") or line.startswith("2 "):
                parts = line.split(" ")
                xy = parts[1] if len(parts) > 1 else ".."
                path = parts[-1].strip().replace("\\", "/")
                abs_path = self.workspace_root / path
                size_bytes = os.path.getsize(abs_path) if abs_path.exists() else 0
                is_binary = any(path.endswith(ext) for ext in [".png", ".jpg", ".bin", ".tar", ".gz", ".zip"])

                # X is staged
                x_char = xy[0]
                # Y is unstaged
                y_char = xy[1]

                if x_char != ".":
                    staged_files.append(
                        GitFileEntry(
                            path=path,
                            status_code=f"{x_char}.",
                            category=GitFileCategory.STAGED.value,
                            is_binary=is_binary,
                            size_bytes=size_bytes,
                        )
                    )
                if y_char != ".":
                    unstaged_files.append(
                        GitFileEntry(
                            path=path,
                            status_code=f".{y_char}",
                            category=GitFileCategory.UNSTAGED.value,
                            is_binary=is_binary,
                            size_bytes=size_bytes,
                        )
                    )

        # 4. Fetch HEAD commit details
        head_hash: Optional[str] = None
        head_short: Optional[str] = None
        head_author: Optional[str] = None
        head_message: Optional[str] = None
        head_committed_at: Optional[str] = None

        log_out, _, log_code = await self._run_git_command(
            "log", "-1", "--pretty=format:%H\x1f%h\x1f%an\x1f%aI\x1f%s"
        )
        if log_code == 0 and log_out:
            fields = log_out.split("\x1f")
            if len(fields) >= 5:
                head_hash = fields[0].strip() or None
                head_short = fields[1].strip() or None
                head_author = fields[2].strip() or "Desconocido"
                head_committed_at = fields[3].strip() or None
                head_message = fields[4].strip() or None

        working_tree = GitWorkingTree(
            staged=staged_files,
            unstaged=unstaged_files,
            untracked=untracked_files,
            conflicts=conflict_files,
        )

        staged_count = len(staged_files)
        unstaged_count = len(unstaged_files)
        untracked_count = len(untracked_files)
        total_modified = staged_count + unstaged_count + untracked_count + len(conflict_files)

        snapshot = GitStatusResponse(
            current_branch=current_branch,
            head_commit_hash=head_hash,
            head_commit_short=head_short,
            head_commit_message=head_message,
            head_commit_author=head_author,
            head_committed_at=head_committed_at,
            upstream_branch=upstream_branch,
            is_detached=is_detached,
            is_conflicted=is_conflicted,
            is_syncing=False,
            staged_count=staged_count,
            unstaged_count=unstaged_count,
            untracked_count=untracked_count,
            total_modified_files=total_modified,
            working_tree=working_tree,
            captured_at_utc=self._now_iso(),
        )

        self._last_snapshot = snapshot
        return snapshot

    async def get_commits(
        self, limit: int = 50, offset: int = 0, branch: Optional[str] = None
    ) -> GitCommitListResponse:
        """
        Returns chronological commit history with pagination and diff elision (>1MB / binary) (US2 / ADR-014).
        """
        self._is_git_repo()

        if limit <= 0 or limit > 500:
            raise HTTPException(status_code=400, detail="El parámetro 'limit' debe ser entre 1 y 500.")
        if offset < 0:
            raise HTTPException(status_code=400, detail="El parámetro 'offset' no puede ser negativo.")

        t_start = time.perf_counter()

        # 1. Prepare commands
        rev_args = ["rev-list", "--count"]
        if branch:
            rev_args.append(branch)
        else:
            rev_args.append("HEAD")

        log_args = [
            "log",
            f"--skip={offset}",
            f"-n{limit}",
            "--pretty=format:COMMIT_START\x1f%H\x1f%h\x1f%an\x1f%ae\x1f%aI\x1f%s",
            "--name-status",
        ]
        if branch:
            log_args.append(branch)

        # Optimize latency (< 300ms SLA): use cached total count if available
        if hasattr(self, "_cached_total_count") and self._cached_total_count is not None and not branch:
            total_count = self._cached_total_count
            stdout, _, _ = await self._run_git_command(*log_args)
        else:
            (count_res, log_res) = await asyncio.gather(
                self._run_git_command(*rev_args),
                self._run_git_command(*log_args),
            )
            count_out, _, count_code = count_res
            stdout, _, _ = log_res
            total_count = int(count_out.strip()) if count_code == 0 and count_out.isdigit() else 0
            if not branch:
                self._cached_total_count = total_count

        commits: List[GitCommitItem] = []

        if stdout:
            blocks = stdout.split("COMMIT_START\x1f")
            for block in blocks:
                block = block.strip()
                if not block:
                    continue

                lines = block.splitlines()
                header_line = lines[0]
                header_fields = header_line.split("\x1f")
                if len(header_fields) < 6:
                    continue

                c_hash = header_fields[0].strip()
                c_short = header_fields[1].strip()
                author_name = header_fields[2].strip() or "Desconocido"
                author_email = header_fields[3].strip()
                committed_at = header_fields[4].strip()
                message = header_fields[5].strip()
                agent_role = self._infer_agent_role(author_name, message)

                file_changes: List[GitCommitFileChange] = []

                # Lines following header are name-status lines: <status>\t<path>
                for stat_line in lines[1:]:
                    stat_line = stat_line.strip()
                    if not stat_line:
                        continue
                    parts = stat_line.split("\t")
                    if len(parts) < 2:
                        continue

                    status_type = parts[0].strip()
                    file_path = parts[-1].strip().replace("\\", "/")

                    change_type = "modified"
                    if status_type.startswith("A"):
                        change_type = "added"
                    elif status_type.startswith("D"):
                        change_type = "deleted"
                    elif status_type.startswith("R"):
                        change_type = "renamed"

                    is_binary = any(
                        file_path.endswith(ext)
                        for ext in [".bin", ".iso", ".tar", ".gz", ".zip", ".png", ".jpg", ".jpeg", ".ico", ".pdf"]
                    )
                    is_diff_omitted = is_binary

                    file_changes.append(
                        GitCommitFileChange(
                            relative_path=file_path,
                            change_type=change_type,
                            is_binary=is_binary,
                            is_diff_omitted=is_diff_omitted,
                            insertions=0,
                            deletions=0,
                        )
                    )

                commits.append(
                    GitCommitItem(
                        commit_hash=c_hash,
                        short_hash=c_short,
                        author_name=author_name,
                        author_email=author_email,
                        committed_at=committed_at,
                        message=message,
                        agent_role=agent_role,
                        files_changed_count=len(file_changes),
                        insertions=0,
                        deletions=0,
                        files=file_changes,
                    )
                )

        t_elapsed_ms = int((time.perf_counter() - t_start) * 1000)

        return GitCommitListResponse(
            commits=commits,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total_count,
            execution_time_ms=t_elapsed_ms,
        )

    async def get_branches(self) -> GitBranchListResponse:
        """
        Returns list of local branches and current active branch (ADR-014).
        """
        self._is_git_repo()

        format_spec = "%(refname:short)\x1f%(objectname)\x1f%(objectname:short)\x1f%(upstream:short)\x1f%(HEAD)"
        stdout, _, _ = await self._run_git_command("branch", f"--format={format_spec}")

        branches: List[GitBranchItem] = []
        current_branch: Optional[str] = None

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue

            fields = line.split("\x1f")
            if len(fields) < 3:
                continue

            name = fields[0].strip()
            target_hash = fields[1].strip()
            short_hash = fields[2].strip()
            upstream = fields[3].strip() if len(fields) > 3 and fields[3].strip() else None
            is_head = len(fields) > 4 and fields[4].strip() == "*"

            if is_head:
                current_branch = name

            branches.append(
                GitBranchItem(
                    name=name,
                    target_commit_hash=target_hash,
                    short_hash=short_hash,
                    is_current=is_head,
                    is_remote_tracking=bool(upstream),
                    upstream_branch=upstream,
                )
            )

        return GitBranchListResponse(
            current_branch=current_branch,
            total_branches=len(branches),
            branches=branches,
        )


# Global singleton instance
git_service = GitService()
