import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException
from app.backend.core.config import settings
from app.backend.models.workflow import WorkflowStageStep, WorkflowStatusResponse


CANONICAL_STAGES = [
    {"key": "PM", "name": "Product Manager", "role": "Product Manager", "order": 1},
    {"key": "BA", "name": "Business Analyst", "role": "Business Analyst", "order": 2},
    {"key": "QA", "name": "QA Documental", "role": "QA Documental", "order": 3},
    {"key": "UX", "name": "Designer UX", "role": "Designer UX", "order": 4},
    {"key": "SA", "name": "Solutions Architect", "role": "Solutions Architect", "order": 5},
    {"key": "DA", "name": "Data Architect", "role": "Data Architect", "order": 6},
    {"key": "API", "name": "API Architect", "role": "API Architect", "order": 7},
    {"key": "QT", "name": "QA-Tech Senior", "role": "QA-Tech Senior", "order": 8},
]

ROLE_TO_KEY = {
    "Product Manager": "PM",
    "Business Analyst": "BA",
    "QA Documental": "QA",
    "Designer UX": "UX",
    "Solutions Architect": "SA",
    "Data Architect": "DA",
    "API Architect": "API",
    "QA-Tech Senior": "QT",
    "QA-Tech": "QT",
}

TOKEN_TO_KEY = {
    "PM": "PM",
    "BA": "BA",
    "QA": "QA",
    "UX": "UX",
    "SA": "SA",
    "DA": "DA",
    "API": "API",
    "QT": "QT",
    "HUMANO": "HUMANO",
}


