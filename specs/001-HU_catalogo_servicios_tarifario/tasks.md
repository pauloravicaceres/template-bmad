# Tareas de Implementación: FEAT-001 - Catálogo de Servicios y Tarifario Parametrizable

**Feature Branch**: `feat/001-HU_catalogo_servicios_tarifario`  
**Especificación de Origen**: `specs/001-HU_catalogo_servicios_tarifario/spec.md`  
**Plan Técnico**: `specs/001-HU_catalogo_servicios_tarifario/plan.md`  

---

## Phase 1: Setup (Infraestructura Compartida)

**Propósito**: Inicialización del proyecto y definición de la estructura base en `app/backend/` y `app/frontend/`.

- [x] T001 Inicializar la estructura base del proyecto con directorios app/backend/ y app/frontend/ en `app/`
- [x] T002 Configurar las dependencias de Node.js, Express, TypeScript y Prisma ORM en `app/backend/package.json` y `app/backend/tsconfig.json`
- [x] T003 [P] Configurar el cliente React 18, Vite y TypeScript en `app/frontend/package.json` y `app/frontend/vite.config.ts`
- [x] T004 [P] Configurar herramientas de linting y formateo de código en `app/backend/.eslintrc.json` y `app/frontend/.eslintrc.json`

---

## Phase 2: Foundational (Prerrequisitos Bloqueantes)

**Propósito**: Infraestructura central que DEBE completarse antes de implementar cualquier Historia de Usuario.

- [x] T005 Diseñar el esquema de base de datos relacional Prisma con modelo Servicio, restricción `UNIQUE(nombre, categoria)` y columna `estado` en `app/backend/prisma/schema.prisma`
- [x] T006 Generar y ejecutar migraciones iniciales de PostgreSQL en `app/backend/prisma/migrations/`
- [x] T007 [P] Configurar la carga y validación de variables de entorno en `app/backend/src/config/env.ts`
- [x] T008 [P] Implementar middleware global de captura de errores y formateo de respuestas JSON estructuradas en `app/backend/src/middlewares/errorHandler.ts`
- [x] T009 Configurar el servidor Express, middlewares centrales y montaje de rutas en `app/backend/src/app.ts` y `app/backend/src/server.ts`
- [x] T010 [P] Configurar el cliente HTTP Axios/Fetch con timeout máximo de 5000ms en `app/frontend/src/services/apiClient.ts`

---

## Phase 3: User Story 1 - Registro exitoso de servicios y componentes en el catálogo (Prioridad: P1) 🌟 MVP

**Meta**: Registrar nuevos servicios y componentes con tarifas numéricas positivas (`tarifa > 0`), unidad de medida y código ISO de moneda (por defecto `USD`), previniendo duplicados por categoría.  
**Prueba Independiente**: Ejecutar `POST /api/v1/servicios` con payload válido y verificar respuesta HTTP 201 Created con ID asignado; validar respuestas 400 Bad Request ante tarifas inválidas y 409 Conflict ante duplicados.

### Pruebas para User Story 1

- [x] T011 [P] [US1] Crear pruebas automatizadas de integración HTTP para el endpoint de creación de servicios en `app/backend/tests/integration/servicios.create.test.ts`

### Implementación Backend para User Story 1

- [x] T012 [P] [US1] Definir esquema de validación Zod con reglas de dominio (tarifa_base > 0, código ISO de 3 letras, campos requeridos) en `app/backend/src/schemas/servicio.schema.ts`
- [x] T013 [P] [US1] Implementar métodos de persistencia y consultas ORM para servicios en `app/backend/src/models/servicio.model.ts`
- [x] T014 [US1] Implementar lógica de negocio y verificación de unicidad por categoría en `app/backend/src/services/servicios.service.ts`
- [x] T015 [US1] Crear controlador HTTP `POST /api/v1/servicios` para recepción de solicitudes y respuestas RESTful en `app/backend/src/controllers/servicios.controller.ts`
- [x] T016 [US1] Registrar la ruta `POST /api/v1/servicios` en `app/backend/src/routes/servicios.routes.ts`

### Implementación Frontend para User Story 1

