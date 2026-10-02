# BMAD Control Center — Frontend

Consola reactiva para el Tech Lead desarrollada en **Vue 3** y **Nuxt 3** para el monitoreo en tiempo real del pipeline de agentes, observabilidad del ecosistema, exploración de entregables y telemetría de control de versiones Git (`002-HU_monitoreo_flujo_explorador_artefactos`, `003-HU_observabilidad_notificacion_eventos_ecosistema` y `004-HU_panel_telemetria_control_versiones_git`).

---

## Arquitectura del Sistema

El frontend opera bajo el patrón **Single Page Application (SPA)** desacoplada montada sobre **Nuxt 3** (`ssr: false`), comunicándose con el backend FastAPI mediante endpoints REST semánticos y un canal de streaming bidireccional sobre WebSockets multiplexado.

### Stack Tecnológico
- **Framework Core:** Vue 3 (Composition API exclusiva con `<script setup lang="ts">`) y Nuxt 3 (Nitro engine).
- **Componentes UI:** PrimeVue con tema Aura, ToastService (`useToast`) y PrimeIcons (`primeicons.css`).
- **Diseño y Maquetación:** Tailwind CSS v3 (clases utilitarias directas en templates, cero maquetación en bloques `<style scoped>`).
- **Procesamiento de Documentos:**
  - `marked.js` para parsing y renderizado de texto enriquecido Markdown con sanitización.
  - `mermaid.js` para renderizado dinámico de diagramas vectoriales en cliente.
- **Resiliencia y Error Boundary (ADR-008 / SC-003):** Encapsulamiento del compilador Mermaid en componentes aislados con bloques defensivos `try/catch`, previniendo caídas globales ante sintaxis inválida y garantizando la visualización del código fuente en un contenedor ámbar con opción de copiado.
- **Seguridad en Navegación y Sandboxing (ADR-007 / SC-002 / US5):**
  - Manejador defensivo de errores HTTP 403 (Path Traversal Guard).
  - Manejo de HTTP 404 con auto-sincronización y poda reactiva del árbol documental.
  - Manejo de HTTP 413/415 para archivos excesivos (>5 MB) o binarios no soportados mediante tarjetas de metadatos (`LargeFileMetadataCard.vue`).
  - Tarjeta de auditoría de seguridad perimetral (`PerimeterSecurityCard.vue`) que inspecciona raíces vigiladas (`files/`, `specs/`, `.specify/`) y contabiliza eventos fuera de perímetro descartados silenciosamente.
- **Canal Reactivo y Observabilidad WebSocket (HU-003):**
  - **Latidos Bidireccionales:** Protocolo Heartbeat PING/PONG cada 30 segundos con cálculo reactivo de latencia en milisegundos (`latencyMs`).
  - **Backoff Exponencial con Jitter:** Reconexión progresiva (1s, 2s, 4s, 8s, máx 10s + jitter aleatorio) ante desconexiones de red (`WebSocketStatusBadge.vue`) con botón de reconexión manual instantánea.
  - **Patrón State Catch-Up:** Hidratación REST concurrente inmediata (`GET /api/v1/workflow/status`, `GET /api/v1/artifacts/tree` y `GET /api/v1/git/status`) tras la reconexión exitosa para garantizar consistencia eventual instantánea sin pérdida de eventos durante la caída.
  - **Detección de Mutaciones de Artefactos:** Eventos `ARTIFACT_CHANGED` actualizan reactivamente el árbol de archivos con un badge temporal animado `[✨ NUEVO]` (5 segundos de expiración) y recarga en caliente instantánea del visor Markdown si el archivo activo ha mutado en disco.
  - **Amortiguación de Ráfagas I/O (Debounce 200ms):** Componente `DebounceIndicator.vue` que presenta un micro-badge flotante `[⚡ Buffer Debounce: N mutaciones (200ms)]` para informar ráfagas de escritura coalescidas.
  - **Stream de Auditoría en Vivo:** Componente `EventLogStream.vue` para inspeccionar el flujo de eventos WebSocket entrantes en tiempo real con filtrado y telemetría.
