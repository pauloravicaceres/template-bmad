import re
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from fastapi import HTTPException
from core.config import settings
from models.workflow import WorkflowStageStep, WorkflowStatusResponse


CANONICAL_STAGES = [
    {"key": "PM", "name": "Product Manager", "role": "Product Manager", "order": 1},
    {"key": "BA", "name": "Business Analyst", "role": "Business Analyst", "order": 2},
    {"key": "QA", "name": "QA Documental", "role": "QA Documental", "order": 3},
    {"key": "W-QA", "name": "Spec Kit", "role": "WATCHER", "order": 4},
    {"key": "UX", "name": "Designer UX", "role": "Designer UX", "order": 5},
    {"key": "SA", "name": "Solutions Architect", "role": "Solutions Architect", "order": 6},
    {"key": "W-SA", "name": "Spec Kit", "role": "WATCHER", "order": 7},
    {"key": "DA", "name": "Data Architect", "role": "Data Architect", "order": 8},
    {"key": "API", "name": "API Architect", "role": "API Architect", "order": 9},
    {"key": "QT", "name": "QA-Tech Senior", "role": "QA-Tech Senior", "order": 10},
    {"key": "W-IMP", "name": "Spec Kit", "role": "WATCHER", "order": 11},
    {"key": "DEV-BACK", "name": "Dev Backend", "role": "Senior Backend Developer", "order": 12},
    {"key": "DEV-FRONT", "name": "Dev Frontend", "role": "Senior Frontend Developer", "order": 13},
    {"key": "QA-AUTO", "name": "QA Automation", "role": "QA Automation", "order": 14},
    {"key": "CR", "name": "Code Review", "role": "SecOps", "order": 15},
]

ROLE_TO_KEY = {
    "Business Storyteller": "BS",
    "Product Analyst": "PA",
    "Product Manager": "PM",
    "Business Analyst": "BA",
    "QA Documental": "QA",
    "Designer UX": "UX",
    "Diseñador UX": "UX",
    "Solutions Architect": "SA",
    "Data Architect": "DA",
    "API Architect": "API",
    "QA-Tech Senior": "QT",
    "QA-Tech": "QT",
    "QA Tech": "QT",
    "Senior Backend Developer": "DEV-BACK",
    "Senior Frontend Developer": "DEV-FRONT",
    "QA Automation": "QA-AUTO",
    "SecOps": "CR",
    "Code Review": "CR",
}

MAX_REWORK_DEFAULT = 2
DEV_STAGE_KEYS = ("DEV-BACK", "DEV-FRONT")

TOKEN_TO_KEY = {
    "BS": "BS",
    "PA": "PA",
    "PM": "PM",
    "BA": "BA",
    "QA": "QA",
    "UX": "UX",
    "SA": "SA",
    "DA": "DA",
    "API": "API",
    "QT": "QT",
    "DEV-BACK": "DEV-BACK",
    "DEV-FRONT": "DEV-FRONT",
    "QA-AUTO": "QA-AUTO",
    "CODE-REVIEW": "CR",
    "CR": "CR",
    "HUMANO": "HUMANO",
}


