---
description: 'Usar EXCLUSIVAMENTE cuando el QT detecta inconsistencias técnicas, alternativas falsas, trade-offs inválidos o violación de trazabilidad UI-Data. Plantilla para feedback_tech_[nombre_corto].md.'
applyTo: '**'
---

# Plantilla de Auditoría Adversarial y Rechazo Técnico

## Convención de Nombres de Archivo
`feedback_tech_[nombre_corto].md`

## Estructura Canónica Obligatoria

```markdown
# REPORTE DE AUDITORÍA ADVERSARIAL Y RECHAZO TÉCNICO ❌

- **Fecha de Auditoría:** {{FECHA_ACTUAL}}
- **Archivos Auditados:** `tech_guidelines.md`, `db_*.md`, `api_*.md` y `ux_*.md` (si existe)
- **Dictamen:** ❌ RECHAZADO (Requiere Subsanación Agéntica)

---

## 1. MATRIZ DE HALLAZGOS ADVERSARIALES

| Nivel de Severidad | Componente / ADR Afectado | Descripción del Hallazgo y Riesgo Técnico | Agente Responsable |
|---|---|---|:---:|
| 🔴 **CRÍTICO** | {{ADR-XX / Tabla / Endpoint}} | {{Problema de integridad, discrepancia UI vs MER, sobre/sub-ingeniería grave o alternativa/trade-off falso}} | `@DA:` / `@API:` / `@SA:` |
| 🟡 **ADVERTENCIA** | {{Sección de Resiliencia / Estado}} | {{Riesgo potencial de concurrencia o costos no explicitados}} | `@DA:` / `@API:` / `@SA:` |
| 🟢 **SUGERENCIA** | {{Convenciones o payloads}} | {{Mejora menor no bloqueante documentada como deuda técnica}} | Informar |

---

## 2. CRITERIOS ADVERSARIALES ESTRICTOS (Detector de Mentiras y Calidad)
- **Alternativa Falsa:** Proponer una tecnología evidentemente absurda para el contexto o proponer "No hacer nada". Una alternativa real debe ser técnicamente viable y competitiva.
- **Trade-off Falso:** Poner justificaciones cosméticas como "Toma tiempo programarlo" o "Requiere esfuerzo de desarrollo". Un trade-off real debe implicar costos de infraestructura, latencia de red, límites de concurrencia, acoplamiento o cuellos de botella.

---

## 3. CHECKLIST DE VERIFICACIÓN FALLIDA
- [ ] **Falsas Alternativas en ADRs:** Se detectaron opciones descartadas que representan un falso dilema o son inviables por diseño solo para rellenar la plantilla.
- [ ] **Omisión o Falsedad en Trade-offs:** El ADR declara únicamente beneficios o incluye trade-offs falsos sin admitir compromisos operativos o de ingeniería reales.
- [ ] **Desconexión UI vs Data:** Existen elementos visuales en `ux_*.md` que no tienen soporte en el modelo relacional `db_*.md` (campos huérfanos).
- [ ] **Desproporción Arquitectónica:** Sobre-ingeniería desmedida o sub-ingeniería vulnerable frente a los requerimientos del Product Brief.
- [ ] **Inconsistencia DB vs API:** Discrepancias entre las columnas del MER y los payloads o rutas de los contratos API.

---

## 4. ORDEN DE REPARACIÓN EN TRACKER
*(Instrucción continua para devolver el turno al agente causante)*

`{{ @DA: | @API: | @SA: }} Se ha emitido feedback adversarial crítico en files/qa-tech/feedback_tech_*.md. Por favor, subsana las inconsistencias señaladas para proceder con la re-auditoría.`
```

---

### ⚠️ Directiva de Rechazo por Violación de Ecosistema Preexistente (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`, constituye motivo inmediato de **RECHAZO TÉCNICO CRÍTICO (🔴)**:
1. Si el diseño de base de datos (`db_*.md`) emplea motores, dialectos o modelos incompatibles con lo declarado en el archivo legacy (dirigir a `@DA:`).
2. Si los contratos de interfaz (`api_*.md`) omiten los protocolos de comunicación existentes o no implementan los adaptadores requeridos para el sistema heredado (dirigir a `@API:`).
3. Si la arquitectura no contempla los servidores o la topología de red documentada (dirigir a `@SA:`).
4. Si se inventaron alternativas artificiales para decisiones impuestas por el sistema existente en lugar de marcarlas como `Aceptado (heredado)`.
