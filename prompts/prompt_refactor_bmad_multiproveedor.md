# Prompt de refactorización BMAD/SDD multiproveedor

Actúa como arquitecto de software senior especializado en Python, patrones de diseño, SOLID, automatización CLI, Herdr, BMAD, Spec Kit y LLMOps.

## Contexto

Trabaja sobre el repositorio abierto, especialmente `start_agents.py`, `watcher_bmad.py`, `ux_routing.py`, `config_bmad.json`, perfiles `AGENTS.md`, skills y pruebas existentes. **Inspecciona primero el código real y la ayuda/versiones instaladas de Herdr, Claude Code, Codex CLI y Gemini CLI. No inventes flags, tipos `--kind`, subcomandos ni equivalencias entre proveedores.** Si no está instalado algún CLI, diseña su adaptador y pruebas con dobles, pero declara sus comandos pendientes de verificación y evita afirmar compatibilidad real.

## Objetivo

Refactoriza el sistema para asignar **proveedor y modelo por agente BMAD y por operación headless de Spec Kit**, mezclando Claude, Codex y Gemini dentro de una misma ejecución. Debe ser posible añadir un cuarto proveedor sin modificar la lógica de orquestación, routing BMAD, watcher ni flujo SDD (principio abierto/cerrado); solo registrar un adaptador y configurar su uso.

## Diagnóstico previo obligatorio

1. Mapea todas las invocaciones directas de `claude`, `herdr`, comandos de panel y comandos de skills, incluidas las ubicadas al final del watcher.
2. Identifica contratos públicos, rutas, configuración, formatos del tracker, tokens `@AGENTE:`, decisiones UX, flujo HITL, retrabajos, límites de iteración, git y estructura de pestañas.
3. Documenta los comandos reales soportados por las versiones instaladas y diferencias entre modo interactivo Herdr y ejecución headless. **No asumas que `herdr agent start --kind gemini` o `--kind codex` funcionan sin verificarlo.**
4. Detecta problemas de seguridad, idempotencia, estado, bloqueo, rutas Windows, codificación UTF-8, `shell=True`, falta de timeouts y fallos silenciados.
5. Presenta un plan breve de migración con riesgos antes de editar.

## Arquitectura exigida

Aplica estas responsabilidades, sin crear abstracciones vacías:

- `AIProvider` (Protocol o ABC): contrato tipado de capacidades y construcción/ejecución de operaciones compatibles. Distingue inicio interactivo, ejecución headless, instalación o resolución de skills, directivas, limpieza de contexto, reconocimiento de límites y normalización de errores. **No fuerces una interfaz idéntica para operaciones que un proveedor no soporta**: utiliza capacidades explícitas y errores `UnsupportedCapability`.
- `ClaudeProvider`, `CodexProvider`, `GeminiProvider`: Strategy + Adapter para traducir configuración neutral a argumentos, entorno, prompts y semántica nativa de cada CLI. No interpolar comandos shell ni reutilizar flags exclusivos de Claude en otros proveedores.
- `ProviderRegistry` y `ProviderFactory`: resuelven el proveedor configurado, validan identificadores y permiten registrar nuevos adaptadores sin editar orquestadores. Evita condicionales `if provider == ...` repartidos por el código.
- `HerdrGateway`: único adaptador responsable de crear/listar/enfocar pestañas, dividir/renombrar/leer paneles, arrancar agentes, enviar instrucciones y consultar estados; verificar compatibilidad del proveedor con Herdr y separar estado de Herdr del estado del CLI.
- `CommandRunner`: ejecuta argumentos como listas con `subprocess.run` o `Popen` según corresponda; maneja timeout, `cwd`, variables de entorno permitidas, retorno, stdout/stderr, UTF-8 Windows, errores y logging seguro. Nunca usar `shell=True` con texto de instrucciones o entradas no confiables.
- `AgentLauncher` / `FleetOrchestrator`: orquesta paneles y perfiles sin conocer comandos de proveedor.
- `AgentDispatcher` / `WatcherService`: mantiene routing, handoffs, vigilancia, límites y reintentos sin conocer flags concretos.
- `SpecKitExecutor`: resuelve proveedor por operación (`specify`, `clarify`, `plan`, `tasks`, `analyze`, `converge`, `implement`) y ejecuta skills equivalentes **solo si su instalación y semántica están verificadas**. Si una skill no existe o no es equivalente en el proveedor seleccionado, detener con error explicativo; no simular éxito.
- `SessionManager`: limpieza o rotación de contexto según capacidades reales del proveedor; nunca asumir que `/clear` funciona universalmente.
- Configuración validada con dataclasses o Pydantic, evitando dependencias innecesarias.

