# Codex CLI — Consolidación y depuración definitiva de documentación BMAD

## Rol y misión
Actúa como mantenedor principal del **framework BMAD multiworkspace**. Tu misión es **ejecutar directamente** una consolidación documental del repositorio actual: corregir, fusionar, reescribir y eliminar documentación redundante u obsoleta. **No entregues solo un diagnóstico, inventario o plan**. No crees carpetas de auditoría ni archivos de reporte.

El repositorio contiene el **framework/orquestador**, no una aplicación de negocio. Debe documentar el estado **real y actual** del runtime, watcher, agentes, Herdr, proveedores LLM, BMAD/SDD/Spec Kit, constituciones, workspaces y panel de control, solo en la medida en que existan en el código.

## Documentos de entrada obligatorios
Inspecciona en profundidad estos archivos, si existen, y sus enlaces:
- `ARCHITECTURE.md`
- `framework_bmad.md`
- `GUIDE.md`
- `INPUTS_POR_AGENTE.md`
- `README.md`
- `SETUP.md`

Busca además otros Markdown relacionados, archivos de configuración, entrypoints, tests y código fuente que permitan verificar las afirmaciones. **El código y los contratos realmente implementados prevalecen sobre la documentación desactualizada.** No inventes comandos, rutas, estados, capacidades ni interfaces.

## Resultado documental esperado
Establece una fuente única de verdad para cada tema. Como estructura inicial sugerida —ajústala solo si el repositorio demuestra que otra organización es mejor—:

1. **`README.md`**: qué es BMAD, funcionalidades reales, requisitos mínimos, inicio rápido verificable, enlaces a documentación, mapa de responsabilidades y un ejemplo breve de creación/selección de workspace. Evita duplicar páginas completas.
2. **`ARCHITECTURE.md`**: documento técnico canónico y completo sobre la arquitectura **del framework**. Debe incluir límites, componentes, flujos, estados, secuencias, datos, aislamiento y orquestación concurrente, respaldados por el código.
3. **`SETUP.md`**: instalación, dependencias, configuración de proveedores y modelos/effort, Herdr, variables de entorno, puesta en marcha y troubleshooting, con comandos reales, preferentemente PowerShell para Windows cuando aplique.
4. **`GUIDE.md`**: guía operacional para crear/inicializar workspaces Brownfield y Greenfield, arrancar/parar servicios y agentes, operar watcher y dashboard, y localizar resultados. Solo procedimientos existentes y verificados.
5. **`framework_bmad.md`**: integra sus secciones vigentes en el destino canónico correspondiente y **elimina el archivo si queda redundante**; actualiza todas las referencias.
6. **`INPUTS_POR_AGENTE.md`**: si describe contratos de entrada/salida y contexto específicos por rol que merecen mantenerse independientes, conviértelo en una referencia canónica concisa enlazada desde `GUIDE.md`/`ARCHITECTURE.md`. En caso contrario, integra el contenido vigente y **elimina el archivo redundante**. No lo conserves solo por su antigüedad.

Elimina otros documentos históricos, duplicados o incorrectos cuando sea seguro, sin destruir documentación única y vigente. **No uses la estrategia «referencia histórica conservada; no usar como instrucciones vigentes».** Reescribe, integra o elimina.

## Requisitos estrictos para `ARCHITECTURE.md`
Debe contener **diagramas Mermaid renderizables en GitHub**, acompañados de explicaciones breves, y referencias a módulos/rutas reales. Cubre como mínimo los siguientes aspectos, separando diagramas cuando la legibilidad lo exija:

### A. Arquitectura y componentes
- Diagrama de contexto: operador/CLI/dashboard, framework BMAD, proveedores y repositorios/workspaces.
- Diagrama de componentes: orquestador, watcher, registro de proyectos, contexto por workspace, gestor de agentes, adaptadores de proveedores, Herdr, configuración, estado, handoffs, dashboard, Spec Kit y artefactos **si efectivamente existen**. Representa dependencias y límites; no inventes componentes.
- Diagrama de estructura lógica de carpetas, distinguiendo framework compartido y recursos por proyecto; muestra rutas reales.
- Diagrama de flujo de datos/eventos y persistencia de estados, tracker, handoffs y artefactos.

### B. Flujos y estados
- Flowchart del ciclo de vida del proyecto: creación/registro, inicialización, configuración, ejecución, supervisión, finalización o recuperación, según lo implementado.
- Flowchart de BMAD + SDD y transiciones entre agentes/etapas; representa puntos de aprobación humana y validación.
- State diagram del ciclo de vida de un workspace/proyecto **si el runtime define estados**.
- State diagram de un agente o tarea y sus transiciones: pendiente, ejecutando, esperando, completado, error/reintento, **solo si corresponden a estados implementados**.
- State diagram de watcher/orquestador o flujo de handoffs si existe una máquina de estados verificable.

