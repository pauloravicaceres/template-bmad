# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** 02-10-2026
- **Solutions Architect:** Agente SA Senior BMAD
- **Fuente SDD:** `specs/001-HU_catalogo_servicios_tarifario.md`, `files/business-analyst/001-HU_catalogo_servicios_tarifario.md` y `files/designer-ux/ux_001_catalogo_servicios_tarifario.md`

---

## 1. Project Overview
- **Qué es el sistema:** Cotizador Freelance - Plataforma de generación y gestión de propuestas comerciales, estimación de proyectos y catálogo parametrizable de tarifarios.
- **Qué problema resuelve:** Elimina el cálculo manual de presupuestos para desarrolladores freelance estandarizando servicios, tarifas por unidad (hora, módulo, proyecto) y garantizando consistencia comercial.
- **Naturaleza del Proyecto:** Greenfield (Ecosistema modular desacoplado Backend REST API y Frontend SPA).
- **Arquitectura general:** Clean Architecture / Vertical Slice Architecture (VSA) de 3 capas desacopladas, orientada a APIs RESTful sin estado (Stateless REST API + SPA React/TypeScript).

## 2. Repository Structure
- **Partición Física Obligatoria (según `constitution.md`):**
  - `app/backend/`: Servidor API RESTful, modelos de dominio, validaciones de esquemas, servicios de persistencia y controladores de recursos.
  - `app/frontend/`: Cliente Web SPA, componentes de interfaz de usuario UI, manejo de estado local, cliente HTTP y validaciones client-side.
- **Estructura Interna backend (`app/backend/`):**
  - `src/controllers/`: Controladores HTTP REST (`servicios.controller.js` / `.ts`).
  - `src/services/`: Lógica de negocio y reglas de dominio (`servicios.service.js` / `.ts`).
  - `src/models/`: Definición de schemas y modelos de persistencia (`servicio.model.js` / `.ts`).
  - `src/middlewares/`: Validation, Error handling y Logger middlewares.
  - `src/routes/`: Definición formal de rutas API (`servicios.routes.js` / `.ts`).
  - `tests/`: Suite de pruebas automatizadas de integración e infra (`servicios.test.js`).
- **Estructura Interna frontend (`app/frontend/`):**
  - `src/components/`: Componentes UI reutilizables (Modales, Tablas, Formularios, Badges).
  - `src/pages/`: Vistas de nivel superior (`CatalogoServiciosPage`).
  - `src/services/`: Capa de consumo API HTTP (Axios / Fetch wrapper).
  - `src/hooks/`: Custom hooks para manejo de estado de catálogo e integración API.
- **Qué NO debe tocar el Agente Dev:** Ningún archivo fuera de `app/backend/` o `app/frontend/` (ej. no modificar archivos en la raíz del repositorio salvo `.env.example`).

## 3. Tech Stack
- **Runtime:** Node.js (v20+ LTS).
- **Backend Framework:** Express.js (o Fastify) / TypeScript con arquitectura en capas.
- **Frontend Framework:** React 18+ / Vite / TypeScript.
- **Database:** PostgreSQL (Persistencia Relacional) / ORM o Query Builder (Prisma / TypeORM / Knex).
- **Validation Library:** Zod / Joi para validación de esquemas y reglas de dominio (tarifa > 0, código ISO).
- **Testing:** Jest / Vitest + Supertest para integración HTTP no tautológica.
- **Infrastructure:** Contenedores Docker (Docker Compose local para BD y API).

## 4. Development Workflow
- **Cómo levantar el proyecto localmente:**
  - Backend: `cd app/backend && npm install && npm run dev`
  - Frontend: `cd app/frontend && npm install && npm run dev`
  - Base de datos local: `docker-compose up -d postgres`
- **Cómo ejecutar tests / lint / build:**
  - Backend: `cd app/backend && npm test`
  - Frontend: `cd app/frontend && npm test`
- **Cómo ejecutar migraciones de DB:**
  - `cd app/backend && npm run db:migrate`

## 5. Architecture Rules & Decision Framework
- **Principios que deben respetarse:**
  - **Stateless REST API:** Autenticación y comunicación mediante tokens JWT / Bearer stateless.
  - **Single Source of Truth (SSOT):** La base de datos relacional es la única fuente de verdad para las tarifas y estados del catálogo.
  - **Separación de Responsabilidades:** Prohibido inyectar lógica de base de datos o SQL directo en los componentes UI del frontend o en los controladores HTTP del backend.
