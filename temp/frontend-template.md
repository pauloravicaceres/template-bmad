# Frontend Architecture Document

## 1. Información general

```text
Nombre del sistema:
Versión:
Fecha:
Arquitecto:
Equipo:
Repositorio:
Frontend:
Backend:
```

### 1.1 Objetivo

Describe brevemente:

* Qué problema resuelve el frontend.
* Usuarios objetivo.
* Principales funcionalidades.
* Sistemas externos con los que interactúa.

---

# 2. Contexto de arquitectura

### 2.1 Diagrama de contexto

Este es el nivel más alto.

```mermaid
flowchart TB

    User["👤 Usuario"]

    subgraph Frontend["Frontend — Nuxt 3"]
        App["Aplicación Web"]
    end

    Backend["Backend API"]
    Identity["Identity Provider / SSO"]
    External["Servicios Externos"]

    User --> App
    App --> Backend
    App --> Identity
    App --> External
```

**Pregunta que responde:**

> ¿Qué actores y sistemas interactúan con nuestra aplicación?

---

# 3. Arquitectura general

Aquí puedes combinar C4 con una arquitectura por capas.

### 3.1 Diagrama de arquitectura

```mermaid
flowchart TB

    User["👤 Usuario"]

    subgraph Frontend["Frontend — Nuxt 3"]

        Presentation["Presentation Layer<br/>Pages / Components / Layouts"]

        Application["Application Layer<br/>Use Cases / Facades"]

        Domain["Domain Layer<br/>Models / Business Rules"]

        Infrastructure["Infrastructure Layer<br/>API / HTTP / Storage / Auth"]
    end

    API["Backend REST API"]

    User --> Presentation

    Presentation --> Application
    Application --> Domain
    Application --> Infrastructure

    Infrastructure --> API
```

Aquí defines **las reglas arquitectónicas**.

Por ejemplo:

> Los componentes de presentación no deben realizar llamadas HTTP directamente. La comunicación con backend debe realizarse mediante servicios de infraestructura.

---

# 4. Contenedores

Aunque todo sea "frontend", conviene separar conceptualmente sus grandes bloques.

### 4.1 Container Diagram

```mermaid
flowchart TB

    subgraph Frontend["Frontend Application"]

        UI["UI Components<br/>Vue Components"]

        Pages["Pages / Routes<br/>Nuxt Pages"]

        Layouts["Layouts"]

        State["State Management<br/>Pinia"]

        Services["Application Services"]

        APIClient["API Client"]

        Auth["Authentication"]

        Storage["Browser Storage"]
    end

    Backend["Backend API"]

    Pages --> Layouts
    Pages --> UI

    UI --> State
    UI --> Services

    Services --> State
    Services --> APIClient
    Services --> Auth

    Auth --> Storage
    APIClient --> Backend
```

Este diagrama te permite explicar **qué componentes arquitectónicos existen y cómo se relacionan**.

---

# 5. Estructura del proyecto

Aquí ya bajas al nivel de código.

### 5.1 Diagrama de módulos

```mermaid
flowchart TB

    App["app/"]

    App --> Pages["pages/"]
    App --> Components["components/"]
    App --> Layouts["layouts/"]
    App --> Composables["composables/"]
    App --> Stores["stores/"]
    App --> Services["services/"]
    App --> Domain["domain/"]
    App --> Infrastructure["infrastructure/"]
    App --> Middleware["middleware/"]
    App --> Utils["utils/"]
```

Y puedes acompañarlo con una tabla:

| Módulo           | Responsabilidad                     |
| ---------------- | ----------------------------------- |
| `pages`          | Rutas y composición de páginas      |
| `components`     | Componentes reutilizables           |
| `layouts`        | Estructura visual                   |
| `composables`    | Lógica reutilizable                 |
| `stores`         | Estado global                       |
| `services`       | Casos de uso                        |
| `domain`         | Modelos y reglas                    |
| `infrastructure` | API, storage, autenticación         |
| `middleware`     | Guards y validaciones de navegación |
| `utils`          | Utilidades transversales            |

---

# 6. Componentes

Aquí documentas componentes importantes.

### 6.1 Component Diagram

```mermaid
flowchart LR

    Dashboard["Dashboard Page"]

    Header["App Header"]
    Sidebar["Sidebar"]
    Filters["Filter Panel"]
    Charts["Charts"]
    DataTable["Data Table"]

    Store["Dashboard Store"]

    API["Dashboard API Service"]

    Dashboard --> Header
    Dashboard --> Sidebar
    Dashboard --> Filters
    Dashboard --> Charts
    Dashboard --> DataTable

    Filters --> Store
    Charts --> Store
    DataTable --> Store

    Store --> API
```

Este diagrama es especialmente útil para **funcionalidades complejas**.

No necesitas hacer uno por cada componente.

---

# 7. Navegación

Este es uno de los diagramas que más ayuda al equipo frontend.

### 7.1 Routing Diagram

