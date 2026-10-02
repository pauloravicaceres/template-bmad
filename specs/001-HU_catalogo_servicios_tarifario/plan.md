# Implementation Plan: FEAT-001 - Catálogo de Servicios y Tarifario Parametrizable

**Branch**: `feat/001-HU_catalogo_servicios_tarifario` | **Date**: 2026-10-02 | **Spec**: [spec.md](file:///D:/Paulo/Cursos/DMC/template-bmad/specs/001-HU_catalogo_servicios_tarifario/spec.md)

**Input**: Feature specification from `specs/001-HU_catalogo_servicios_tarifario/spec.md`

## Summary

Implementar el módulo de **Catálogo de Servicios y Tarifario Parametrizable** (FEAT-001) para la plataforma Cotizador Freelance. La solución provee un listado estandarizado y reutilizable de servicios y componentes funcionales con sus respectivas tarifas base y unidades de medida. El enfoque técnico consiste en una arquitectura en capas desacoplada de 3 niveles (Stateless REST API + SPA React/TypeScript) con persistencia relacional síncrona en PostgreSQL administrada a través de Prisma ORM. Se garantiza prevención estricta de duplicados mediante un índice de unicidad compuesto `UNIQUE(nombre, categoria)` y control de borrado lógico (Soft Delete) para preservar la integridad de cotizaciones históricas.

## Technical Context

**Language/Version**: Node.js v20+ LTS, TypeScript 5.3+
**Primary Dependencies**: Express.js 4.18+, React 18+, Prisma ORM 5.10+, Zod 3.22+, Axios 1.6+
**Storage**: PostgreSQL 16 (Persistencia Relacional) con Prisma ORM
**Testing**: Jest 29+, Supertest 6.3+, ts-jest
**Target Platform**: Web Browsers (Modern SPA) / Linux Container Server (Node.js REST API)
**Project Type**: Web Application (Backend REST API + Frontend SPA)
**Performance Goals**: Persistencia y respuesta de registro en < 500 ms (SC-001), consulta paginada en < 200 ms
**Constraints**: Validación numérico-monetaria positiva (`tarifa_base > 0`), restricción estricta de unicidad `UNIQUE(nombre, categoria)` (SC-003), Soft Delete obligatorio (`estado = 'INACTIVO'`) para mantener integridad referencial (FR-006)
**Scale/Scope**: Catálogo reutilizable para cotizaciones comerciales, 2 User Stories (P1: Registro, P2: Consulta/Filtrado), 31 tareas compiladas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Physical Partitioning Gate**: Backend local en `app/backend/` y Frontend local en `app/frontend/`. Cumple con la regla inmutable de `.specify/memory/constitution.md` y `tech_guidelines.md`.
- [x] **Test-First / BDD Gate**: Cobertura automatizada del 100% de escenarios BDD mediante pruebas de integración HTTP (`supertest` / Jest).
- [x] **Data Integrity Gate**: Uso de tipo monetario exacto `DECIMAL(12, 2)` (evitando imprecisión flotante), UUID v4 como PK y Soft Delete para preservar el historial de cotizaciones.
- [x] **Stateless REST Gate**: Comunicación mediante JSON estructurado sobre HTTP REST con manejo global de errores e impedimento de variables/credenciales hardcodeadas.

## Project Structure

### Documentation (this feature)

```text
specs/001-HU_catalogo_servicios_tarifario/
├── plan.md              # Este plan de implementación congelado
├── spec.md              # Especificación técnica del feature
└── tasks.md             # Tareas de implementación desglosadas (Fases 1 a 5)
```

### Source Code (repository root)

```text
app/
├── backend/
│   ├── prisma/
│   │   ├── migrations/   # Migraciones de base de datos PostgreSQL
│   │   ├── schema.prisma # Esquema relacional del modelo Servicio
│   │   └── seed.ts       # Script de datos iniciales
│   ├── src/
│   │   ├── config/       # Variables de entorno e infra
│   │   ├── controllers/  # ServiciosController (Endpoints REST HTTP)
│   │   ├── middlewares/  # ErrorHandler & Zod Validation
│   │   ├── models/       # ServicioModel (Prisma Client Wrapper)
│   │   ├── routes/       # Rutas Express /api/v1/servicios
│   │   ├── schemas/      # Esquemas de validación Zod (servicio & query)
│   │   ├── services/     # ServiciosService (Lógica de Negocio)
│   │   ├── app.ts        # Configuración de Express App
│   │   └── server.ts     # Entrypoint del servidor Node.js
│   └── tests/
│       └── integration/  # Pruebas de integración HTTP (servicios.create / servicios.get)
│
└── frontend/
    ├── src/
    │   ├── components/   # TablaServicios, FiltrosCatalogo, FormularioServicioModal
    │   ├── pages/        # CatalogoServiciosPage
    │   ├── services/     # apiClient (Axios wrapper) & serviciosApi
    │   ├── App.tsx       # Componente principal React
    │   └── main.tsx      # Entrypoint Vite React
    └── vite.config.ts    # Configuración de Vite SPA
```

**Structure Decision**: Seleccionada la Opción 2 (Web application) con partición física estricta entre `app/backend/` y `app/frontend/` según lo normado en la arquitectura del ecosistema BMAD (`tech_guidelines.md` y `ARCHITECTURE.md`).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations. All design patterns align 100% with project guidelines and constitution.*
