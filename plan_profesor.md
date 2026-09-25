# Plan de Integración: Rigor Arquitectónico y Auditoría Adversarial en BMAD (`plan_profesor.md`)

> **Rol del Emisor:** BMAD Core Architect (CTO del Swarm)  
> **Fecha de Emisión:** 24 de Septiembre de 2026  
> **Estado:** Propuesta Técnica Aprobada para Implementación  
> **Objetivo:** Extraer e inyectar el rigor analítico, el formato MADR, la trazabilidad UI-Data y el mindset adversarial de los modelos externos (`profe/generar-tech-design` y `profe/revision-adversarial`) en las plantillas `.instructions.md` del ecosistema BMAD, preservando intacta la topología distribuida, el desacoplamiento asíncrono y la estrategia agnóstica Greenfield/Brownfield.

---

## 1. 🔍 DIAGNÓSTICO ARQUITECTÓNICO (BMAD vs. ENFOQUES EXTERNOS)

Hemos analizado minuciosamente las dos habilidades de arquitectura externa provistas en [`profe/`](file:///D:/Paulo/Cursos/DMC/template-bmad/profe):
1. **`generar-tech-design`:** Enfoque conversacional monolítico que formula preguntas paso a paso para construir un Technical Design Document (TDD) y ADRs en formato MADR.
2. **`revision-adversarial`:** Enfoque de auditoría crítica que caza activamente sesgos de confirmación, alternativas falsas, riesgos no considerados y brechas entre el diseño visual y los datos.

### Cuadro Comparativo de Paradigmas

| Dimensión Arquitectónica | Enfoque Externo (`profe`) | Framework BMAD Actual | Visión Objetivo (BMAD Upgrade) |
|---|---|---|---|
| **Topología Agéntica** | **Monolítico:** Un único agente LLM diseña componentes, datos, red y stack. | **Distribuido (Especialistas):** `SA` (Gobernanza), `DA` (Persistencia), `API` (Contratos), `QT` (Auditor/Compilador). | **Mantiene Especialistas:** Segregación estricta de dominios sin agentes monolíticos. |
| **Interacción y Despacho** | **Conversacional Bloqueante:** Entrevista al usuario decisión por decisión, deteniendo el flujo. | **Token-Passing Asíncrono:** Comunicación exclusiva por adición al [`tracker_bmad.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/files/tracker_bmad.md). | **Autonomía Total:** El enjambre decide y audita de forma autónoma; solo consulta al humano en hitos HITL críticos. |
| **Formato de Decisiones (ADR)** | **MADR Exhaustivo:** Estado (`Aceptado` / `Aceptado (heredado)`), Contexto, Alternativas reales y Consecuencias con trade-offs. | **ADR Simplificado:** Contexto, Alternativas Descartadas, Decisión y Consecuencias. | **MADR Enriquecido:** Adopción formal del estándar MADR con trazabilidad de estado `Heredado` para Brownfield. |
| **Dimensiones de Gobernanza** | **7 Áreas de Decisión:** Componentes, Datos, API, Stack, Estado, Resiliencia y Requisitos No Funcionales (RNF). | **12 Puntos de Guidelines:** Foco en repo, stack, Docker, testing y reglas de codificación. | **Síntesis Estratégica:** Inyección formal de *Manejo de Estado* y *Resiliencia/Errores* en las directrices del SA. |
| **Trazabilidad UI -> Persistencia** | **Cruce Explícito:** El modelo de datos debe cubrir cada elemento que la UI revela (`Design.md`). | **Trazabilidad Implícita:** DA lee HUs y Product Brief, pero no auditaba formalmente los wireframes UX. | **Cruce Forzoso UI-Data:** DA y QT cruzan obligatoriamente `ux_*.md` contra `db_*.md` (salvo en Bypass Headless). |
| **Rol del QA Técnico** | **Revisión Manual:** Genera un reporte para que el humano corrija a mano el diseño. | **Compilador Coherente:** Audita consistencia matemática MER vs. API y compila el TDD maestro. | **Auditor Adversarial Autónomo:** QT duda por defecto (*Zero-Trust*), clasifica en Crítico/Advertencia/Sugerencia y rechaza con handoff de auto-sanación. |

---

## 2. 🚫 ELEMENTOS DESCARTADOS (ANTI-PATRONES FRENTE A FILOSOFÍA BMAD)

Para preservar la resiliencia operativa y la autonomía del swarm, rechazamos tajantemente tres anti-patrones presentes en los modelos externos:

### ❌ Anti-Patrón 1: El Agente Conversacional Bloqueante (*"Step-by-step human interview"*)
* **Manifestación externa:** La directiva de `profe/generar-tech-design` exige: *"This skill is conversational, not one-shot. Walk the user through each architecture decision one at a time... Wait for the answer before continuing"*.
* **Por qué se rechaza:** Viola el **Pilar 1 de BMAD (Autonomía y Cero Fricción)**. Detener el proceso 7 veces para que el humano autorice cada decisión destruye la eficiencia de los agentes autónomos.
* **Solución BMAD:** El `SA` toma decisiones basadas en su marco de arquitectura, las HUs y el contexto Brownfield/Greenfield. Solo abre pausa interactiva en Greenfield para su cuestionario macro inicial, avanzando luego de manera 100% desatendida.

### ❌ Anti-Patrón 2: El Agente Monolítico (*"All-in-One Architecture Agent"*)
* **Manifestación externa:** Un solo prompt asume el rol de Solutions Architect, DBA, API Designer y QA Engineer simultáneamente.
* **Por qué se rechaza:** Provoca sobrecarga cognitiva y alucinaciones por dilución de contexto en proyectos de mediana/gran escala. Viola el **Principio de Responsabilidad Única**.
* **Solución BMAD:** Mantenemos la cadena de valor especializada:
  - `solutions-architect` (SA): Decide el stack, cloud, gobernanza, manejo de estado y resiliencia macro.
  - `data-architect` (DA): Especialista exclusivo en datos en reposo (MER, SQL, diccionario, normalización).
  - `api-architect` (API): Especialista exclusivo en datos en movimiento (HTTP, contratos REST/GraphQL, payloads, códigos de estado).
  - `qa-tech` (QT): Juez neutral y compilador que no diseñó ninguno de los artefactos previos.

### ❌ Anti-Patrón 3: La Remedición Manual Humana (*"Human-Driven Fixes"*)
* **Manifestación externa:** En `profe/revision-adversarial`, el agente emite un reporte pasivo porque *"The skill reports; the human decides what to change"*.
* **Por qué se rechaza:** Convierte al humano en un cuello de botella de edición manual y rompe el ciclo agéntico cerrado.
* **Solución BMAD:** El reporte adversarial del QT se transforma en un **mecanismo de auto-sanación (Self-Healing Loop)**. Si el QT detecta fallos críticos, emite `feedback_tech_*.md` y delega asíncronamente en el tracker hacia `@DA:`, `@API:` o `@SA:` con instrucciones técnicas precisas para su corrección automática.

---

## 3. 🎯 ELEMENTOS ADOPTADOS (EL "UPGRADE" METODOLÓGICO)

Adoptamos lo más valioso del rigor técnico y analítico del profesor:

### A. Estandarización MADR y Estado `Aceptado (heredado)`
* **Estructura Canónica:** Todos los ADRs en `SA`, `DA`, `API` y el consolidado en `QT` adoptarán la anatomía MADR estricta:
  - `Estado`: `Aceptado` | `Aceptado (heredado)`.
  - `Contexto y Planteamiento del Problema`.
  - `Decisión Tomada`.
  - `Alternativas Consideradas` (con justificación real de descarte).
  - `Consecuencias` (obligatoriedad de consignar al menos un trade-off o costo real).
* **Integración Brownfield:** Cuando exista [`files/context/legacy_ecosystem.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/files/context/legacy_ecosystem.md), las decisiones técnicas impuestas por el sistema existente se catalogan automáticamente como `Aceptado (heredado)`, quedando exentas de inventar alternativas ficticias.

### B. Inyección de las Áreas de Decisión: Estado y Resiliencia
* Se enriquecen las directrices corporativas del SA ([`guidelines-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/solutions-architect/instructions/guidelines-template.instructions.md)) incorporando dos secciones dedicadas:
  1. **Estrategia de Manejo de Estado (State Management):** Fronteras de estado (cliente, servidor, distribuido), consistencia transaccional y sincronización.
  2. **Estrategia de Resiliencia y Fallos:** Timeouts, reintentos con backoff exponencial, circuit breakers, degradación elegante proporcional y Dead Letter Queues (DLQ).

### C. Trazabilidad Estricta UI -> Persistencia (Cruce `ux_*.md` vs. `db_*.md`)
* **Regla Anti-Campos Huérfanos:** El Data Architect (`DA`) debe leer obligatoriamente el artefacto visual generado por el UX (`files/designer-ux/ux_*.md`). Todo elemento visual que implique datos (etiquetas de descuento, badges de estado, contadores, timestamps de auditoría) debe tener su columna y tipo de dato explícito en el MER.
* **Compatibilidad Headless:** Si el flujo ejecutó el Bypass Headless (proyectos ETL/APIs puras), esta regla se desactiva limpiamente sin bloquear al agente.

### D. Mindset Adversarial para el QA Tech (`QT`)
* El QT abandona la presunción de confianza y aplica **Zero-Trust Agéntico**:
  - Duda sistemáticamente de los supuestos del SA, DA y API.
  - Audita que las alternativas descartadas en los ADRs no sean ficticias o cosméticas (*two names for the same thing*).
  - Verifica que no exista sobre-ingeniería innecesaria (ej. Kafka para 10 transacciones diarias) ni sub-ingeniería riesgosa.
  - Verifica que cada decisión admita sus costos reales y no solo beneficios publicitarios.
* **Matriz de Severidad de Hallazgos:**
  - 🔴 **Crítico (Bloqueante):** Provoca dictamen `RECHAZADO`, genera `feedback_tech_*.md` y devuelve el turno al agente causante en el tracker.
  - 🟡 **Advertencia:** Riesgo técnico notable que debe quedar documentado en la sección de Deuda Técnica del TDD.
  - 🟢 **Sugerencia:** Optimización menor no bloqueante.

---

## 4. 📝 ESPECIFICACIÓN DETALLADA DE INYECCIÓN EN `.instructions.md`

A continuación se presentan los bloques exactos listos para ser inyectados en las plantillas del framework.

---

### 4.1. Solutions Architect: [`solutions-architect/instructions/guidelines-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/solutions-architect/instructions/guidelines-template.instructions.md)

#### Bloque a Inyectar en la Estructura Canónica (Secciones 5.1 y 5.2):
```markdown
## 5. Architecture Rules & Decision Framework

### 5.1. State Management Architecture
- **Frontera de Estado:** {{Definir explícitamente dónde reside la verdad: Cliente (SPA/Mobile), Servidor (Sesiones/Cache) o Base de Datos Distribuida}}.
- **Estrategia de Sincronización:** {{Optimistic UI, Polling, WebSockets o Server-Sent Events}}.
- **Consistencia:** {{Fuerte o Eventual, detallando cómo se mitigan condiciones de carrera}}.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:** {{Qué ocurre si la base de datos, servicio externo o API de terceros cae}}.
- **Patrones de Tolerancia a Fallos:** {{Timeouts obligatorios, Retries con Exponential Backoff, Circuit Breaker, Fallbacks estáticos}}.
- **Proporcionalidad:** {{La complejidad de resiliencia debe ser proporcional al riesgo real del proyecto, evitando sobre-ingeniería}}.

---

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

#### ADR-001: {{Título de la Decisión de Infraestructura o Stack}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de files/context/legacy_ecosystem.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué requerimiento del PRD o restricción técnica motiva esta decisión}}.
- **Decisión:** {{Qué patrón, tecnología o servicio se seleccionó en una frase clara y verificable}}.
- **Alternativas Consideradas (Obligatorio en decisiones nuevas):**
  - **Alternativa A:** {{Por qué era viable y por qué se descartó con argumentos técnicos reales}}.
  - **Alternativa B:** {{Por qué era viable y por qué se descartó}}.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** {{Beneficio técnico o de negocio}}.
  - ⚠️ **Trade-off / Costo Real:** {{Toda decisión técnica tiene un compromiso en costo, latencia o complejidad. Prohibido omitir el costo}}.
```

---

### 4.2. Data Architect: [`data-architect/instructions/db-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/data-architect/instructions/db-template.instructions.md)

#### Bloque a Inyectar para Trazabilidad UI-Data y ADRs MADR:
```markdown
---

## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

### ADR-01: {{Título de la decisión, ej. Motor de Persistencia o Tipo de Llave Primaria}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
- **Contexto:** {{Qué necesidad de modelado o restricción del legacy_ecosystem.md motiva la elección}}.
- **Decisión:** {{Tipo de dato, motor o normalización seleccionada}}.
- **Alternativas Evaluadas:**
  - **Alternativa A:** {{Opción viable descartada y justificación técnica}}.
  - *(Exento de alternativas si el estado es Aceptado (heredado))*.
- **Consecuencias:**
  - ✅ **Ventajas:** {{Eficiencia transaccional o integridad}}.
  - ⚠️ **Trade-off:** {{Complejidad en migraciones, costo de storage o sobrecarga de índices}}.

---

### ⚠️ DIRECTIVA OBLIGATORIA DE TRAZABILIDAD UI -> DATA (Cruce con UX)
1. **Inspección Visual de Datos:** Si el proyecto cuenta con diseño visual (`files/designer-ux/ux_*.md`), el Data Architect debe auditar cada wireframe y estado visual antes de cerrar el MER.
2. **Cero Campos Huérfanos:** Cada elemento de interfaz que requiera persistencia o cálculo (ej. etiquetas de descuento, badges de estado, contadores, timestamps de edición, preferencias de visualización) debe tener su columna correspondiente en el Diccionario de Datos.
3. **Excepción Headless:** Si el proyecto proviene de un Bypass Headless (sin `ux_*.md`), el modelo se deriva exclusivamente de las Historias de Usuario (`hu_*.md`) y del Product Brief (`pb_*.md`).
```

---

### 4.3. API Architect: [`api-architect/instructions/api-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/api-architect/instructions/api-template.instructions.md)

#### Bloque a Inyectar para ADRs MADR:
```markdown
## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

### ADR-01: {{Título de la decisión de integración o payload}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
- **Contexto:** {{Requerimiento de red o adaptación al sistema legado}}.
- **Decisión:** {{Protocolo, mecanismo de autenticación o estructura de respuesta elegido}}.
- **Alternativas Evaluadas:**
  - **Alternativa A:** {{Por qué no se eligió otra opción viable}}.
- **Consecuencias:**
  - ✅ **Beneficio:** {{Baja latencia, estandarización o simplicidad}}.
  - ⚠️ **Trade-off:** {{Overhead en payload, acoplamiento o serialización}}.
```

---

### 4.4. QA Tech: [`qa-tech/instructions/qa-tech-feedback.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-tech/instructions/qa-tech-feedback.instructions.md)

#### Bloque a Inyectar para Transformar el Rechazo en Auditoría Adversarial:
```markdown
# REPORTE DE AUDITORÍA ADVERSARIAL Y RECHAZO TÉCNICO ❌

- **Fecha de Auditoría:** {{FECHA_ACTUAL}}
- **Archivos Auditados:** `tech_guidelines.md`, `db_*.md`, `api_*.md` y `ux_*.md` (si existe)
- **Dictamen:** ❌ RECHAZADO (Requiere Subsanación Agéntica)

---

## 1. MATRIZ DE HALLAZGOS ADVERSARIALES

| Nivel de Severidad | Componente / ADR Afectado | Descripción del Hallazgo y Riesgo Técnico | Agente Responsable |
|---|---|---|:---:|
| 🔴 **CRÍTICO** | {{ADR-XX / Tabla / Endpoint}} | {{Problema de integridad, discrepancia UI vs MER, sobre/sub-ingeniería grave o alternativa falsa}} | `@DA:` / `@API:` / `@SA:` |
| 🟡 **ADVERTENCIA** | {{Sección de Resiliencia / Estado}} | {{Riesgo potencial de concurrencia o costos no explicitados}} | `@DA:` / `@API:` / `@SA:` |
| 🟢 **SUGERENCIA** | {{Convenciones o payloads}} | {{Mejora menor no bloqueante documentada como deuda técnica}} | Informar |

---

## 2. CRITERIOS DE RECHAZO ADVERSARIAL (Checklist de Verificación Fallida)
- [ ] **Falsas Alternativas en ADRs:** Se detectaron opciones descartadas que representan un falso dilema o son inviables por diseño solo para rellenar la plantilla.
- [ ] **Omisión de Trade-offs:** El ADR declara únicamente beneficios sin admitir compromisos o costos operativos.
- [ ] **Desconexión UI vs Data:** Existen elementos visuales en `ux_*.md` que no tienen soporte en el modelo relacional `db_*.md`.
- [ ] **Desproporción Arquitectónica:** Sobre-ingeniería desmedida o sub-ingeniería vulnerable frente a los requerimientos del Product Brief.

---

## 3. ORDEN DE REPARACIÓN EN TRACKER
*(Instrucción continua para devolver el turno al agente causante)*

`{{ @DA: | @API: | @SA: }} Se ha emitido feedback adversarial crítico en files/qa-tech/feedback_tech_*.md. Por favor, subsana las inconsistencias señaladas para proceder con la re-auditoría.`
```

---

### 4.5. QA Tech: [`qa-tech/instructions/tech-design-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-tech/instructions/tech-design-template.instructions.md)

#### Bloque a Inyectar en la Sección 7 (Architecture Decisions Consolidadas):
```markdown
## 7. Architecture Decisions (ADRs - Matriz Consolidada MADR)

*(Consolidar todos los ADRs generados por SA, DA y API, verificando que ninguno mantenga alternativas cosméticas y que todos reconozcan sus consecuencias reales).*

| ID | Título de la Decisión | Área | Estado | Trade-off / Costo Admitido |
|:---:|---|:---:|:---:|---|
| **ADR-001** | {{Stack y Hosting}} | Infraestructura | Aceptado / Heredado | {{Costo operativo / Curva de aprendizaje}} |
| **ADR-002** | {{Estrategia de Estado}} | Arquitectura | Aceptado | {{Latencia de sincronización}} |
| **ADR-003** | {{Modelo de Persistencia}} | Datos | Aceptado | {{Sobrecarga en índices de búsqueda}} |
| **ADR-004** | {{Protocolo de Integración}} | APIs | Aceptado | {{Payload overhead en red}} |

### ADR-001: {{Título}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos):** ...
```

---

## 5. 🛡️ MATRIZ DE RESPETO Y NO-REGRESIÓN GREENFIELD / BROWNFIELD

| Capacidad Existente en BMAD | Impacto del Upgrade Adversarial | Garantía de No-Regresión |
|---|---|---|
| **Bypass Headless** (`BA -> QA -> SA -> DA -> QT`) | Nulo | Si no existe `ux_*.md`, el DA y el QT saltan la validación UI-Data automáticamente sin arrojar error. |
| **Interruptor Brownfield** (`legacy_ecosystem.md`) | Reforzado | Las decisiones del sistema legado pasan directamente a estado `Aceptado (heredado)`, agilizando el flujo sin preguntas redundantemente formuladas. |
| **Token-Passing del Tracker** (`tracker_bmad.md`) | Intacto | Las órdenes de rechazo o aprobación del QT siguen la sintaxis formal de una sola línea (`@DA:`, `@API:`, `@HUMANO:`). |
| **Diagramación Resiliente Dual** (`archify` + `mermaid`) | Intacto | Mantiene la generación dual con fallback autónomo en la Sección 5 del Tech Design. |

---

## 6. 🚀 PLAN DE ACCIÓN PARA EJECUCIÓN

Una vez aprobado este plan, el despliegue se realizará en 4 pasos quirúrgicos:
1. **Paso 1:** Actualizar [`solutions-architect/instructions/guidelines-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/solutions-architect/instructions/guidelines-template.instructions.md) y [`solutions-architect/agents/solutions-architect.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/solutions-architect/agents/solutions-architect.agent.md).
2. **Paso 2:** Actualizar [`data-architect/instructions/db-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/data-architect/instructions/db-template.instructions.md) y [`data-architect/agents/data-architect.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/data-architect/agents/data-architect.agent.md).
3. **Paso 3:** Actualizar [`api-architect/instructions/api-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/api-architect/instructions/api-template.instructions.md) y [`api-architect/agents/api-architect.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/api-architect/agents/api-architect.agent.md).
4. **Paso 4:** Actualizar [`qa-tech/instructions/qa-tech-feedback.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-tech/instructions/qa-tech-feedback.instructions.md), [`qa-tech/instructions/tech-design-template.instructions.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-tech/instructions/tech-design-template.instructions.md) y [`qa-tech/agents/qa-tech.agent.md`](file:///D:/Paulo/Cursos/DMC/template-bmad/qa-tech/agents/qa-tech.agent.md).
5. **Paso 5:** Recompilar los `AGENTS.md` ejecutando el motor de ensamblaje de [`watcher_bmad.py`](file:///D:/Paulo/Cursos/DMC/template-bmad/watcher_bmad.py) y verificar la integridad global.
