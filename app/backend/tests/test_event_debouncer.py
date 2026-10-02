import asyncio
import pytest
from app.backend.services.event_debouncer import EventDebouncer
from app.backend.models.observability import SystemNoticePayload


@pytest.mark.asyncio
async def test_event_debouncer_coalesces_burst_into_single_event():
    """
    T020 / US4: Test that a burst of 10 consecutive mutations within < 200ms
    results in exactly 1 consolidated event with coalesced_count = 10.
    """
    dispatched_events = []
    received_notices = []

    async def mock_system_notice(notice: SystemNoticePayload):
        received_notices.append(notice)

    loop = asyncio.get_running_loop()
    # Create debouncer with 100ms window for faster test execution
    debouncer = EventDebouncer(loop=loop, window_ms=100, system_notice_callback=mock_system_notice)

    async def mock_dispatch(count: int):
        dispatched_events.append({"count": count})

    # Simulate 10 rapid mutations in 30ms (< 100ms window)
    for _ in range(10):
        debouncer.submit_event(
            "files/tracker_bmad.md",
            "WORKFLOW_UPDATED",
            lambda c: mock_dispatch(c)
        )
        await asyncio.sleep(0.003)

    # Immediately after burst, timer hasn't fired yet
    assert len(dispatched_events) == 0

    # Wait for the debouncer window to elapse
    await asyncio.sleep(0.15)

    # Exactly 1 event should have been dispatched with coalesced_count == 10
    assert len(dispatched_events) == 1
    assert dispatched_events[0]["count"] == 10

    # System notice for debounce should have been generated
    assert len(received_notices) == 1
    assert received_notices[0].notice_code == "DEBOUNCE_COALESCENCE_APPLIED"
    assert received_notices[0].absorbed_mutations_count == 10


@pytest.mark.asyncio
async def test_event_debouncer_independent_resource_paths():
    """Test that different resource paths maintain isolated debounce timers."""
    dispatched = {}
    loop = asyncio.get_running_loop()
    debouncer = EventDebouncer(loop=loop, window_ms=80)

    async def record_event(path: str, count: int):
        dispatched[path] = count

    # Emit 3 mutations for file A and 5 mutations for file B
    for _ in range(3):
        debouncer.submit_event("files/doc_a.md", "ARTIFACT_CHANGED", lambda c: record_event("files/doc_a.md", c))
        await asyncio.sleep(0.005)

    for _ in range(5):
        debouncer.submit_event("files/doc_b.md", "ARTIFACT_CHANGED", lambda c: record_event("files/doc_b.md", c))
        await asyncio.sleep(0.005)

    await asyncio.sleep(0.12)

    assert "files/doc_a.md" in dispatched
    assert dispatched["files/doc_a.md"] == 3
    assert "files/doc_b.md" in dispatched
    assert dispatched["files/doc_b.md"] == 5


@pytest.mark.asyncio
async def test_event_debouncer_single_event_no_system_notice():
    """Test that a single isolated mutation (count=1) does not emit a SYSTEM_NOTICE."""
    dispatched = []
    notices = []
    loop = asyncio.get_running_loop()
    debouncer = EventDebouncer(
        loop=loop,
        window_ms=50,
        system_notice_callback=lambda n: notices.append(n)
    )

    debouncer.submit_event("files/single.md", "ARTIFACT_CHANGED", lambda c: dispatched.append(c))
    await asyncio.sleep(0.08)

    assert len(dispatched) == 1
    assert dispatched[0] == 1
    assert len(notices) == 0
