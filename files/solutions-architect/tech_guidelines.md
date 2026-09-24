# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** 23-09-2026
- **Solutions Architect:** Agente SA Senior BMAD

---

## 1. Project Overview
- **Qué es el sistema:** Aplicación web moderna, sobria y auto-contenida para la exhibición del Perfil Profesional Digital y trayectoria técnica de un desarrollador de software.
- **Qué problema resuelve:** Elimina la dispersión y saturación visual de plataformas externas tradicionales, permitiendo a reclutadores técnicos y líderes de talento evaluar de forma inmediata y en una sola pantalla la identidad, datos de contacto, trayectoria cronológica y tecnologías dominadas.
- **Naturaleza del Proyecto:** Greenfield (desarrollo 100% desde cero, sin código legacy ni repositorios preexistentes que condicionen la arquitectura).
- **Arquitectura general:** Jamstack con Generación Estática (SSG - Static Site Generation) sobre Next.js (App Router), con renderizado pre-compilado en el Edge, consumo desacoplado de datos locales (Markdown/JSON) y persistencia de temas visuales en cliente (`localStorage`).

---

## 2. Repository Structure
```text
/
├── public/                     # Assets estáticos públicos (fotografía de perfil, favicon, robots.txt)
├── src/
│   ├── app/                    # Next.js App Router (rutas, layout raíz, page principal)
│   │   ├── layout.tsx          # Root Layout con inyección de ThemeProvider
│   │   ├── page.tsx            # Vista principal auto-contenida (Single-Page View)
│   │   └── globals.css         # Estilos globales de Tailwind y variables CSS de tema
│   ├── components/             # Componentes modulares y atómicos
│   │   ├── layout/             # Header, Footer, ThemeToggle, Container
│   │   ├── profile/            # ProfileHeader, ContactCard, ContactItem
│   │   └── experience/         # ExperienceTimeline, ExperienceCard, TechBadge
│   ├── context/                # Contextos de cliente (ThemeProvider, ThemeContext)
│   ├── hooks/                  # Custom hooks (useTheme, useProfileData)
│   ├── data/                   # Archivos de datos estructurados (profile.json / markdown)
│   ├── types/                  # Definiciones e interfaces estrictas TypeScript
│   └── lib/                    # Utilidades auxiliares y parsers de datos locales
├── tests/
│   ├── unit/                   # Pruebas unitarias de componentes con Vitest
│   └── setup.ts                # Configuración de entorno de pruebas (jsdom)
├── .github/
│   └── workflows/              # CI/CD Workflows (lint, typecheck, test en GitHub Actions)
├── .env.example                # Plantilla de variables de entorno públicas
├── next.config.mjs             # Configuración de Next.js (output: 'export' para SSG puro)
├── tailwind.config.ts          # Configuración de Tailwind CSS (darkMode: 'class')
├── tsconfig.json               # Configuración estricta de TypeScript
└── package.json                # Dependencias y scripts de desarrollo
```
- **Importante:** Separación lógica estricta entre la capa de presentación (`components/`), la capa de rutas/páginas (`app/`), el estado de tema del cliente (`context/` y `hooks/`) y el modelo de datos (`data/` y `types/`).
- **Qué NO debe tocar el Developer:** No modificar configuraciones centrales de infraestructura y empaquetado (`next.config.mjs`, `tsconfig.json`, `.github/workflows/`) sin validación arquitectónica previa.

---

## 3. Tech Stack
- **Runtime:** Node.js (v20.x LTS).
- **Framework:** Next.js 14+ (App Router con React y TypeScript).
- **Styling:** Tailwind CSS configurado con estrategia de clase `dark` para alternancia fluida y alto contraste (WCAG 2.1 AA).
- **Data Source & Storage:** Archivos locales en formato JSON y/o Markdown (`src/data/`), parseados y tipados estáticamente en tiempo de compilación. No requiere API dedicada ni base de datos externa.
- **Theme Persistence:** Client-side State persistido en `localStorage` con fallback a `prefers-color-scheme`.
- **Infrastructure & Hosting:** Vercel (Hobby Plan / 100% Free Tier) con despliegue continuo automático desde la rama principal de GitHub.
- **Testing:** Vitest + React Testing Library + jsdom.
- **Quality & CI/CD:** ESLint + Prettier + GitHub Actions (pipeline preventivo de lint, typecheck y test).

---

## 4. Development Workflow
- **Cómo levantar el proyecto localmente:**
  ```bash
  npm install
  npm run dev
  ```
- **Cómo ejecutar tests / lint / build:**
  - Pruebas unitarias: `npm run test`
  - Cobertura de tests: `npm run test:coverage`
  - Linter: `npm run lint`
  - Formateo: `npm run format`
  - Verificación de tipos: `npm run typecheck`
  - Compilación de producción (SSG): `npm run build`
