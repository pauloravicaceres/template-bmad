# Ecosistema Portafolio SSG Constitution

## Core Principles

### I. Zero External APIs y Pre-renderizado Total
Sin dependencias de red dinámicas en tiempo de ejecución. El sitio debe ser 100% pre-renderizado (Static Site Generation - SSG) garantizando máxima velocidad y seguridad.

### II. Zero JavaScript by Default
Uso estricto de componentes de presentación (`ProfileCard`, `NavigationMenu`, `ExperienceList`) sin enviar JavaScript innecesario al cliente, aprovechando la arquitectura nativa de Astro.

### III. Resiliencia y Degradación Elegante
Todo componente debe tener mecanismos de fallback. El avatar fotográfico usa manejador `onerror` con fallback a silueta/iniciales SVG. Las preferencias de tema tienen degradación resiliente a memoria en modo incógnito o mediante `window.matchMedia`.

### IV. Estrategia Anti-FOUT Estricta
Prevención de parpadeos de estilo (Flash of Unstyled Text/Theme). Se requiere un script bloqueante síncrono inyectado en el `<head>` de `Layout.astro` que evalúe `localStorage` y preferencias del sistema antes del renderizado del DOM.

## Stack & Technical Constraints

- **Runtime & Plataforma:** Node.js 20.x LTS.
- **Framework Principal:** Astro 4.x multirruta (`/` y `/experiencia`) compartiendo `Layout.astro` global.
- **Estilos:** Tailwind CSS 3.x con modo oscuro por clases (`darkMode: 'class'`) y contraste WCAG 2.1 AA.
- **Tipado & Validación:** TypeScript 5.x estricto + Zod 3.x para validación en tiempo de compilación.
- **Infraestructura:** Vercel / GitHub Pages con Edge CDN Anycast, compresión Brotli/Gzip y forzado HTTPS.
- **Persistencia de Datos:** Sin base de datos. Uso de archivo JSON tipado local (`src/config/profile.config.json`) validado mediante `src/config/profile.schema.ts`.
- **Persistencia Cliente:** `localStorage` bajo la clave `theme_preference`.

## Quality & CI/CD Gates

- **Testing de Contratos:** Vitest para pruebas unitarias de contratos y schemas.
- **Testing E2E:** Playwright para navegación bidireccional, renderizado de experiencia, descarga de PDF y accesibilidad.
- **Pipeline:** GitHub Actions automatizado con Quality Gates de linting, typecheck, testing, verificación de assets (PDFs en `/public/docs/`) y métrica estricta LCP < 1.0s.

## Architecture Decision Records (ADRs)

| ID | Área | Resumen de Decisión / Invariante |
|:---:|:---:|---|
| **ADR-001** | Frontend | Adopción de Astro + Tailwind para SSG puro y cero sobrepeso de JS. |
| **ADR-002** | Estado | Inyección síncrona en `<head>` para control de tema y persistencia local. |
| **ADR-003** | Persistencia | Centralización de datos en JSON con validación en build-time (`profile.config.json`). |
| **ADR-004** | Infraestructura | Distribución global en Vercel / GitHub Pages vía GitHub Actions. |
| **ADR-005** | Integridad | Esquema tipado obligatorio `ProfileConfigSchema` en `profile.schema.ts`. |
| **ADR-006** | Datos | Almacenamiento local de clave `theme_preference` con fallback resiliente. |
| **ADR-007** | Rutas | Menú estático embebido en Layout compartido con ruta nativa a `/experiencia`. |
| **ADR-008** | Esquemas | Metadata de navegación y documentos centralizada en `profile.config.json`. |
| **ADR-009** | DevOps | Entrega de PDFs en CDN con Quality Gate en GitHub Actions para prevenir 404s. |
| **ADR-010** | UI/Frontend | Lista estructurada `ExperienceList.astro` responsiva Zero JS. |
| **ADR-011** | Esquemas | Integración de colección de puestos con validación Zod y Empty State visual. |
| **ADR-012** | Navegación/CI | Enlace de retorno nativo a `/` con suite E2E y chequeo de LCP < 1.0s. |

## Governance

Esta Constitución actúa como la "Lex Superior" del ecosistema BMAD. Toda tarea generada por `/speckit.tasks` y todo código emitido por los agentes de desarrollo (Fase A y Fase D) debe ser analizado por `/speckit.analyze` contra estas reglas. Ningún agente tiene autorización para evadir los esquemas Zod, inyectar APIs externas o romper la arquitectura SSG.

**Version**: 1.0 | **Ratified**: 25-09-2026 | **Framework**: BMAD + SDD