- [x] T017 [P] [US1] Crear módulo de consumo API para creación de servicios en `app/frontend/src/services/serviciosApi.ts`
- [x] T018 [P] [US1] Crear componente Modal de formulario con validaciones client-side para registro de servicios en `app/frontend/src/components/FormularioServicioModal.tsx`
- [x] T019 [US1] Integrar el modal de creación y la actualización reactiva en la página principal `app/frontend/src/pages/CatalogoServiciosPage.tsx`

---

## Phase 4: User Story 2 - Consulta y filtrado del catálogo de servicios (Prioridad: P2)

**Meta**: Permitir consultar y filtrar la lista de servicios registrados por categoría o estado con soporte de paginación.  
**Prueba Independiente**: Enviar una petición `GET /api/v1/servicios` con parámetros opcionales `categoria` o `estado` y verificar el listado retornado con código HTTP 200 OK.

### Pruebas para User Story 2

- [x] T020 [P] [US2] Crear pruebas automatizadas de integración HTTP para la consulta y filtrado de servicios en `app/backend/tests/integration/servicios.get.test.ts`

### Implementación Backend para User Story 2

- [x] T021 [P] [US2] Definir esquema de validación Zod para parámetros de consulta `categoria`, `estado`, `page` y `limit` en `app/backend/src/schemas/servicioQuery.schema.ts`
- [x] T022 [US2] Implementar consultas paginadas y filtradas en el modelo ORM `app/backend/src/models/servicio.model.ts`
- [x] T023 [US2] Extender el servicio de negocio para soportar filtrado y paginación en `app/backend/src/services/servicios.service.ts`
- [x] T024 [US2] Crear controlador HTTP `GET /api/v1/servicios` en `app/backend/src/controllers/servicios.controller.ts`
- [x] T025 [US2] Registrar la ruta `GET /api/v1/servicios` en `app/backend/src/routes/servicios.routes.ts`

### Implementación Frontend para User Story 2

- [x] T026 [P] [US2] Implementar componente de tabla paginada con indicadores de tarifa y estado en `app/frontend/src/components/TablaServicios.tsx`
- [x] T027 [P] [US2] Crear componente de filtros por categoría y estado en `app/frontend/src/components/FiltrosCatalogo.tsx`
- [x] T028 [US2] Conectar los filtros y la tabla en la página del catálogo `app/frontend/src/pages/CatalogoServiciosPage.tsx`

---

## Phase 5: Pulido y Aspectos Transversales

**Propósito**: Tareas de configuración final, datos semilla y documentación general.

- [x] T029 [P] Crear script de inicialización con datos de prueba (seeding) en `app/backend/prisma/seed.ts`
- [x] T030 [P] Configurar el archivo de orquestación Docker Compose para servicios de desarrollo en `docker-compose.yml`
- [x] T031 Actualizar la documentación de instalación y guía de uso de endpoints en `README.md`

---

## Dependencias y Orden de Ejecución

### Dependencias entre Fases

- **Setup (Fase 1)**: Sin dependencias - se puede iniciar de inmediato.
- **Foundational (Fase 2)**: Depende de la Fase 1. BLOQUEA la ejecución de las Historias de Usuario.
- **Historias de Usuario (Fases 3 y 4)**: Dependen de la Fase 2. Pueden avanzar en paralelo o en orden de prioridad (P1 -> P2).
- **Pulido (Fase 5)**: Depende de la finalización de las historias de usuario elegidas para la entrega.

### Oportunidades de Trabajo en Paralelo

- **Fase 1**: T003 y T004 pueden ejecutarse en paralelo.
- **Fase 2**: T007, T008 y T010 pueden desarrollarse simultáneamente.
- **Fase 3 (US1)**: T011 (Tests), T012 (Schema), T013 (Model), T017 (API Service) y T018 (Form Modal) se pueden construir en paralelo.
- **Fase 4 (US2)**: T020 (Tests), T021 (Query Schema), T026 (Table) y T027 (Filters) se pueden construir en paralelo.

---

## Estrategia de Implementación

### Alcance MVP Recomendado

1. Completar **Fase 1** (Setup) y **Fase 2** (Foundational).
2. Completar **Fase 3** (User Story 1 - Registro de Servicios).
3. Validar de forma independiente la historia MVP antes de continuar con la Fase 4.
