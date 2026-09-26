# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** 25-09-2026
- **Solutions Architect:** Agente SA Senior BMAD

---

## 1. Project Overview
- **Qué es el sistema:** Tarjeta de Identidad Digital Ultra-Minimalista con Menú de Navegación Multirruta, Descarga de Documentos y Módulo de Experiencia Profesional, diseñada para proyectar la marca personal del titular y exhibir su trayectoria laboral estructurada en una vista dedicada sin sobrecarga visual.
- **Qué problema resuelve:** Centraliza la presencia digital del profesional permitiendo a visitantes y reclutadores auditar su historial de puestos, empresas, períodos y responsabilidades laborales de forma legible, responsiva y ultrarrápida, complementando el perfil inicial y la descarga de credenciales.
- **Naturaleza del Proyecto:** Brownfield (Subordinado a las directrices de `files/context/legacy_ecosystem.md`, la tarjeta de identidad base y el menú de navegación multirruta).
- **Arquitectura general:** Arquitectura Jamstack / Static Site Generation (SSG) multirruta con **Astro 4.x**, orientada a "Zero JavaScript by default", con distribución perimetral en Edge CDN (Vercel / GitHub Pages), renderizado sin servidor (Serverless Static Delivery), enrutamiento estático basado en archivos y persistencia de tema en cliente.

## 2. Repository Structure
```text
├── .github/
│   └── workflows/
│       └── ci-cd.yml             # Pipeline de validación (astro check, lint, vitest, playwright, performance) y deploy
├── public/
│   ├── docs/
│   │   └── estudios.pdf          # Asset documental estático representativo para descarga
│   ├── favicon.ico
│   └── robots.txt
├── src/
│   ├── assets/
│   │   ├── images/               # Fotografía de perfil optimizada (WebP / AVIF)
│   │   └── icons/                # Iconografía SVG (toggle de tema, descarga, retorno, fallback)
│   ├── components/
│   │   ├── ExperienceList.astro  # Componente SSG responsivo de trayectoria laboral (Grid/Cards)
│   │   ├── NavigationMenu.astro  # Componente SSG reutilizable para menú de navegación
│   │   ├── ProfileCard.astro     # Componente núcleo de presentación de identidad
│   │   └── ThemeToggle.astro     # Componente interactivo ultra-ligero de conmutación Light/Dark
│   ├── config/
│   │   ├── profile.config.json   # Fuente de verdad única: identidad, navegación, docs y experiencia
│   │   └── profile.schema.ts     # Contrato tipado y validación de esquema con Zod
│   ├── layouts/
│   │   └── Layout.astro          # Layout maestro global compartido con script anti-FOUT en <head>
│   ├── pages/
│   │   ├── index.astro           # Vista principal: Tarjeta de Identidad con menú integrado
│   │   └── experiencia.astro     # Vista de Experiencia: Lista estructurada con enlace de retorno
│   ├── scripts/
│   │   └── theme-manager.ts      # Lógica encapsulada de detección y persistencia de tema
│   └── styles/
│       ├── globals.css           # Tokens de diseño y variables CSS de temas (Light / Dark)
│       └── tailwind.css          # Directivas de utilidad atómica de Tailwind CSS
├── tests/
│   ├── unit/                     # Pruebas unitarias de esquemas Zod, parseo de JSON y lógica de tema (Vitest)
│   └── e2e/                      # Pruebas de renderizado, navegación bidireccional, PDF y accesibilidad (Playwright)
├── astro.config.mjs              # Configuración base de Astro y Tailwind
├── package.json
├── tailwind.config.cjs
└── tsconfig.json
```
- **Importante:**
  - *Regla de Coexistencia y No-Regresión:* La vista `experiencia.astro` consume obligatoriamente `Layout.astro` para heredar el script síncrono anti-FOUT, el `NavigationMenu.astro`, el `ThemeToggle.astro` y las variables de estilo globales.
  - *Desacoplamiento Estático:* Todos los datos de la trayectoria profesional residen exclusivamente en `src/config/profile.config.json` tipados mediante `src/config/profile.schema.ts`.
