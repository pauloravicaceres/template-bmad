# Phase 0: Research & Technical Clarifications

## Technical Context Clarifications

### 1. `applicationId` Validation Across Modules
- **Decision:** Use Synchronous Intra-Process Communication.
- **Rationale:** The `constitution.md` states: "Comunicacin Sncrona (Intra-proceso): Invocacin de interfaces o mtodos pblicos entre mdulos dentro de la misma memoria del proceso." Since this is a validation step before creating the record, we need a fast, synchronous check. The Backlog module will invoke a public interface (e.g., `IApplicationModuleApi.ExistsAsync(applicationId)`) exposed by the Application module.
- **Alternatives considered:** Replicating application data via Integration Events into the Backlog schema (rejected due to overhead for just a simple existence check); skipping validation (violates FR-007).

### 2. Domain Event Publishing Strategy
- **Decision:** `IDomainEvent` via `DispatchDomainEventsInterceptor`.
- **Rationale:** `spec.md` FR-010 explicitly requires a `DomainEvent` (`BacklogItemCreatedDomainEvent`), not an `IntegrationEvent`. According to `constitution.md`, Domain Events are dispatched by the EF Core interceptor `DispatchDomainEventsInterceptor` right before/after SaveChanges, which handles it in the same process/module without needing the Transactional Outbox pattern.
- **Alternatives considered:** Transactional Outbox pattern (rejected because Outbox is mandated for `IIntegrationEvent` published to MassTransit, whereas this is local `IDomainEvent` published to MediatR).

### 3. Architecture Layout (Vertical Slice Architecture)
- **Decision:** Place all related components in `src/Modules/Backlog/Features/BacklogItems/CreateBacklogItem/`.
- **Rationale:** Constitution mandates Vertical Slice Architecture (VSA) under Feature Folders for Carter endpoints, MediatR handlers, Mapster configs, and FluentValidation rules.
- **Alternatives considered:** Traditional layered architecture (explicitly prohibited by `@API` mandate).

### 4. Technical Constraints
- **Performance Goals:** P95 < 500ms (as per SC-004).
- **Scale/Scope:** Standard enterprise application scale.
