---
name: update-specs-map
description: Habilidad determinista para actualizar el Mapa de Specs (Ledger) en specs/README.md sin romper la estructura de la tabla Markdown.
---

# CONTEXTO
Eres responsable de actualizar el archivo `specs/README.md` (Product State Ledger). Este archivo contiene una tabla Markdown que actúa como la única fuente de verdad sobre el estado de cada especificación (Spec) o Historia de Usuario (HU) en el proyecto.

# INSTRUCCIONES ESTRICTAS DE MANIPULACIÓN
1. **Regla de Cero Destrucción:** Nunca sobrescribas el archivo completo a menos que estés absolutamente seguro. Prefiere manipular las filas específicas usando una herramienta de reemplazo de contenido exacto (ej. `replace_file_content`) sobre la tabla.
2. **Uso de Herramientas:** Utiliza herramientas de lectura (ej. `view_file` o `read_file`) para ver el estado actual de la tabla y luego herramientas de edición estructurada para cambiar la celda de Estado.
3. **Formatos de Fila:** 
   El formato estricto de la tabla es:
   `| N° | Épica Origen | Nombre spec / HU | Qué aporta | Estado | Rama |` (el mismo orden de columnas de `specs/README.md` y de la constitución). Una fila `BACKLOG` aún sin rama lleva `—` en *Rama*; puedes agregar varias filas nuevas seguidas, cada una con su `N°` consecutivo
4. **Estados Permitidos (GLOSARIO ESTRICTO):** Solo puedes ingresar uno de los siguientes valores exactos en la columna `Estado`:
   - `ACTIVE`
   - `IN-PROGRESS`
   - `READY-FOR-DEV`
   - `DRAFT` / `BACKLOG`
   - `BLOCKED`
   - `DEPRECATED`
   - `DEPRECATED-PARTIAL`
5. **Generación de ID (N°):** Si vas a agregar una nueva Spec, el número (N°) debe ser secuencial de 3 dígitos basado en el último registro (ej. `001`, `002`, `003`...).

# FLUJO DE TRABAJO (ALGORITMO)
1. Lee `specs/README.md` para extraer la tabla y la sección de "Notas de Relación".
2. Verifica si la Spec ya existe:
   - Si existe y solo cambia el estado: Modifica únicamente la celda de `Estado` usando un replace exacto en la fila correspondiente.
   - Si es nueva: Agrega la nueva fila **inmediatamente después de la última fila de la tabla** (la última línea que empieza con `| 0`), NUNCA al final del archivo: tras la tabla hay otras secciones (`---`, "Notas de Relación") y una fila escrita después de ellas queda fuera de la tabla y los parsers no la ven. Respeta los delimitadores de columna `|` y genera el siguiente `N°` secuencial. Si agregas varias filas seguidas, insértalas todas juntas en ese mismo punto, sin líneas en blanco entre ellas.
3. Si la nueva spec afecta o depreca a una anterior, añade un bullet point explicativo en la sección "Notas de Relación entre Specs".
4. Usa las herramientas de edición de archivos de tu entorno para guardar los cambios y valida con una lectura posterior que la tabla no se haya corrompido y que **todas** las filas (también las nuevas) sigan contiguas, sin ninguna línea en blanco ni sección entre ellas.

