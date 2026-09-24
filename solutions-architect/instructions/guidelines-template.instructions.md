---
description: 'Plantilla determinista para el artefacto generado por el Solutions Architect (tech_guidelines.md). Estructura corporativa de 12 puntos para guiar a la Fase A y D.'
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

## 5. Architecture Rules
- **Principios que deben respetarse:** {{Ej. Stateless, High Availability}}
- **Patrones obligatorios:** {{Ej. Retries, DLQs}}
- **Dependencias permitidas:** {{Preferencias de servicios administrados vs custom}}
- **Patrones prohibidos:** Queda estrictamente prohibido el uso de variables "hardcodeadas".

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
- Todo el código nuevo cuenta con patrones de resiliencia definidos.
- No hay ninguna credencial o variable de entorno hardcodeada.
- Las migraciones de base de datos han sido auditadas.
- Tests y Lint pasan exitosamente en el entorno de CI.
```

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