class WorkflowService:
    """Parses tracker_bmad.md to project the 8 canonical stages and overall pipeline status."""

    def __init__(self, tracker_path: Optional[Path] = None):
        self.tracker_path = tracker_path or settings.TRACKER_FILE

    def _parse_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extracts audit blocks and directives from tracker text."""
        blocks: List[Dict[str, Any]] = []
        raw_blocks = re.split(r'(?=^###\s+\[)', content, flags=re.MULTILINE)

        block_index = 0
        for chunk in raw_blocks:
            chunk = chunk.strip()
            if not chunk or not chunk.startswith("### ["):
                continue

            header_match = re.search(r'^###\s+\[(\d{2}-\d{2}-\d{4})\]\s+([^\n]+)', chunk, re.MULTILINE)
            if not header_match:
                continue

            date_str = header_match.group(1).strip()
            author_role = header_match.group(2).strip()

            time_match = re.search(r'-\s+\*\*Hora:\*\*\s+([\d:]+)', chunk)
            time_str = time_match.group(1).strip() if time_match else "00:00:00"

            artifact_match = re.search(r'-\s+\*\*Artefacto generado:\*\*\s+`?([^`\n]+)`?', chunk)
            artifact_path = artifact_match.group(1).strip() if artifact_match else None

            status_match = re.search(r'-\s+\*\*Estado:\*\*\s+([^\n]+)', chunk)
            status_desc = status_match.group(1).strip() if status_match else ""

            handoff_match = re.search(r'-\s+\*\*Handoff:\*\*\s+@?([A-Za-z0-9_-]+):?\s*([^\n]*)', chunk)
            target_token = handoff_match.group(1).strip().upper() if handoff_match else None
            handoff_directive = handoff_match.group(0).strip() if handoff_match else ""

            # Attempt ISO timestamp parse
            iso_timestamp = None
            try:
                # Format: DD-MM-YYYY HH:MM:SS
                dt = datetime.strptime(f"{date_str} {time_str}", "%d-%m-%Y %H:%M:%S")
                iso_timestamp = dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            except Exception:
                iso_timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

            block_index += 1
            blocks.append({
                "block_index": block_index,
                "date": date_str,
                "time": time_str,
                "author_role": author_role,
                "generated_artifact": artifact_path,
                "status_description": status_desc,
                "target_token": target_token,
                "handoff_directive": handoff_directive,
                "timestamp": iso_timestamp,
            })

        return blocks

    def get_workflow_status(self, include_history: bool = True) -> WorkflowStatusResponse:
        """Projects memory state of the workflow from files/tracker_bmad.md."""
        tracker_file = Path(self.tracker_path)
        if not tracker_file.exists():
            # Return empty / idle pipeline
            steps = [
                WorkflowStageStep(
                    stage_key=item["key"],
                    stage_name=item["name"],
                    agent_role=item["role"],
                    order_index=item["order"],
                    status="PENDING",
                    is_active=False,
                )
                for item in CANONICAL_STAGES
            ]
            return WorkflowStatusResponse(
                active_stage=None,
                overall_status="IDLE",
                active_agent_role=None,
                active_artifact_in_progress=None,
                last_updated=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                total_stages=8,
                completed_stages=0,
                sync_channel="WEBSOCKET_LIVE",
                stages=steps,
                current_stage=None,
                status="IDLE",
                history=[],
            )

        try:
            with open(tracker_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error de E/S al intentar acceder y proyectar el estado de '{self.tracker_path}': {str(e)}"
            )

        blocks = self._parse_blocks(content)
        
        # Track completed stages and active stage
        completed_stage_map: Dict[str, Dict[str, Any]] = {}
        for block in blocks:
            role = block["author_role"]
            key = ROLE_TO_KEY.get(role)
            if key:
                completed_stage_map[key] = block

        # Check last block to find what is next
        active_stage_key: Optional[str] = None
        active_agent_role: Optional[str] = None
        overall_status = "IN_PROGRESS"
        active_artifact: Optional[str] = None
        last_updated: Optional[str] = None

        if blocks:
            last_block = blocks[-1]
            last_updated = last_block["timestamp"]
            target = last_block.get("target_token")

            # Check if all completed (e.g. QT hands off to SPEC-KIT or DEV-BACK)
            if last_block["author_role"] in ["QA-Tech Senior", "QA-Tech"] and target in ["SPEC-KIT", "DEV-BACK", "DEV-FRONT", "WATCHER", "PM"]:
                overall_status = "COMPLETED"
                active_stage_key = "COMPLETED"
                active_agent_role = None
                active_artifact = None
            elif target == "HUMANO":
                # Preservar la última etapa del autor o marcar intervención humana
                author_key = ROLE_TO_KEY.get(last_block["author_role"])
                active_stage_key = author_key or "HUMANO"
                active_agent_role = f"Revisión Humana (@HUMANO)"
            elif target and target in TOKEN_TO_KEY:
                active_stage_key = TOKEN_TO_KEY[target]
                for stage in CANONICAL_STAGES:
                    if stage["key"] == active_stage_key:
                        active_agent_role = stage["role"]
                        break
            else:
                # If target is unknown or watcher, deduce from completed stages
                for stage in CANONICAL_STAGES:
                    if stage["key"] not in completed_stage_map:
                        active_stage_key = stage["key"]
                        active_agent_role = stage["role"]
                        break

        # Build 8 canonical steps
        stage_steps: List[WorkflowStageStep] = []
        completed_count = len(completed_stage_map)
        if completed_count == 8:
            overall_status = "COMPLETED"

        for stage in CANONICAL_STAGES:
            s_key = stage["key"]
            if s_key in completed_stage_map:
                b = completed_stage_map[s_key]
                step = WorkflowStageStep(
                    stage_key=s_key,
                    stage_name=stage["name"],
                    agent_role=stage["role"],
                    order_index=stage["order"],
                    status="COMPLETED",
                    is_active=False,
                    started_at=b["timestamp"],
                    completed_at=b["timestamp"],
                    origin_block_index=b["block_index"],
                    generated_artifact_path=b["generated_artifact"],
                )
            elif s_key == active_stage_key and overall_status != "COMPLETED":
                step = WorkflowStageStep(
                    stage_key=s_key,
                    stage_name=stage["name"],
                    agent_role=stage["role"],
                    order_index=stage["order"],
                    status="IN_PROGRESS",
                    is_active=True,
                    started_at=last_updated,
                    completed_at=None,
                    origin_block_index=None,
                    generated_artifact_path=None,
                )
            else:
                step = WorkflowStageStep(
                    stage_key=s_key,
                    stage_name=stage["name"],
                    agent_role=stage["role"],
                    order_index=stage["order"],
                    status="PENDING",
                    is_active=False,
                    started_at=None,
                    completed_at=None,
                    origin_block_index=None,
                    generated_artifact_path=None,
                )
            stage_steps.append(step)

        # Prepare history if requested
        history_list = []
        if include_history:
            for b in blocks:
                history_list.append({
                    "block_index": b["block_index"],
                    "author_role": b["author_role"],
                    "generated_artifact": b["generated_artifact"],
                    "status_description": b["status_description"],
                    "handoff_directive": b["handoff_directive"],
                    "timestamp": b["timestamp"],
                })

        return WorkflowStatusResponse(
            active_stage=active_stage_key,
            overall_status=overall_status,
            active_agent_role=active_agent_role,
            active_artifact_in_progress=active_artifact,
            last_updated=last_updated or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            total_stages=8,
            completed_stages=completed_count,
            sync_channel="WEBSOCKET_LIVE",
            stages=stage_steps,
            current_stage=active_agent_role or active_stage_key,
            status=overall_status,
            history=history_list,
        )
