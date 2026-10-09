# EJECUCIÓN DIRECTA — Limpieza, consolidación y documentación vigente del ecosistema BMAD

## Rol y objetivo
Actúa como ingeniero principal de mantenimiento de repositorios Python y arquitecto del ecosistema BMAD + SDD + Herdr. **Ejecuta cambios reales en este repositorio**: elimina residuos, retira código sin uso, consolida duplicaciones y deja la documentación alineada con el código actual. **No entregues una auditoría, propuesta, inventario, plan, carpeta de informes ni lista de acciones para otro agente.** Tu resultado son archivos modificados/eliminados y validaciones ejecutadas.

Este repositorio ya recibió refactorizaciones de **multiworkspace**, **multiproveedor (Claude/Codex/Gemini)** y **configuración de esfuerzo (`effort`)**. Debes conservar esas capacidades, el flujo BMAD/SDD, la integración existente con Herdr, el watcher y el manejo de handoffs. **No implementes ahora nuevas mejoras de Herdr.**

## Reglas operativas
1. **Trabaja en el repositorio actual**; identifica su raíz mediante Git o archivos de proyecto. No presupongas rutas internas ni nombres de módulos.
2. **Ejecuta, no informes.** Inspecciona dependencias de forma interna y procede a editar, mover, fusionar o eliminar según corresponda. No pidas aprobación para cada eliminación ordinaria de residuos demostrablemente obsoletos.
3. **No crees archivos de auditoría** (`audit/`, `reports/`, `diagnostico*.md`, `cleanup-plan*.md`, `inventario*.md`, etc.) ni documentos de transición. No generes reportes intermedios en el repositorio.
4. **No uses frases de archivo histórico** como «Referencia histórica conservada; no usar como instrucciones vigentes», «deprecated, consultar documento nuevo» ni anexos de arquitectura antigua. Reescribe el contenido para reflejar el estado vigente o elimina el documento si es redundante y actualiza sus enlaces.
5. **Nunca borres datos de usuario o entregables de proyectos**: workspaces externos, código de `app/` generado para un proyecto, artefactos de `documents/` que sean entregables, handoffs vigentes, trackers/estado activo, secretos, credenciales o archivos no rastreados de origen incierto. Distingue el motor BMAD de los workspaces. Si un archivo de proyecto parece obsoleto, déjalo intacto.
6. **No elimines archivos solo por nombre o fecha.** Antes de retirar código o configuración, verifica referencias por imports, búsquedas de texto, entrypoints, CLI, tareas, tests, GitHub Actions, carga dinámica, prompts, watcher, Herdr, SpecKit y rutas configurables. Si la referencia no puede descartarse con seguridad, conserva el archivo y continúa con otros cambios.
7. **No alteres configuraciones reales de usuario ni datos sensibles.** No uses `git clean -fdx`, `rm -rf` indiscriminado, reseteos masivos, cambios de permisos, ni comandos destructivos fuera del repositorio. No ejecutes agentes reales, despliegues, instalaciones globales ni acciones de red que puedan generar costes sin necesidad.
8. Respeta modificaciones preexistentes: inspecciona `git status` antes de comenzar, no sobrescribas cambios ajenos y no hagas `git commit` ni `git push`.
9. Prioriza eliminar **duplicación de responsabilidades**, no solo archivos. Mantén una fuente canónica para resolución de rutas, configuración, providers, orquestación, watcher y estado. Si dos implementaciones están activas, migra sus consumidores a la implementación canónica antes de eliminar la redundante.
10. **No detengas el trabajo tras el análisis**. Usa un presupuesto razonable de contexto y realiza cambios verificables en esta misma ejecución. Si una operación concreta es insegura o está bloqueada, omítela, continúa con las demás y menciona únicamente ese bloqueo al final.

## Secuencia obligatoria de ejecución

### A. Inspección breve, sin producir informes
- Verifica `git status`, árbol del repositorio, documentación principal, scripts de arranque, tests y configuración.
- Localiza referencias a rutas anteriores (`utils`, `documents`, `app`), mecanismos multiworkspace, multiproveedor, `effort`, watcher, handoffs y Herdr.
- Identifica archivos auxiliares generados por agentes o auditorías anteriores, duplicados y documentación obsoleta. No confundas un archivo de entrada de un proyecto con un residuo.
- Toma decisiones y **aplica cambios inmediatamente**; no escribas un informe.

