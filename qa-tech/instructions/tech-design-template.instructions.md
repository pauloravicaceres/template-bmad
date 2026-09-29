---
description: 'Usar EXCLUSIVAMENTE cuando el QT aprueba la arquitectura. Plantilla determinista para consolidar db_*.md, api_*.md y artefactos Spec Kit en el documento maestro tech-design_[nombre_corto].md con diagramación híbrida, matriz consolidada MADR y orden hacia /speckit.implement.'
applyTo: '**'
---

# Plantilla del Tech Design Maestro (Consolidado) — SDD Bridge

> Este documento unifica la visión de componentes, el MER, la API, los diagramas de arquitectura, valida la correspondencia con `spec.md` y `tasks.md`, y centraliza todos los ADRs generados bajo el formato MADR.

## Convención de Nombres de Archivo
`tech-design_[nombre_corto].md` (ej. `tech-design_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# TECH-DESIGN: {{TITULO_DEL_PROYECTO}}

- **Fecha de Compilación:** {{FECHA_ACTUAL}}
- **Auditor y Consolidador:** Agente QT Senior BMAD
- **Fuente SDD:** `spec.md` y `tasks.md` (GitHub Spec Kit)
- **Estado:** ✅ AUDITADO Y APROBADO (Auditoría Adversarial Exitosa)

---

## 1. Architecture Overview
*(Resumen de alto nivel del propósito técnico del sistema y su patrón de diseño principal, validado contra el plan.md y tasks.md).*

---

## 2. Components
*(Listado de los módulos o subsistemas lógicos que componen la solución y su relación con las tareas de tasks.md).*

---

## 3. Data Model
*(Integrar aquí el contenido completo y exacto de la sección Modelo Entidad-Relación y Diccionario de Datos extraído del archivo `db_*.md`, incluyendo la validación de no-orfandad frente al diseño UX y contratos de spec.md).*

---

## 4. Integrations
*(Integrar aquí el contenido completo y exacto de los Contratos REST/GraphQL y endpoints extraídos del archivo `api_*.md`).*

---

## 5. DIAGRAMAS DE ARQUITECTURA (Componentes, Secuencia, Despliegue)

**Regla de diagramación híbrida y resiliente (`archify` + `mermaid`):**

- **Escenario A: Con acceso a la skill `archify` (Modo Dual Enriquecido):**
  - Si la skill `archify` está disponible en tu entorno, debes generar **AMBOS** formatos para cada diagrama:
    1. Genera los artefactos interactivos de `archify` (archivos HTML interactivos y especificaciones JSON) en la carpeta `{{CARPETA_SALIDA_DIAGRAMAS}}`.
    2. Incrusta obligatoriamente debajo de las referencias a los artefactos el bloque nativo en sintaxis `mermaid` correspondiente, garantizando visualización inmediata tanto en visores Markdown estándar como en navegadores web interactivos.
  - **Formato canónico obligatorio por diagrama en Escenario A:**
    ### 5.X. [Título del Diagrama] (`[tipo: sequence | workflow | component]`)
    - 🌐 **Visor Interactivo HTML:** [`diagrams/[nombre].html`]({{CARPETA_SALIDA_DIAGRAMAS}}/[nombre].html)
    - 📄 **Especificación Fuente JSON:** [`diagrams/[nombre].[tipo].json`]({{CARPETA_SALIDA_DIAGRAMAS}}/[nombre].[tipo].json)
    - **Estado de Validación:** ✅ *Showcase Pass (N/N checks)*

    ```mermaid
    [código nativo de mermaid representando la arquitectura]
    ```

- **Escenario B: Sin acceso a la skill `archify` (Fallback Nativo - Cero Fricción):**
  - Si la skill no está disponible en tu entorno de herramientas, **no te detengas ni solicites instalación manual al humano**.
  - Aplica el principio de degradación elegante y genera los diagramas **únicamente en sintaxis nativa `mermaid`** directamente dentro de este documento, omitiendo los enlaces HTML/JSON e incluyendo esta nota al pie del bloque:
    > *Nota de Arquitectura: Diagrama generado exclusivamente con Mermaid por ausencia de dependencias externas. Para habilitar visores HTML interactivos, instale la skill en la raíz del proyecto (`npx skills add tt-a1i/archify -g`) y solicite la actualización de esta sección.*

- **Consistencia Inmutable:** Sea cual sea el escenario aplicado, ningún diagrama puede contradecir lo estipulado en los ADRs.

---

## 6. Technology Stack
*(Listado de las tecnologías, bases de datos y frameworks asumidos o explícitamente requeridos por la arquitectura).*

---

## 7. Architecture Decisions (ADRs - Matriz Consolidada MADR)
*(Consolidar en esta sección TODOS los ADRs generados por SA, DA y API, verificando que ninguno mantenga alternativas cosméticas y que todos reconozcan sus consecuencias reales).*

| ID | Título de la Decisión | Área | Estado | Trade-off / Costo Admitido |
|:---:|---|:---:|:---:|---|
| **ADR-001** | {{Stack y Hosting}} | Infraestructura (SA) | Aceptado / Aceptado (heredado) | {{Costo operativo / Curva de aprendizaje}} |
| **ADR-002** | {{Estrategia de Estado}} | Arquitectura (SA) | Aceptado / Aceptado (heredado) | {{Latencia de sincronización}} |
| **ADR-003** | {{Modelo de Persistencia}} | Datos (DA) | Aceptado / Aceptado (heredado) | {{Sobrecarga en índices de búsqueda}} |
| **ADR-004** | {{Protocolo de Integración}} | APIs (API) | Aceptado / Aceptado (heredado) | {{Payload overhead en red}} |

### ADR-001: {{Título del ADR original del SA}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...

### ADR-002: {{Título del ADR original del DA}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...

### ADR-003: {{Título del ADR original de la API}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...

---

## 8. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción para cerrar la rama GitOps y gatillar Spec Kit Implement hacia la Fase D)*

Obligatorio inyectar la macro de cierre de rama antes de gatillar Spec Kit, en líneas separadas:
```markdown
@WATCHER: GITOPS-MERGE-CLOSE feat/HU_{{nombre_corto}}
@SPEC-KIT: La arquitectura técnica consolidada ha sido verificada y aprobada en tech-design_{{nombre_corto}}.md. Gatillar /speckit.implement para despacho de tareas a la Fase D (@DEV-BACK, @DEV-FRONT, @DEVOPS).
```

---

### ⚠️ Directiva de Compilación para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `.specify/memory/constitution.md` o `.specify/memory/constitution.md`:
1. **Auditoría Cruzada de Restricciones Legacy:** Verificar que el modelo de persistencia (`db_*.md`) y los contratos de red (`api_*.md`) respeten estrictamente las tecnologías, protocolos y motores especificados en la constitución.
2. **Registro MADR Heredado:** Asegurar que las decisiones técnicas provenientes del sistema existente estén registradas con estado `Aceptado (heredado)`.
3. **Diagramas de Arquitectura (Sección 5):** Los diagramas de componentes y despliegue deben representar explícitamente la convivencia entre la nueva solución y la infraestructura heredada.
4. **Sección de Integraciones (Sección 4):** Consignar formalmente los mecanismos de adaptación y protocolos de interoperabilidad con el sistema preexistente.
5. **Si el archivo NO existe (Modo Greenfield):** Compila el Tech Design Document estándar consolidando el MER, la API y los ADRs sin precondiciones heredadas.

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
