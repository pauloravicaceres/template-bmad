# Backend Architecture Document

## 1. Diagrama de contexto

Primero responde:

> ¿Quién consume el backend y con qué sistemas se integra?

```mermaid
flowchart TB

    User["👤 Usuario"]

    Frontend["Frontend<br/>Nuxt 3"]

    Backend["Backend<br/>FastAPI"]

    DB["Database"]

    Identity["Identity Provider"]

    External["External Services"]

    User --> Frontend
    Frontend --> Backend

    Backend --> DB
    Backend --> Identity
    Backend --> External
```

Este es equivalente al **Context Diagram** del frontend.

---

# 2. Diagrama de contenedores

Aquí muestras las grandes piezas del backend.

```mermaid
flowchart TB

    Frontend["Frontend<br/>Nuxt 3"]

    subgraph Backend["Backend — FastAPI"]

        API["API Layer<br/>Routers / Controllers"]

        Application["Application Layer<br/>Use Cases"]

        Domain["Domain Layer<br/>Entities / Rules"]

        Infrastructure["Infrastructure Layer<br/>Repositories / Clients"]

        Persistence["Persistence<br/>SQLAlchemy / ORM"]

        Security["Security<br/>Auth / Authorization"]

    end

    DB[("Database")]

    External["External APIs"]

    Frontend --> API

    API --> Security
    API --> Application

    Application --> Domain
    Application --> Infrastructure

    Infrastructure --> Persistence
    Infrastructure --> External

    Persistence --> DB
```

Este probablemente será **uno de los diagramas principales de tu arquitectura**.

---

# 3. Arquitectura por capas

Si utilizas Clean Architecture, puedes representar explícitamente las dependencias.

```mermaid
flowchart TB

    Presentation["Presentation<br/>FastAPI Routers"]

    Application["Application<br/>Use Cases"]

    Domain["Domain<br/>Entities / Business Rules"]

    Infrastructure["Infrastructure<br/>DB / APIs / Messaging"]

    Presentation --> Application
    Application --> Domain
    Application --> Infrastructure

    Infrastructure -.-> Domain
```

La regla arquitectónica importante sería:

```text
Presentation
      ↓
Application
      ↓
Domain

Infrastructure → implementa interfaces definidas por Application/Domain
```

Es decir, el dominio **no debería depender de FastAPI, SQLAlchemy ni de una base de datos concreta**.

---

# 4. Diagrama de módulos

Muestra cómo está organizado el código.

Por ejemplo:

```mermaid
flowchart TB

    Backend["backend/"]

    Backend --> API["api/"]
    Backend --> Application["application/"]
    Backend --> Domain["domain/"]
    Backend --> Infrastructure["infrastructure/"]
    Backend --> Core["core/"]
    Backend --> Tests["tests/"]

    API --> Routers["routers/"]
    API --> Dependencies["dependencies/"]

    Application --> UseCases["use_cases/"]
    Application --> DTOs["dtos/"]

    Domain --> Entities["entities/"]
    Domain --> Services["services/"]
    Domain --> Repositories["repositories/"]

    Infrastructure --> Database["database/"]
    Infrastructure --> RepositoriesImpl["repositories/"]
    Infrastructure --> External["external/"]
```

Esto después se puede reflejar en la estructura física:

```text
backend/
├── api/
│   ├── routers/
│   └── dependencies/
│
├── application/
│   ├── use_cases/
│   └── dtos/
│
├── domain/
│   ├── entities/
│   ├── services/
│   └── repositories/
│
├── infrastructure/
│   ├── database/
│   ├── repositories/
│   └── external/
│
├── core/
└── tests/
```

---

# 5. Diagrama de componentes

Este es para profundizar en un módulo.

Por ejemplo, **Clientes**:

```mermaid
flowchart LR

    Router["Client Router"]

    UseCase["Create Client<br/>Use Case"]

    Validator["Client Validator"]

    Repository["Client Repository"]

    DB["Database"]

    Router --> Validator
    Router --> UseCase
    UseCase --> Repository
    Repository --> DB
```

Aquí el arquitecto puede explicar claramente:

```text
HTTP Request
     ↓
Router
     ↓
Validation
     ↓
Use Case
     ↓
Repository
     ↓
Database
```

---

# 6. Diagrama de secuencia

Este es **fundamental** para backend.

Por ejemplo:

### Registrar cliente

```mermaid
sequenceDiagram

    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant UC as CreateClient
    participant Repo as ClientRepository
    participant DB as Database

    User->>FE: Registrar cliente

    FE->>API: POST /clients

    API->>API: Validate request

    API->>UC: execute(command)

    UC->>UC: Validate business rules

    UC->>Repo: exists(document)

    Repo->>DB: SELECT

    DB-->>Repo: Result

    alt Cliente existe
        Repo-->>UC: true
        UC-->>API: Conflict
        API-->>FE: 409 Conflict
    else Cliente nuevo
        UC->>Repo: save(client)
        Repo->>DB: INSERT
        DB-->>Repo: Created
        Repo-->>UC: Client
        UC-->>API: Client
        API-->>FE: 201 Created
    end
```

