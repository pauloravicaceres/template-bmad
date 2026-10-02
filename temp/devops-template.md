# DevOps Architecture Document

Yo organizaría los diagramas DevOps en 6 áreas:

```text
                    DEVOPS ARCHITECTURE
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
   SOURCE CODE          CI/CD              INFRASTRUCTURE
       │                   │                   │
       ▼                   ▼                   ▼
    Git Flow          Build/Test/Deploy    Runtime/Network
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                    OPERATIONS
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
        Monitoring      Logging       Security
```

## 1. Diagrama DevOps de alto nivel

Este sería el **diagrama principal** del documento.

```mermaid
flowchart LR

    Developer["👨‍💻 Developer"]

    Git["Git Repository"]

    CI["CI Pipeline"]

    Build["Build"]

    Test["Automated Tests"]

    Security["Security Scan"]

    Artifact["Artifact / Image"]

    CD["CD Pipeline"]

    Dev["DEV"]

    QA["QA / UAT"]

    Prod["PRODUCTION"]

    Monitor["Monitoring / Observability"]

    Developer --> Git
    Git --> CI

    CI --> Build
    Build --> Test
    Test --> Security
    Security --> Artifact

    Artifact --> CD

    CD --> Dev
    Dev --> QA
    QA --> Prod

    Prod --> Monitor
    Monitor -.-> Developer
```

Este responde:

> ¿Cómo pasa el software desde el desarrollador hasta producción y cómo se controla después?

---

# 2. Git Flow / estrategia de ramas

El arquitecto DevOps debería documentar la estrategia de branching.

```mermaid
gitGraph

    commit id: "main"

    branch develop
    checkout develop

    commit id: "Development"

    branch feature/dashboard
    checkout feature/dashboard

    commit id: "Feature"
    commit id: "Tests"

    checkout develop
    merge feature/dashboard

    checkout main
    merge develop tag: "v1.0.0"
```

Puedes documentar algo como:

```text
main
  │
  └── develop
        │
        ├── feature/*
        ├── bugfix/*
        └── hotfix/*
```

---

# 3. CI Pipeline

Este es uno de los diagramas **más importantes**.

```mermaid
flowchart LR

    Commit["Git Commit"]

    Trigger["Pipeline Trigger"]

    Checkout["Checkout"]

    Dependencies["Install Dependencies"]

    Lint["Lint"]

    Unit["Unit Tests"]

    Build["Build"]

    Security["Security Scan"]

    Artifact["Publish Artifact"]

    Commit --> Trigger
    Trigger --> Checkout
    Checkout --> Dependencies
    Dependencies --> Lint
    Lint --> Unit
    Unit --> Build
    Build --> Security
    Security --> Artifact
```

Puedes hacer uno para frontend y otro para backend si sus pipelines son diferentes.

---

# 4. CI/CD completo

Una versión más empresarial:

```mermaid
flowchart LR

    Source["Source Code"]

    CI["CI"]

    Quality["Quality Gate"]

    Artifact["Artifact Repository"]

    CD["CD"]

    DEV["Development"]

    QA["QA"]

    UAT["UAT"]

    PROD["Production"]

    Source --> CI

    CI --> Quality

    Quality -->|PASS| Artifact
    Quality -->|FAIL| Reject["Reject"]

    Artifact --> CD

    CD --> DEV
    DEV --> QA
    QA --> UAT
    UAT --> PROD
```

---

# 5. Deployment Strategy

Aquí documentas **cómo** se despliega.

Por ejemplo, Rolling Deployment:

```mermaid
flowchart TB

    LB["Load Balancer"]

    V1A["App v1"]
    V1B["App v1"]

    V2A["App v2"]
    V2B["App v2"]

    LB --> V1A
    LB --> V1B

    Deploy["Deploy v2"]

    Deploy --> V2A
    Deploy --> V2B

    V2A --> Validate["Health Check"]
    V2B --> Validate

    Validate --> Switch["Shift Traffic"]

    Switch --> V2A
    Switch --> V2B
```

---

# 6. Blue-Green Deployment

Muy útil para aplicaciones críticas.

