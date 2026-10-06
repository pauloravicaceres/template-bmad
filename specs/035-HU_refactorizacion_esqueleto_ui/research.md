# Research: Refactorización de Esqueleto UI

Fase 0. No quedaron marcadores `NEEDS CLARIFICATION`; los puntos abiertos del spec ("componente de navegación", RT-01..RT-09) y B-01..B-06 del UX los cierra el Tech Design del SA (`documents/solutions-architect/035-HU_refactorizacion_esqueleto_ui.md`). Aquí se consolidan las decisiones y la verificación contra `primeng@22.1.2` instalado.

## Decisiones

| # | Tema | Decisión | Rationale | Alternativas descartadas |
|---|---|---|---|---|
| D1 | Montaje del shell | Ruta padre `path: ''` con `LayoutComponent` y `canActivateChild: [authGuard]`; rutas actuales como hijas con los mismos `path`/`data`/`providers`/`loadComponent` (ADR-003) | Un solo punto de montaje; URL sin cambios (FR-004); toda pantalla futura nace dentro (FR-015) | Layout en `AppComponent` (se pinta sin sesión); layout por pantalla (toca 8 pantallas) |
| D2 | Navegación lateral | `p-menu` con `NAV_ITEMS`, en `aside` acoplado (≥ 1024 px) o en `p-drawer` modal (< 1024 px) (ADR-004) | Cero CSS propio; accesibilidad delegada a PrimeNG | Solo `p-drawer`; `aside` con `hidden`/`md:block` |
| D3 | Umbral y estado | `matchMedia('(min-width: 1024px)')` en `ViewportService`; `navOpen` en memoria; al cruzar el umbral se reinicia a `isWide` (ADR-005, Opción B del humano) | A 768 px arranca colapsada; capturas deterministas | Umbral 768 px (a 768 px quedaría expandida); `localStorage` (rechazado) |
| D4 | Módulo activo | `computed` sobre el primer segmento de la URL (`backlog`/`sprints`/`equipos`) desde `NavigationEnd` con `toSignal` | Cubre URL profundas y recarga | Estado duplicado en el shell |
| D5 | Tipografía | Una regla sin capa `body { margin: 0; font-family: var(--font-sans); }` en `styles.css` (ADR-006) | Una línea auditable; sin fuentes externas | `@layer base`; preset de PrimeNG o `index.html` |
| D6 | Perfil y acciones | `AuthService.userName` (signal) y `logout()` aditivos (ADR-007) | Mantiene aislado el token `KEYCLOAK` | Solo icono; leer Keycloak en el layout |
| D7 | Ruta inexistente | `**` como última hija del shell → `NotFoundComponent` con `p-message severity="info"` (ADR-008) | FR-005: el centro no muestra otra pantalla | Mantener la redirección; centro vacío |
| D8 | Textos | `LAYOUT_TEXTS` tipado en `layout.texts.ts` (ADR-009) | No hay infraestructura i18n; un solo archivo a migrar | `@angular/localize`; literales en plantillas |
| D9 | Compuertas | Reglas globales en `scripts/lint-primeng.mjs` (ADR-010) | CA-06.1/SC-006 reproducibles en CI | Verificación manual; prueba Jest sobre el FS |

## Verificación contra `primeng@22.1.2` (puntos obligatorios de ADR-004)

- **`p-menu` marca la entrada activa de un `routerLink`**: ✅ confirmado en `primeng-menu.mjs` (usa `routerLinkActive="p-menu-item-link-active"` con `routerLinkActiveOptions` por ítem). Implicación: para que `Backlog` quede activo en `/backlog/nuevo`, `Sprints` en `/sprints/42/elementos` y `Equipo` en todas las rutas `/equipos/**`, los ítems deben declarar `routerLinkActiveOptions: { exact: false }` (valor por defecto del componente). Se mantiene además el `computed` del módulo activo para pruebas deterministas y para `aria-current`.
- **`p-drawer` modal con Escape, máscara y trampa de foco**: ✅ confirmado (`closeOnEscape`, `dismissible`, `FocusTrapModule`).
- **Foco al abrir (primera entrada) y devolución a `≡` al cerrar**: ⚠️ **no confirmado por inspección del bundle**. Queda como verificación obligatoria en la implementación (prueba Jest + verificación manual); si PrimeNG no lo hace, se gestiona con `focus()` tras `afterNextRender`, sin CSS propio (ADR-004).
- **Plantillas `#start`/`#end` de `p-menubar`**: verificar al implementar contra el `.d.ts` instalado (ADR §11.2).

## Línea base del repositorio (auditoría)

- `app.routes.ts` actual: `backlog/nuevo`, `sprints/**` y `equipos/**` con `canActivate: [authGuard]` individual; raíz y `**` redirigen a `backlog/nuevo`.
- `AppComponent` es solo `<router-outlet />`; `styles.css` solo importa Tailwind, `tailwindcss-primeui` y PrimeIcons (sin `font-family` ni margen de `body`).
- `AuthService` expone `isAuthenticated`, `token`, `login`, `reauthenticate`, `refreshToken`; no hay `userName` ni `logout`.
- `lint-primeng.mjs` revisa solo `.html`.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Regresión de rutas al reubicarlas bajo el padre | `app.routes.spec.ts` valida cada URL del alcance contra su componente |
| `canActivateChild` no replica `canActivate` por hija | Prueba: sin sesión, `authGuard` bloquea y el shell no se activa |
| `MessageService` por ruta (`providers`) se pierde al anidar | Se conservan los `providers` en las rutas hijas `sprints` y `equipos` tal cual |
| Falsos positivos del lint por regex | Documentarlo en el script; no escribir `font-family` en comentarios |
| Umbral 1024 px sin confirmar por el humano | Es un único valor en `ViewportService`; punto abierto informativo |