Este tipo de diagrama documenta **el comportamiento real**.

---

# 7. Diagrama de flujo de una petición

Para explicar el pipeline general:

```mermaid
flowchart TD

    Request["HTTP Request"]

    Request --> Middleware["Middleware"]

    Middleware --> Auth["Authentication"]

    Auth --> Authorization["Authorization"]

    Authorization --> Router["Router"]

    Router --> Validation["Request Validation"]

    Validation --> UseCase["Use Case"]

    UseCase --> Domain["Domain Rules"]

    Domain --> Repository["Repository"]

    Repository --> DB["Database"]

    DB --> Response["Response"]

    Response --> Serializer["Response Serialization"]

    Serializer --> Client["HTTP Response"]
```

Este diagrama es excelente para explicar **qué ocurre con una request desde que entra hasta que sale**.

---

# 8. Diagrama de autenticación

```mermaid
sequenceDiagram

    actor User
    participant FE as Frontend
    participant API as FastAPI
    participant IDP as Identity Provider

    User->>FE: Login

    FE->>IDP: Authenticate

    IDP-->>FE: Access Token

    FE->>API: Request + Bearer Token

    API->>API: Validate Token

    API->>API: Extract Claims

    API-->>FE: Response
```

---

# 9. Diagrama de autorización

Autenticación y autorización conviene documentarlas por separado.

```mermaid
flowchart TD

    Request["Request"]

    Request --> Token["Validate Token"]

    Token --> Claims["Extract Claims"]

    Claims --> Role["Resolve Roles"]

    Role --> Permission["Check Permission"]

    Permission -->|Allowed| Endpoint["Execute Endpoint"]

    Permission -->|Denied| Forbidden["403 Forbidden"]
```

Por ejemplo:

```text
USER
 └── ROLE_MANAGER
       ├── CLIENT_READ
       ├── CLIENT_CREATE
       └── CLIENT_UPDATE
```

---

# 10. Diagrama de persistencia

Muestra cómo se conecta la aplicación con la base de datos.

```mermaid
flowchart LR

    UseCase["Use Case"]

    Repository["Repository Interface"]

    RepositoryImpl["Repository Implementation"]

    ORM["SQLAlchemy"]

    DB[("PostgreSQL")]

    UseCase --> Repository
    Repository --> RepositoryImpl
    RepositoryImpl --> ORM
    ORM --> DB
```

Aquí queda muy clara la separación:

```text
Domain/Application
       │
       ▼
Repository Interface
       │
       ▼
Repository Implementation
       │
       ▼
SQLAlchemy
       │
       ▼
Database
```

---

# 11. Diagrama entidad-relación

Este ya es un diagrama de **datos**, no propiamente de componentes.

Por ejemplo:

```mermaid
erDiagram

    CUSTOMER {
        int id PK
        string document
        string name
        string email
        datetime created_at
    }

    ORDER {
        int id PK
        int customer_id FK
        decimal total
        string status
        datetime created_at
    }

    ORDER_DETAIL {
        int id PK
        int order_id FK
        int product_id FK
        int quantity
        decimal price
    }

    PRODUCT {
        int id PK
        string name
        decimal price
    }

    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_DETAIL : contains
    PRODUCT ||--o{ ORDER_DETAIL : included
```

Para sistemas grandes, recomiendo separar:

* modelo lógico
* modelo físico
* ERD por dominio

en lugar de crear un único diagrama gigantesco.

---

# 12. Diagrama de transacciones

Muy importante cuando tienes operaciones que modifican varias entidades.

```mermaid
sequenceDiagram

    participant API
    participant UC as Use Case
    participant DB as Database

    API->>UC: Execute operation

    UC->>DB: BEGIN TRANSACTION

    UC->>DB: INSERT Order
    UC->>DB: INSERT OrderDetail
    UC->>DB: UPDATE Inventory

    alt Everything OK
        UC->>DB: COMMIT
        DB-->>UC: Success
    else Error
        UC->>DB: ROLLBACK
        DB-->>UC: Failure
    end

    UC-->>API: Result
```

---

# 13. Manejo global de errores

Muy recomendable en FastAPI.

```mermaid
flowchart TD

    Request["Request"]

    Request --> API["FastAPI"]

    API --> Error{"Error?"}

    Error -->|No| Response["Success Response"]

    Error -->|Yes| Handler["Global Exception Handler"]

    Handler --> Validation["Validation Error"]
    Handler --> Business["Business Error"]
    Handler --> Auth["Authentication Error"]
    Handler --> Forbidden["Authorization Error"]
    Handler --> NotFound["Not Found"]
    Handler --> Unexpected["Unexpected Error"]

    Validation --> JSON["Standard Error Response"]
    Business --> JSON
    Auth --> JSON
    Forbidden --> JSON
    NotFound --> JSON
    Unexpected --> JSON
```

