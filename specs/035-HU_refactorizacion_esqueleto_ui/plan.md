# Implementation Plan: Refactorización de Esqueleto UI — Layout de Aplicación y Tipografía Global

**Branch**: `feat/035-HU_refactorizacion_esqueleto_ui` | **Date**: 2026-10-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/035-HU_refactorizacion_esqueleto_ui/spec.md` y Tech Design `documents/solutions-architect/035-HU_refactorizacion_esqueleto_ui.md` (ADR-001..ADR-010)

## Summary

Crear el shell de la aplicación (barra superior, navegación lateral colapsable, área de contenido, pie de página) como **ruta padre sin segmento de URL** en `app/frontend`, y fijar la tipografía/margen del `body` en una única regla de `styles.css`. Es un refactor de presentación: cero cambios en backend, API, contratos de datos ni en `features/**`.

Enfoque técnico (decidido por el SA, ver [research.md](./research.md)):
- `LayoutComponent` standalone/OnPush en `core/layout/`, montado en `app.routes.ts` con `canActivateChild: [authGuard]`; las rutas actuales pasan a hijas con los mismos `path`, `data`, `providers` y `loadComponent`.
- Navegación: un modelo `NAV_ITEMS` renderizado con `p-menu` acoplado (`aside`, ≥ 1024 px) o dentro de `p-drawer` (< 1024 px), elegido por `ViewportService.isWide` (`matchMedia`).
- Contenedor de contenido `max-w-7xl mx-auto p-6` solo en el shell; comodín `**` dentro del shell con `NotFoundComponent`.
- `AuthService` se amplía de forma aditiva (`userName`, `logout()`).
- `lint:primeng` incorpora compuertas globales (una sola declaración de `font-family`/margen de `body`, sin `::ng-deep`/`!important`/`ed-grid`).

## Technical Context

**Language/Version**: TypeScript ~6.0, Angular 22.2 (Zoneless + Signals)

**Primary Dependencies**: PrimeNG ^22.1.2 (`p-menubar`, `p-menu`, `p-drawer`, `p-message`, `p-button`; tema Aura), Tailwind CSS v4 + `tailwindcss-primeui`, `keycloak-js` ^26.2.4, PrimeIcons. Sin paquetes nuevos.

**Storage**: N/A (estado efímero de cliente; sin `localStorage`/`sessionStorage`, ADR-005)

**Testing**: Jest 30 + `jest-preset-angular` (zoneless), `RouterTestingHarness`; `npm run lint:primeng`, `npm run build`, `npm test`

**Target Platform**: SPA en navegador moderno (anchos de 768 px a 1920 px)

**Project Type**: Aplicación web (frontend Angular; backend .NET sin cambios)

**Performance Goals**: Sin objetivos nuevos; el shell no realiza llamadas de red y no debe romper la carga perezosa de pantallas.

**Constraints**: Skeleton sí / Theme no; sin CSS propio de color/borde/sombra/tipografía; sin `::ng-deep` ni `!important`; sin código de `app/template-primeng`; `features/**` intacto; umbral de ancho amplio 1024 px.

**Scale/Scope**: 1 shell + 1 página de ruta inexistente; 9 URL existentes reubicadas bajo el shell (8 pantallas); 6 capturas de cierre.

Sin `NEEDS CLARIFICATION`: los puntos abiertos B-01..B-06 del UX los resolvió el SA (ver research.md).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Regla de la constitución | Estado | Evidencia |
|---|---|---|
| Idioma estricto: español | ✅ | Todos los artefactos en español |
| Angular 22 Zoneless + Signals, PrimeNG 22.1.x, Tailwind v4 | ✅ | ADR-001/002; sin dependencias nuevas |
| Skeleton (topbar, sidebar colapsable, footer) sin Theme corporativo | ✅ | Solo componentes PrimeNG con tema Aura; sin `.scss` en el shell |
| Tailwind solo para grid/espaciado/flex | ⚠️ Justificado | `max-w-7xl` y `p-6` por mandato RT-02 de la HU; acotadas al contenedor del shell (ADR-002). Ver Complexity Tracking |
| Rutas físicas con prefijo `app/frontend/` | ✅ | Estructura del proyecto abajo |
| `npm run lint:primeng` antes del handoff | ✅ | Extendido por ADR-010 |
| Sin clases PrimeFlex ni PrimeNG ≤ 15, sin `::ng-deep` | ✅ | Compuerta automática en lint |
| Backend/BD/mensajería/seguridad servidor | ✅ N/A | Sin cambios (FR-012) |
| Vertical Slicing / GitOps | ✅ | Una HU, rama `feat/035-HU_...`; los agentes no ejecutan Git |
| `app/template-primeng` solo referencia visual | ✅ | FR-011, RT-07 |

**Resultado de la compuerta**: PASA, con una excepción acotada y justificada (Tailwind de tamaño en el shell).

**Re-evaluación post-diseño (Fase 1)**: PASA. El diseño no introduce backend, persistencia ni dependencias; la única tensión (utilidades de tamaño) permanece confinada a `LayoutComponent`.

## Project Structure

### Documentation (this feature)

```text
specs/035-HU_refactorizacion_esqueleto_ui/
├── plan.md              # Este archivo
├── research.md          # Fase 0
├── data-model.md        # Fase 1
├── quickstart.md        # Fase 1
├── contracts/
│   └── ui-shell-contract.md   # Fase 1
├── checklists/requirements.md
├── evidence/            # 6 capturas (Task-UI-11, se crean en implementación)
└── tasks.md             # Fase 2 (/speckit-tasks, NO lo crea este comando)
```

### Source Code (repository root)

```text
app/frontend/
├── scripts/
│   └── lint-primeng.mjs                  # + reglas globales RT-05/RT-06/RT-07
└── src/
    ├── styles.css                        # + única regla body { margin: 0; font-family: var(--font-sans) }
    └── app/
        ├── app.routes.ts                 # shell como ruta padre; `**` dentro del shell
        ├── app.routes.spec.ts            # nuevo
        └── core/
            ├── auth/
            │   ├── auth.service.ts       # + userName, logout() (aditivo)
            │   └── auth.service.spec.ts  # doble de Keycloak ampliado
            └── layout/
                ├── layout.component.ts|html|spec.ts
                ├── layout.texts.ts
                ├── layout-nav.ts|spec.ts
                ├── viewport.service.ts|spec.ts
                └── not-found/not-found.component.ts|html|spec.ts
```

**Structure Decision**: Aplicación web con frontend en `app/frontend`. El shell vive en `core/layout/` (infraestructura transversal, junto a `core/auth/`), no en `features/`; ninguna pantalla se importa desde el shell. `app/backend/**`, `app/frontend/src/app/features/**` y `app/template-primeng/**` no se tocan.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Utilidades Tailwind de tamaño (`max-w-7xl`, `p-6`, `w-64`, `min-h-screen`) más allá de grid/flex/espaciado | RT-02 de la HU fija 1280 px de ancho máximo y 1.5 rem de padding | Un `.scss` propio viola RT-06 y la directiva de no overrides de CSS |
| Dos caminos de render para la navegación (`aside` + `p-drawer`) | Modo acoplado en ancho amplio y capa a 768 px sin CSS propio | Solo `p-drawer` exige márgenes calculados en CSS; `aside` único reimplementa capa, máscara y trampa de foco (ADR-004) |