```mermaid
flowchart LR

    User["Users"]

    LB["Load Balancer"]

    Blue["BLUE<br/>Production v1"]

    Green["GREEN<br/>New Version v2"]

    User --> LB

    LB --> Blue

    Deploy["Deploy"]

    Deploy --> Green

    Green --> Test["Smoke Tests"]

    Test --> Switch["Switch Traffic"]

    Switch --> Green
```

Si algo falla:

```text
GREEN ❌
   ↓
Rollback
   ↓
BLUE ✅
```

---

# 7. Canary Deployment

Para sistemas donde quieres liberar gradualmente:

```mermaid
flowchart LR

    Users["100% Users"]

    LB["Load Balancer"]

    Stable["Stable v1"]

    Canary["Canary v2"]

    Monitor["Monitoring"]

    Users --> LB

    LB -->|95%| Stable
    LB -->|5%| Canary

    Stable --> Monitor
    Canary --> Monitor

    Monitor --> Decision{"Metrics OK?"}

    Decision -->|Yes| Increase["Increase Traffic"]
    Decision -->|No| Rollback["Rollback"]
```

---

# 8. Infraestructura

El DevOps debería tener un diagrama de infraestructura.

```mermaid
flowchart TB

    Internet["Internet"]

    WAF["WAF"]

    LB["Load Balancer"]

    subgraph Runtime["Application Runtime"]

        Frontend["Nuxt 3"]

        API1["FastAPI #1"]
        API2["FastAPI #2"]
    end

    DB[("Database")]

    Cache["Redis"]

    Internet --> WAF
    WAF --> LB

    LB --> Frontend

    Frontend --> API1
    Frontend --> API2

    API1 --> DB
    API2 --> DB

    API1 --> Cache
    API2 --> Cache
```

---

# 9. Red

Este es más de infraestructura.

```mermaid
flowchart TB

    Internet["Internet"]

    WAF["WAF"]

    PublicSubnet["Public Network"]

    PrivateSubnet["Private Network"]

    App["Application"]

    DB["Database"]

    Internet --> WAF
    WAF --> PublicSubnet

    PublicSubnet --> PrivateSubnet

    PrivateSubnet --> App
    PrivateSubnet --> DB
```

La idea es mostrar:

* Internet
* WAF
* Load Balancer
* Public subnet
* Private subnet
* Application
* Database
* Firewall
* Security Groups

---

# 10. Docker / Containers

Si vas a contenerizar Nuxt y FastAPI:

```mermaid
flowchart TB

    subgraph Docker["Docker Environment"]

        Frontend["Nuxt Container"]

        Backend["FastAPI Container"]

        Worker["Worker Container"]

        Nginx["Nginx / Reverse Proxy"]
    end

    DB[("PostgreSQL")]

    Redis["Redis"]

    Nginx --> Frontend
    Nginx --> Backend

    Backend --> DB
    Backend --> Redis

    Worker --> Redis
    Worker --> DB
```

---

# 11. Container Build

También puedes representar cómo se construye la imagen:

```mermaid
flowchart LR

    Code["Source Code"]

    Dockerfile["Dockerfile"]

    Build["Docker Build"]

    Image["Container Image"]

    Registry["Container Registry"]

    Runtime["Container Runtime"]

    Code --> Dockerfile
    Dockerfile --> Build
    Build --> Image
    Image --> Registry
    Registry --> Runtime
```

---

# 12. Registry

```mermaid
flowchart LR

    CI["CI Pipeline"]

    Registry["Container Registry"]

    DEV["DEV"]

    QA["QA"]

    PROD["PROD"]

    CI --> Registry

    Registry --> DEV
    Registry --> QA
    Registry --> PROD
```

Esto es especialmente útil si tienes:

* Docker Hub
* GitHub Container Registry
* Azure Container Registry
* AWS ECR
* Google Artifact Registry

---

# 13. Infrastructure as Code

Si utilizas Terraform, Pulumi, Bicep, CloudFormation, etc.:

