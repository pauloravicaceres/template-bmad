from typing import Optional, Dict, Any
from pydantic import BaseModel, field_validator


MAX_ARTIFACT_SIZE = 5 * 1024 * 1024  # 5 MB


class ArtifactContent(BaseModel):
    """Payload representing an inspected artifact file with 5MB validation."""
    relative_path: str
    filename: str
    raw_content: Optional[str] = None
    detected_format: str = "MARKDOWN"  # MARKDOWN, TEXT, UNSUPPORTED
    encoding: str = "utf-8"
    size_bytes: int
    is_oversized: bool = False
    is_unsupported_media: bool = False
    mime_type: str = "text/markdown"
    last_modified: Optional[str] = None

    # Interoperability aliases for api-contract.md
    content: Optional[str] = None
    format: Optional[str] = None

    @field_validator("is_oversized", mode="before")
    @classmethod
    def compute_oversized(cls, v: Optional[bool], info) -> bool:
        if v is not None:
            return v
        size = info.data.get("size_bytes", 0) if info.data else 0
        return size > MAX_ARTIFACT_SIZE


# Alias for ArtifactContent
ArtifactContentResponse = ArtifactContent