Usa SOLID: SRP por módulo, OCP mediante registro de proveedores, LSP con contratos comprobables, ISP por capacidades y DIP mediante inyección de dependencias. Prefiere composición a herencia profunda. Mantén un único origen de verdad para configuración.

## Configuración declarativa deseada

Diseña un esquema validado, por ejemplo `providers.yaml` o una sección compatible con `config_bmad.json`:

```yaml
schema_version: 1
defaults:
  provider: claude
  model: null  # null: modelo por defecto del CLI, sin inventar nombres
providers:
  claude: {executable: claude}
  codex: {executable: codex}
  gemini: {executable: gemini}
phases:
  M: {provider: claude}
  D: {provider: codex}
agents:
  business-storyteller: {provider: claude}
  business-analyst: {provider: gemini}
  solutions-architect: {provider: claude}
  qa-auto: {provider: codex}
speckit:
  specify: {provider: gemini}
  clarify: {provider: gemini}
  plan: {provider: claude}
  tasks: {provider: claude}
  analyze: {provider: gemini}
  converge: {provider: claude}
  implement: {provider: codex}
```

Esta configuración es **ilustrativa**, no implica soporte confirmado de cada combinación. Establece precedencia explícita: operación/agente > fase > defaults; valida proveedores desconocidos, modelos, opciones y capacidades antes de arrancar. Permite perfiles de ejecución, esfuerzo y parámetros solo cuando sean compatibles con cada CLI. Nunca registrar credenciales en YAML ni logs.

## Compatibilidad y comportamiento

1. Conservar los nombres, rutas y puntos de entrada `start_agents.py` y `watcher_bmad.py` como wrappers finos si se mueven responsabilidades.
2. Mantener la organización de pestañas y agentes, el filtrado `agentes_omitidos()` y las decisiones `ux_routing`.
3. Preservar formato `documents/tracker_bmad.md`, tokens, autorías, compuertas HITL, flujo SDD, retrabajos, clasificación por capa y documentación viva.
4. Preservar aislamiento de perfiles y skills; verificar cómo se carga `AGENTS.md` y las instrucciones equivalentes en cada proveedor. No copiar indiscriminadamente instrucciones a ubicaciones incompatibles.
5. Separar el proceso interactivo de Herdr de los procesos headless de Spec Kit: son rutas de ejecución distintas con configuración potencialmente distinta.
6. Persistir correlación `agent_id`, `provider`, `model`, `pane_id`, `run_id`, fase, intento y estado, para reinicios y diagnósticos; no guardar prompts completos ni secretos por defecto.
7. Limitar tiempo, intentos, tamaño de salida, tokens/contexto cuando el CLI lo soporte, número de subprocesos y profundidad de reintentos. Evitar loops y duplicación de handoffs. Si un límite de tokens no es configurable, documentar la limitación y usar límites observables alternativos.
8. No reintentar ciegamente tareas no idempotentes ni cambiar de proveedor automáticamente sin política explícita y validación del estado parcial.
9. Nunca habilitar por defecto bypass de permisos o ejecución irrestricta; mantener un modo seguro configurable, con confirmación explícita para operaciones destructivas.
10. Preservar los archivos y cambios de trabajo existentes; no borrar pestañas/sesiones previas sin una política explícita y comprobación de pertenencia al proyecto.