- **Patrones Prohibidos:** Queda estrictamente prohibido el uso de variables o credenciales "hardcodeadas" en código fuente, así como la eliminación física (`DELETE FROM`) de servicios vinculados a cotizaciones.

### 5.1. State Management Architecture
- **Frontera de Estado:** 
  - La verdad absoluta reside en la Base de Datos Relacional servida por el Backend (`app/backend`).
  - El Frontend (`app/frontend`) gestiona un estado UI reactivo local (React Query / Zustand / useState) para reflejar la paginación, filtros activos, búsquedas con debounce y visibilidad del modal de registro.
- **Estrategia de Sincronización:** 
  - HTTP REST Request/Response con actualización reactiva tras mutaciones (`POST /api/v1/servicios` invalida el cache de la lista para refrescar el catálogo).
- **Consistencia:** 
  - Consistencia Fuerte (Strong Consistency). Las escrituras en `POST /api/v1/servicios` son transaccionales síncronas en la base de datos relacional.
  - Prevención de condiciones de carrera a nivel de BD con restricción UNIQUE en `(nombre, categoria)`.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:** 
  - Middleware global de captura de errores en Backend que transforma excepciones unhandled en respuestas estructuradas JSON con código HTTP 500 y enmascaramiento de trazas sensibles.
- **Patrones de Tolerancia a Fallos:** 
  - **Timeouts obligatorios:** Cliente HTTP en frontend configurado con timeout máximo de 5000ms.
  - **Validación Temprana (Fail-Fast):** Validaciones client-side en modal UX antes de enviar el payload a red, complementado con validación estricta de esquema Zod/Joi en middleware backend antes de tocar la DB.
- **Proporcionalidad:** Arquitectura ligera y limpia adaptada a una aplicación de gestión comercial freelance sin sobre-ingeniería de microservicios distribuida.

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

#### ADR-001: Separación Física de Código en app/backend y app/frontend
- **Estado:** Aceptado (heredado)
  > *Proviene de las directivas globales de `.specify/memory/constitution.md`.*
- **Contexto:** Garantizar la modularidad, aislamiento de despliegues y evitar la dispersión de artefactos en la raíz del repositorio.
- **Decisión:** Organizar todo el código fuente del lado servidor en `app/backend/` y todo el cliente SPA en `app/frontend/`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Claridad de límites para agentes de desarrollo y pipelines de CI/CD.
  - ⚠️ **Trade-off / Costo Real:** Requiere mantener dos contextos de `package.json` o monorepo tooling básico.

#### ADR-002: Base de Datos Relacional PostgreSQL con Restricción de Unicidad por (Nombre, Categoría)
- **Estado:** Aceptado
- **Contexto:** La Historia de Usuario `001-HU_catalogo_servicios_tarifario` exige prevenir servicios duplicados en la misma categoría (SC-04, FR-003, CB-03) e impedir el borrado físico si existen relaciones históricas.
- **Decisión:** Implementar PostgreSQL con una tabla `servicios` con restricción de unicidad compuesta `UNIQUE(nombre, categoria)` e inhabilitación mediante Soft Delete (`estado = 'INACTIVO'`).
- **Alternativas Consideradas:**
  - **Alternativa A (NoSQL / MongoDB):** Permite esquemas flexibles, pero dificulta la aplicación estricta de restricciones de unicidad compuestas y transacciones ACF de integridad referencial.
  - **Alternativa B (In-Memory Data Store / Redis):** Rápido pero sin persistencia durable garantizada ni soporte relacional para auditoría de cotizaciones.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Integridad de datos robusta a nivel de BD, rendimiento óptimo en consultas filtradas e imposibilidad de duplicidad por concurrencia.
  - ⚠️ **Trade-off / Costo Real:** Necesidad de gestionar migraciones de esquema de base de datos (`npm run db:migrate`).

