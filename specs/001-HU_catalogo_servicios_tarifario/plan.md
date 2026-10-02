# Implementation Plan: FEAT-001 - Catálogo de Servicios y Tarifario Parametrizable

**Feature Name**: FEAT-001 - Catálogo de Servicios y Tarifario Parametrizable
**Tech Stack**: Node.js (v20+), Express.js / TypeScript, PostgreSQL (Prisma ORM), React 18+ / Vite / TypeScript, Jest / Supertest.
**Structure**:
- `app/backend/`: API RESTful, controllers, services, models, middlewares, routes, tests.
- `app/frontend/`: SPA React, components, pages, services, hooks.

---

## User Stories & Technical Breakdown

### User Story 1 - Registro de Servicios (P1)
- Endpoint: `POST /api/v1/servicios`
- Backend Components: `ServicioController.create`, `ServicioService.createServicio`, `ServicioModel`, validation middleware (Zod schema for `nombre`, `categoria`, `unidad_medida`, `tarifa_base > 0`, `moneda ISO 3-letter`).
- Database: Unique index `(nombre, categoria)` in `servicios` table. Soft delete column `estado` (`ACTIVO`/`INACTIVO`).
- Frontend Components: `CatalogoServiciosPage`, `FormularioServicioModal`, `servicioService.createServicio`.

### User Story 2 - Consulta y Filtrado de Servicios (P2)
- Endpoint: `GET /api/v1/servicios` (query params: `categoria`, `estado`, `page`, `limit`).
- Backend Components: `ServicioController.getAll`, `ServicioService.getServicios`, query filtering with pagination.
- Frontend Components: `CatalogoServiciosPage`, `FiltrosCatalogo`, `TablaServicios`.

---

## Architecture & Infrastructure Setup

- `app/backend/package.json`, `tsconfig.json`, Prisma Schema for `Servicio`.
- `app/backend/src/app.ts`, `src/server.ts`, error handling middleware.
- `app/frontend/package.json`, `tsconfig.json`, Vite React setup.

---

## Technical Considerations

- Failure handling: Central error handling middleware mapping `ValidationException` (400), `DuplicateResourceException` (409), `NotFoundException` (404), `InternalServerError` (500).
- Data integrity: `UNIQUE(nombre, categoria)` constraint on `servicios` table. Soft delete implementation.