- **Qué NO debe tocar:** Queda estrictamente restringido modificar la lógica del script inline anti-FOUT en `<head>`, alterar las claves de almacenamiento de `localStorage` (`theme_preference`) o incorporar frameworks pesados en cliente que fuercen hidratación de componentes estáticos.

## 3. Tech Stack
- **Runtime & SSG Framework:** Node.js 20.x LTS / Astro 4.x (Generación estática multirruta sin sobrecarga de JS en cliente).
- **Styling Layer:** Tailwind CSS 3.x con tokens de diseño atómicos, soporte para `darkMode: 'class'` y prefijos semánticos `dark:` certificados para contraste WCAG AA.
- **Language & Integrity:** TypeScript 5.x estricto + Zod 3.x para validación estructural de esquemas en tiempo de compilación.
- **Database / Data Source:** Archivo de configuración estático tipado `src/config/profile.config.json` (sin base de datos transaccional en servidor).
- **Infrastructure & Hosting:** Vercel / GitHub Pages (Edge CDN Anycast multirregión con compresión Brotli/Gzip y TLS 1.3).
- **Testing:** Vitest para pruebas unitarias de contratos y validación de schemas; Playwright para pruebas E2E de renderizado, navegación bidireccional y regresión visual.
- **CI/CD:** GitHub Actions para pipeline automatizado (`astro check`, `eslint`, `vitest`, `playwright`, auditoría de assets en `public/` y métrica LCP < 1.0s).

## 4. Development Workflow
- **Cómo levantar el proyecto:**
  ```bash
  npm install
  npm run dev
  ```
- **Cómo ejecutar tests / lint / build:**
  ```bash
  npm run lint       # Validación estática de código con ESLint y Prettier
  npm run typecheck  # Verificación estricta de tipos y contratos con astro check
  npm run test       # Ejecución de suite de pruebas unitarias con Vitest
  npm run test:e2e   # Ejecución de pruebas de integración y navegación con Playwright
  npm run build      # Generación de artefacto SSG multirruta optimizado en dist/
  npm run preview    # Previsualización local del artefacto compilado
  ```
- **Cómo ejecutar migraciones:** No aplica migración SQL/NoSQL. Las extensiones de datos se rigen por la evolución tipada y versionada de `profile.schema.ts` y `profile.config.json`.

## 5. Architecture Rules & Decision Framework
- **Principios que deben respetarse:**
  - *Zero JavaScript by Default:* Las páginas `/` y `/experiencia`, así como los componentes `ProfileCard.astro`, `NavigationMenu.astro` y `ExperienceList.astro`, se renderizan como HTML/CSS estático puro.
  - *Preservación de Core Web Vitals:* Mantener LCP < 1.0s, CLS = 0 y TTFB < 200ms en todas las rutas estáticas servidas por la CDN.
  - *Garantía Anti-FOUT / Anti-FOUC Multirruta:* La navegación bidireccional entre páginas no debe provocar parpadeos visuales ni reinicios del tema seleccionado.
  - *Accesibilidad Universal (a11y):* Marcado semántico (`<main>`, `<article>`, `<section>`, `<ul>`), contraste tipográfico certificado WCAG 2.1 AA en temas claro y oscuro, y navegación por teclado fluida.
- **Dependencias permitidas:** Paquetes estrictamente ligeros (`clsx`, `tailwind-merge`, `zod`). Prohibido incorporar librerías SPA dinámicas de navegación en cliente.
- **Patrones prohibidos:** Queda estrictamente prohibido el uso de variables "hardcodeadas" en componentes, tablas HTML rígidas con desbordamiento horizontal en móviles y mutaciones no encapsuladas del DOM.

### 5.1. State Management Architecture
- **Frontera de Estado:** El estado reside al 100% en el cliente (Browser Runtime). Se mantiene un único estado persistente: la preferencia de tema visual (`theme: 'light' | 'dark'`).
- **Estrategia de Sincronización:**
  - *Prevención Anti-FOUT:* Inyección síncrona y bloqueante del script en el `<head>` de `Layout.astro` que lee `localStorage.getItem('theme_preference')` y la media query `prefers-color-scheme: dark`, aplicando `.dark` a `document.documentElement` antes de renderizar cualquier vista.
  - *Consistencia Multirruta:* Al navegar entre `/` e `/experiencia`, el navegador ejecuta el script inline en el `<head>` del layout base, manteniendo el tema sin desincronización ni latencia.