- **Telemetría y Control de Versiones Git (HU-004 / US1, US2, US3):**
  - **Operación Estrictamente de Solo Lectura (Strict Read-Only / ADR-013):** Interfaz libre de mutaciones destructivas en el repositorio Git; la consola inspecciona pasivamente sin exponer acciones de commit, stage o checkout.
  - **Resumen de Telemetría Git (`GitTelemetryOverview.vue`):** Despliegue de tarjetas de rama activa, último commit HEAD (hash corto, mensaje sanitizado, autor y timestamp relativo) y resumen cuantitativo del working tree.
  - **Clasificador Tripartito del Working Tree (`GitWorkingTreeClassifier.vue`):** Acordeones semánticos con códigos de color para cambios preparados (🟢 `Staged`), modificaciones en disco (🟡 `Unstaged`), archivos no rastreados (⚪ `Untracked`) y alertas de conflictos (🔴 `Merge Conflicts`).
  - **Línea de Tiempo Cronológica de Commits (`GitCommitTimeline.vue`):** Timeline vertical con nodos visuales para confirmaciones agénticas y panel lateral interactivo con metadatos completos y desglose de mutaciones de archivos.
  - **Resiliencia ante Contención `.git/index.lock` (`GitLockWarningBanner.vue` / ADR-015):** Detección defensiva de transacciones en curso con degradación elegante hacia el snapshot en memoria con bandera `is_syncing: true` (0% errores 5xx).
  - **Aislamiento de Entorno sin Repositorio (`GitRepoEmptyState.vue`):** Empty State orientativo ante respuestas HTTP 404 (`GIT_REPO_NOT_FOUND`) con instrucciones claras para inicializar Git (`git init && git add .`) sin afectar el resto de los módulos operativos.
  - **Alertas de Estados Especiales (`GitSpecialStateBadge.vue`):** Detección visual destacada para puntero `[DETACHED HEAD]`, `[CONFLICTO DE FUSIÓN]` y `[SINCRONIZANDO]`.
  - **Protección contra Diffs Masivos/Binarios (`GitBinaryDiffNotice.vue` / ADR-014):** Elisión segura de diffs para archivos binarios o cambios que excedan 1MB, preservando la memoria del navegador.
  - **Composable Reactivo (`useGitTelemetry.ts`):** Orquestación del estado Git, paginación a 50 commits y suscripción al evento WebSocket `GIT_STATUS_CHANGED`.
- **Pruebas y Control de Calidad:** Vitest + `@vue/test-utils` + `happy-dom` (71 pruebas unitarias automatizadas cubriendo componentes, composables y edge cases).

