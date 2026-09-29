# Implementation Plan: Live Tracker

## Phase 1: File Parsing and Monitoring Service
- Implement file watcher for `tracker_bmad.md`.
- Implement robust parser to extract blocks, timestamps, agent names, and status.
- Handle edge cases: missing file, locked file, invalid format.

## Phase 2: Core Dashboard UI
- Create the main layout for the Live Tracker.
- Implement the "Active Agent" card component showing current phase and status.
- Implement the "Timeline" component showing chronological events.

## Phase 3: HITL Alerts and Edge States
- Implement visual alerts for `@HUMANO:` handoffs.
- Implement empty state (file not initialized).
- Implement error state boundaries.

## Phase 4: Integration
- Connect the file watcher service to the React frontend state.
- Ensure UI updates reactively within 10 seconds of file changes.