- **Consistencia:** Sincronía inmediata en el cliente sin llamadas de red ni servidores de estado.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:**
  - *Colección de Experiencia Vacía (Empty State):* Si el array `experience` en `profile.config.json` no contiene elementos (`experience.length === 0`), `ExperienceList.astro` renderiza un bloque de fallback amigable con iconografía SVG informando que no hay registros disponibles, evitando errores de renderizado.
  - *Asset Documental PDF Faltante:* Verificación en build-time en GitHub Actions para asegurar la presencia física de `public/docs/estudios.pdf`.
  - *Fallo en Fotografía de Perfil:* Manejador `onerror` en `<img>` con fallback automático a iniciales vectoriales SVG (`fallbackInitials`).
  - *Excepciones de Storage en Navegador:* Operaciones de `localStorage` protegidas en bloques `try/catch` con degradación a memoria volátil ante bloqueos de cookies o modo incógnito restrictivo.
  - *Ruta No Encontrada (404):* Página estática `404.astro` con enlace directo de retorno al perfil principal.
- **Patrones de Tolerancia a Fallos:** Empty state defensivo, verificación estática en build time, fallback visual inmediato y degradación suave.
- **Proporcionalidad:** Arquitectura SSG proporcional al alcance del MVP, sin sobre-ingeniería de bases de datos remotas ni endpoints dinámicos.

---

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

#### ADR-001: Selección del Framework SSG (Astro + Tailwind CSS)
- **Estado:** Aceptado (heredado)
- **Contexto:** Decisión consolidada en la arquitectura base para maximizar rendimiento y eliminar sobrecarga de JavaScript en cliente.
- **Decisión:** Utilizar **Astro 4.x** + **Tailwind CSS 3.x** para generación estática pura.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** 0 KB de JavaScript en componentes de presentación, HTML estático ultra-rápido y LCP < 1.0s.
  - ⚠️ **Trade-off / Costo Real:** Compilación obligatoria en build time y sintaxis `.astro`.

#### ADR-002: Gestión de Tema con Script Inline Anti-FOUT y Persistencia Local
- **Estado:** Aceptado (heredado)
- **Contexto:** Requerimiento de soporte de tema claro/oscuro con detección de sistema y persistencia sin parpadeo visual.
- **Decisión:** Inyección de script síncrono bloqueante en el `<head>` de `Layout.astro` consumiendo `localStorage` (`theme_preference`) y `matchMedia`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Cero parpadeo visual (anti-FOUT) y persistencia sin latencia de red.
  - ⚠️ **Trade-off / Costo Real:** Script inline bloqueante mínimo en el `<head>` del layout maestro.

#### ADR-003: Fuente de Datos Estática Tipada (`profile.config.json`)
- **Estado:** Aceptado (heredado)
- **Contexto:** Centralización de la información del perfil sin aprovisionamiento de bases de datos remotas.
- **Decisión:** Configuración estructurada en `src/config/profile.config.json` validada por `profile.schema.ts`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Costo $0, cero latencia de red y seguridad absoluta contra inyecciones.
  - ⚠️ **Trade-off / Costo Real:** Modificaciones de contenido requieren commit y rebuild.

#### ADR-004: Infraestructura y Despliegue en Edge CDN con CI/CD
- **Estado:** Aceptado (heredado)
- **Contexto:** Disponibilidad global con TTFB < 200ms y despliegues automatizados.
- **Decisión:** Alojamiento en Vercel / GitHub Pages gestionado mediante GitHub Actions.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** CDN Anycast global, SSL automático y costo $0.
  - ⚠️ **Trade-off / Costo Real:** Límites de uso en planes gratuitos estándar.