### B. Depuración física del repositorio
- Elimina archivos temporales o diagnósticos inequívocamente prescindibles generados durante refactorizaciones y auditorías anteriores, incluidos reportes intermedios sin consumidores y copias redundantes, después de comprobar sus referencias.
- Retira módulos, wrappers, scripts y configuraciones sustituidos que ya no se usan. Si tienen consumidores, migra primero esos consumidores.
- Limpia referencias rotas, imports obsoletos, entrypoints redundantes, comandos antiguos y archivos de documentación duplicados.
- Ajusta `.gitignore` únicamente para residuos reproducibles y evita ignorar entregables legítimos.
- Mantén intactos los archivos de trabajo y estado de cada proyecto.

### C. Consolidación funcional
- Centraliza la resolución de rutas en el mecanismo multiworkspace existente, evitando rutas absolutas o rutas implícitas al directorio del motor para salidas del proyecto.
- Conserva la selección de proveedor por fase/agente y la traducción de opciones `effort` según el proveedor, sin reescribir comportamientos que ya funcionan.
- Garantiza que watcher, handoffs, tracker, documentos, SpecKit y generación de aplicación sigan apuntando al workspace correcto.
- Evita duplicar lógica de lanzamiento, monitoreo o configuración. Migra consumidores antes de eliminar código.
- No introduzcas nuevas abstracciones innecesarias.

### D. Documentación: sustitución definitiva, no anotaciones históricas
- **Reescribe en su ubicación canónica** `README.md`, `ARCHITECTURE.md`, `GUIDE.md`, `AGENTS.md`, `framework_bmad.md`, `INPUTS_POR_AGENTE.md`, documentos operativos y README de módulos que existan y correspondan a funciones actuales.
- Mantén solo documentos que cumplan una finalidad distinta. Fusiona y elimina duplicados, actualizando todos los enlaces.
- Describe exclusivamente la arquitectura y comandos **que existan realmente en el código**: instalación, dependencias, configuración, creación/selección de workspace, estructura de salidas, inicio/parada, providers, `effort`, Herdr, watcher, handoffs, pruebas y resolución de problemas.
- Elimina secciones obsoletas por completo. No conserves texto histórico, notas de migración permanentes, párrafos tachados ni advertencias «no usar» para sustituir una actualización real.
- No inventes flags CLI, claves JSON, variables de entorno, rutas o compatibilidades. Si un comportamiento no está implementado, no lo documentes como disponible.
- Revisa referencias cruzadas y ejemplos para que apunten a los nombres y rutas actuales.

### E. Validación y corrección
- Ejecuta los tests relevantes disponibles, incluyendo configuración/providers, multiworkspace, watcher, orquestación y documentación/CLI cuando existan.
- Ejecuta dry-runs sin iniciar flotas reales. Comprueba rutas de salida, selección de proveedores y traducción de `effort`.
- Revisa que no queden imports o enlaces a archivos eliminados y que los ejemplos de comandos sean válidos.
- Si una prueba falla por tus cambios, corrige el problema y repite. Si existen fallos previos, distingue esos fallos de los introducidos; no los atribuyas sin evidencia.
- Confirma con `git diff --check`, `git status --short` y un resumen de cambios real.

## Criterios de aceptación obligatorios
- Hay **modificaciones y eliminaciones reales** cuando se identifican residuos o duplicaciones seguros; no se considera terminado un trabajo que solo genera reportes.
- No se crea una nueva carpeta de auditoría ni documentación de diagnóstico.
- Los documentos vigentes describen la arquitectura implementada y no contienen frases como «Referencia histórica conservada; no usar como instrucciones vigentes».
- Las referencias a archivos eliminados han sido corregidas.
- Se mantienen las capacidades multiworkspace, multiproveedor y `effort`.
- Los workspaces y entregables de usuario no se eliminan ni mezclan.
- Se ejecutan pruebas y se corrigen regresiones atribuibles a la limpieza.

## Formato de respuesta final (solo en el chat, no en archivos nuevos)
Al terminar, informa **brevemente**: (1) archivos eliminados; (2) archivos fusionados/modificados; (3) documentación reescrita; (4) pruebas ejecutadas y resultado; (5) bloqueos concretos si los hubo. No sustituyas la ejecución por esta respuesta. **No hagas commits.**

## Instrucción de arranque
Comienza ahora inspeccionando el estado del repositorio y ejecuta directamente la depuración y reescritura. No me devuelvas un plan para aprobación; aplica todas las modificaciones seguras dentro del alcance indicado.
