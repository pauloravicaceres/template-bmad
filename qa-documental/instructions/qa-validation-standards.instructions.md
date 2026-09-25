---
description: 'Usar durante la fase de auditoría de Historias de Usuario. Rúbrica de evaluación documental en 5 dimensiones: Trazabilidad, Atomicidad/INVEST, Cobertura BDD/Gherkin, Consistencia Lógica y Separación de Responsabilidades.'
applyTo: '**'
---

# Estándares y Rúbrica de Validación Documental (QA)

> Rúbrica formal de inspección de Historias de Usuario bajo metodología BMAD.
> El dictamen de APROBACIÓN exige el 100% de cumplimiento en los criterios obligatorios.

---

## Dimensión 1: Trazabilidad y Fidelidad de Alcance (Scope)

- [ ] **Alineación con la Fuente:** Todo comportamiento exigido corresponde directamente a un requerimiento del Product Brief.
- [ ] **Gestión de Asunciones:** Todo dato inferido o no explicitado en el PB cuenta con la etiqueta visible `⚠️ [PROPUESTO]` o `⚠️ SUPUESTO:`.
- [ ] **Puntos Abiertos Legítimos:** Si existen dependencias externas no resueltas, se encuentran catalogadas como `❓ No documentado` dentro del DoD y no como reglas inventadas.
- [ ] **Fronteras Negativas (Scope Negativo):** La historia respeta los "No Incluye" definidos en el Product Brief y en el Backlog del MVP.

---

## Dimensión 2: Atomicidad e Estándar INVEST

- [ ] **Independent (Independiente):** La HU no está acoplada transaccionalmente a otra historia en curso de forma que impida su prueba aislada.
- [ ] **Negotiable (Negociable):** La historia describe el qué y el para qué sin encasillar la implementación de ingeniería en piedra.
- [ ] **Valuable (Valiosa):** La narrativa **Como / Quiero / Para** expresa un beneficio de negocio medible para un actor del sistema, no un paso técnico.
- [ ] **Estimable (Estimable):** El alcance está lo suficientemente acotado como para que un equipo de desarrollo evalúe su esfuerzo.
- [ ] **Small (Atómica / Pequeña):** La HU aborda **una única interacción o transacción de negocio**. Si abarca múltiples flujos concurrentes (ej. catálogo + checkout + analítica), debe ser rechazada para su partición.
- [ ] **Testable (Verificable):** Cada Criterio de Aceptación puede transformarse inequívocamente en un caso de prueba binario (Pasa / Falla).

---

## Dimensión 3: Cobertura BDD y Criterios Gherkin

- [ ] **Sintaxis BDD Canónica:** Cada criterio sigue rigurosamente la formulación:
  `Dado [Contexto inicial precondición]`  
  `Cuando [Acción o evento disparador del usuario/sistema]`  
  `Entonces [Resultado observable, medible y verificable]`
- [ ] **Cobertura del Happy Path (Mínimo 1):** Especifica el flujo óptimo donde las precondiciones se satisfacen y el valor se entrega.
- [ ] **Cobertura de Sad Paths / Edge Cases (Mínimo 1 Obligatorio):** Modela explícitamente escenarios de fallo, tales como:
  - Datos de entrada inválidos, incompletos o fuera de rango.
  - Colisiones de concurrencia o recursos no disponibles.
  - Timeouts, cancelaciones anticipadas o estados inconsistentes.
- [ ] **Resultados Específicos:** El bloque `Entonces` evita ambigüedades como "el sistema funciona bien" o "muestra información adecuada"; debe detallar la respuesta exacta del sistema.

---

## Dimensión 4: Consistencia Lógica y No-Contradicción

- [ ] **Coherencia Interna:** Ningún Criterio de Aceptación contradice a otro dentro de la misma HU.
- [ ] **Coherencia con el PRD:** Ninguna regla estipulada en la HU anula una restricción estratégica del Product Brief (ej. mostrar precios cuando el PRD ordena expresamente ocultarlos).
- [ ] **Diagramación Coherente:** Si la HU incluye un diagrama Mermaid (`sequenceDiagram` o `flowchart`), los pasos del diagrama deben coincidir uno a uno con los flujos descritos en los Criterios de Aceptación.

---

## Dimensión 5: Separación de Responsabilidades (Negocio vs. Técnica)

- [ ] **Libre de Polución Técnica:** El cuerpo de la HU y sus Criterios de Aceptación no mencionan nombres de tablas de bases de datos, tipos de datos (`VARCHAR`, `INT`), endpoints REST (`POST /api/v1`), frameworks o directivas de infraestructura.
- [ ] **Comportamiento Funcional Puro:** Emplea lenguaje centrado en el usuario o en las capacidades observables del sistema (ej. "el sistema solicita confirmación" en lugar de "se renderiza el modal con z-index 999").

---

---

## Dimensión 6: Coexistencia con Ecosistema Preexistente (Modo Brownfield)
*(Aplica si existe el archivo `files/context/legacy_ecosystem.md`)*

- [ ] **No-Regresión Operativa:** La HU no contradice las máquinas de estado, reglas de negocio o limitaciones descritas en el archivo legacy.
- [ ] **Verificación en DoD:** La sección Definition of Done de la HU incluye formalmente el ítem de respeto y no-regresión contra el ecosistema preexistente.

---

## Matriz de Decisión Binaria

```
¿Existen alucinaciones de alcance sin etiquetar?   ──► SÍ ──► RECHAZADO (Opción A)
¿Falta al menos un Sad Path / Edge Case en Gherkin? ──► SÍ ──► RECHAZADO (Opción A)
¿La historia mezcla más de una transacción básica? ──► SÍ ──► RECHAZADO (Opción A)
¿Existe contradicción con el PRD o archivo legacy?  ──► SÍ ──► RECHAZADO (Opción A)
                    │
                    └──► NO a todo lo anterior: 100% de cumplimiento
                                │
                                └──► APROBADO (Opción B)
```


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]