- **Cómo ejecutar migraciones:** No aplica (arquitectura estática basada en archivos locales tipados).

---

## 5. Architecture Rules
- **Principios que deben respetarse:**
  - *Static First / Serverless Edge:* Compilación estática pura (SSG) sin dependencias de servidores backend en tiempo de ejecución.
  - *Single View Design:* La totalidad de la experiencia debe concentrarse en una vista unificada y responsiva sin saltos de navegación externos.
  - *Auto-contención:* No depender de APIs externas de terceros para la carga de datos del perfil.
  - *Accesibilidad y Confort Visual:* Soporte nativo para modo claro y oscuro con contraste mínimo 4.5:1.
- **Patrones obligatorios:**
  - Server Components por defecto para el renderizado inicial y Client Components (`'use client'`) únicamente donde exista interactividad (ej. `ThemeToggle`).
  - Tipado exhaustivo de interfaces en `src/types/`.
- **Patrones prohibidos:**
  - Queda estrictamente prohibido el uso de variables o datos personales "hardcodeados" directamente en el JSX de los componentes; todos los datos deben provenir del módulo `src/data/`.
  - Prohibido el uso de `any` en TypeScript.

---

## 6. Coding Conventions
- **Naming Conventions:**
  - Componentes: `PascalCase` (ej. `ProfileHeader.tsx`, `ThemeToggle.tsx`).
  - Hooks: `camelCase` con prefijo `use` (ej. `useTheme.ts`).
  - Types / Interfaces: `PascalCase` (ej. `UserProfile`, `ContactInfo`, `ExperienceItem`).
  - Constantes: `SCREAMING_SNAKE_CASE` o `camelCase` según aplicabilidad.
- **Organización:** Exportaciones nombradas (`export const ComponentName = ...`).
- **Error Handling:** Implementación de `error.tsx` en Next.js App Router para manejo controlado de excepciones en la UI.
- **CSS / Styling:** Utilizar clases utilitarias de Tailwind y tokens de diseño semánticos (`bg-background`, `text-foreground`, etc.).

---

## 7. Testing
- **Qué debe testearse:**
  - Renderizado de componentes críticos (Header de perfil, Tarjetas de trayectoria, Datos de contacto).
  - Comportamiento del toggle de tema claro/oscuro y persistencia correcta en `localStorage`.
  - Validación de integridad de los datos cargados desde `src/data/`.
- **Dónde están los tests:** Ubicados en `tests/unit/` replicando la estructura de componentes.

---

## 8. Security
- **Manejo de secretos:** Todas las variables públicas deben prefijarse con `NEXT_PUBLIC_` en `.env.example`.
- **Protección de datos:** No versionar datos personales privados ni credenciales sensibles.
- **Sanitización:** Todo contenido renderizado dinámicamente desde Markdown debe ser sanitizado para mitigar riesgos de XSS.

---

## 9. Database & Data Architecture
- **Schema:** Esquema documental / estructurado en TypeScript representando:
  - `Profile`: Información biográfica, fotografía, título, resumen.
  - `Contact`: Canales de comunicación directa (correo, teléfono, ubicación).
  - `Experience`: Trayectoria cronológica con empresa, periodo, rol, logros y tecnologías.
  - `Skill`: Catálogo de tecnologías dominadas.
- **Reglas de modificación de datos:** Toda modificación en el esquema de datos debe reflejarse en los tipos de TypeScript y contar con validación unitaria.

---

## 10. Git & PR Rules
- **Naming de branches:**
  - `feature/hu-XX-nombre-funcionalidad`
  - `fix/hu-XX-descripcion-bug`
  - `chore/configuracion-ci`
- **Commits:** Conventional Commits (`feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`).

---

## 11. Agent Instructions (Dev Guidelines)
- **Qué debe hacer antes de modificar código:**
  1. Revisar este `tech_guidelines.md` para alinearse con el stack Next.js / Tailwind.
  2. Verificar los contratos de datos en `src/types/`.
  3. Asegurar compatibilidad estricta con modo claro y modo oscuro.
- **Qué debe validar después / Cuándo pedir confirmación:**
  - Ejecutar `npm run lint`, `npm run typecheck` y `npm run test` antes de marcar cualquier tarea como lista.
  - Solicitar confirmación antes de introducir librerías externas adicionales.

---

## 12. Definition of Done
- Código 100% tipado en TypeScript sin advertencias de linter ni errores de compilación.
- Componentes visuales probados en modo claro y modo oscuro.
- Persistencia de tema funcional en `localStorage`.
- Pruebas unitarias en Vitest ejecutadas y con cobertura satisfactoria.
- Build estático (`next build`) completado con éxito.
- Pipeline de GitHub Actions configurado y verificado en verde.
