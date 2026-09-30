# Plan de Implementación: Mapa de Specs (Ledger de Estado del Producto)

## 1. Resumen Ejecutivo
El **Mapa de Specs** nace para erradicar la pérdida de contexto y la alucinación arquitectónica en proyectos BMAD de larga duración. Actuará como un *Ledger* inmutable y base de datos en texto plano (`specs/README.md`) que rastrea el ciclo de vida, estado y dependencias de todas las especificaciones e Historias de Usuario (HUs). Esta fuente única de verdad permitirá a los agentes (especialmente `@BA` y `@SA`) inyectar contexto histórico preciso antes de generar nuevos diseños, asegurando continuidad estructural y coherencia de negocio a lo largo de las iteraciones.

## 2. Definición de la Estructura de Datos (`specs/README.md`)
El archivo utilizará una estructura tabular rígida en Markdown, complementada con un área de texto libre para documentar el grafo de dependencias o restricciones temporales.

```markdown
# 🗺️ Mapa de Specs (Product State Ledger)

> **Regla de Actualización:** Este archivo es el registro histórico del estado del producto. Las modificaciones a la tabla deben respetar estrictamente el formato Markdown para permitir su parseo automatizado.

| N° | Spec / Nombre | HU / Épica Origen | Qué aporta | Estado | Rama |
|----|---------------|-------------------|------------|--------|------|
| 01 | Autenticación JWT | Épica-01: Seguridad | Emisión y validación de tokens JWT para API | ACTIVE | main |
| 02 | Dashboard de Ventas | HU-04: Reporte Diario | Vistas consolidadas de transacciones diarias | IN-PROGRESS | feat/dashboard-ventas |
| 03 | Exportar CSV Antiguo | HU-02: Exportación | Motor legado de exportación | DEPRECATED-PARTIAL | N/A |

---

## 🔗 Notas de Relación entre Specs
* **Spec 02 (Dashboard)** depende directamente de la API protegida por **Spec 01 (Autenticación)**.
* **Spec 03 (CSV Antiguo)** está en proceso de deprecación; ninguna HU nueva debe utilizar su base de código, debe proponerse el nuevo motor de reportes.
```

### Glosario de Estados Permitidos (Diccionario Finito)
Para mantener el determinismo del *Ledger*, los agentes mutadores y lectores utilizarán estrictamente este conjunto cerrado de estados:
* **`ACTIVE`**: Funcionalidad probada y en producción. Es la fuente de verdad actual.
* **`IN-PROGRESS`**: Spec en diseño activo o en desarrollo.
* **`DRAFT` / `BACKLOG`**: Idea o requerimiento sin refinar; sin diseño técnico ni código asociado.
* **`BLOCKED`**: Avance detenido por falta de definiciones o dependencias externas.
* **`DEPRECATED`**: Funcionalidad completamente obsoleta o reemplazada. Estrictamente prohibido usarla como base.
* **`DEPRECATED-PARTIAL`**: Funcionalidad reemplazada solo parcialmente. Obligatorio consultar las *Notas de Relación* para identificar qué partes siguen vivas.

## 3. Matriz de Impacto en los Agentes
Para integrar este sistema de manera determinista y sin fricción en el ecosistema BMAD, se afectarán los siguientes componentes:

* **Nuevo Artefacto/Componente:** `skills/update-specs-map/SKILL.md`
  * **Rol:** Habilidad (Skill) reutilizable que detalla las instrucciones para leer, parsear, modificar celdas (ej. mutación de `IN-PROGRESS` a `ACTIVE`) y agregar nuevas filas a la tabla Markdown manteniendo intacta la alineación estructural.
* **Impacto en Agentes Lectores (Modificación de `.instructions.md`):**
  * `@BA` (Business Analyst): Obligatoriedad de ingesta de `specs/README.md` durante el análisis inicial. Debe asegurarse de que las nuevas HUs respeten el estado de componentes existentes (`ACTIVE` vs `DEPRECATED`).
  * `@SA` (Solutions Architect): Ingesta obligatoria para alinear los nuevos diseños técnicos con la topología ya documentada en el *Ledger*.
* **Impacto en Agentes Escritores (Modificación de `.instructions.md`):**
  * `@PM` (Product Manager) y `@QT` (QA Tech):
    * Se dotará a estos agentes de la habilidad `update-specs-map`.
    * **Trigger de PM:** Actualiza o inserta el estado a `IN-PROGRESS` cuando una HU inicia diseño o entra al pipeline.
    * **Trigger de QT:** Actualiza el estado a `ACTIVE` como auditoría final de compilación y cruzando el diseño contra el *Ledger* previo a habilitar la fase de desarrollo/implementación.

## 4. Plan de Ejecución Paso a Paso
Lista de tareas preparadas para ejecución secuencial. Esperando confirmación para proceder con el Paso 1.

* [ ] **Paso 1: Generar Estructura Base.** Crear el directorio `specs/` (si no existe) y el archivo base `specs/README.md` con la plantilla inicial.
* [ ] **Paso 2: Desarrollar Skill de Manipulación.** Crear el archivo `skills/update-specs-map/SKILL.md` definiendo el protocolo exacto de manipulación de la tabla Markdown.
* [ ] **Paso 3: Adaptar Ingesta (Fase Diseño).** Inyectar la directiva de lectura del Mapa de Specs en los archivos de instrucción correspondientes a `@BA` y `@SA`.
* [ ] **Paso 4: Habilitar Modificación de Estados.** Enseñar el uso de la nueva Skill a `@PM` y `@QT` mediante actualización de sus instrucciones, estableciendo reglas claras de cuándo modificar los estados.