```mermaid
flowchart TD

    Login["/login"]

    Login --> Dashboard["/dashboard"]

    Dashboard --> Clients["/clients"]
    Dashboard --> Products["/products"]
    Dashboard --> Reports["/reports"]

    Clients --> ClientDetail["/clients/:id"]
    Clients --> ClientCreate["/clients/new"]

    Products --> ProductDetail["/products/:id"]

    Reports --> Sales["/reports/sales"]
    Reports --> Operations["/reports/operations"]
```

Puedes agregar:

* rutas públicas
* rutas protegidas
* roles
* permisos
* lazy loading

---

# 8. Autenticación y autorización

Para una aplicación empresarial este diagrama es importante.

### 8.1 Authentication Flow

```mermaid
sequenceDiagram

    actor User
    participant FE as Nuxt Frontend
    participant IDP as Identity Provider
    participant API as Backend API

    User->>FE: Login
    FE->>IDP: Authenticate
    IDP-->>FE: Access Token
    FE->>FE: Store authentication state

    FE->>API: Request + Token
    API-->>FE: Response

    FE-->>User: Render application
```

---

# 9. Autorización

Puedes separar autenticación de autorización.

```mermaid
flowchart TD

    User["Usuario"]

    Auth["Authenticated?"]

    Role["Role / Permissions"]

    Route["Protected Route"]

    Component["UI Component"]

    Forbidden["403 / Access Denied"]

    User --> Auth

    Auth -->|No| Login["Login"]
    Auth -->|Yes| Role

    Role -->|Authorized| Route
    Role -->|Unauthorized| Forbidden

    Route --> Component
```

---

# 10. Gestión del estado

Si utilizas Pinia:

```mermaid
flowchart LR

    Component["Vue Component"]

    Store["Pinia Store"]

    Action["Action"]

    API["API Service"]

    Backend["Backend API"]

    State["Reactive State"]

    Component --> Action
    Action --> Store
    Store --> API
    API --> Backend

    Backend --> API
    API --> Store
    Store --> State
    State --> Component
```

Aquí debes documentar qué estado es:

* local
* global
* persistente
* temporal
* derivado

---

# 11. Comunicación con backend

### 11.1 API Communication

```mermaid
sequenceDiagram

    participant UI as UI
    participant Store as Pinia
    participant Service as API Service
    participant API as Backend

    UI->>Store: Load data
    Store->>Service: getData()
    Service->>API: GET /api/data

    API-->>Service: JSON Response
    Service-->>Store: DTO
    Store-->>UI: Reactive State
```

Esto ayuda muchísimo cuando varios desarrolladores trabajan sobre el frontend.

---

# 12. Manejo de errores

Un arquitecto debería definir esto explícitamente.

```mermaid
flowchart TD

    Request["API Request"]

    Request --> Response["Response"]

    Response --> OK{"HTTP Status"}

    OK -->|2xx| Success["Process Response"]
    OK -->|400| Validation["Validation Error"]
    OK -->|401| Unauthorized["Refresh / Login"]
    OK -->|403| Forbidden["Access Denied"]
    OK -->|404| NotFound["Not Found"]
    OK -->|409| Conflict["Business Conflict"]
    OK -->|500| Server["Server Error"]
    OK -->|Network| Network["Network Error"]

    Validation --> UI["Display Message"]
    Unauthorized --> Login["Login"]
    Forbidden --> UI
    NotFound --> UI
    Conflict --> UI
    Server --> UI
    Network --> UI
    Success --> UI
```

---

# 13. Flujo de una funcionalidad crítica

No hagas diagramas de secuencia para absolutamente todo.

Selecciona los procesos críticos.

Por ejemplo:

```mermaid
sequenceDiagram

    actor User
    participant UI as UI
    participant Store as Store
    participant Service as Service
    participant API as Backend

    User->>UI: Registrar cliente

    UI->>UI: Validate form

    alt Datos inválidos
        UI-->>User: Mostrar errores
    else Datos válidos
        UI->>Store: createClient()
        Store->>Service: POST /clients
        Service->>API: POST /api/clients

        alt Creación exitosa
            API-->>Service: 201 Created
            Service-->>Store: Client
            Store-->>UI: Update state
            UI-->>User: Cliente creado
        else Error
            API-->>Service: Error
            Service-->>Store: Error
            Store-->>UI: Error state
            UI-->>User: Mostrar mensaje
        end
    end
```

---

# 14. Diagrama de estados

Muy útil para entidades con workflow.

Por ejemplo, un presupuesto:

```mermaid
stateDiagram-v2

    [*] --> Borrador

    Borrador --> Enviado: Enviar
    Enviado --> Aceptado: Aceptar
    Enviado --> Rechazado: Rechazar
    Enviado --> Caducado: Expirar

    Rechazado --> Borrador: Editar
    Aceptado --> [*]
    Caducado --> [*]
```

Esto evita que cada desarrollador interprete el flujo de manera diferente.

---