#### ADR-005: Validación de Contratos con Zod y TypeScript
- **Estado:** Aceptado (heredado)
- **Contexto:** Garantizar integridad estructural de los datos antes de la compilación estática.
- **Decisión:** Validación con Zod Schema en `src/config/profile.schema.ts`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Errores de tipado detectados tempranamente en build time.
  - ⚠️ **Trade-off / Costo Real:** Dependencia de desarrollo ligera de Zod.

#### ADR-006: Persistencia Cliente de Preferencia de Tema (`localStorage`)
- **Estado:** Aceptado (heredado)
- **Contexto:** Almacenar de manera persistente la elección del usuario entre sesiones.
- **Decisión:** Uso de `localStorage` bajo la clave `theme_preference` con manejo defensivo de excepciones.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Experiencia de usuario consistente sin autenticación ni backend.
  - ⚠️ **Trade-off / Costo Real:** Volatilidad si el usuario limpia el almacenamiento del navegador.

#### ADR-007: Enrutamiento Estático Multirruta y Componente `NavigationMenu.astro` en Layout Compartido
- **Estado:** Aceptado (heredado)
- **Contexto:** Navegación entre páginas manteniendo coherencia visual y cero parpadeo FOUT.
- **Decisión:** Menú SSG estático (`NavigationMenu.astro`) embebido dentro de `Layout.astro` con ruta nativa a `/experiencia`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Cero sobrepeso de JS y prevención total de FOUT.
  - ⚠️ **Trade-off / Costo Real:** Navegación estándar del navegador sin animaciones SPA complejas.

#### ADR-008: Extensión del Esquema Tipado para Enlaces de Navegación y Documentos Descargables
- **Estado:** Aceptado (heredado)
- **Contexto:** Estructurar enlaces de menú y ruta de PDF desacoplados de la capa de presentación.
- **Decisión:** Extender `profile.schema.ts` y `profile.config.json` con `navItems` y `documents`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Centralización de metadata en un único archivo de configuración tipado.
  - ⚠️ **Trade-off / Costo Real:** Actualización de schemas y tests unitarios.

#### ADR-009: Distribución de Documentos Estáticos en `/public/docs/` y Verificación en Pipeline CI/CD
- **Estado:** Aceptado (heredado)
- **Contexto:** Servir el archivo PDF de manera instantánea y con garantía de existencia.
- **Decisión:** Alojar el documento en `public/docs/estudios.pdf` con validación en GitHub Actions.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Descarga instantánea (< 500ms) y prevención de errores 404 en CI.
  - ⚠️ **Trade-off / Costo Real:** El archivo PDF forma parte del repositorio.

#### ADR-010: Componente de Visualización de Experiencia (`ExperienceList.astro`) basado en Tarjetas Grid/Flexbox Responsivas
- **Estado:** Aceptado
- **Contexto:** El despliegue de los antecedentes laborales (empresa, rol, período, responsabilidades) debe ser altamente legible, sin desbordamientos horizontales en dispositivos móviles y con renderizado estático puro.
- **Decisión:** Implementar el componente `ExperienceList.astro` utilizando una estructura semántica basada en listas (`<ul>` / `<li>`) y tarjetas con Tailwind CSS (CSS Grid / Flexbox con stacking vertical automático en viewports reducidos), prescindiendo de tablas HTML tradicionales rígidas.
- **Alternativas Consideradas (Obligatorio en decisiones nuevas):**
  - **Alternativa A: Tabla HTML tradicional (`<table>`, `<tr>`, `<td>`):** Genera desbordamiento horizontal en pantallas móviles (overflow-x) o requiere barras de scroll secundarias que degradan la experiencia de usuario y el minimalismo del diseño.
  - **Alternativa B: Componente interactivo con acordeones desplegables en cliente (JavaScript):** Obligaría a introducir librerías de componentes reactivos en cliente, violando el principio de arquitectura "Zero JavaScript by default".
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Adaptabilidad fluida en cualquier resolución, marcado semántico limpio, lectura visual ágil y cero sobrepeso de JavaScript.
  - ⚠️ **Trade-off / Costo Real:** Mayor cantidad de clases de utilidad en Tailwind para gestionar bordes y espaciados responsivos.