### Estructura de Directorios
```text
app/frontend/
├── components/
│   ├── artifacts/
│   │   ├── ArtifactEmptyState.vue       # Estado 5 UX: Etapas agénticas sin entregables físicos
│   │   ├── ArtifactErrorCard.vue        # Manejador visual para HTTP 404, 403, 413 y 415
│   │   ├── ArtifactTreeExplorer.vue     # Árbol jerárquico navegable con filtro y badge [✨ NUEVO]
│   │   ├── ArtifactViewer.vue           # Visor Markdown interactivo y header de metadatos
│   │   ├── MermaidErrorBoundary.vue     # Error Boundary y fallback ámbar con código crudo
│   │   └── TreeNodeItem.vue             # Nodo recursivo con auto-expansión, conteos y badge nuevo
│   ├── git/
│   │   ├── GitBinaryDiffNotice.vue      # Aviso de elisión de diffs binarios o > 1MB (CB-05)
│   │   ├── GitCommitTimeline.vue        # Timeline vertical de commits y panel de detalle
│   │   ├── GitLockWarningBanner.vue     # Banner no bloqueante ante contención .git/index.lock
│   │   ├── GitRepoEmptyState.vue        # Empty State instructivo ante GIT_REPO_NOT_FOUND
│   │   ├── GitSpecialStateBadge.vue     # Badges de alerta (Detached HEAD / Conflicto / Syncing)
│   │   ├── GitTelemetryOverview.vue     # Resumen: Rama activa, HEAD y estado del working tree
│   │   └── GitWorkingTreeClassifier.vue # Acordeón clasificador: Staged, Unstaged, Untracked
│   ├── observability/
│   │   ├── DebounceIndicator.vue        # Micro-badge de absorción de ráfagas I/O (200ms)
│   │   ├── EventLogStream.vue           # Auditoría visual en caliente del stream WS
│   │   ├── LargeFileMetadataCard.vue    # Tarjeta informativa para archivos > 5MB (Metadata-Only)
│   │   ├── PerimeterSecurityCard.vue    # Panel de Sandboxing y telemetría de eventos descartados
│   │   └── WebSocketStatusBadge.vue     # Indicador de estado WS, latencia y botón de reconexión
│   ├── ui/
│   │   ├── DirectoryTree.vue            # Wrapper de compatibilidad para árbol
│   │   ├── EmptyState.vue               # Wrapper de compatibilidad para empty state
│   │   ├── MarkdownViewer.vue           # Wrapper de compatibilidad para visor
│   │   └── WorkflowVisualizer.vue       # Wrapper de compatibilidad para stepper
│   ├── workflow/
│   │   └── WorkflowStepper.vue          # Barra de 8 etapas con pulso luminoso reactivo
│   └── GateControl.vue                  # Panel Human-in-the-Loop (HITL)
├── composables/
│   ├── useArtifacts.ts                  # Estado del árbol, badges temporales y hot-reload del visor
│   ├── useGitTelemetry.ts               # Estado reactivo de Git, paginación y sincronización WS
│   ├── useSafeMermaid.ts                # Compilación asíncrona segura de diagramas Mermaid
│   ├── useTrackerWebsocket.ts           # Cliente WS con backoff, jitter, latidos y State Catch-Up
│   └── useWorkflow.ts                   # Estado reactivo del pipeline y normalización de etapas
├── pages/
│   └── index.vue                        # Layout maestro con tabs para Artefactos y Telemetría Git
├── plugins/
│   └── primevue.ts                      # Inicialización de PrimeVue y ToastService
├── services/
│   └── api_client.ts                    # Cliente HTTP (fetch) con endpoints Git y perimeter status
├── types/
│   ├── artifacts.ts                     # Modelos para DirectoryNode, ArtifactContent, ApiError
│   ├── events.ts                        # Modelos para eventos WS multiplexados (GIT_STATUS_CHANGED)
│   ├── git.ts                           # Modelos para GitStatusResponse, GitCommitItem, etc.
│   ├── workflow.ts                      # Modelos para WorkflowState y WorkflowStageStep
│   └── index.ts                         # Re-exportador central de modelos TypeScript
└── tests/
    ├── ArtifactStates.spec.ts           # Pruebas de estados de selección, carga y errores
    ├── ArtifactTreeExplorer.spec.ts     # Pruebas de árbol, filtrado y badge [✨ NUEVO] (T014)
    ├── ArtifactViewer.spec.ts           # Pruebas de renderizado Markdown y metadatos
    ├── DebounceIndicator.spec.ts        # Pruebas de absorción de debounce y temporizador (T021)
    ├── GateControl.spec.ts              # Pruebas del módulo HITL
    ├── GitCommitTimeline.spec.ts        # Pruebas de timeline de commits y navegación (T014)
    ├── GitRepoEmptyState.spec.ts        # Pruebas de Empty State y banner index.lock (T019)
    ├── GitTelemetryOverview.spec.ts     # Pruebas de resumen de rama, HEAD y métricas (T009)
    ├── GitWorkingTreeClassifier.spec.ts # Pruebas de acordeón clasificador de área de trabajo
    ├── MermaidErrorBoundary.spec.ts     # Pruebas de captura de sintaxis y fallback (SC-003)
    ├── ObservabilityQA.spec.ts          # Pruebas de certificación de observabilidad
    ├── useGitTelemetry.spec.ts          # Pruebas del composable Git y sincronización WS (T006)
    ├── useTrackerWebsocket.spec.ts      # Pruebas de reconexión, latidos y State Catch-Up (T017)
    ├── WebSocketStatusBadge.spec.ts     # Pruebas de badges de estado y reconexión forzada (T007)
    └── WorkflowStepper.spec.ts          # Pruebas de transición de etapas y pulso activo (T009)
```

---

## Cómo Compilar y Ejecutar

### 1. Prerrequisitos
- **Node.js:** Versión 18.x LTS o 20.x LTS o superior.
- **npm:** Gestor de paquetes incluido con Node.js.

### 2. Instalación de Dependencias
Ejecuta en la terminal posicionado en la carpeta del frontend (`app/frontend`):
```bash
npm install
```

### 3. Levantar en Modo Desarrollo
Para iniciar el servidor de desarrollo local con recarga en caliente (HMR):
```bash
npm run dev
```
La aplicación se expondrá localmente en:
- `http://localhost:3000`
- `http://127.0.0.1:3000`

### 4. Ejecución de Pruebas Unitarias
Para ejecutar la suite completa de pruebas unitarias automatizadas con Vitest:
```bash
npx vitest run
```

Para ejecutar pruebas en modo continuo (watch):
```bash
npx vitest
```

### 5. Compilación para Producción
Para generar el empaquetado optimizado de producción (Nuxt Nitro build):
```bash
npm run build
```

### 6. Previsualización de Producción
Para probar el bundle generado localmente antes de desplegar:
```bash
npm run preview
```