# 15. Seguridad

Además del login, documentaría las principales decisiones:

```mermaid
flowchart TB

    Browser["Browser"]

    CSP["Content Security Policy"]
    Auth["Authentication"]
    Guard["Route Guards"]
    Token["Access Token"]
    API["API"]

    Browser --> CSP
    Browser --> Auth
    Auth --> Guard
    Guard --> Token
    Token --> API
```

Y en texto:

```text
- Authentication: OAuth2 / OIDC
- Authorization: RBAC
- Transport: HTTPS
- API authentication: Bearer Token
- Route protection: Nuxt Middleware
- Secrets: Never stored in frontend
- Sensitive data: Never stored in localStorage unless explicitly justified
```

---

# 16. Performance

Aquí normalmente no necesitas un diagrama enorme.

Puedes representar:

```mermaid
flowchart LR

    User["User"]

    CDN["CDN"]

    App["Nuxt Application"]

    Lazy["Lazy Loaded Modules"]

    Cache["Browser Cache"]

    API["Backend API"]

    User --> CDN
    CDN --> App

    App --> Lazy
    App --> Cache
    App --> API
```

Y documentar decisiones como:

* SSR / CSR / SSG
* lazy loading
* code splitting
* caching
* CDN
* optimización de imágenes
* virtualización de tablas
* debounce/throttle
* bundle optimization

---

# 17. Observabilidad

En aplicaciones empresariales modernas yo incluiría esto.

```mermaid
flowchart LR

    FE["Frontend"]

    Logs["Logs"]
    Metrics["Metrics"]
    Errors["Error Tracking"]
    Traces["Distributed Tracing"]

    FE --> Logs
    FE --> Metrics
    FE --> Errors
    FE --> Traces

    Logs --> Observability["Observability Platform"]
    Metrics --> Observability
    Errors --> Observability
    Traces --> Observability
```

Por ejemplo, si utilizas Dynatrace, Application Insights, New Relic, etc., aquí documentas la integración.

---

# 18. Deployment

Finalmente:

```mermaid
flowchart TB

    Developer["Developer"]

    Git["Git Repository"]

    CI["CI/CD Pipeline"]

    Build["Nuxt Build"]

    Artifacts["Build Artifacts"]

    CDN["CDN / WAF"]

    Web["Web Server"]

    API["Backend API"]

    Developer --> Git
    Git --> CI
    CI --> Build
    Build --> Artifacts
    Artifacts --> Web
    Web --> CDN
    CDN --> User["Users"]

    CDN --> API
```

---

# 19. ADR — Architecture Decision Records

Y aquí hay algo que considero **muy importante**.

Los diagramas explican **qué arquitectura tenemos**.

Los ADR explican **por qué la tenemos**.

Por ejemplo:

```text
ADR-001 — Selección de Nuxt 3

Contexto:
La aplicación requiere SSR, routing y estructura modular.

Decisión:
Utilizar Nuxt 3 sobre Vue 3 standalone.

Consecuencias:
+ Routing integrado
+ SSR
+ Estructura convencional
+ Ecosistema Nuxt

Trade-offs:
- Mayor complejidad que Vue standalone
```

Otros ADR podrían ser:

```text
ADR-002 — Pinia para State Management
ADR-003 — API Client centralizado
ADR-004 — Estrategia de autenticación
ADR-005 — Manejo global de errores
ADR-006 — Estrategia SSR/CSR
ADR-007 — Estructura de módulos
ADR-008 — Estrategia de testing
ADR-009 — Observabilidad
ADR-010 — Estrategia de deployment
```

---

# La estructura final que yo usaría

Para tu documentación, quedaría así:

```text
docs/
└── architecture/
    └── frontend/
        │
        ├── 01-context.md
        ├── 02-architecture.md
        ├── 03-containers.md
        ├── 04-components.md
        ├── 05-routing.md
        ├── 06-state-management.md
        ├── 07-api-integration.md
        ├── 08-authentication.md
        ├── 09-authorization.md
        ├── 10-error-handling.md
        ├── 11-critical-flows.md
        ├── 12-security.md
        ├── 13-performance.md
        ├── 14-observability.md
        ├── 15-deployment.md
        │
        └── adr/
            ├── ADR-001-nuxt.md
            ├── ADR-002-state-management.md
            ├── ADR-003-authentication.md
            └── ...
```

## 🎯 Y si quieres hacerlo realmente "de arquitecto"

Yo no intentaría tener **20 diagramas**.

Para un proyecto real, el conjunto mínimo que considero bastante sólido sería:

```text
                    FRONTEND ARCHITECTURE
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
       CONTEXTO          ESTRUCTURA        DESPLIEGUE
           │                 │                 │
           ▼                 ▼                 ▼
       C4 Context        Containers        Deployment
                             │
                             ▼
                         Components
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
           Routing         State           API
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                      SECUENCIAS / FLOWS
                             │
                             ▼
                     SECURITY / ERRORS
```
