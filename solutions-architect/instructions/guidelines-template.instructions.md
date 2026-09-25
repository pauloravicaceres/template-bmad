---
description: 'Plantilla determinista para el artefacto generado por el Solutions Architect (tech_guidelines.md). Estructura corporativa de 12 puntos con MADR, manejo de estado y resiliencia para guiar a la Fase A y D.'
applyTo: '**'
---

# Plantilla de Tech Guidelines (Gobernanza)

## Convención de Nombres de Archivo
`tech_guidelines.md` (Este archivo es único y global por proyecto).

## Estructura Canónica Obligatoria

```markdown
# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** {{FECHA_ACTUAL}}
- **Solutions Architect:** Agente SA Senior BMAD

---

## 1. Project Overview
- **Qué es el sistema:** {{Resumen técnico}}
- **Qué problema resuelve:** {{Enfoque de valor}}
- **Naturaleza del Proyecto:** {{Greenfield (arquitectura desde cero) o Brownfield (especificar repositorios, bases de datos o infraestructura legacy que deba respetarse y/o integrarse)}}.
- **Arquitectura general:** {{Ej. Serverless orientada a eventos, Monolito, Microservicios}}

## 2. Repository Structure
- {{Definición de carpetas principales, ej. src/handlers, src/services}}
- **Importante:** {{Regla de separación lógica}}
- **Qué NO debe tocar:** {{Límites de infraestructura para el agente developer}}

## 3. Tech Stack
- **Runtime:** {{Ej. Node.js, Python, Java}}
- **Framework:** {{Ej. Serverless Framework, NestJS, Django}}
- **Database:** {{Ej. PostgreSQL, MongoDB, DynamoDB}}
- **Infrastructure:** {{Cloud provider y servicios principales}}
- **Testing:** {{Framework de pruebas}}

## 4. Development Workflow
- **Cómo levantar el proyecto:** {{Comandos locales}}
- **Cómo ejecutar tests / lint / build:** {{Scripts npm / pip}}
- **Cómo ejecutar migraciones:** {{Reglas de despliegue de base de datos}}

## 5. Architecture Rules & Decision Framework
- **Principios que deben respetarse:** {{Ej. Stateless, High Availability}}
- **Dependencias permitidas:** {{Preferencias de servicios administrados vs custom}}
- **Patrones prohibidos:** Queda estrictamente prohibido el uso de variables "hardcodeadas".

### 5.1. State Management Architecture
- **Frontera de Estado:** {{Definir explícitamente dónde reside la verdad: Cliente (SPA/Mobile), Servidor (Sesiones/Cache) o Base de Datos Distribuida}}.
- **Estrategia de Sincronización:** {{Optimistic UI, Polling, WebSockets o Server-Sent Events}}.
- **Consistencia:** {{Fuerte o Eventual, detallando cómo se mitigan condiciones de carrera}}.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:** {{Qué ocurre si la base de datos, servicio externo o API de terceros cae}}.
- **Patrones de Tolerancia a Fallos:** {{Timeouts obligatorios, Retries con Exponential Backoff, Circuit Breaker, Fallbacks estáticos}}.
- **Proporcionalidad:** {{La complejidad de resiliencia debe ser proporcional al riesgo real del proyecto, evitando sobre-ingeniería}}.

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

#### ADR-001: {{Título de la Decisión de Infraestructura o Stack}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de files/context/legacy_ecosystem.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué requerimiento del PRD o restricción técnica motiva esta decisión}}.
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

### ⚠️ Directiva para Gobernanza de Arquitectura (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`:
1. **Sección 1 (Project Overview):** Consignar obligatoriamente: `Naturaleza del Proyecto: Brownfield (Subordinado a las directrices de files/context/legacy_ecosystem.md)`.
2. **Sección 3 (Tech Stack) y Sección 5 (Architecture Rules):** Explicitar las tecnologías, componentes e infraestructura heredadas documentadas en el archivo legacy, y establecer las reglas obligatorias de coexistencia, interoperabilidad y no-regresión para los nuevos componentes. Todas las decisiones tecnológicas impuestas por el sistema existente deben registrarse como ADRs con `Estado: Aceptado (heredado)` sin requerir alternativas consideradas.
3. **Sección 9 (Database):** Subordinar el motor, esquema y dialecto a las restricciones de base de datos declaradas en el archivo legacy.
4. **Si el archivo NO existe (Modo Greenfield):** Define la arquitectura y gobernanza estándar según las respuestas del stakeholder sin precondiciones heredadas.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