#### ADR-011: Extensión del Esquema Tipado para la Colección de Experiencia Laboral (`experience`) con Soporte de Empty State
- **Estado:** Aceptado
- **Contexto:** Se requiere estructurar los registros de experiencia laboral en el modelo centralizado de persistencia, manteniendo tipado estricto en tiempo de compilación y tolerancia a fallos ante ausencia de datos.
- **Decisión:** Extender `src/config/profile.schema.ts` y `src/config/profile.config.json` con la colección `experience: Array<ExperienceItem>` (validada con Zod) conteniendo `id`, `company`, `role`, `period` y `responsibilities`, pre-ordenada en cronología inversa y con soporte de fallback (Empty State) en el componente Astro.
- **Alternativas Consideradas (Obligatorio en decisiones nuevas):**
  - **Alternativa A: Archivo JSON independiente (`experience.config.json`):** Fragmenta la fuente de verdad y obliga a gestionar múltiples lecturas de archivos de configuración en build time.
  - **Alternativa B: Carga dinámica vía fetch en cliente hacia un endpoint mock:** Introduce latencia de red, riesgo de fallos en ejecución y rompe la arquitectura SSG estática.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Fuente de verdad única unificada, validación exhaustiva en tiempo de compilación y resiliencia visual ante colecciones vacías.
  - ⚠️ **Trade-off / Costo Real:** El archivo `profile.config.json` incrementa su tamaño de bytes en el repositorio.

#### ADR-012: Navegación de Retorno Bidireccional Multirruta y Quality Gates en CI/CD
- **Estado:** Aceptado
- **Contexto:** La vista `/experiencia` requiere un mecanismo de retorno accesible a la tarjeta principal (`/`) preservando el tema visual, respaldado por pruebas automatizadas de integración y rendimiento en CI.
- **Decisión:** Integrar un botón/enlace de retorno explícito en la cabecera de la vista de experiencia utilizando enrutamiento nativo de Astro, respaldado por una suite en GitHub Actions que ejecuta Vitest (validación de schema Zod), Playwright (navegación bidireccional y DOM) y chequeo de LCP < 1.0s.
- **Alternativas Consideradas (Obligatorio en decisiones nuevas):**
  - **Alternativa A: Depender únicamente del botón "Atrás" del navegador (`history.back()`):** Es poco intuitivo en interfaces web de escritorio y no ofrece trazabilidad clara dentro del diseño visual.
  - **Alternativa B: Omitir pruebas E2E de navegación en el pipeline de CI:** Aumenta el riesgo de regresiones visuales o enlaces rotos en despliegues futuros a producción.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Navegación bidireccional accesible, verificación exhaustiva en cada pull request y garantía de performance perimetral.
  - ⚠️ **Trade-off / Costo Real:** Tiempo de ejecución ligeramente mayor en el pipeline de GitHub Actions (~45s adicionales).

---

## 6. Coding Conventions
- **Naming Conventions:**
  - Componentes Astro: `PascalCase.astro` (ej. `ExperienceList.astro`, `NavigationMenu.astro`, `ProfileCard.astro`).
  - Páginas de Enrutamiento: `kebab-case.astro` (ej. `index.astro`, `experiencia.astro`, `404.astro`).
  - Schemas y Contratos: `kebab-case.ts` (ej. `profile.schema.ts`).
- **Organización de Código:**
  - Extracción y ordenamiento de datos en el frontmatter `---` de `experiencia.astro` y paso a `ExperienceList.astro` vía props tipadas.
  - Props de componentes definidas estrictamente mediante `interface Props`.
- **Error Handling & Logging:**
  - Manejo defensivo en renderizado: comprobación de longitud de array (`experience.length > 0`) antes de iterar.
  - Cero llamadas a `console.log` en compilaciones de producción.

## 7. Testing Strategy
- **Pruebas Unitarias (Vitest):**
  - Validación del esquema Zod `ProfileConfigSchema` con la colección `experience`.
  - Validación del parseo correcto de `profile.config.json` y verificación de tipos de cada campo (`id`, `company`, `role`, `period`, `responsibilities`).