class WorkflowService:
    """Parses tracker_bmad.md to project the 8 canonical stages and overall pipeline status."""

    def __init__(self, tracker_path: Optional[Path] = None):
        self.tracker_path = tracker_path or settings.TRACKER_FILE

    @staticmethod
    def _watcher_key(prev_key: Optional[str]) -> str:
        """Etapa del WATCHER según el último agente canónico que lo precede.

        La Fase D (W-IMP) abarca también a DEV-BACK/DEV-FRONT: el watcher sigue
        escribiendo bloques mientras implementa el frontend.
        """
        if prev_key == "SA":
            return "W-SA"
        if prev_key in ("QT", "DEV-BACK", "DEV-FRONT", "CR", "QA-AUTO"):
            # CR/QA-AUTO: el watcher corre el ciclo de retrabajo (converge + implement) tras un rechazo
            return "W-IMP"
        return "W-QA"

    def _watcher_key_before(self, blocks: List[Dict[str, Any]], index: int) -> str:
        """Etapa del bloque WATCHER en `index`, mirando el primer autor no-WATCHER anterior."""
        for i in range(index - 1, -1, -1):
            role_i = blocks[i]["author_role"]
            # HUMANO no es una etapa del pipeline: sus entradas (aprobaciones, reanudaciones) no cambian la fase del watcher
            if role_i not in ("WATCHER", "HUMANO"):
                return self._watcher_key(ROLE_TO_KEY.get(role_i))
        return "W-QA"

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

            status_match = re.search(r'-\s+\*\*(?:Estado|Mensaje):\*\*\s+([^\n]+)', chunk)
            status_desc = status_match.group(1).strip() if status_match else ""

            handoff_match = re.search(r'-\s+\*\*Handoff:\*\*\s+@?([A-Za-z0-9_-]+):?\s*([^\n]*)', chunk)
            target_token = handoff_match.group(1).strip().upper() if handoff_match else None
            handoff_directive = handoff_match.group(0).strip() if handoff_match else ""

            # Todos los destinatarios del handoff (puede asignar a varios agentes a la vez)
            handoff_idx = chunk.find("**Handoff:**")
            handoff_section = chunk[handoff_idx:] if handoff_idx != -1 else ""
            handoff_targets: List[str] = []
            for tok in re.findall(r'@([A-Za-z0-9_-]+):', handoff_section):
                tkey = TOKEN_TO_KEY.get(tok.upper())
                if tkey and tkey not in handoff_targets:
                    handoff_targets.append(tkey)

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
                "handoff_targets": handoff_targets,
                # Rama que abre un nuevo ciclo (HU/épica): la macro solo vale como línea propia, no citada en prosa
                "branch_create": (re.search(
                    r'^\s*(?:[-*]\s+)*(?:\*\*Handoff:\*\*\s*)?@WATCHER:\s*GITOPS-BRANCH-CREATE\s+([^\s`\'"]+)',
                    chunk, re.MULTILINE) or [None, None])[1],
                # Cierre de rama emitido por el revisor: la HU quedó certificada y fusionada
                "merge_close": (re.search(
                    r'^\s*(?:[-*]\s+)*(?:\*\*Handoff:\*\*\s*)?@WATCHER:\s*GITOPS-MERGE-CLOSE\s+([^\s`\'"]+)',
                    chunk, re.MULTILINE) or [None, None])[1],
                # Avisos del Watcher (vigilante o error de una fase): anotaciones, NO un paso en curso
                "is_annotation": author_role == "WATCHER" and bool(re.search(r"\[Vigilante\]|🚨|\bERROR\b", status_desc)),
                "timestamp": iso_timestamp,
            })

        return blocks

    @staticmethod
    def _current_cycle_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Bloques del ciclo actual (la HU/épica en curso). Cada macro GITOPS-BRANCH-CREATE abre un ciclo nuevo:
        sin esto el tracker se leía como una sola historia y, al empezar la HU siguiente, las 15 etapas de la
        anterior seguían en verde. El ciclo arranca en el último bloque del PM anterior o igual a la macro
        (el PM asigna la épica, ya sea en su propio bloque o en el HUMANO que la aprueba).
        """
        macro_idx = None
        for i, b in enumerate(blocks):
            if b.get("branch_create"):
                macro_idx = i
        if macro_idx is None:
            return blocks
        start = macro_idx
        for j in range(macro_idx, -1, -1):
            if ROLE_TO_KEY.get(blocks[j]["author_role"]) == "PM":
                start = j
                break
            # Un cierre de rama termina el ciclo anterior: no se retrocede más allá (HU abierta sin bloque de PM)
            if j < macro_idx and blocks[j].get("merge_close"):
                break
        return blocks[start:]

    @staticmethod
    def _detect_rework(blocks: List[Dict[str, Any]], completed_stage_map: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Detecta un ciclo de retrabajo: el último revisor (CR / QA-AUTO) rechazó y aún hay correcciones pendientes."""
        last_review: Optional[Tuple[str, Dict[str, Any]]] = None
        for b in blocks:
            key = ROLE_TO_KEY.get(b["author_role"])
            if key in ("CR", "QA-AUTO"):
                last_review = (key, b)
        if not last_review or "RECHAZ" not in last_review[1]["status_description"].upper():
            return None

        origin_key, rejected = last_review
        pending: List[str] = []
        for t in rejected.get("handoff_targets", []):
            if t in DEV_STAGE_KEYS + ("QA-AUTO",) and t != origin_key:
                done = completed_stage_map.get(t)
                if not done or done["block_index"] <= rejected["block_index"]:
                    pending.append(t)

        iteration, max_iterations = 0, MAX_REWORK_DEFAULT
        for b in blocks:
            if b["block_index"] > rejected["block_index"] and b["author_role"] == "WATCHER":
                m = re.search(r'Iteración\s+(\d+)/(\d+)', b["status_description"])
                if m:
                    iteration, max_iterations = int(m.group(1)), int(m.group(2))

        return {
            "active": True,
            "origin_stage": origin_key,
            "origin_role": rejected["author_role"],
            "iteration": iteration,
            "max_iterations": max_iterations,
            "reason": rejected["status_description"][:240],
            "pending_stages": pending,
            "since_block_index": rejected["block_index"],
        }

    def get_workflow_status(self, include_history: bool = True) -> WorkflowStatusResponse:
        """Projects memory state of the workflow from docs/tracker_bmad.md."""
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
                total_stages=len(CANONICAL_STAGES),
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

        all_blocks = self._parse_blocks(content)
        # Un aviso del vigilante o un error del Watcher al final NO es "Spec Kit trabajando": deja la etapa real
        # (la del último handoff) marcada como estancada en lugar de iluminar una caja del Watcher.
        alerta: Optional[Dict[str, Any]] = None
        if all_blocks and all_blocks[-1].get("is_annotation"):
            alerta = {
                "type": "STALLED",
                "message": all_blocks[-1]["status_description"],
                "since_block_index": all_blocks[-1]["block_index"],
            }
        blocks = [b for b in self._current_cycle_blocks(all_blocks) if not b.get("is_annotation")]

        # Track completed stages and active stage
        completed_stage_map: Dict[str, Dict[str, Any]] = {}
        last_canonical_key = None
        for block in blocks:
            role = block["author_role"]
            key = ROLE_TO_KEY.get(role)
            if key and key not in ["W-QA", "W-SA", "W-IMP"]:
                completed_stage_map[key] = block
                if key != "HUMANO":
                    last_canonical_key = key
            elif role == "WATCHER":
                key = self._watcher_key(last_canonical_key)
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

            # Check if all completed
            # Un bloque del revisor que lleva la macro de cierre de rama es el final de la HU aunque su Handoff
            # apunte a HUMANO (aviso informativo): no debe quedar como "POR APROBAR".
            if last_block["author_role"] in ("SecOps", "Code Review") and (
                target in ["WATCHER", "PM"] or last_block.get("merge_close")
            ):
                overall_status = "COMPLETED"
                active_stage_key = "COMPLETED"
                active_agent_role = None
                active_artifact = None
            elif target == "HUMANO":
                # Si el último bloque fue WATCHER, activar W-QA o W-SA o W-IMP
                if last_block["author_role"] == "WATCHER":
                    author_key = self._watcher_key_before(blocks, len(blocks) - 1)
                else:
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
                # Si el autor es WATCHER y no hay target (está procesando en silencio)
                if last_block["author_role"] == "WATCHER":
                    active_stage_key = self._watcher_key_before(blocks, len(blocks) - 1)
                    active_agent_role = "Spec Kit"
                else:
                    # If target is unknown, deduce from completed stages
                    for stage in CANONICAL_STAGES:
                        if stage["key"] not in completed_stage_map:
                            active_stage_key = stage["key"]
                            active_agent_role = stage["role"]
                            break

        rework = self._detect_rework(blocks, completed_stage_map)
        parallel_active_keys = [active_stage_key] if active_stage_key else []
        if active_stage_key == "W-IMP" and blocks:
            msg = blocks[-1].get("status_description", "")
            if "Frontend" in msg:
                parallel_active_keys.append("DEV-FRONT")
            elif "Backend" in msg:
                parallel_active_keys.append("DEV-BACK")

        # Build 15 canonical steps
        stage_steps: List[WorkflowStageStep] = []
        # El Watcher deja un bloque '⏭️ [UX] Diseño UX omitido' cuando el diseño no aplica: la etapa se muestra OMITIDA, no pendiente
        skipped_keys = {'UX'} if any(
            b['author_role'] == 'WATCHER' and 'Diseño UX omitido' in b['status_description'] for b in blocks
        ) else set()
        skipped_keys -= set(completed_stage_map)
        completed_count = len(completed_stage_map) + len(skipped_keys)
        if completed_count >= len(CANONICAL_STAGES) and not rework:
            overall_status = "COMPLETED"
        elif rework and overall_status == "COMPLETED":
            # Un rechazo activo de Code Review / QA-AUTO reabre el pipeline
            overall_status = "IN_PROGRESS"

        for stage in CANONICAL_STAGES:
            s_key = stage["key"]
            if s_key in parallel_active_keys and overall_status != "COMPLETED":
                b = completed_stage_map.get(s_key)
                step = WorkflowStageStep(
                    stage_key=s_key,
                    stage_name=stage["name"],
                    agent_role=stage["role"],
                    order_index=stage["order"],
                    status="IN_PROGRESS",
                    is_active=True,
                    started_at=b["timestamp"] if b else last_updated,
                    completed_at=None,
                    origin_block_index=b["block_index"] if b else None,
                    generated_artifact_path=b["generated_artifact"] if b else None,
                )
            elif s_key in skipped_keys:
                step = WorkflowStageStep(
                    stage_key=s_key,
                    stage_name=stage['name'],
                    agent_role=stage['role'],
                    order_index=stage['order'],
                    status='SKIPPED',
                    is_active=False,
                )
            elif s_key in completed_stage_map:
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
            if rework and overall_status != "COMPLETED":
                if s_key == rework["origin_stage"] and step.status == "COMPLETED":
                    step.rework_state = "REJECTED"
                elif s_key in rework["pending_stages"]:
                    step.rework_state = "REWORK"
                    if step.status == "COMPLETED":
                        # La etapa ya había terminado pero el revisor la rechazó: vuelve a estar pendiente.
                        # Solo pasa a IN_PROGRESS la que el watcher está ejecutando (parallel_active_keys);
                        # las demás quedan "en cola" hasta que les toque.
                        step.status = "PENDING"
                        step.is_active = False
                        step.completed_at = None
                if step.rework_state:
                    step.rework_iteration = rework["iteration"]
                    step.rework_max = rework["max_iterations"]
                    step.rework_reason = rework["reason"]
            if alerta and s_key in parallel_active_keys and step.status != "COMPLETED":
                step.alert_state = "STALLED"
                step.alert_reason = alerta["message"][:240]
            stage_steps.append(step)

        # Prepare history if requested
        history_list = []
        if include_history:
            for b in all_blocks:
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
            total_stages=len(CANONICAL_STAGES),
            completed_stages=completed_count,
            sync_channel="WEBSOCKET_LIVE",
            stages=stage_steps,
            current_stage=active_agent_role or active_stage_key,
            status=overall_status,
            history=history_list,
            rework=rework,
            alert=alerta,
        )