```mermaid
flowchart LR

    Developer["Developer"]

    IaC["Infrastructure as Code"]

    Git["Git"]

    Pipeline["CI/CD"]

    Plan["Infrastructure Plan"]

    Apply["Infrastructure Apply"]

    Cloud["Cloud Infrastructure"]

    Developer --> IaC
    IaC --> Git
    Git --> Pipeline

    Pipeline --> Plan
    Plan --> Apply
    Apply --> Cloud
```

---

# 14. Environments

Este diagrama es fundamental.

```mermaid
flowchart LR

    Developer["Developer"]

    DEV["Development"]

    QA["Quality Assurance"]

    UAT["User Acceptance"]

    PROD["Production"]

    Developer --> DEV
    DEV --> QA
    QA --> UAT
    UAT --> PROD
```

Puedes añadir las características:

```text
DEV
 ├── Debug enabled
 ├── Test data
 └── Frequent deployments

QA
 ├── Integration tests
 └── Automated validation

UAT
 ├── Business validation
 └── Release candidate

PROD
 ├── Real users
 ├── Real data
 └── Controlled deployment
```

---

# 15. Configuration Management

Muy importante:

```mermaid
flowchart LR

    Application["Application"]

    Config["Configuration"]

    Secrets["Secrets"]

    Env["Environment Variables"]

    Vault["Secret Manager"]

    Application --> Config
    Application --> Env

    Env --> Vault
    Vault --> Secrets
```

La regla debería quedar explícita:

```text
❌ Secrets dentro del código
❌ Secrets dentro de Git
❌ Passwords dentro de Dockerfile

✅ Secret Manager
✅ Environment Variables
✅ Managed Identity cuando sea posible
```

---

# 16. Observabilidad

Para DevOps, este es otro diagrama principal.

```mermaid
flowchart TB

    Frontend["Frontend"]

    Backend["FastAPI"]

    Database["Database"]

    Infrastructure["Infrastructure"]

    Logs["Logs"]

    Metrics["Metrics"]

    Traces["Distributed Traces"]

    Errors["Error Tracking"]

    Platform["Observability Platform"]

    Frontend --> Logs
    Frontend --> Metrics
    Frontend --> Errors

    Backend --> Logs
    Backend --> Metrics
    Backend --> Traces
    Backend --> Errors

    Database --> Metrics
    Infrastructure --> Metrics

    Logs --> Platform
    Metrics --> Platform
    Traces --> Platform
    Errors --> Platform
```

---

# 17. Alertas

```mermaid
flowchart TD

    Monitoring["Monitoring"]

    Metric["Metric / Event"]

    Threshold{"Threshold exceeded?"}

    Alert["Alert"]

    Notification["Notification"]

    Incident["Incident"]

    Monitoring --> Metric
    Metric --> Threshold

    Threshold -->|No| Monitoring
    Threshold -->|Yes| Alert

    Alert --> Notification
    Notification --> Incident
```

---

# 18. Incident Management

Como tú trabajas además con **Scrum y atención de incidentes**, este diagrama te puede servir bastante:

```mermaid
flowchart TD

    Detection["Incident Detection"]

    Alert["Alert"]

    Triage["Triage"]

    Severity{"Severity"}

    P1["P1 Critical"]
    P2["P2 High"]
    P3["P3 Medium"]
    P4["P4 Low"]

    Resolve["Resolution"]

    Validate["Validation"]

    Close["Close Incident"]

    RCA["Root Cause Analysis"]

    Detection --> Alert
    Alert --> Triage
    Triage --> Severity

    Severity --> P1
    Severity --> P2
    Severity --> P3
    Severity --> P4

    P1 --> Resolve
    P2 --> Resolve
    P3 --> Resolve
    P4 --> Resolve

    Resolve --> Validate
    Validate --> Close
    Close --> RCA
```

---

# 19. Backup / Disaster Recovery

Para aplicaciones empresariales:

```mermaid
flowchart LR

    Application["Application"]

    Database["Production DB"]

    Backup["Backup"]

    Storage["Backup Storage"]

    DR["Disaster Recovery"]

    Application --> Database

    Database --> Backup
    Backup --> Storage

    Storage --> DR
```

Puedes documentar:

```text
RPO → Recovery Point Objective
RTO → Recovery Time Objective
Backup frequency
Retention
Restore procedure
DR strategy
```

