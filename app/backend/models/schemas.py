from enum import Enum
from typing import Optional
from pydantic import BaseModel, field_validator

from app.backend.models.workflow import WorkflowStageStep, WorkflowStatusResponse, WorkflowState
from app.backend.models.directory import DirectoryNode, ArtifactTreeResponse
from app.backend.models.artifact import ArtifactContent, ArtifactContentResponse, MAX_ARTIFACT_SIZE
from app.backend.models.errors import ErrorResponse
from app.backend.models.observability import (
    WebSocketEventType,
    ChangeType,
    FileMetadataRecord,
    WorkflowUpdatedPayload,
    ArtifactChangedPayload,
    HeartbeatPongPayload,
    SystemNoticePayload,
    WebSocketEventMessage,
    MonitoredRootStatus,
    PerimeterStatusResponse,
)
from app.backend.models.git import (
    GitFileCategory,
    GitFileEntry,
    GitWorkingTree,
    GitStatusResponse,
    GitCommitFileChange,
    GitCommitItem,
    GitCommitListResponse,
    GitBranchItem,
    GitBranchListResponse,
    GitStatusChangedPayload,
    GitErrorResponse,
)


class ActionEnum(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class DecisionPayload(BaseModel):
    action: ActionEnum
    feedback: Optional[str] = None

    @field_validator('feedback', mode='before')
    @classmethod
    def check_feedback(cls, v):
        return v

    def model_post_init(self, __context) -> None:
        if self.action == ActionEnum.REJECT and (not self.feedback or not self.feedback.strip()):
            raise ValueError('Feedback is required when action is REJECT')


__all__ = [
    "ActionEnum",
    "DecisionPayload",
    "WorkflowStageStep",
    "WorkflowStatusResponse",
    "WorkflowState",
    "DirectoryNode",
    "ArtifactTreeResponse",
    "ArtifactContent",
    "ArtifactContentResponse",
    "MAX_ARTIFACT_SIZE",
    "ErrorResponse",
    "WebSocketEventType",
    "ChangeType",
    "FileMetadataRecord",
    "WorkflowUpdatedPayload",
    "ArtifactChangedPayload",
    "HeartbeatPongPayload",
    "SystemNoticePayload",
    "WebSocketEventMessage",
    "MonitoredRootStatus",
    "PerimeterStatusResponse",
    "GitFileCategory",
    "GitFileEntry",
    "GitWorkingTree",
    "GitStatusResponse",
    "GitCommitFileChange",
    "GitCommitItem",
    "GitCommitListResponse",
    "GitBranchItem",
    "GitBranchListResponse",
    "GitStatusChangedPayload",
    "GitErrorResponse",
]
