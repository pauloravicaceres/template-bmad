# Feature Specification: Live Tracker

**Feature Branch**: `[01-live-tracker]`

**Created**: 29-09-2026

**Status**: Draft

**Input**: User description: "Monitor de Flujo y Trazabilidad en Vivo (Live Tracker)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Visualización en Tiempo Real (Priority: P1)

Como Líder Técnico, quiero visualizar en tiempo real el estado del flujo, el agente activo y las transiciones desde tracker_bmad.md para gobernar el avance de los agentes.

**Why this priority**: Es la funcionalidad principal del monitor.

**Independent Test**: Can be tested by running the agents and observing the tracker updates visually.

**Acceptance Scenarios**:

1. **Given** que el archivo tracker_bmad.md existe y contiene eventos, **When** el servicio detecta una actualización, **Then** el sistema parsea los bloques y la interfaz presenta la tarjeta de estado del agente activo actual y la línea de tiempo.

### User Story 2 - Detección de Pausas HITL (Priority: P2)

Como Líder Técnico, quiero ser alertado cuando un agente solicite intervención humana.

**Why this priority**: Crítico para evitar cuellos de botella en la ejecución del enjambre.

**Independent Test**: Can be tested by manually appending an `@HUMANO:` handoff.

**Acceptance Scenarios**:

1. **Given** que tracker_bmad.md registra un handoff a @HUMANO:, **When** el servicio procesa el bloque, **Then** el sistema muestra una alerta visual destacada.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST parse tracker_bmad.md extracting timestamp, agent, artifact, status and handoff.
- **FR-002**: System MUST display a chronological timeline of events.
- **FR-003**: System MUST highlight the current active agent.
- **FR-004**: System MUST alert visually when an `@HUMANO:` handoff is detected.
- **FR-005**: System MUST handle missing or empty tracker file gracefully.

### Key Entities

- **Tracker Event**: Represents a single handoff or status update from an agent.
- **Agent State**: Represents the current execution phase (e.g., UX, BA, QA).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dashboard updates within 10 seconds of a file change.
- **SC-002**: Missing files or lock errors do not crash the application.
- **SC-003**: HITL pauses are clearly distinguishable in the UI.

## Assumptions

- The tracker file is encoded in UTF-8.
- The dashboard has read access to the file system where the tracker resides.