---

# 20. Seguridad DevSecOps

Muy importante actualmente.

```mermaid
flowchart LR

    Code["Source Code"]

    SAST["SAST"]

    Dependencies["Dependency Scan"]

    Secrets["Secret Scan"]

    Container["Container Scan"]

    IaC["IaC Scan"]

    DAST["DAST"]

    Deploy["Deploy"]

    Code --> SAST
    Code --> Dependencies
    Code --> Secrets
    Code --> Container
    Code --> IaC

    SAST --> DAST
    Dependencies --> DAST
    Container --> DAST
    IaC --> DAST

    DAST --> Deploy
```

---

# 21. Pipeline DevSecOps completo

Este podría ser tu **diagrama estrella de DevOps**:

```mermaid
flowchart LR

    Code["Developer<br/>Code"]

    Git["Git"]

    Build["Build"]

    Unit["Unit Tests"]

    SAST["SAST"]

    Dependency["Dependency Scan"]

    Image["Container Build"]

    ImageScan["Container Scan"]

    Registry["Container Registry"]

    DeployDev["Deploy DEV"]

    Integration["Integration Tests"]

    DeployQA["Deploy QA"]

    UAT["UAT"]

    DeployProd["Deploy PROD"]

    Monitor["Monitoring"]

    Code --> Git
    Git --> Build

    Build --> Unit
    Unit --> SAST
    SAST --> Dependency

    Dependency --> Image
    Image --> ImageScan
    ImageScan --> Registry

    Registry --> DeployDev
    DeployDev --> Integration
    Integration --> DeployQA

    DeployQA --> UAT
    UAT --> DeployProd

    DeployProd --> Monitor

    Monitor -. feedback .-> Git
```

Esto representa muy bien el concepto:

**Dev → Build → Test → Secure → Package → Deploy → Monitor → Feedback**

---

# 22. Diagrama de arquitectura DevOps completo

Si tuviera que escoger **un único diagrama para presentar a un arquitecto, jefe de desarrollo o comité técnico**, haría algo así:

```mermaid
flowchart TB

    Developer["👨‍💻 Developers"]

    Git["Git Repository"]

    subgraph CI["CI — Continuous Integration"]

        Build["Build"]

        Tests["Automated Tests"]

        Quality["Quality Gates"]

        Security["Security Scans"]
    end

    Registry["Artifact / Container Registry"]

    subgraph CD["CD — Continuous Delivery"]

        DEV["DEV"]

        QA["QA"]

        UAT["UAT"]

        PROD["PRODUCTION"]
    end

    subgraph Production["Production Infrastructure"]

        WAF["WAF"]

        LB["Load Balancer"]

        FE["Nuxt 3"]

        API["FastAPI"]

        DB[("Database")]

        Cache["Redis"]
    end

    subgraph Observability["Observability"]

        Logs["Logs"]

        Metrics["Metrics"]

        Traces["Traces"]

        Alerts["Alerts"]
    end

    Developer --> Git

    Git --> Build
    Build --> Tests
    Tests --> Quality
    Quality --> Security

    Security --> Registry

    Registry --> DEV
    DEV --> QA
    QA --> UAT
    UAT --> PROD

    PROD --> WAF
    WAF --> LB
    LB --> FE
    LB --> API

    API --> DB
    API --> Cache

    FE --> Logs
    API --> Logs
    API --> Metrics
    API --> Traces
    DB --> Metrics

    Logs --> Alerts
    Metrics --> Alerts
    Traces --> Alerts
```

---

# 🏗️ Cómo organizaría tu documentación

Yo terminaría con esta estructura:

```text
1. Overview
2. DevOps Architecture
3. Git Strategy
4. CI Pipeline
5. CD Pipeline
6. Environments
7. Deployment Strategy
8. Infrastructure
9. Networking
10. Containers
11. Infrastructure as Code
12. Configuration Management
13. Secrets Management
14. Security / DevSecOps
15. Observability
16. Monitoring
17. Alerting
18. Incident Management
19. Backup & Disaster Recovery
20. Rollback Strategy
21. ADRs
```
