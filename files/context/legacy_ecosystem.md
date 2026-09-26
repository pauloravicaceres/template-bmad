# ECOSISTEMA TÉCNICO Y REGLAS ARQUITECTÓNICAS (CONTEXT SNAPSHOT)

- **Tipo de Ecosistema:** Brownfield Consolidado (Base Fundacional + Extensión Multirruta + Módulo de Experiencia)
- **Fecha de Destilación:** 25-09-2026
- **Auditor & Compilador:** Agente QT Senior BMAD
- **Estado del Snapshot:** `Activo / Vigente`

---

## 1. STACK TECNOLÓGICO BASE E INVARIANTES

- **Runtime & Plataforma:** Node.js 20.x LTS.
- **Framework Principal:** Astro 4.x orientado a Static Site Generation (SSG) multirruta con arquitectura "Zero JavaScript by default" para componentes de presentación (`ProfileCard`, `NavigationMenu`, `ExperienceList`).
- **Capa de Estilos & Diseño:** Tailwind CSS 3.x con estrategia de modo oscuro basada en clases (`darkMode: 'class'`) y contraste certificado WCAG 2.1 AA.
- **Lenguaje & Tipado:** TypeScript 5.x estricto + Zod 3.x para validación estructural de esquemas en tiempo de compilación.
- **Infraestructura & CDN:** Vercel / GitHub Pages con distribución perimetral global (Edge CDN Anycast), compresión Brotli/Gzip y forzado HTTPS.
- **Testing & Quality:** Vitest para pruebas unitarias de contratos y schemas; Playwright para pruebas E2E, navegación bidireccional, renderizado de experiencia, descarga de PDF y accesibilidad.
- **CI/CD:** GitHub Actions para pipeline automatizado con Quality Gates de linting, typecheck, testing, verificación de assets y métrica estricta LCP < 1.0s.

---

## 2. TOPOLOGÍA DE PERSISTENCIA Y MODELO DE DATOS

- **Motor de Base de Datos Principal:** No aplica base de datos SQL/NoSQL en servidor.
- **Fuente de Verdad Centralizada:** Archivo JSON tipado local `src/config/profile.config.json` validado en tiempo de compilación mediante `src/config/profile.schema.ts`.
- **Entidades Core:**
  - `PROFILE_CONFIG`: `{ name: string, avatarUrl: string, avatarAlt: string, fallbackInitials: string, navItems: Array<NAV_ITEM>, documents: DOCUMENTS_CONFIG, experience: Array<EXPERIENCE_ITEM> }`.
  - `NAV_ITEM`: `{ id: string, label: string, href: string, isDownload?: boolean, downloadFilename?: string }`.
  - `DOCUMENTS_CONFIG`: `{ studiesPdfUrl: string, studiesPdfName: string }`.
  - `EXPERIENCE_ITEM`: `{ id: string, company: string, role: string, period: string, responsibilities: Array<string> }`.
  - `THEME_PREFERENCE` (Cliente): `{ storageKey: 'theme_preference', selectedTheme: 'light' | 'dark', systemFallback: 'light' | 'dark' }`.
- **Persistencia en Cliente:** `localStorage` (Browser Runtime) bajo la clave `theme_preference` con fallback resiliente a `window.matchMedia('(prefers-color-scheme: dark)')` y degradación a memoria en modo incógnito.

---

## 3. PATRONES DE COMUNICACIÓN Y ARQUITECTURA DE ESTADO

- **Zero External APIs:** Sin dependencias de red dinámicas en tiempo de ejecución. Sitio 100% pre-renderizado.
- **Enrutamiento Estático Multirruta:** Enrutamiento basado en archivos nativo de Astro (`/` y `/experiencia`) compartiendo `Layout.astro` global.
- **Estrategia Anti-FOUT Multirruta:** Script bloqueante síncrono inyectado en el `<head>` de `Layout.astro` que evalúa `localStorage` y `prefers-color-scheme` antes del renderizado del DOM, preservando el tema visual durante transiciones de ruta.
- **Componente de Experiencia Responsivo:** Renderizado mediante CSS Grid / Flexbox con stacking vertical en móviles sin desbordamiento horizontal y soporte defensivo de Empty State.
- **Entrega Estática de Documentos:** Assets PDF servidos directamente desde `public/docs/` con validación de existencia en pipeline CI/CD.
- **Resiliencia de Assets:** Manejador `onerror` en el avatar fotográfico con fallback a silueta/placeholder SVG con iniciales (`fallbackInitials`).

---

## 4. MATRIZ DE ADRs GLOBALES CONSOLIDADOS

| ID | Título de la Decisión | Área | Estado | Resumen de Decisión / Invariante |
|:---:|---|:---:|:---:|---|
| **ADR-001** | Selección del Framework SSG (Astro + Tailwind CSS) | Frontend | Aceptado (heredado) | Adopción de Astro + Tailwind para SSG puro y cero sobrepeso de JS. |
| **ADR-002** | Gestión de Tema con Script Inline Anti-FOUT | Estado | Aceptado (heredado) | Inyección síncrona en `<head>` para control de tema y persistencia local. |
| **ADR-003** | Fuente de Datos Estática Tipada (`profile.config.json`) | Persistencia | Aceptado (heredado) | Centralización de datos en JSON con validación en build-time. |
| **ADR-004** | Infraestructura y Despliegue en Edge CDN con CI/CD | Infraestructura | Aceptado (heredado) | Distribución global en Vercel / GitHub Pages vía GitHub Actions. |
| **ADR-005** | Validación de Datos con Zod y TypeScript | Integridad | Aceptado (heredado) | Esquema tipado obligatorio `ProfileConfigSchema` en `profile.schema.ts`. |
| **ADR-006** | Persistencia Cliente de Preferencia de Tema (`localStorage`) | Datos | Aceptado (heredado) | Almacenamiento local de clave `theme_preference` con fallback resiliente. |
| **ADR-007** | Enrutamiento Multirruta y `NavigationMenu.astro` en Layout | Rutas | Aceptado (heredado) | Menú estático embebido en Layout compartido con ruta nativa a `/experiencia`. |
| **ADR-008** | Extensión del Esquema Tipado (`navItems`, `documents`) | Esquemas | Aceptado (heredado) | Metadata de navegación y documentos centralizada en `profile.config.json`. |
| **ADR-009** | Distribución de PDF en `/public/docs/` con Verificación CI | DevOps | Aceptado (heredado) | Entrega en CDN con Quality Gate en GitHub Actions para prevenir errores 404. |
| **ADR-010** | Componente `ExperienceList.astro` con Grid/Flexbox Responsivo | UI/Frontend | Aceptado (heredado) | Lista estructurada responsiva Zero JS sin desbordamiento horizontal. |
| **ADR-011** | Extensión de Esquema para `experience` con Empty State | Esquemas | Aceptado (heredado) | Integración de colección de puestos con validación Zod y fallback visual. |
| **ADR-012** | Navegación Bidireccional Multirruta y Quality Gates en CI | Navegación/CI | Aceptado (heredado) | Enlace de retorno nativo a `/` con suite E2E y chequeo de LCP < 1.0s. |
