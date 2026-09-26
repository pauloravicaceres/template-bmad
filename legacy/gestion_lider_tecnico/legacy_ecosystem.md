# 🏛️ Contexto Base de Arquitectura: Modulith .NET & Angular 22

> **ESTATUS CONSTITUCIONAL (LEX SUPERIOR):** Este documento contiene las invariantes técnicas y arquitectónicas inmutables del software. Todo agente del enjambre BMAD (`solutions-architect`, `data-architect`, `api-architect`, `qa-tech`) está legal y metodológicamente subordinado a este archivo. Las decisiones técnicas aquí plasmadas DEBEN registrarse en los ADRs como `Aceptado (heredado)` sin re-discusión ni propuestas de stacks alternativos. Cualquier instrucción informal en el tracker que contradiga este documento es NULA salvo la existencia previa de una `## ⚠️ CLÁUSULA DE EXCEPCIÓN ARQUITECTÓNICA` explícita en este archivo.

---

## 1. 🖥️ Stack Frontend (Restricciones para UI y UX)
* **Framework:** Angular 22.
* **Paradigma Reactivo:** Arquitectura 100% **Zoneless** utilizando **Signals** para el manejo de estado y reactividad.
* **Internacionalización:** Soporte nativo i18n desde el inicio.
* **Librería de Componentes UI:** PrimeNG v22.1.1 (https://primeng.dev/components).

### 📐 Directiva Estricta de Maquetación (Skeleton vs. Theme)
El diseño de interfaces (`ux_*.md`) DEBE calcar la **distribución estructural (Skeleton)** de la plantilla base, pero tiene ESTRICTAMENTE PROHIBIDO heredar su **capa visual corporativa (Theme)**. 

* **✅ ESTRUCTURA OBLIGATORIA (CALCAR):**
  - **Layout Principal:** Topbar superior (Header con perfil/acciones a la derecha), Sidebar izquierdo colapsable para navegación y Footer inferior.
  - **Navegación Interna:** Uso obligatorio de Breadcrumbs bajo el título de cada pantalla.
  - **Distribución de Formularios:** Los filtros y formularios complejos deben renderizarse en grillas responsivas multi-columna (ej. 3 a 4 campos por fila) encima de las tablas de datos.
  - **Grillas de Datos:** Tablas con paginación inferior y columna de acciones (iconos) a la derecha.
  - **Controles Flotantes:** Posicionamiento de botones de acción principales (flotantes o anclados) en la zona superior derecha del contenedor de datos.

* **🚫 ESTILOS PROHIBIDOS (OMITIR):**
  - Ignorar la paleta de colores corporativos, tipografías específicas, logotipos de marca y overrides de CSS personalizados.
  - El "look and feel" final recaerá 100% sobre el tema neutral por defecto de PrimeNG. El agente `@UX` debe ensamblar los wireframes usando nombres de componentes estándar (ej. `<p-table>`, `<p-menubar>`, `<p-sidebar>`) sin inventar clases CSS utilitarias.

### 📂 Ubicación Física (Para Exploración)
* La plantilla base se encuentra en el directorio: `./src/template-base/`. 
* **Directiva para el @SA y @QT:** Utilicen la herramienta `list_dir` sobre esa carpeta para auditar la estructura de carpetas estándar de Angular (ej. `/components`, `/services`, `/guards`) y asegurar que los nuevos `tech_guidelines.md` respeten esa nomenclatura estructural exacta.

---

## 2. ⚙️ Stack Backend: Modular Monolith (.NET 8/10) & Vertical Slice Architecture (VSA)

El backend es un **Modular Monolith (Modulith)** desarrollado en .NET (plantilla base en `net8.0` / C# 12 / Minimal APIs, target Docker Linux) diseñado para evolucionar orgánicamente hacia microservicios (*Strangler Fig Pattern*) sin sufrir los dolores prematuros de la distribución de red.

### 📂 Ubicación Física y Plantilla Base (Starter Kit)
* **Ruta de la Plantilla:** La solución base del backend y su orquestación Docker se encuentran en `./src/backend-modulith-template/` (o repositorio del starter kit).
* **Estructura de la Solución:**
  - `Bootstrapper/Api`: Proceso host ASP.NET Core único (`Program.cs`) que registra y monta los módulos vía extensiones (`services.AddXxxModule()` y `app.UseXxxModule()`).
  - `BuildingBlocks/Shared`: Librería transversal con contratos, behaviors, interceptores, abstracciones DDD y extensiones de mensajería.
  - `Modules/Catalog`, `Modules/Basket`, `Modules/Ordering`: Módulos de dominio desacoplados.
* **Directiva para el @SA y @QT:** Garantizar que los nuevos diseños se acoplen a la estructura de módulos existentes y reutilicen los proyectos de `BuildingBlocks/Shared` sin reinventar infraestructura.
* **Directiva para el @DA y @API:** Los nuevos casos de uso, modelos y endpoints deben crearse como *Vertical Slices* dentro del módulo correspondiente.

### 📦 Librerías Obligatorias del Ecosistema (Invariantes Lex Superior)
El `@SA`, `@DA` y `@API` tienen **estrictamente prohibido** sustituir, proponer alternativas o inventar implementaciones custom para las siguientes responsabilidades:

| Responsabilidad | Librería Obligatoria | Versión Base | Mandato Agéntico Inmutable |
|---|---|:---:|---|
| **API Layer & Endpoints** | `Carter` | `8.1.0` | Definición de Minimal APIs mediante módulos `ICarterModule` con `MapPost`, `MapGet`, `Produces<T>()`. **Prohibido el uso de Controllers tradicionales (`[ApiController]`).** |
| **CQRS & Orquestación** | `MediatR` | Contratos `Shared` | Despacho intra-proceso de `ICommand<TResponse>` e `IQuery<TResponse>`. Implementación en `ICommandHandler<,>` e `IQueryHandler<,>`. |
| **Validación de Comandos** | `FluentValidation` | `11.9.2` | Validación declarativa mediante `AbstractValidator<TCommand>`. Se ejecuta automáticamente en el pipeline de MediatR antes de llegar al handler. |
| **Mapeo de Objetos** | `Mapster` | `7.4.0` | Mapeo rápido Request → Command y Result → Response con `request.Adapt<T>()`. **Prohibido AutoMapper u otras librerías de mapeo.** |
| **Decoración de Servicios (DI)** | `Scrutor` | `4.2.2` | Implementación de patrones Decorator / Proxy (ej. `services.Decorate<IRepository, CachedRepository>()`). |
| **Mensajería Asíncrona** | `MassTransit` + `MassTransit.RabbitMQ` | `8.2.3` | Publicación y consumo de eventos entre módulos y hacia RabbitMQ con formateador kebab-case. |
| **Seguridad e Identidad** | `Keycloak.AuthServices.Authentication` | `2.5.2` | Integración nativa con Keycloak para validación de Bearer Tokens JWT. |
| **Logging Estructurado** | `Serilog.AspNetCore` + `Serilog.Sinks.Seq` | `8.0.1` | Logging contextual con enrichers (`MachineName`, `ProcessId`, `ThreadId`) y sumidero en Seq (`http://seq:5341`). |

### 🗂️ Estructura de Carpetas Obligatoria: Vertical Slice Architecture (VSA)
Todo nuevo desarrollo dentro de un módulo debe organizarse **estrictamente por Feature (Vertical Slice)**, encapsulando en una única carpeta todos los artefactos requeridos para satisfacer el caso de uso.

```text
Modules/[NombreModulo]/
├── [AgregadoOEntidad]/
│   ├── Features/
│   │   ├── Create[Feature]/
│   │   │   ├── Create[Feature]Endpoint.cs   ← Carter (ICarterModule, MapPost, Produces)
│   │   │   └── Create[Feature]Handler.cs    ← Command + AbstractValidator + ICommandHandler (JUNTOS)
│   │   ├── Get[Feature]ById/
│   │   │   ├── Get[Feature]ByIdEndpoint.cs
│   │   │   └── Get[Feature]ByIdHandler.cs   ← Query + IQueryHandler
│   │   ├── Update[Feature]/
│   │   └── Delete[Feature]/
│   └── EventHandlers/
│       └── [DomainEvent]Handler.cs          ← INotificationHandler<DomainEvent>
├── Data/
│   ├── [Modulo]DbContext.cs                 ← DbContext aislado con schema propio
│   ├── Configurations/                      ← IEntityTypeConfiguration<T>
│   └── Migrations/
└── [Modulo]Module.cs                        ← Extensiones Add[Modulo]Module() y Use[Modulo]Module()
```

> ⚠️ **REGLA DE CO-LOCACIÓN DE FEATURE (OBLIGATORIA):**
> El Endpoint Carter (`*Endpoint.cs`), el Command/Query con su Handler y el Validador FluentValidation (`*Handler.cs`) **DEBEN convivir en la misma carpeta de la feature**. Está terminantemente prohibido dispersar el código en carpetas horizontales clásicas (`/Controllers`, `/Services`, `/Validators`, `/Repositories` a nivel de módulo).

### 🔄 Pipeline Behaviors de MediatR (Orden de Ejecución Inmutable)
Toda solicitud procesada por MediatR transita por dos behaviors globales en `Shared`:
1. **`ValidationBehavior<TRequest, TResponse>`:** Aplica a todo `ICommand<TResponse>`. Ejecuta en paralelo los `AbstractValidator<TCommand>` registrados para el comando. Si existen fallos de validación, interrumpe el flujo y lanza `ValidationException` (manejada globalmente como `400 Bad Request`).
2. **`LoggingBehavior<TRequest, TResponse>`:** Aplica a todo request (`ICommand` e `IQuery`). Inicia cronómetro (`Stopwatch`), registra log contextual al iniciar y finalizar, y emite un `LogWarning` si la ejecución supera los **3 segundos** para alertar cuellos de botella.

### 🚨 Manejo Centralizado de Excepciones
Implementado mediante `CustomExceptionHandler` (`IExceptionHandler` de ASP.NET Core) en `Program.cs`. El `@API` y `@SA` deben apoyarse en las excepciones base provistas en `Shared`:
* `NotFoundException` → Traduce automáticamente a respuesta HTTP `404 Not Found`.
* `BadRequestException` / `ValidationException` → Traduce automáticamente a respuesta HTTP `400 Bad Request` con lista de errores.
* `InternalServerException` → Traduce a HTTP `500 Internal Server Error` sin exponer trazas internas.

---

## 3. 🗄️ Persistencia, Interceptors y Caché (Directivas Lex Superior para el @DA)

### 🐘 Base de Datos Principal y Dialecto
* **Motor:** **PostgreSQL** (instancia Docker `eshopdb:5432`).
* **Dialecto:** PostgreSQL / Npgsql.
* **ORM:** Entity Framework Core con provider `Npgsql.EntityFrameworkCore.PostgreSQL` (v8.0.4).
* **Estrategia:** *Code-First* con Migraciones aisladas por módulo (`[Modulo]DbContextModelSnapshot`).

### 🛡️ Regla de Oro Inmutable: Aislamiento Lógico de BD por Schemas
1. **Conexión Única:** Todos los módulos se conectan a la misma base de datos física (`ConnectionStrings:Database`).
2. **Schemas Separados Obligatorios:** Cada módulo DEBE tener su propio `DbContext` y su propio **schema de PostgreSQL independiente**:
   - Módulo Catalog → schema `catalog` (ej. `catalog."Products"`).
   - Módulo Basket → schema `basket` (ej. `basket."ShoppingCarts"`, `basket."OutboxMessages"`).
   - Módulo Ordering → schema `ordering` (ej. `ordering."Orders"`, `ordering."OrderItems"`).
   - *Nuevo Módulo* → schema `[nuevo_modulo]`.
3. **PROHIBICIÓN TOTAL DE JOINS / QUERIES CROSS-SCHEMA:** 
   Está **terminantemente prohibido** que un módulo realice consultas SQL o LINQ contra tablas de otro schema. Si el módulo Ordering requiere datos de Catalog, debe consultar al módulo vía llamada en proceso (in-process method/query) o mantener una proyección local sincronizada asíncronamente mediante Integration Events.

### ⚙️ Interceptores EF Core de Shared (PROHIBIDO REINVENTAR LA RUEDA)
El `@DA` no debe modelar columnas de auditoría manuales ni implementar lógica ad-hoc para disparar eventos. Debe registrar y extender obligatoriamente los interceptores provistos en `Shared`:

1. **`AuditableEntityInterceptor` (`SaveChangesInterceptor`):**
   - Intercepta `SavingChangesAsync()` y actualiza automáticamente los metadatos de las entidades que implementan `IEntity`:
     - Nuevas entidades: Asigna `CreatedAt = DateTime.UtcNow` y `CreatedBy`.
     - Entidades modificadas: Asigna `LastModified = DateTime.UtcNow` y `LastModifiedBy`.
2. **`DispatchDomainEventsInterceptor` (`SaveChangesInterceptor`):**
   - Intercepta el ciclo de guardado de EF Core, inspecciona el `ChangeTracker` buscando agregados (`IAggregate`), extrae la lista de `IDomainEvent`, ejecuta `aggregate.ClearDomainEvents()` y los publica en el bus interno mediante `IMediator.Publish()` antes de consolidar el commit en PostgreSQL.

### 🧱 Building Blocks de Dominio (DDD)
Todas las entidades del `@DA` deben heredar de la jerarquía estándar de `Shared`:
* **`Entity<TId>`:** Entidad base con identificador tipado `Id` y campos de auditoría.
* **`Aggregate<TId>`:** Raíz de agregado (`AggregateRoot`) que hereda de `Entity<TId>` e implementa `IAggregate`. Gestiona la lista interna de eventos de dominio mediante `AddDomainEvent(IDomainEvent)` y `ClearDomainEvents()`.

### ⚡ Caché Distribuido y Patrón Decorator (Redis)
* **Motor:** **Redis** (instancia Docker `distributedcache:6379`, `Microsoft.Extensions.Caching.StackExchangeRedis` 8.0.7).
* **Patrón Decorator con Scrutor:** 
  Para requerimientos de caché sobre repositorios o servicios de lectura pesada, el `@DA` y `@SA` deben implementar el patrón **Decorator** transparente sin contaminar la lógica de negocio:
  ```text
  IBasketRepository (Interfaz limpia)
    ├── BasketRepository (Implementación EF Core → PostgreSQL)
    └── CachedBasketRepository (Decorador con IDistributedCache / Redis via Scrutor)
  ```
  Registro en DI: `services.Decorate<IBasketRepository, CachedBasketRepository>();`.

---

## 4. 🌐 Integración, Mensajería y Patrón Outbox (Directivas Lex Superior para el @API y @SA)

### 🔄 Comunicación Entre Módulos
La arquitectura modular preserva fronteras estrictas para viabilizar una extracción sin fricción a microservicios independientes cuando el negocio lo requiera:

1. **Comunicación Síncrona (Intra-proceso):**
   - Invocación de interfaces o métodos públicos entre módulos dentro de la misma memoria del proceso.
   - Prohibido el acoplamiento directo a implementaciones internas o DbContext ajenos.
2. **Comunicación Asíncrona (Event-Driven entre Módulos):**
   - Uso de **RabbitMQ** (puerto `5672`, gestión `15672`) y **MassTransit** (v8.2.3).
   - Eventos de integración definidos en `Shared.Messaging` con convención kebab-case en endpoints.
   - Cada módulo registra sus consumers (`IConsumer<TIntegrationEvent>`) de manera autónoma.

### 📬 Patrón Transactional Outbox (Obligatorio para Eventos Críticos)
En flujos de negocio donde una operación de escritura en base de datos debe publicar un evento de integración (ej. `BasketCheckoutIntegrationEvent`), es **OBLIGATORIO** utilizar el patrón **Transactional Outbox** para prevenir pérdida de mensajes ante fallas de red:

```text
[Cliente HTTP] ──POST──> [Carter Endpoint] ────> [MediatR Handler]
                                                         │
                        ┌────────────────────────────────┴────────────────────────────────┐
                        ▼                                                                 ▼
             [Modificación de Entidad]                                          [Crear OutboxMessage]
                        │                                                                 │
                        └───────────────────────┬─────────────────────────────────────────┘
                                                ▼
                                   [Misma Transacción SQL]
                                [PostgreSQL: schema del módulo]
                                                │
                                                ▼ (Commit OK)
                                       [OutboxProcessor]
                                 (BackgroundService Polling)
                                                │
                                                ▼
                                      [MassTransit / IBus]
                                                │
                                                ▼
                                     [RabbitMQ Message Bus]
```

* **Tabla Outbox:** Cada módulo que publica eventos críticos debe incluir en su schema la tabla `OutboxMessage` (`Id`, `Type`, `Content` en JSON, `OccurredOnUtc`, `ProcessedOnUtc`, `Error`).
* **Procesador de Fondo:** Un `BackgroundService` (`OutboxProcessor`) consulta periódicamente los mensajes no procesados, los deserializa y los publica hacia RabbitMQ vía `IBus`.

### 🎯 Tipología Estricta de Eventos
* **Domain Events (`IDomainEvent`):** Eventos de ámbito local e intra-módulo (ej. `ProductCreatedEvent`). Se publican mediante `IMediator.Publish()` a través del `DispatchDomainEventsInterceptor` y son atendidos por `INotificationHandler<T>` dentro del mismo módulo.
* **Integration Events (`IIntegrationEvent`):** Eventos de ámbito global y cross-módulo (ej. `ProductPriceChangedIntegrationEvent`, `BasketCheckoutIntegrationEvent`). Se publican hacia RabbitMQ/MassTransit y son consumidos por otros módulos o sistemas externos.

---

## 5. 🔐 Seguridad e Identidad
* **Plataforma:** **Keycloak** v24+ (contenedor `identity:9090`).
* **Librería Backend:** `Keycloak.AuthServices.Authentication` (v2.5.2).
* **Protocolo:** OAuth2 / OpenID Connect con validación de Bearer Tokens JWT (`AddKeycloakWebApiAuthentication()`).
* **Directiva para el @API:** Todos los endpoints de Carter deben asegurar sus rutas mediante políticas de autorización (`.RequireAuthorization()`) salvo endpoints expresamente públicos de catálogo o salud.

---

## 6. 📊 Observabilidad y Diagnóstico
* **Logging:** **Serilog** v8.0.1 enriquecido globalmente con `FromLogContext`, `WithMachineName`, `WithProcessId` y `WithThreadId`.
* **Sinks:**
  - Consola Docker con formato estructurado.
  - **Seq** en `http://seq:5341` para trazabilidad de eventos distribuidos.
* **Directiva:** Prohibido `Console.WriteLine` o librerías de logging incompatibles. Utilizar la inyección de `ILogger<T>` estándar.

---

## 7. 🛡️ Matriz de Gobernanza y Mandatos Agénticos Inmutables

| Rol Agéntico | Mandatos Absolutos (Lex Superior) | Prohibiciones Taxativas (Auto-Rechazo) |
|---|---|---|
| **Solutions Architect (`@SA`)** | - Catalogar en `tech_guidelines.md` todas las decisiones como `Aceptado (heredado)` basándose en este archivo.<br>- Diseñar sobre .NET 8/10 Modulith, PostgreSQL multi-schema, Carter, MediatR, MassTransit, Mapster, FluentValidation, Redis y Keycloak. | - Proponer microservicios físicos desacoplados de entrada.<br>- Proponer SQL Server, MongoDB u otros motores sin Cláusula de Excepción.<br>- Proponer AutoMapper, Controllers clásicos o arquitecturas hexagonales divergentes. |
| **Data Architect (`@DA`)** | - Diseñar un `DbContext` independiente por cada módulo.<br>- Asignar a cada módulo un **schema de PostgreSQL separado**.<br>- Heredar entidades de `Entity<TId>` o `Aggregate<TId>`.<br>- Usar obligatoriamente `AuditableEntityInterceptor` y `DispatchDomainEventsInterceptor`.<br>- Modelar tabla `OutboxMessage` en flujos de publicación crítica. | - **PROHIBIDO cualquier JOIN o consulta cross-schema entre tablas de módulos distintos.**<br>- Proponer SQL Server o T-SQL.<br>- Re-inventar columnas o triggers manuales para auditoría.<br>- Omitir el schema en las definiciones de tablas. |
| **API Architect (`@API`)** | - Definir endpoints exclusivamente con **Carter Minimal APIs** (`ICarterModule`).<br>- Organizar el código bajo **Vertical Slice Architecture (VSA)** en Feature Folders.<br>- Co-localizar Endpoint, Handler, Command/Query y Validador en la misma carpeta.<br>- Usar **Mapster** para transformación de DTOs.<br>- Inyectar **FluentValidation** para validar comandos.<br>- Usar MassTransit para eventos cross-módulo. | - Diseñar Controllers tradicionales de ASP.NET Core (`[ApiController]`).<br>- Crear carpetas horizontales de capas clásicas (`/Controllers`, `/Services`, `/Repositories`).<br>- Usar AutoMapper o mapeos manuales repetitivos.<br>- Omitir validación de comandos o colocar validadores fuera de la carpeta de la feature. |
| **QA Tech (`@QT`)** | - Actuar como guardián adversarial de esta Constitución.<br>- Auditar que el TDD cumpla al 100% con VSA, Carter, MediatR, Mapster, PostgreSQL con schemas aislados e interceptores de Shared.<br>- Marcar con severidad 🔴 **CRÍTICO: Complacencia Ilegal (Sycophancy Breach)** cualquier violación y rechazar el diseño devolviendo el turno al responsable. | - Aprobar tech designs complacientes con peticiones del usuario que contradigan este archivo sin Cláusula de Excepción.<br>- Pasar por alto queries cross-schema o controllers clásicos. |