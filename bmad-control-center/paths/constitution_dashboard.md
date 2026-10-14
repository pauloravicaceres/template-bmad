# BMAD Control Center Constitution

## Core Principles

### I. File-System as a Database (FSaaDB)
El sistema debe operar de manera estrictamente local y carecer de bases de datos tradicionales. Actuará como un envoltorio reactivo sobre el espacio de trabajo de los agentes (leyendo y mutando `tracker_bmad.md`, el directorio `docs/` y `.specify/`).

### II. Observabilidad y Desacoplamiento Reactivo en Tiempo Real
El sistema se compone de una arquitectura desacoplada donde el Frontend no requiere gestionar estado pesado de los agentes; se limita a reaccionar en tiempo real a los eventos disparados por un servidor de WebSockets multiplexado que monitorea el sistema de archivos y el árbol Git local.

## Stack & Technical Constraints

- **Runtime & Plataforma:** Node.js (Frontend) y Python (Backend).
- **Frontend Principal:** Vue 3 (Composition API) + Nuxt 3 + PrimeVue/Tailwind. (Obligatorio, innegociable).
- **Backend Principal:** Python + FastAPI + Watchdog + Uvicorn (WebSockets y REST). (Obligatorio, innegociable).
- **Infraestructura & Despliegue:** Ejecución Local Exclusiva (BMAD local environment).
- **Persistencia de Datos:** Sistema de Archivos local (archivos Markdown, carpetas operativas, repositorio Git).

## Quality & CI/CD Gates

- **Testing:** Pruebas unitarias para endpoints REST/WS de FastAPI (ej. Pytest) y testing de componentes reactivos en Vue/Nuxt.
- **Reglas de Calidad:** Procesamiento seguro de artefactos con `marked.js` y renderizado de gráficos `mermaid.js` garantizado sin fallos silenciosos. Actualización de vistas del DOM mediante WebSockets en tiempo real sin recarga manual.

## Architecture Decision Records (ADRs)

| ID | Área | Estado | Resumen de Decisión / Invariante |
|:---:|:---:|:---:|---|
| **ADR-001** | Backend | Vigente | Uso de FastAPI con WebSockets y Watchdog para monitorizar en vivo el File-System. |
| **ADR-002** | Frontend | Vigente | Elección mandatoria de Vue 3 (Composition API) con Nuxt 3 y PrimeVue/Tailwind, excluyendo explícitamente otros frameworks SPA. |
| **ADR-003** | Arquitectura | Vigente | Independencia de despliegue cloud; la solución es una herramienta HITL (Human-in-the-Loop) ejecutada localmente. |
| **ADR-004** | Topología | Vigente | Segregación estricta de código fuente. Todo el código de la aplicación debe residir obligatoriamente bajo el subdirectorio raíz `/app/` (ej. `/app/frontend/` y `/app/backend/`), prohibiendo el andamiaje directo en la raíz del ecosistema BMAD. |

## Governance

Esta Constitución actúa como la "Lex Superior" del ecosistema. Toda tarea generada por `/speckit.tasks` y todo código emitido por los agentes de desarrollo debe ser analizado por `/speckit.analyze` contra estas reglas. Ningún agente tiene autorización para evadir este stack o proponer tecnologías no listadas sin una enmienda formal a este documento.

**Version**: 1.0.0 | **Ratified**: 2026-09-28 | **Last Amended**: 2026-09-28