### C. Secuencias
- Sequence diagram desde el inicio de un proyecto hasta la ejecución de agentes y persistencia de resultados.
- Sequence diagram de handoff entre agentes y watcher/orquestador, incluyendo aprobaciones humanas cuando existan.
- Sequence diagram de consulta del dashboard y sus fuentes de datos; distingue polling, eventos o lectura directa según implementación.
- Sequence diagram de resolución de contexto: constitución global, constitución de proyecto, stack/arquitectura, ADRs y tarea; refleja **cómo se cargan realmente** y no una precedencia hipotética.

### D. Orquestación de uno y múltiples proyectos
Incluye **dos ejemplos diagramados**, con nombres ficticios y claramente identificados como ejemplos:
1. **Un proyecto activo:** operador → registro/selector → orquestador → agentes → watcher → artefactos de un workspace.
2. **Dos o más proyectos activos simultáneamente:** un framework compartido, workspaces aislados, procesos/sesiones/trackers/logs/artefactos separados; indica cómo se evita la contaminación cruzada y cómo se supervisan desde el dashboard. **No afirmes paralelismo efectivo si el código solo permite alternar entre proyectos**: en ese caso, representa el comportamiento actual y señala concisamente la limitación en el propio documento.

Para cada diagrama:
- Utiliza sintaxis Mermaid válida (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`, etc.).
- Evita nodos ilegibles, flechas sin significado y diagramas duplicados.
- Mantén nombres coherentes con el código y agrega una breve leyenda si hace falta.
- No atribuyas garantías de concurrencia, aislamiento, GitOps o seguridad que no estén respaldadas por la implementación.

## Separación framework/proyecto
- **No** reintroduzcas `tech-work-hub` como proyecto activo, ejemplo obligatorio ni dependencia del framework.
- **No** impongas Angular, .NET, PostgreSQL, PrimeNG u otro stack de aplicación como requisito del framework.
- Distingue constitución global de framework, constitución por proyecto, `tech-stack.md`, arquitectura de aplicación y ADRs.
- Para Brownfield, documenta el descubrimiento/verificación del stack existente; para Greenfield, documenta la definición/aprobación de stack, de acuerdo con las capacidades reales del sistema.
- Verifica soporte multiproveedor y `effort` antes de documentar comandos o valores.

## Ejecución obligatoria
1. Lee los seis documentos y verifica sus afirmaciones importantes contra código, configuración, tests y entrypoints.
2. Determina qué contenido vigente tiene un único destino canónico; **aplica los cambios inmediatamente**.
3. Reescribe `ARCHITECTURE.md` como documento técnico integral con los diagramas solicitados.
4. Reestructura `README.md`, `SETUP.md` y `GUIDE.md` para eliminar duplicaciones y mantener instrucciones utilizables.
5. Fusiona y **elimina** `framework_bmad.md` y/o `INPUTS_POR_AGENTE.md` cuando su contenido haya sido migrado y ya no justifiquen existir; haz lo mismo con otros duplicados seguros.
6. Actualiza enlaces relativos, referencias en `AGENTS.md`, prompts, guías y otras ubicaciones afectadas. **No rompas rutas consumidas por el runtime**: si algún archivo es leído programáticamente, adapta el consumidor o mantenlo como contrato operativo necesario.
7. Comprueba que no queden enlaces rotos, referencias a archivos eliminados, instrucciones contradictorias ni contenido específico del proyecto anterior en documentación canónica.
8. Valida los bloques Mermaid con una herramienta local disponible si existe; si no, revisa cuidadosamente su sintaxis sin instalar herramientas globales innecesarias.
9. Ejecuta las pruebas relevantes y corrige regresiones introducidas. No invoques proveedores LLM reales ni levantes la flota de agentes.

## Restricciones
- **No generes un informe de auditoría ni un plan en Markdown**; el entregable son los documentos editados y los archivos redundantes eliminados.
- No realices commits ni alteres el historial Git.
- No elimines código de producción, configuraciones operativas, datos de otros workspaces ni archivos fuera del repositorio.
- No inventes funcionalidades futuras como si ya existieran.
- No sacrifiques información técnica única y vigente por reducir el número de archivos.
- Si una capacidad solicitada no está implementada, documéntala explícitamente como limitación actual; no simules que funciona.
- No detengas el trabajo tras la inspección; ejecuta la consolidación completa.

## Criterios de aceptación
- `ARCHITECTURE.md` representa fielmente la arquitectura real e incluye diagramas de componentes, flujos, estados, secuencias y ejemplos de orquestación de 1 y 2+ proyectos.
- `README.md`, `SETUP.md` y `GUIDE.md` tienen responsabilidades claras, sin repetición sustancial.
- Archivos redundantes fueron fusionados y eliminados cuando procedía, con enlaces corregidos.
- El framework queda documentado como plataforma genérica multiworkspace, no como una aplicación concreta.
- Comandos, rutas y capacidades están contrastados con la implementación.
- Las validaciones y pruebas relevantes no presentan regresiones introducidas.

**Respuesta final breve en consola**: documentos modificados, documentos eliminados, diagramas añadidos, validaciones ejecutadas y limitaciones reales detectadas. No crees un archivo para esa respuesta.
