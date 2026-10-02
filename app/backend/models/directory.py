from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field


class DirectoryNode(BaseModel):
    """Hierarchical node for directories and files in workspace explorer."""
    node_id: str
    name: str
    node_type: str  # DIRECTORY, FILE
    relative_path: str
    parent_path: Optional[str] = None
    child_file_count: int = 0
    is_empty: bool = False
    last_modified: Optional[str] = None
    children: List[DirectoryNode] = Field(default_factory=list)

    # Interoperability fields for api-contract.md
    type: Optional[str] = None
    path: Optional[str] = None


class ArtifactTreeResponse(BaseModel):
    """Response structure for GET /api/v1/artifacts/tree and /api/v1/workspace/tree."""
    root_node: DirectoryNode
    
    # Interoperability root aliases for api-contract.md
    type: str = "DIRECTORY"
    name: str = "root"
    path: str = "/"
    children: List[DirectoryNode] = Field(default_factory=list)
