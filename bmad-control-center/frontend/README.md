# Dashboard BMAD: frontend

Consola Nuxt 3 / Vue 3 con PrimeVue, Tailwind, Markdown y Mermaid. Muestra identidad del proyecto, etapas BMAD, compuertas humanas, entregables, eventos y telemetría Git. HTTP y WebSocket se configuran para la misma API.

## Conexión y ejecución

Desde la raíz del motor, tras instalar las dependencias de [SETUP](../../SETUP.md):

```powershell
$env:VITE_BMAD_API_BASE = 'http://localhost:8001/api/v1'
npm --prefix bmad-control-center/frontend run dev -- --port 3000
```

`services/api_client.ts` lee `VITE_BMAD_API_BASE`; el valor predeterminado es `http://localhost:8000/api/v1`. La URL WebSocket se deriva de esa base y termina en `/ws/v1/events`. Define la variable antes de compilar y reinicia o recompila para cambiar backend. Comprueba `/api/v1/project` antes de operar las compuertas.

Un backend se fija a un workspace por proceso. Para varios proyectos, usa APIs y frontends con puertos distintos. La configuración CORS implementada se describe en el [backend](../backend/README.md).

## Estructura

| Ruta | Uso |
|---|---|
| `pages/index.vue` | Registro y selección visible del proyecto; estado vacío |
| `components/WorkspaceDashboard.vue` | Paneles del proyecto seleccionado |
| `components/` | Gates, workflow, artefactos, observabilidad y Git |
| `composables/useTrackerWebsocket.ts` | Reconexión y actualización por eventos |
| `composables/useSafeMermaid.ts` | Renderizado y contención de errores de diagramas |
| `services/api_client.ts` | Peticiones HTTP, contratos y cliente WebSocket |
| `assets/css/main.css`, `tailwind.config.js`, `plugins/` | Estilos y componentes visuales |
| `tests/`, `vitest.config.ts` | Pruebas Vue con happy-dom |

## Compilación y pruebas

Los scripts están declarados en [package.json](package.json):

```powershell
npm --prefix bmad-control-center/frontend test
npm --prefix bmad-control-center/frontend run build
npm --prefix bmad-control-center/frontend run generate
npm --prefix bmad-control-center/frontend run preview
```

`postinstall` prepara Nuxt al instalar dependencias. El script test usa carga nativa de configuración TypeScript y workers en threads para evitar procesos de empaquetado del config en Windows. Requiere una versión de Node con soporte de TypeScript nativo (22.18 o posterior) y las dependencias de desarrollo instaladas.

Sin proyecto seleccionado, la consola muestra el registro y las instrucciones de conexión.
El botón Actualizar proyectos consulta de nuevo `/project` y `/projects`. Los paneles,
las peticiones de artefactos y el WebSocket solo arrancan al recibir un proyecto seleccionado.
