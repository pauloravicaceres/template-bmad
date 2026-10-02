import asyncio
from typing import Callable, Coroutine, Dict, Any, Optional
from datetime import datetime, timezone
from core.config import settings
from models.observability import SystemNoticePayload


class DebounceEntry:
    """Internal entry holding coalesced state and timer handle for a resource."""

    def __init__(
        self,
        resource_path: str,
        event_type: str,
        dispatch_coro_factory: Callable[[int], Coroutine[Any, Any, None]],
        coalesced_count: int = 1,
        timer_handle: Optional[asyncio.TimerHandle] = None,
    ):
        self.resource_path = resource_path
        self.event_type = event_type
        self.dispatch_coro_factory = dispatch_coro_factory
        self.coalesced_count = coalesced_count
        self.timer_handle = timer_handle


class EventDebouncer:
    """
    Debouncing and coalescence buffer (ADR-010).
    Aggregates rapid I/O mutations within a 200ms window into a single consolidated event.
    """

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        window_ms: int = settings.DEBOUNCE_WINDOW_MS,
        system_notice_callback: Optional[Callable[[SystemNoticePayload], Coroutine[Any, Any, None]]] = None,
    ):
        self._loop = loop
        self.window_duration_ms = window_ms
        self.window_seconds = window_ms / 1000.0
        self.system_notice_callback = system_notice_callback
        self._entries: Dict[str, DebounceEntry] = {}

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.get_event_loop()
        return self._loop

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def set_system_notice_callback(
        self, cb: Callable[[SystemNoticePayload], Coroutine[Any, Any, None]]
    ) -> None:
        self.system_notice_callback = cb

    def get_pending_count(self, resource_path: str) -> int:
        norm = resource_path.replace("\\", "/")
        entry = self._entries.get(norm)
        return entry.coalesced_count if entry else 0

    def submit_event(
        self,
        resource_path: str,
        event_type: str,
        dispatch_coro_factory: Callable[[int], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Thread-safe entrypoint to submit a mutation event.
        Can be invoked from watchdog background thread or asyncio coroutines.
        """
        loop = self.loop
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._process_event(resource_path, event_type, dispatch_coro_factory),
                loop,
            )
        else:
            loop.run_until_complete(
                self._process_event(resource_path, event_type, dispatch_coro_factory)
            )

    async def _process_event(
        self,
        resource_path: str,
        event_type: str,
        dispatch_coro_factory: Callable[[int], Coroutine[Any, Any, None]],
    ) -> None:
        norm_path = resource_path.replace("\\", "/")
        if norm_path in self._entries:
            entry = self._entries[norm_path]
            entry.coalesced_count += 1
            entry.event_type = event_type
            entry.dispatch_coro_factory = dispatch_coro_factory
            if entry.timer_handle:
                entry.timer_handle.cancel()
        else:
            entry = DebounceEntry(
                resource_path=norm_path,
                event_type=event_type,
                dispatch_coro_factory=dispatch_coro_factory,
                coalesced_count=1,
            )
            self._entries[norm_path] = entry

        # Schedule timer for window_seconds
        timer = self.loop.call_later(
            self.window_seconds,
            lambda p=norm_path: asyncio.create_task(self._fire(p)),
        )
        entry.timer_handle = timer

    async def _fire(self, resource_path: str) -> None:
        entry = self._entries.pop(resource_path, None)
        if not entry:
            return

        coalesced_count = entry.coalesced_count
        # Execute the dispatch coroutine with the final coalesced_count
        try:
            await entry.dispatch_coro_factory(coalesced_count)
        except Exception:
            pass

        # If coalesced_count > 1 and system notice callback is configured, emit notice
        if coalesced_count > 1 and self.system_notice_callback:
            try:
                notice = SystemNoticePayload(
                    notice_code="DEBOUNCE_COALESCENCE_APPLIED",
                    message=(
                        f"Se agruparon {coalesced_count} escrituras consecutivas en "
                        f"{resource_path} dentro de la ventana de {int(self.window_duration_ms)}ms, "
                        f"emitiendo 1 único evento consolidado."
                    ),
                    absorbed_mutations_count=coalesced_count,
                    window_duration_ms=int(self.window_duration_ms),
                    coalesced_resource=resource_path,
                )
                await self.system_notice_callback(notice)
            except Exception:
                pass

    async def flush_all(self) -> None:
        """Immediately executes all pending debounced entries."""
        for path in list(self._entries.keys()):
            entry = self._entries.get(path)
            if entry and entry.timer_handle:
                entry.timer_handle.cancel()
            await self._fire(path)

    def cancel_all(self) -> None:
        """Cancels all pending timers without executing."""
        for entry in self._entries.values():
            if entry.timer_handle:
                entry.timer_handle.cancel()
        self._entries.clear()


# Global debouncer singleton
debouncer = EventDebouncer()
