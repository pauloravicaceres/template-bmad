import os
import re
import urllib.parse
from pathlib import Path
from typing import List, Optional, Union
from fastapi import HTTPException
from app.backend.core.config import settings


class PathTraversalError(HTTPException):
    """Exception raised when a path traversal attempt is detected."""
    def __init__(self, detail: str = "Acceso denegado por seguridad. La ruta solicitada intenta resolver fuera de las zonas autorizadas del espacio de trabajo."):
        super().__init__(status_code=403, detail=detail)
        self.error_code = "PATH_TRAVERSAL_DETECTED"


def sanitize_feedback(feedback: Optional[str]) -> Optional[str]:
    """Escapes reserved agent tokens like @PM: to prevent injection."""
    if not feedback:
        return feedback
    
    # Simple regex to replace @TOKEN: with [@TOKEN:_ESCAPED]
    sanitized = re.sub(r'(@[A-Za-z0-9_-]+:)', r'[\1_ESCAPED]', feedback)
    return sanitized


def validate_sandbox_path(
    requested_path: str,
    allowed_roots: Optional[List[Union[Path, str]]] = None,
    workspace_root: Optional[Path] = None
) -> Path:
    """
    Validates that requested_path canonically resolves strictly inside one of allowed_roots (ADR-007).
    Guarantees 100% rejection of '../', '..\\', absolute OS paths, and double URL encoding attempts.
    Returns the resolved Path object.
    Raises PathTraversalError (HTTP 403) if path resolution escapes sandbox boundaries.
    """
    if not requested_path or not requested_path.strip():
        raise PathTraversalError("La ruta solicitada no puede estar vacía.")

    # 1. Reject null bytes
    if "\x00" in requested_path:
        raise PathTraversalError("Acceso denegado. Se detectaron caracteres nulos en la ruta.")

    # 2. Multi-pass URL decode to prevent %252e%252e%252f bypass
    decoded = requested_path
    for _ in range(3):
        prev = decoded
        decoded = urllib.parse.unquote(decoded)
        if prev == decoded:
            break

    # 3. Establish root boundaries
    ws_root = (workspace_root or settings.WORKSPACE_ROOT).resolve()
    
    # Allowed roots list resolved
    if allowed_roots is None:
        allowed_roots = settings.ALLOWED_ROOTS

    resolved_allowed_roots: List[Path] = []
    for r in allowed_roots:
        if isinstance(r, str):
            resolved_allowed_roots.append((ws_root / r).resolve())
        else:
            resolved_allowed_roots.append(r.resolve())

    # 4. Canonical resolution of requested target
    # If decoded is absolute, resolve directly; if relative, resolve from ws_root
    target = Path(decoded)
    if not target.is_absolute():
        resolved_target = (ws_root / target).resolve()
    else:
        resolved_target = target.resolve()

    # 5. Check prefix containment via commonpath
    is_contained = False
    str_resolved_target = str(resolved_target)

    for root_dir in resolved_allowed_roots:
        str_root = str(root_dir)
        try:
            common = os.path.commonpath([str_resolved_target, str_root])
            if common == str_root:
                is_contained = True
                break
        except (ValueError, Exception):
            continue

    if not is_contained:
        raise PathTraversalError(
            f"Acceso denegado por seguridad. La ruta solicitada '{requested_path}' resuelve fuera de los límites autorizados del sandbox ('files/', 'specs/', '.specify/')."
        )

    return resolved_target


_ignored_external_events_count: int = 0


def increment_ignored_external_events() -> int:
    """Increments the telemetry counter for discarded external events."""
    global _ignored_external_events_count
    _ignored_external_events_count += 1
    return _ignored_external_events_count


def get_ignored_external_events_count() -> int:
    """Returns the current telemetry counter of discarded external events."""
    return _ignored_external_events_count


def reset_ignored_external_events_count() -> None:
    """Resets the telemetry counter (useful for unit tests)."""
    global _ignored_external_events_count
    _ignored_external_events_count = 0


def is_path_in_perimeter(
    target_path: Union[str, Path],
    allowed_roots: Optional[List[Union[Path, str]]] = None,
    workspace_root: Optional[Path] = None
) -> bool:
    """
    Validates if a target path canonically resolves strictly within the perimeter of allowed roots (ADR-007 / ADR-012).
    Returns True if contained inside one of allowed_roots (files/, .specify/, specs/).
    Returns False if it resolves outside or belongs to excluded directories (.git/, .idea/, etc.).
    """
    if not target_path:
        return False

    str_target = str(target_path)

    # 1. Reject null bytes
    if "\x00" in str_target:
        return False

    # 2. Fast check for common excluded directories (silent discard)
    normalized_slash = str_target.replace("\\", "/")
    excluded_fragments = ["/.git", "/.idea", "/.vscode", "/node_modules", "/__pycache__", "/.pytest_cache"]
    for exc in excluded_fragments:
        if exc in normalized_slash or normalized_slash.startswith(exc.lstrip("/")):
            return False

    # 3. Establish root boundaries
    ws_root = (workspace_root or settings.WORKSPACE_ROOT).resolve()
    if allowed_roots is None:
        allowed_roots = settings.ALLOWED_ROOTS

    resolved_allowed_roots: List[Path] = []
    for r in allowed_roots:
        if isinstance(r, str):
            resolved_allowed_roots.append((ws_root / r).resolve())
        else:
            resolved_allowed_roots.append(r.resolve())

    # 4. Canonical resolution using os.path.realpath
    try:
        if os.path.isabs(str_target):
            real_target = os.path.realpath(str_target)
        else:
            real_target = os.path.realpath(os.path.join(str(ws_root), str_target))

        # Check prefix containment via os.path.commonpath
        for root_dir in resolved_allowed_roots:
            real_root = os.path.realpath(str(root_dir))
            try:
                common = os.path.commonpath([real_target, real_root])
                if common == real_root:
                    return True
            except (ValueError, Exception):
                continue
    except Exception:
        return False

    return False