## Plan de implementación

**Etapa 1 — Caracterización:** crea pruebas sobre el comportamiento actual antes de refactorizar. Identifica invariantes y establece baseline.

**Etapa 2 — Infraestructura:** extrae `CommandRunner`, `HerdrGateway`, tipos de resultado, excepciones, validación de configuración y registro de proveedores.

**Etapa 3 — Adaptadores:** implementa Claude, Codex y Gemini para las capacidades verificadas. Usa una matriz de compatibilidad por CLI y modo. Las operaciones no verificadas deben fallar de forma explícita.

**Etapa 4 — Lanzador:** migra `start_agents.py` para resolver el proveedor por agente sin cambiar la lógica de tabs, panes, perfiles o exclusiones.

**Etapa 5 — Watcher:** migra despacho, lectura de estados, recordatorios, cuotas, limpieza de sesiones y ejecución Spec Kit a servicios neutrales al proveedor.

**Etapa 6 — Pruebas:** incluye unit tests con mocks de procesos y Herdr, integración controlada opcional con CLI real, y pruebas de regresión de BMAD/SDD. Cubre mezclas de proveedores, precedencia de configuración, proveedor inexistente, CLI ausente, flags incompatibles, timeout, errores de cuota, UTF-8, rutas con espacios, restart, doble handoff, fallo parcial, HITL, retrabajo y limpieza segura. Añade prueba de extensión con un `FakeProvider` registrado externamente sin editar orquestadores.

**Etapa 7 — Documentación:** README de arquitectura, guía de migración, configuración de ejemplo, matriz de capacidades verificadas, comandos de ejecución y rollback.

## Criterios de aceptación

- [ ] Puedo cambiar el proveedor de un agente editando solo configuración.
- [ ] Dos agentes de la misma fase pueden usar proveedores distintos.
- [ ] `speckit.implement` puede elegir proveedor independiente del agente que lo disparó.
- [ ] Añadir `FakeProvider` o un proveedor futuro no requiere editar `start_agents.py`, `watcher_bmad.py` ni reglas BMAD.
- [ ] Se mantiene el flujo funcional del tracker, UX, HITL, retrabajos y Git.
- [ ] El código no contiene invocaciones directas a `claude`, `codex` o `gemini` fuera de adaptadores/configuración/tests.
- [ ] Ningún adaptador afirma capacidades no verificadas ni comparte flags incompatibles.
- [ ] Pruebas existentes y nuevas pasan; se reportan por separado las pruebas que requieren CLI real.
- [ ] Errores de arranque y ejecución no se registran como éxito.
- [ ] Se dispone de `--dry-run` que muestra proveedor, modelo y comando sanitizado sin ejecutar procesos.
- [ ] Hay guía de rollback y se puede restaurar la configuración previa.

## Entregables y reporte final

1. Código refactorizado con árbol de archivos final y justificación de responsabilidades.
2. Configuración de ejemplo realista y validada.
3. Matriz `proveedor × capacidad × modo (Herdr/headless)` con estado `verificado`, `no soportado` o `pendiente`.
4. Pruebas automatizadas y comandos para ejecutarlas.
5. Resumen de archivos cambiados, compatibilidad, riesgos pendientes y pasos manuales.
6. Demostración `--dry-run` de un escenario mixto: fase M con Claude, agente BA con Gemini, fase D con Codex.

**Forma de trabajo:** primero inspecciona y presenta diagnóstico/plan; luego implementa incrementalmente, ejecutando pruebas después de cada etapa. No reescribas todo de golpe. No elimines lógica BMAD/SDD por simplificación. No inventes compatibilidad ni declares éxito si hay fallos. Si necesitas una decisión humana sobre un cambio funcional, detente y explica las alternativas.
