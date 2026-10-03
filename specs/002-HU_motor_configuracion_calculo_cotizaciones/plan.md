# Implementation Plan: 001-HU_configurador_y_calculo_cotizaciones

**Branch**: `feat/001-HU_configurador_y_calculo_cotizaciones` | **Date**: 2026-10-02 | **Spec**: [001-HU_configurador_y_calculo_cotizaciones.md](file:///D:/Paulo/Cursos/DMC/template-bmad/files/business-analyst/001-HU_configurador_y_calculo_cotizaciones.md)

**Input**: Feature specification from `/files/business-analyst/001-HU_configurador_y_calculo_cotizaciones.md`, `files/solutions-architect/tech_guidelines.md` y `files/designer-ux/ux_001_configurador_y_calculo_cotizaciones.md`.

## Summary

Desarrollar el motor de cálculo interactivo de cotizaciones y la interfaz web reactiva de dos paneles (Configurador y Resumen Transaccional) para desarrolladores freelance. El motor de cálculo operará en el cliente (TypeScript funcional inmutable) garantizando recálculos instantáneos (<1ms) de subtotales y total general ante cambios de selección o cantidad. Incluirá validaciones defensivas síncronas que bloqueen cantidades inválidas (≤ 0) y carritos vacíos deshabilitando la acción principal ("Generar PDF"), complementado con backend Node.js/Express y PostgreSQL en contenedores Docker rootless.

## Technical Context

**Language/Version**: Node.js 20 LTS, TypeScript 5.x, React 18
**Primary Dependencies**: React 18, Express, TailwindCSS, Lucide Icons, Jest, React Testing Library
**Storage**: PostgreSQL 16 (persistencia de catálogo de servicios y cotizaciones emitidas)
**Testing**: Jest + React Testing Library (100% cobertura en motor de cálculo funcional y componentes reactivos)
**Target Platform**: Web Browsers (SPA React) / Docker Container Infrastructure (Linux rootless)
**Project Type**: Web application (`app/frontend` + `app/backend`)
**Performance Goals**: Recálculo reactivo en UI en < 1ms por interacción
**Constraints**: Respetar separación estricta `app/frontend/` y `app/backend/` según la Constitución Técnica de BMAD. Toda documentación en Español.
**Scale/Scope**: 1 Módulo Core (Motor de Cómputo y UI de Configurador de Cotizaciones)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Idioma Estricto**: Todo el plan, contratos y artefactos redactados en Español.
- [x] **Identificador Universal**: Mantenido inmutable `001-HU_configurador_y_calculo_cotizaciones`.
- [x] **Estructura de Carpetas Subordinada**: Código fuente ubicado en `app/frontend/` y `app/backend/`.
- [x] **Feature Branch Prolongada**: Vinculado a `feat/001-HU_configurador_y_calculo_cotizaciones`.
- [x] **Modo Máquina (Anti-conversacional)**: Ejecución declarativa y directa.

## Project Structure

### Documentation (this feature)

```text
specs/002-HU_motor_configuracion_calculo_cotizaciones/
├── plan.md              # Este archivo (Plan de Implementación)
├── research.md          # Investigación técnica de alternativas de cálculo
├── data-model.md        # Modelos de datos TypeScript y Esquema Relacional PostgreSQL
├── quickstart.md        # Guía rápida para levantar y probar el módulo
└── contracts/           # Interfaces TypeScript e I/O del motor de cálculo
```

### Source Code (repository root)

```text
app/
├── backend/
│   ├── src/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── routes/
│   │   └── models/
│   ├── tests/
│   │   ├── unit/
│   │   └── integration/
│   ├── package.json
│   └── Dockerfile
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ConfiguratorPanel.tsx
    │   │   ├── QuoteSummaryCard.tsx
    │   │   └── ServiceItemCard.tsx
    │   ├── engine/
    │   │   ├── calculationEngine.ts
    │   │   └── validators.ts
    │   ├── types/
    │   │   └── quote.ts
    │   └── App.tsx
    ├── tests/
    │   ├── engine/
    │   └── components/
    ├── package.json
    └── Dockerfile
```

**Structure Decision**: Se adopta la estructura decoupled cliente-servidor dentro de `app/frontend/` y `app/backend/` en pleno cumplimiento con la regla de la Constitución Técnica BMAD (Sección ESTRUCTURA DE CARPETAS DEL REPOSITORIO).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Cómputo Duplicado (Frontend/Backend) | Garantizar latencia instantánea (<1ms) en UI y prevenir manipulaciones del cliente antes de guardar en base de datos. | Realizar fetch API al backend en cada keystroke introducía latencia de red y degradaba UX. |

---

## Phase 0: Research & Technical Validation

Se investigó el patrón de diseño para el motor de cálculo reactivo:
- **Motor Puramente Funcional inmutable (`app/frontend/src/engine/calculationEngine.ts`)**: Recibe `QuoteItem[]` y parámetros, y retorna `CalculationResult` estructurado (`subtotal`, `total`, `isValid`, `errors`).
- **Resiliencia & Fail-safe**: En caso de error de red con la API del catálogo de backend, el cliente usará una caché local temporal.

## Phase 1: Data Model & Contracts

### Data Model (`app/frontend/src/types/quote.ts`)

```typescript
export interface ServiceItem {
  id: string;
  name: string;
  basePrice: number;
  description: string;
}

export interface QuoteItem {
  serviceId: string;
  quantity: number;
  customPrice?: number;
}

export interface CalculationResult {
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  isValid: boolean;
  errors: Record<string, string>;
}
```

### Database Schema (`app/backend/migrations/001_init.sql`)
- `services_catalog` (id, name, base_price, description)
- `quotes` (id, created_at, subtotal, total, status)
- `quote_items` (id, quote_id, service_id, quantity, unit_price, subtotal)

## Phase 2: Quickstart & Developer Setup

1. **Instalación de dependencias:**
   - Frontend: `cd app/frontend && npm install`
   - Backend: `cd app/backend && npm install`
2. **Ejecución de Pruebas Unitarias del Motor:**
   - `cd app/frontend && npm test -- calculationEngine.test.ts`
3. **Servidor de Desarrollo:**
   - `npm run dev` en ambas carpetas o mediante `docker-compose up --build`.
