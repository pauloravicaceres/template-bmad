---
description: 'Plantilla determinista para el artefacto generado por el Solutions Architect (tech_guidelines.md). Estructura corporativa de 12 puntos con MADR, enriquecida desde plan.md de Spec Kit, manejo de estado y resiliencia para guiar a la Fase A y D.'
applyTo: '**'
---

# Plantilla de Tech Guidelines (Gobernanza y Puente SDD)

## Convención de Nombres de Archivo
`tech_guidelines.md` (Este archivo es único y global por proyecto).

## Estructura Canónica Obligatoria

```markdown
# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** {{FECHA_ACTUAL}}
- **Solutions Architect:** Agente SA Senior BMAD
- **Fuente SDD:** `plan.md` y `tasks.md` (GitHub Spec Kit)

---

## 1. Project Overview
- **Qué es el sistema:** {{Resumen técnico}}
- **Qué problema resuelve:** {{Enfoque de valor}}
- **Naturaleza del Proyecto:** {{Greenfield (arquitectura desde cero) o Brownfield (especificar repositorios, bases de datos o infraestructura legacy que deba respetarse y/o integrarse)}}.
- **Arquitectura general:** {{Ej. Serverless orientada a eventos, Monolito, Microservicios, VSA}}

## 2. Repository Structure
- {{Definición de carpetas principales alineada a tasks.md}}
- **Importante:** {{Regla de separación lógica}}
- **Qué NO debe tocar:** {{Límites de infraestructura para el agente developer}}

## 3. Tech Stack
- **Runtime:** {{Ej. .NET 8/10, Node.js, Python, Java}}
- **Framework:** {{Ej. Carter, FastEndpoints, NestJS, Angular 22}}
- **Database:** {{Ej. PostgreSQL, SQL Server}}
- **Infrastructure:** {{Cloud provider, contenedores Docker rootless y servicios principales}}
- **Testing:** {{Framework de pruebas no-tautológicas}}

## 4. Development Workflow
- **Cómo levantar el proyecto:** {{Comandos locales}}
- **Cómo ejecutar tests / lint / build:** {{Scripts dotnet / npm / docker}}
- **Cómo ejecutar migraciones:** {{Reglas de despliegue de base de datos}}

## 5. Architecture Rules & Decision Framework
- **Principios que deben respetarse:** {{Ej. Stateless, High Availability, VSA}}
- **Dependencias permitidas:** {{Preferencias de servicios administrados vs custom}}
- **Patrones prohibidos:** Queda estrictamente prohibido el uso de variables "hardcodeadas".

### 5.1. State Management Architecture
- **Frontera de Estado:** {{Definir explícitamente dónde reside la verdad: Cliente, Servidor o Base de Datos Distribuida}}.
- **Estrategia de Sincronización:** {{Optimistic UI, Polling, WebSockets o Server-Sent Events}}.
- **Consistencia:** {{Fuerte o Eventual, detallando cómo se mitigan condiciones de carrera}}.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:** {{Qué ocurre si la base de datos, servicio externo o API de terceros cae}}.
- **Patrones de Tolerancia a Fallos:** {{Timeouts obligatorios, Retries con Exponential Backoff, Circuit Breaker, Fallbacks estáticos}}.
- **Proporcionalidad:** {{La complejidad de resiliencia debe ser proporcional al riesgo real del proyecto, evitando sobre-ingeniería}}.

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)
*(Validados, formalizados y enriquecidos desde el plan.md de Spec Kit)*

#### ADR-001: {{Título de la Decisión de Infraestructura o Stack}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de .specify/memory/constitution.md o .specify/memory/constitution.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué requerimiento de plan.md o restricción técnica motiva esta decisión}}.
- **Decisión:** {{Qué patrón, tecnología o servicio se seleccionó en una frase clara y verificable}}.
- **Alternativas Consideradas (Obligatorio en decisiones nuevas):**
  - **Alternativa A:** {{Por qué era viable y por qué se descartó con argumentos técnicos reales}}.
  - **Alternativa B:** {{Por qué era viable y por qué se descartó con argumentos técnicos reales}}.
  - *(Exento de alternativas si el estado es Aceptado (heredado))*.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** {{Beneficio técnico o de negocio}}.
  - ⚠️ **Trade-off / Costo Real:** {{Toda decisión técnica tiene un compromiso en costo, latencia o complejidad. Prohibido omitir el costo o usar justificaciones cosméticas}}.

## 6. Coding Conventions
- **Naming / Organización / Error handling / Logging / Async patterns.** {{Especificar según el stack elegido}}

## 7. Testing
- **Qué debe testearse y Dónde están los tests.** {{Estrategia de cobertura}}

## 8. Security
- **Manejo de secretos:** Todas las credenciales deben inyectarse mediante variables de entorno.
- **Datos sensibles y Acciones prohibidas.**

## 9. Database
- **Schema:** {{Relacional o NoSQL}}
- **Reglas para modificar DB:** {{Ej. Migraciones no bloqueantes CONCURRENTLY}}

## 10. Git & PR Rules
- **Naming de branches y Commits:** {{Ej. Conventional Commits}}

## 11. Agent Instructions (Dev Guidelines)
- **Qué debe hacer antes de modificar código:** {{Directivas para el agente codificador}}
- **Qué debe validar después / Cuándo pedir confirmación.**

## 12. Definition of Done
- Todo el código nuevo cuenta con patrones de resiliencia y manejo de estado definidos.
- No hay ninguna credencial o variable de entorno hardcodeada.
- Las migraciones de base de datos han sido auditadas.
- Tests y Lint pasan exitosamente en el entorno de CI.
```

---

### ⚠️ Directiva para Gobernanza de Arquitectura y Sincronización SDD
1. **Consumo de `plan.md` y `tasks.md`:** Los ADRs y directivas de desarrollo se construyen formalizando el plan técnico macro de Spec Kit (`plan.md`) y mapeando las tareas de arquitectura definidas en `tasks.md`.
2. **Modo Brownfield:** Si existe el archivo `.specify/memory/constitution.md` o `.specify/memory/constitution.md`:
   - Consignar: `Naturaleza del Proyecto: Brownfield (Subordinado a las directrices de la Constitución Técnica)`.
   - Explicitar tecnologías heredadas y asentar las decisiones impuestas como ADRs con `Estado: Aceptado (heredado)`.
3. **Lex Superior y Blindaje Anti-Sycophancy:** Queda estrictamente prohibido adoptar stacks incompatibles con la constitución técnica física, incluso ante peticiones en el tracker, salvo que exista una sección titulada `## ⚠️ CLÁUSULA DE EXCEPCIÓN ARQUITECTÓNICA` explícita en el archivo.

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