#### ADR-003: Estrategia de Soft Delete para Preservación de Integridad Referencial
- **Estado:** Aceptado
- **Contexto:** Requerimiento FR-006 indica que los servicios vinculados a cotizaciones históricas no deben eliminarse físicamente de la base de datos.
- **Decisión:** Usar el campo `estado ENUM('ACTIVO', 'INACTIVO')` para deshabilitar servicios del catálogo activo sin alterar registros históricos.
- **Alternativas Consideradas:**
  - **Alternativa A (Hard Delete con borrado en cascada):** Destruye el historial de cotizaciones emitidas previamente. Descartado por violar la integridad comercial.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Preservación inmutable de cotizaciones históricas.
  - ⚠️ **Trade-off / Costo Real:** Las consultas de catálogo activo deben incluir siempre el filtro implícito `WHERE estado = 'ACTIVO'`.

---

## 6. Coding Conventions
- **Naming:** 
  - Backend: `camelCase` para variables y funciones, `snake_case` para columnas DB y endpoints API (`/api/v1/servicios`), `PascalCase` para clases y modelos.
  - Frontend: `PascalCase` para componentes React (`CatalogoServiciosTable.tsx`), `camelCase` para hooks (`useServicios`).
- **Error Handling:** 
  - Las API responses de error deben devolver siempre el formato estándar: `{ "error": { "code": "DUPLICATE_RESOURCE", "message": "...", "details": [...] } }`.
- **Logging:** Usem Logger estructurado (Pino / Winston) en JSON. Nunca `console.log` en producción.
- **Async patterns:** `async/await` con bloques `try/catch` o wrappers de middlewares de control de errores.

## 7. Testing
- **Qué debe testearse:**
  - Validaciones de dominio (Tarifa base > 0, campos obligatorios).
  - Casos HTTP BDD: `POST /api/v1/servicios` (201 Created, 400 Bad Request, 409 Conflict).
  - Consultas paginadas `GET /api/v1/servicios` (200 OK).
- **Dónde están los tests:** 
  - Backend: `app/backend/tests/`
  - Frontend: `app/frontend/tests/`

## 8. Security
- **Manejo de secretos:** Todas las variables de entorno (`PORT`, `DATABASE_URL`, `JWT_SECRET`) se configuran vía `.env` y se acceden mediante `process.env`. Prohibido hardcodear credenciales.
- **Sanitización:** Sanitizar inputs HTTP para prevenir Inyección SQL (usar queries parametrizadas / ORM) y XSS.

## 9. Database
- **Schema Name:** `cotizador`
- **Tabla Primaria (`servicios`):**
  - `id`: UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `nombre`: VARCHAR(150) NOT NULL
  - `descripcion`: TEXT NULL
  - `categoria`: VARCHAR(80) NOT NULL
  - `unidad_medida`: VARCHAR(50) NOT NULL
  - `tarifa_base`: NUMERIC(10, 2) NOT NULL CHECK (tarifa_base > 0)
  - `moneda`: VARCHAR(3) NOT NULL DEFAULT 'USD'
  - `estado`: VARCHAR(20) NOT NULL DEFAULT 'ACTIVO' CHECK (estado IN ('ACTIVO', 'INACTIVO'))
  - `created_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - `updated_at`: TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - Restricción Unicidad: `CONSTRAINT uq_servicio_nombre_categoria UNIQUE (nombre, categoria)`
- **Reglas para modificar DB:** Usar migraciones con scripts SQL reversibles (`up` / `down`).

## 10. Git & PR Rules
- **Naming de branches:** `feat/001-HU_catalogo_servicios_tarifario`
- **Commits:** Mensajes bajo convención Conventional Commits (ej. `feat(backend): implement REST controller for catalog services`).

## 11. Agent Instructions (Dev Guidelines)
- **Antes de modificar código:** Verificar la lectura de `specs/001-HU_catalogo_servicios_tarifario.md` y este `tech_guidelines.md`.
- **Después de modificar:** Ejecutar suite de pruebas unitarias/integración (`npm test`) y linter.
- **Confirmación:** Confirmar que no hay variables ni URLs absolutas hardcodeadas en componentes ni controladores.

## 12. Definition of Done
- Todo el código nuevo cuenta con patrones de resiliencia y manejo de estado definidos.
- No hay ninguna credencial o variable de entorno hardcodeada.
- Las migraciones de base de datos han sido auditadas.
- Tests y Lint pasan exitosamente en el entorno de CI.
