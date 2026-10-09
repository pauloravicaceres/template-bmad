---
description: 'Plantilla y reglas estrictas para la creación o actualización del constitution.md bajo el estándar Spec Kit SDD.'
applyTo: '**'
---

# 🏛️ PROTOCOLO DE DESTILACIÓN DE CONTEXTO (SPEC KIT CONSTITUTION)

Como Auditor Técnico (QA-Tech), tu responsabilidad final tras aprobar una arquitectura (0 bloqueos críticos) es gestionar el `constitution.md`. Este documento gobierna las restricciones técnicas del proyecto y debe adherirse estrictamente al formato requerido por **GitHub Spec Kit**.

## Resolución constitucional BMAD

Resuelve WORKSPACE_ROOT y ENGINE_ROOT desde el contrato de ejecución. Lee la política
operativa ENGINE_ROOT/constitution.md y exclusivamente la constitución técnica
WORKSPACE_ROOT/.specify/memory/constitution.md. No uses la memoria del motor como
fallback para otro proyecto. Spec Kit y QA-Tech comparten ese archivo canónico.
Conserva sus enlaces a guías y ADRs; no los sustituyas por un resumen del plan.
Observación, propuesta y aprobación son estados distintos: ni la existencia del
archivo ni una dependencia detectada conceden aprobación. Las decisiones pendientes
requieren aprobación humana explícita antes de declararlas obligatorias. Registra
fuente y estado, preserva enmiendas y nunca modifica la política del motor.

La condición Brownfield se determina por código/manifests existentes, no por la
mera existencia de la constitución neutral. Usa `Aceptado (heredado)` solo para una
decisión previamente aprobada con evidencia; para código usa `Observado` y para
opciones aún no ratificadas `Propuesto`. Esta precisión gobierna las instrucciones
legacy de herencia que aparecen a continuación.

## 🔄 LÓGICA DE EJECUCIÓN (GREENFIELD VS BROWNFIELD)

### ESCENARIO A: GREENFIELD (El archivo NO existe)
Si el orquestador reporta que el archivo no existe, debes redactarlo desde cero. Extrae las invariantes del `tech-design_*.md` recién aprobado y formatea el contenido EXACTAMENTE con la estructura de la **Plantilla SDD Spec Kit** detallada más abajo.

### ESCENARIO B: BROWNFIELD (El archivo YA existe)
Tienes **ESTRICTAMENTE PROHIBIDO** sobrescribir el archivo borrando su contenido fundacional.
1. Lee el archivo existente.
2. Evalúa si el `tech-design_*.md` actual introduce cambios estructurales (nuevas bases de datos, nuevos patrones arquitectónicos, nuevos ADRs globales).
3. Si hay cambios estructurales: Inyéctalos cuidadosamente en las secciones correspondientes de la plantilla existente (ej. añadiendo una fila a la tabla de ADRs o un nuevo Core Principle).
4. Actualiza la fecha en `**Last Amended**`.
5. Si no hay cambios estructurales (solo es un CRUD o feature menor): **ABORTA** la escritura. No modifiques el archivo.

---

## 📄 PLANTILLA SDD SPEC KIT (USO OBLIGATORIO)

Al generar o estructurar el documento, debes utilizar obligatoriamente estos encabezados (H2 y H3). No inventes nuevas secciones principales.

```markdown
# [NOMBRE_DEL_PROYECTO] Constitution

## Core Principles
<!-- Principios innegociables de ingeniería del proyecto. Define reglas de arquitectura limpia, enfoques (ej. API-First, Zero-Trust) y resiliencia. -->
### I. [Nombre del Principio 1]
[Descripción exacta extraída de la arquitectura]
### II. [Nombre del Principio 2]
[Descripción exacta extraída de la arquitectura]

## Stack & Technical Constraints
<!-- Invariantes tecnológicas extraídas del Tech Design. Nombra versiones específicas si están disponibles. -->
- **Runtime & Plataforma:** [Ej. Node.js 20.x, .NET 8]
- **Framework Principal:** [Ej. Angular 22 Zoneless, Astro 4]
- **Infraestructura & Despliegue:** [Ej. AWS, Vercel, Docker]
- **Persistencia de Datos:** [Ej. PostgreSQL 16, Redis]

## Quality & CI/CD Gates
<!-- Estándares de prueba y calidad que el código deberá pasar. -->
- **Testing:** [Ej. xUnit estricto, Playwright E2E]
- **Reglas de Calidad:** [Ej. Cobertura > 80%, LCP < 1.0s]

## Architecture Decision Records (ADRs)
<!-- Matriz consolidada de las decisiones estructurales. Añade filas aquí en escenarios Brownfield. -->
| ID | Área | Estado | Resumen de Decisión / Invariante |
|:---:|:---:|:---:|---|
| **ADR-001** | [Área] | [Aceptado/Vigente] | [Descripción técnica concisa] |

## Governance
<!-- Cláusula de cierre inmutable para Spec Kit. -->
Esta Constitución gobierna las restricciones técnicas del proyecto. Toda tarea generada por `/speckit.tasks` y todo código emitido por los agentes de desarrollo debe ser analizado por `/speckit.analyze` contra estas reglas. Ningún agente tiene autorización para evadir este stack o proponer tecnologías no listadas sin una enmienda formal a este documento.

**Version**: [EJ: 1.0.0] | **Ratified**: [FECHA DE CREACIÓN] | **Last Amended**: [FECHA DE MODIFICACIÓN ACTUAL]
```
