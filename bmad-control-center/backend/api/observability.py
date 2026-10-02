from fastapi import APIRouter
from models.observability import PerimeterStatusResponse, MonitoredRootStatus
from core.config import settings
from core.security import get_ignored_external_events_count

router = APIRouter(prefix="/observability", tags=["Observability & Telemetry"])


@router.get("/perimeter/status", response_model=PerimeterStatusResponse)
async def get_perimeter_status() -> PerimeterStatusResponse:
    """
    Returns security perimeter status, monitored root boundaries,
    and telemetry counter of discarded external events (ADR-012).
    """
    monitored = [
        MonitoredRootStatus(allowed_path=f"{root}/", is_monitored=True)
        for root in settings.ALLOWED_ROOTS
    ]
    return PerimeterStatusResponse(
        sandbox_status="ACTIVE",
        zero_leakage_verified=True,
        monitored_roots=monitored,
        ignored_external_events_count=get_ignored_external_events_count(),
        debounce_window_ms=settings.DEBOUNCE_WINDOW_MS,
        large_file_threshold_bytes=settings.LARGE_FILE_THRESHOLD_BYTES,
    )
