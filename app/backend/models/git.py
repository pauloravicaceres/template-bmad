import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GitFileCategory(str, Enum):
    STAGED = "staged"
    UNSTAGED = "unstaged"
    UNTRACKED = "untracked"
    CONFLICT = "conflict"


class GitFileEntry(BaseModel):
    """File item in the working tree."""
    path: str
    status_code: str
    category: str
    lines_added: int = 0
    lines_deleted: int = 0
    is_binary: bool = False
    size_bytes: int = 0


class GitWorkingTree(BaseModel):
    """Segmented working tree files."""
    staged: List[GitFileEntry] = Field(default_factory=list)
    unstaged: List[GitFileEntry] = Field(default_factory=list)
    untracked: List[GitFileEntry] = Field(default_factory=list)
    conflicts: List[GitFileEntry] = Field(default_factory=list)


class GitStatusResponse(BaseModel):
    """Payload for GET /api/v1/git/status (ADR-013 / ADR-014)."""
    current_branch: Optional[str] = None
    head_commit_hash: Optional[str] = None
    head_commit_short: Optional[str] = None
    head_commit_message: Optional[str] = None
    head_commit_author: Optional[str] = None
    head_committed_at: Optional[str] = None
    upstream_branch: Optional[str] = None
    is_detached: bool = False
    is_conflicted: bool = False
    is_syncing: bool = False
    staged_count: int = 0
    unstaged_count: int = 0
    untracked_count: int = 0
    total_modified_files: int = 0
    working_tree: GitWorkingTree = Field(default_factory=GitWorkingTree)
    captured_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )


class GitCommitFileChange(BaseModel):
    """Individual file modification inside a commit."""
    relative_path: str
    change_type: str  # added, modified, deleted, renamed
    is_binary: bool = False
    is_diff_omitted: bool = False
    insertions: int = 0
    deletions: int = 0


class GitCommitItem(BaseModel):
    """Commit record in chronological history."""
    commit_hash: str
    short_hash: str
    author_name: str
    author_email: str
    committed_at: str
    message: str
    agent_role: Optional[str] = None
    files_changed_count: int = 0
    insertions: int = 0
    deletions: int = 0
    files: List[GitCommitFileChange] = Field(default_factory=list)


class GitCommitListResponse(BaseModel):
    """Payload for GET /api/v1/git/commits."""
    commits: List[GitCommitItem] = Field(default_factory=list)
    total_count: int = 0
    limit: int = 50
    offset: int = 0
    has_more: bool = False
    execution_time_ms: int = 0


class GitBranchItem(BaseModel):
    """Branch record."""
    name: str
    target_commit_hash: str
    short_hash: str
    is_current: bool = False
    is_remote_tracking: bool = False
    upstream_branch: Optional[str] = None


class GitBranchListResponse(BaseModel):
    """Payload for GET /api/v1/git/branches."""
    current_branch: Optional[str] = None
    total_branches: int = 0
    branches: List[GitBranchItem] = Field(default_factory=list)


class GitStatusChangedPayload(BaseModel):
    """Payload for WebSocket event GIT_STATUS_CHANGED."""
    current_branch: Optional[str] = None
    head_hash_short: Optional[str] = None
    head_commit_message: Optional[str] = None
    head_commit_author: Optional[str] = None
    is_detached: bool = False
    is_conflicted: bool = False
    is_syncing: bool = False
    staged_count: int = 0
    unstaged_count: int = 0
    untracked_count: int = 0
    total_modified_files: int = 0
    trigger_source: str = "WATCHDOG_FS_EVENT"
    sync_latency_ms: int = 0


class GitErrorResponse(BaseModel):
    """RFC 7807 structured error for Git endpoints."""
    error_code: str
    detail: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