Y definir un contrato estándar:

```json
{
  "code": "CLIENT_ALREADY_EXISTS",
  "message": "The client already exists",
  "details": [],
  "trace_id": "..."
}
```

---

# 14. Integraciones externas

Si tu backend consume otros sistemas:

```mermaid
flowchart LR

    API["FastAPI"]

    Service["Application Service"]

    Client["External API Client"]

    External["External System"]

    Retry["Retry Policy"]

    Circuit["Circuit Breaker"]

    API --> Service
    Service --> Client

    Client --> Retry
    Retry --> Circuit
    Circuit --> External
```

Aquí puedes documentar:

* timeout
* retry
* circuit breaker
* rate limiting
* fallback
* idempotencia

---

# 15. Procesamiento asíncrono

Si tienes Celery, RabbitMQ, Kafka, Redis, etc.:

```mermaid
flowchart LR

    API["FastAPI"]

    Queue["Message Queue"]

    Worker["Background Worker"]

    DB[("Database")]

    External["External Service"]

    API --> Queue
    Queue --> Worker

    Worker --> DB
    Worker --> External
```

Y para un proceso:

```mermaid
sequenceDiagram

    participant Client
    participant API
    participant Queue
    participant Worker

    Client->>API: POST /process

    API->>Queue: Publish Job

    API-->>Client: 202 Accepted

    Queue->>Worker: Job

    Worker->>Worker: Process

    Worker-->>Queue: Completed
```

---

# 16. Caché

Si utilizas Redis:

```mermaid
flowchart TD

    Request["Request"]

    Request --> Service["Application Service"]

    Service --> Cache{"Cache"}

    Cache -->|HIT| Response["Return Cached Data"]

    Cache -->|MISS| DB["Database"]

    DB --> CacheUpdate["Update Cache"]

    CacheUpdate --> Response
```

---

# 17. Observabilidad

Para backend empresarial esto es casi obligatorio.

```mermaid
flowchart LR

    API["FastAPI"]

    Logs["Logs"]
    Metrics["Metrics"]
    Traces["Traces"]

    API --> Logs
    API --> Metrics
    API --> Traces

    Logs --> Platform["Observability Platform"]
    Metrics --> Platform
    Traces --> Platform
```

Y puedes definir:

```text
Correlation ID
Trace ID
Request ID
Application logs
Business logs
Error logs
Performance metrics
Database metrics
External API metrics
```

---

# 18. Health Checks

```mermaid
flowchart LR

    LB["Load Balancer"]

    API["FastAPI"]

    Health["/health"]

    Readiness["/ready"]

    DB[("Database")]

    Redis["Redis"]

    LB --> Health
    LB --> Readiness

    Readiness --> DB
    Readiness --> Redis

    Health --> API
```

Puedes diferenciar:

```text
/health
→ ¿el proceso está vivo?

/ready
→ ¿el servicio está preparado para recibir tráfico?
```

---

# 19. Rate Limiting

Especialmente importante para APIs públicas.

```mermaid
flowchart TD

    Client["Client"]

    API["API"]

    RateLimiter["Rate Limiter"]

    Endpoint["Endpoint"]

    Client --> API
    API --> RateLimiter

    RateLimiter -->|Within limit| Endpoint
    RateLimiter -->|Limit exceeded| TooMany["429 Too Many Requests"]
```

---

# 20. Deployment

Finalmente, el diagrama físico.

```mermaid
flowchart TB

    Internet["Internet"]

    WAF["WAF"]

    LB["Load Balancer"]

    API1["FastAPI Instance 1"]
    API2["FastAPI Instance 2"]

    DB[("Database")]

    Redis["Redis"]

    Internet --> WAF
    WAF --> LB

    LB --> API1
    LB --> API2

    API1 --> DB
    API2 --> DB

    API1 --> Redis
    API2 --> Redis
```

---

# 21. CI/CD

También puede formar parte de arquitectura operacional:

```mermaid
flowchart LR

    Developer["Developer"]

    Git["Git Repository"]

    CI["CI Pipeline"]

    Tests["Tests"]

    Build["Build"]

    Security["Security Scan"]

    Deploy["Deployment"]

    Runtime["Backend Runtime"]

    Developer --> Git
    Git --> CI

    CI --> Tests
    Tests --> Build
    Build --> Security
    Security --> Deploy
    Deploy --> Runtime
```

---

# 22. ADR

Al igual que frontend, recomiendo ADR para las decisiones importantes.

```text
adr/
├── ADR-001-fastapi.md
├── ADR-002-clean-architecture.md
├── ADR-003-database.md
├── ADR-004-orm.md
├── ADR-005-authentication.md
├── ADR-006-authorization.md
├── ADR-007-error-handling.md
├── ADR-008-caching.md
├── ADR-009-async-processing.md
├── ADR-010-observability.md
└── ADR-011-deployment.md
```