- **Pruebas E2E & Regresión Visual (Playwright):**
  - Renderizado completo de `/experiencia` verificando presencia de tarjetas de trabajo.
  - Navegación bidireccional (`/` -> `/experiencia` -> `/`) comprobando persistencia de tema (Light/Dark) sin parpadeos visuales (cero FOUT).
  - Validación de renderizado del estado vacío (Empty State) ante ausencia de registros.
  - Comprobación de que la métrica LCP se mantiene inferior a 1.0s.
- **Cobertura Mínima Esperada:** 100% en contratos de esquema y servicios críticos.

## 8. Security
- **Manejo de Secretos:** Arquitectura 100% estática sin credenciales ni tokens en repositorio.
- **Cabeceras de Seguridad (Vercel / GitHub Pages):**
  - `Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none';`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- **Sanitización de Datos:** Validación estricta con Zod en build-time para prevenir cadenas maliciosas en campos de texto.

## 9. Database & Data Model
- **Schema Extendido (`profile.schema.ts`):**
  ```typescript
  import { z } from 'zod';

  export const ExperienceItemSchema = z.object({
    id: z.string().min(1),
    company: z.string().min(1),
    role: z.string().min(1),
    period: z.string().min(1),
    responsibilities: z.array(z.string().min(1)).min(1)
  });

  export const NavItemSchema = z.object({
    id: z.string(),
    label: z.string().min(1),
    href: z.string().min(1),
    isDownload: z.boolean().optional().default(false),
    downloadFilename: z.string().optional()
  });

  export const DocumentsSchema = z.object({
    studiesPdfUrl: z.string().min(1),
    studiesPdfName: z.string().min(1)
  });

  export const ProfileConfigSchema = z.object({
    name: z.string().min(1),
    avatarUrl: z.string().min(1),
    avatarAlt: z.string().min(1),
    fallbackInitials: z.string().min(1).max(3),
    navItems: z.array(NavItemSchema),
    documents: DocumentsSchema,
    experience: z.array(ExperienceItemSchema).default([])
  });

  export type ExperienceItem = z.infer<typeof ExperienceItemSchema>;
  export type NavItem = z.infer<typeof NavItemSchema>;
  export type DocumentsConfig = z.infer<typeof DocumentsSchema>;
  export type ProfileConfig = z.infer<typeof ProfileConfigSchema>;
  ```
- **Reglas de Modificación:** Todo nuevo campo debe definirse como opcional (`?`) o con valor por defecto (`default()`) para asegurar retrocompatibilidad.

## 10. Git & PR Rules
- **Branches:** `main` (producción), `feature/modulo-experiencia`, `fix/nombre-bug`.
- **Commits:** Conventional Commits obligatorio (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- **PR Quality Gate:** Paso exitoso de `astro check`, `eslint`, `vitest` y `playwright` antes de aprobar el merge.

## 11. Agent Instructions (Dev Guidelines)
- **Antes de programar:**
  - Leer este documento `tech_guidelines.md`, las historias de usuario aprobadas (`hu_*.md`), wireframes de UX (`ux_*.md`) y el snapshot `legacy_ecosystem.md`.
  - Construir `ExperienceList.astro` con CSS Grid/Flexbox y utilidades de Tailwind semánticas (`dark:`).
- **Qué debe validar después / Cuándo pedir confirmación:**
  - Ejecutar `npm run build` y comprobar que `experiencia/index.html` se compile correctamente.
  - Probar el estado vacío pasando un array vacío para validar el fallback visual.

## 12. Definition of Done
- [x] Arquitectura Brownfield formalizada y subordinada a `legacy_ecosystem.md`.
- [x] Componente `ExperienceList.astro` especificado con diseño responsivo y Zero JS overhead.
- [x] Matriz de ADRs (ADR-001 a ADR-012) consolidada bajo formato MADR con trade-offs reales.
- [x] Extensión del contrato de datos tipado (`profile.schema.ts`) con la colección `experience` y Zod.
- [x] Estrategia de testing unitario, E2E y Quality Gates en CI/CD estandarizados.
