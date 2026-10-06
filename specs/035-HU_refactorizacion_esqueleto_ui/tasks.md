---

description: "Lista de tareas para la HU 035 — Refactorización de Esqueleto UI (Layout de Aplicación y Tipografía Global)"
---

# Tasks: Refactorización de Esqueleto UI — Layout de Aplicación y Tipografía Global

**Input**: Documentos de diseño en `/specs/035-HU_refactorizacion_esqueleto_ui/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ui-shell-contract.md, quickstart.md

**Tests**: Incluidos. El plan y el Tech Design (ADR-004/§TDD) exigen escribir primero la prueba Jest que falla (Task-UI-10) y la HU exige tests en verde (FR-013).

**Organization**: Tareas agrupadas por historia de usuario. Todas las rutas son relativas a la raíz del repositorio y llevan el prefijo `app/frontend/` (constitución). **No se toca** `app/backend/**`, `app/frontend/src/app/features/**` ni `app/template-primeng/**`.

## Format: `[ID] [P?] [Story] Descripción`

- **[P]**: Puede ejecutarse en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: Historia a la que pertenece (US1..US5)
- Restricciones transversales: sin `.scss`/CSS propio de color, borde, sombra o tipografía; sin `::ng-deep` ni `!important`; sin `localStorage`/`sessionStorage`; componentes standalone, `OnPush`, `@if/@for`; textos solo desde `LAYOUT_TEXTS`.

---

## Phase 1: Setup (Línea base)

**Purpose**: Confirmar el estado inicial del frontend antes de cambiar código

- [ ] T001 Ejecutar la línea base en `app/frontend`: `npm test` y `npm run build` deben terminar en verde; anotar el resultado como referencia de FR-013/SC-007
- [X] T002 [P] Verificar contra el `.d.ts` instalado de `primeng@22.1.2` las plantillas `#start`/`#end` de `p-menubar`, las entradas `MenuItem` (`routerLink`, `routerLinkActiveOptions`) de `p-menu` y las entradas `visible`/`modal`/`dismissible` de `p-drawer` en `app/frontend/node_modules/primeng/`; dejar la conclusión como comentario en la PR (sin crear archivos)

---

## Phase 2: Foundational (Prerrequisitos bloqueantes)

**Purpose**: Piezas base que consumen todas las historias (textos, modelo de navegación, ancho de viewport, perfil de usuario)

**⚠️ CRITICAL**: Ninguna historia puede empezar hasta completar esta fase

- [X] T003 [P] Crear `app/frontend/src/app/core/layout/layout.texts.ts` exportando `LAYOUT_TEXTS` tipado (`as const`) con: nombre de la app, etiquetas `Backlog`/`Sprints`/`Equipo`, `aria-label` del control `≡`, `aria-label` de la navegación, `profileFallback`, `logout` ("Cerrar sesión"), texto del pie, y título/mensaje de ruta inexistente (ADR-009)
- [X] T004 [P] Escribir primero `app/frontend/src/app/core/layout/layout-nav.spec.ts`: `NAV_ITEMS` tiene exactamente 3 entradas (`backlog` → `/backlog/nuevo`, `sprints` → `/sprints`, `equipos` → `/equipos`), cada ítem con `routerLinkActiveOptions: { exact: false }`; `resolveActiveModule(url)` devuelve `backlog` para `/backlog/nuevo`, `sprints` para `/sprints/42/elementos`, `equipos` para `/equipos/responsables/miembro` y `null` para `/zzz` (debe fallar antes de T006)
- [X] T005 [P] Escribir primero `app/frontend/src/app/core/layout/viewport.service.spec.ts`: `isWide` es `true` si `matchMedia('(min-width: 1024px)').matches`, se actualiza al emitir el evento `change`, remueve el listener al destruirse (`DestroyRef`) y vale `true` si `window.matchMedia` no existe (debe fallar antes de T007)
- [X] T006 Crear `app/frontend/src/app/core/layout/layout-nav.ts` con `NavModuleId = 'backlog' | 'sprints' | 'equipos'`, `NAV_ITEMS: MenuItem[]` (3 entradas, etiquetas de `LAYOUT_TEXTS`, `routerLinkActiveOptions: { exact: false }`) y `resolveActiveModule(url: string): NavModuleId | null` por primer segmento de la URL (depende de T003; satisface T004)
- [X] T007 Crear `app/frontend/src/app/core/layout/viewport.service.ts`: `@Injectable({ providedIn: 'root' })` con `readonly isWide: Signal<boolean>` según `matchMedia('(min-width: 1024px)')`, listener `change` limpiado vía `DestroyRef`, fallback `true` (satisface T005)
- [X] T008 [P] Ampliar el doble de Keycloak en `app/frontend/src/app/core/auth/auth.service.spec.ts` con `tokenParsed` y `logout`, y añadir pruebas: tras `init()` `userName()` es `tokenParsed.name`, si no `preferred_username`, si no `null`; `logout()` llama `keycloak.logout({ redirectUri: window.location.origin })` (debe fallar antes de T009)
- [X] T009 Ampliar `app/frontend/src/app/core/auth/auth.service.ts` de forma aditiva: `readonly userName` (signal de solo lectura en la API pública, `string | null`) cargado en `init()` desde `keycloak.tokenParsed` (`name` ⇒ `preferred_username` ⇒ `null`) y `logout(): Promise<void>`; no cambiar `isAuthenticated`, `token`, `login`, `reauthenticate`, `refreshToken` (satisface T008)

**Checkpoint**: Textos, navegación, viewport y perfil listos; las historias pueden comenzar

---

## Phase 3: User Story 1 - Ver todas las pantallas dentro de un esqueleto común (Priority: P1) 🎯 MVP

**Goal**: Todas las rutas autenticadas se muestran dentro del shell (barra superior con perfil/acciones, navegación lateral acoplada, contenido, pie); las URL existentes resuelven a la misma pantalla y una ruta inexistente mantiene el shell sin mostrar otra pantalla.

**Independent Test**: Con sesión, visitar las 9 URL del contrato de rutas: se ven las 4 zonas y la misma pantalla de antes; en `/zzz` el shell sigue visible con mensaje informativo y ninguna entrada activa (URL sin reescribir).

### Tests for User Story 1

> Escribir primero y verificar que FALLAN antes de implementar

- [X] T010 [P] [US1] Crear `app/frontend/src/app/core/layout/not-found/not-found.component.spec.ts`: renderiza un `p-message` `severity="info"` con el texto de `LAYOUT_TEXTS` y no contiene `router-outlet`
- [X] T011 [P] [US1] Crear `app/frontend/src/app/core/layout/layout.component.spec.ts` (con `RouterTestingHarness`, `AuthService` simulado): renderiza `header`, `nav` (con `aria-label`), `main`, `footer`; `p-menu` con exactamente 3 entradas; muestra `userName()` o `LAYOUT_TEXTS.profileFallback`; la opción "Cerrar sesión" invoca `AuthService.logout()`; marca como activa la entrada del módulo según la URL (`/sprints/42/elementos` ⇒ Sprints) y ninguna en una URL desconocida
- [X] T012 [P] [US1] Crear `app/frontend/src/app/app.routes.spec.ts` (`RouterTestingHarness`): cada una de las 9 URL del contrato (`''`→redirige a `/backlog/nuevo`, `/backlog/nuevo`, `/sprints`, `/sprints/nuevo`, `/sprints/:id/elementos`, `/sprints/:id`, `/equipos`, `/equipos/roles`, `/equipos/responsables`, `/equipos/responsables/miembro`) resuelve a su componente con su `data` original; `/zzz` activa `NotFoundComponent` dentro del shell sin redirigir; sin sesión `authGuard` bloquea y el shell no se activa

### Implementation for User Story 1

- [X] T013 [P] [US1] Crear `app/frontend/src/app/core/layout/not-found/not-found.component.ts` y `not-found.component.html`: standalone/`OnPush`, `<p-message severity="info">` con texto de `LAYOUT_TEXTS` (ADR-008)
- [X] T014 [US1] Crear `app/frontend/src/app/core/layout/layout.component.ts` (standalone, `OnPush`; imports `RouterOutlet`, `Menubar`, `Menu`, `Button`/`Menu` emergente de perfil; inyecta `AuthService`, `Router`, `ViewportService`): señal `activeModule = computed` desde `NavigationEnd` con `toSignal` + `resolveActiveModule`, `userName`, `navOpen = signal(viewport.isWide())`, y acción de logout (depende de T006, T007, T009)
- [X] T015 [US1] Crear `app/frontend/src/app/core/layout/layout.component.html`: `<header>` con `p-menubar` (nombre de la app a la izquierda; perfil con menú emergente "Cerrar sesión" a la derecha en `#end`), contenedor `min-h-screen flex flex-col` con `<aside class="w-64">` + `<nav [attr.aria-label]>` + `<p-menu [model]="NAV_ITEMS">` en modo acoplado, `<main>` con `<router-outlet />` y `<footer>` con el texto de `LAYOUT_TEXTS`; sin clases PrimeFlex, sin estilos propios (depende de T014)
- [X] T016 [US1] Reescribir `app/frontend/src/app/app.routes.ts`: mantener primero `{ path: '', pathMatch: 'full', redirectTo: 'backlog/nuevo' }`; luego ruta padre `{ path: '', canActivateChild: [authGuard], loadComponent: LayoutComponent, children: [...] }` con las rutas `backlog/nuevo`, `sprints` (con `providers: [MessageService]`, hijas `''`, `nuevo`, `:id/elementos` antes de `:id`), `equipos` (con `providers: [MessageService]` y `data` de `tab`/`view` idénticos) y, última, `{ path: '**', loadComponent: NotFoundComponent }` (sin `redirectTo`); eliminar los `canActivate` individuales y conservar `path`, `data`, `providers` y `loadComponent` originales (depende de T013, T015)
- [X] T017 [US1] Ejecutar `npm test` en `app/frontend` y corregir hasta que T010–T012 y las specs existentes de `features/**` pasen sin modificar `features/**`

**Checkpoint**: US1 funcional y verificable de forma independiente (MVP)

---

## Phase 4: User Story 2 - Usar el esqueleto con ancho reducido o navegación colapsada (Priority: P2)

**Goal**: A < 1024 px la navegación arranca colapsada y se abre como `p-drawer`; el control `≡` siempre visible alterna la navegación; el contenido no desborda a 768 px.

**Independent Test**: A 768 px la navegación está cerrada, `≡` es visible, no hay desplazamiento horizontal y `≡` abre el drawer con las 3 entradas; a 1920 px `≡` colapsa/expande el aside.

### Tests for User Story 2

- [X] T018 [US2] Ampliar `app/frontend/src/app/core/layout/layout.component.spec.ts` (con `ViewportService` simulado): ancho amplio ⇒ `aside` visible y sin drawer; ancho reducido ⇒ `navOpen` inicia en `false` y no hay drawer visible; `≡` alterna `navOpen`; en modo capa, seleccionar una entrada o cerrar el drawer pone `navOpen = false`; al cruzar el umbral `navOpen` se reinicia a `isWide`; el drawer devuelve el foco a `≡` al cerrar y enfoca la primera entrada al abrir (si PrimeNG no lo hace, el test debe fallar para exigir T020)

### Implementation for User Story 2

- [X] T019 [US2] En `app/frontend/src/app/core/layout/layout.component.ts` añadir `toggleNav()`, `effect`/`computed` que reinicia `navOpen` a `viewport.isWide()` al cruzar el umbral (descarta la elección manual, sin persistencia) y `closeNav()` para selección de entrada/cierre del drawer
- [X] T020 [US2] En `app/frontend/src/app/core/layout/layout.component.html` añadir en `#start` de `p-menubar` el botón `≡` (`p-button` icono `pi pi-bars`, `[attr.aria-label]` de `LAYOUT_TEXTS`, `[attr.aria-expanded]`), mostrar el `aside` solo si `viewport.isWide() && navOpen()` y renderizar el `p-menu` dentro de `<p-drawer [(visible)]="navOpen" [modal]="true" [dismissible]="true">` si `!viewport.isWide()`; si T018 demuestra que PrimeNG no gestiona el foco, enfocar la primera entrada y devolver el foco a `≡` con `afterNextRender`, sin CSS propio (ADR-004)
- [ ] T021 [US2] Verificar con `npm start` a 768 px y 1920 px: sin desplazamiento horizontal, `≡` abre/cierra, Escape y máscara cierran el drawer; los diálogos de registro de miembro y asignación a Sprint se muestran sobre el shell sin alterarlo (Task-UI-08, sin código nuevo)

**Checkpoint**: US1 y US2 funcionan de forma independiente

---

## Phase 5: User Story 3 - Contenido con medidas uniformes en todas las pantallas (Priority: P2)

**Goal**: El área de contenido mide como máximo 1280 px, centrada, con 1.5 rem de padding, definido una sola vez en el shell.

**Independent Test**: A 1920 px, `main` mide ≤ 1280 px, centrado, padding 1.5 rem en las 8 pantallas.

- [X] T022 [US3] Ampliar `app/frontend/src/app/core/layout/layout.component.spec.ts`: el contenedor de `<router-outlet />` tiene exactamente las clases `max-w-7xl mx-auto p-6` y ese conjunto aparece una sola vez en la plantilla del shell
- [X] T023 [US3] En `app/frontend/src/app/core/layout/layout.component.html` aplicar `class="max-w-7xl mx-auto p-6"` al contenedor del contenido (`<main>`), dentro de una zona `flex-1 min-w-0` para evitar desborde horizontal (Task-UI-06)
- [X] T024 [US3] Verificar con `Grep` que ninguna pantalla de `app/frontend/src/app/features/**` declara `max-w-*`, `mx-auto` ni padding de página en su raíz introducidos por esta HU (solo lectura; no modificar `features/**`; si ya existían, anotarlos como hallazgo para la HU derivada)

**Checkpoint**: Medidas uniformes verificadas

---

## Phase 6: User Story 4 - Tipografía base uniforme (Priority: P2)

**Goal**: Exactamente una declaración global de `font-family` y de margen de `body`, en `styles.css`, con fuente sans-serif del sistema y compuertas automáticas que lo garanticen.

**Independent Test**: `npm run lint:primeng` pasa; buscar `font-family` en `app/frontend/src` da una única coincidencia, en `styles.css`.

- [X] T025 [P] [US4] Añadir al final de `app/frontend/src/styles.css`, sin capa, la única regla `body { margin: 0; font-family: var(--font-sans); }` (ADR-006); no añadir `@font-face` ni fuentes externas
- [X] T026 [US4] Extender `app/frontend/scripts/lint-primeng.mjs` (ADR-010) con reglas globales sobre `src/`: (a) más de una declaración de `font-family` en `.css/.scss/.html/.ts` ⇒ violación, (b) más de una regla de margen de `body`, (c) `::ng-deep`, `!important` y `ed-grid` en `.css/.scss/.html/.ts`, (d) imports `primeng/dropdown` y `primeng/calendar`; excluir comentarios y documentar en el script que no deben escribirse `font-family` en comentarios (depende de T025)
- [X] T027 [US4] Ejecutar `npm run lint:primeng` en `app/frontend`: debe terminar sin violaciones; comprobar que introducir temporalmente una segunda `font-family` o un `::ng-deep` hace fallar el lint y revertir el cambio de prueba

**Checkpoint**: Tipografía global verificada y protegida por lint

---

## Phase 7: User Story 5 - Cierre verificado de la refactorización (Priority: P3)

**Goal**: Verificaciones de calidad en verde y 6 capturas de evidencia.

**Independent Test**: `lint:primeng`, `build` y `test` terminan sin errores y existen las 6 capturas.

- [X] T028 [US5] Ejecutar en `app/frontend` `npm run lint:primeng`, `npm run build` y `npm test`; los tres deben terminar con cero errores y la suite existente 100 % en verde (FR-013, SC-007)
- [ ] T029 [US5] Con la aplicación en ejecución y sesión activa, generar 6 capturas en `specs/035-HU_refactorizacion_esqueleto_ui/evidence/` con nombre `{modulo}-{ancho}.png` (`backlog`, `sprints`, `equipo` × `1920`, `768`): 1920 px con la navegación expandida y 768 px con la navegación colapsada, mostrando barra superior, navegación, contenido y pie (FR-014, SC-008, Task-UI-11)
- [X] T030 [US5] Confirmar con `git diff --stat` que no hay cambios en `app/backend/**`, `app/frontend/src/app/features/**` ni `app/template-primeng/**`, y que `Grep` de `font-family` en `app/frontend/src` devuelve una sola coincidencia (SC-006, FR-011, FR-012)

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T031 [P] Ejecutar la validación manual completa de `specs/035-HU_refactorizacion_esqueleto_ui/quickstart.md` §4 (esqueleto en 9 URL, ruta inexistente, navegación en 1–2 clics, foco con teclado, diálogos) y registrar el resultado
- [X] T032 [P] Revisar que `app/frontend/src/app/core/layout/` no contiene `.scss`, `::ng-deep`, `!important`, literales de texto fuera de `layout.texts.ts` ni `localStorage`/`sessionStorage`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias
- **Foundational (Phase 2)**: depende de Setup; BLOQUEA todas las historias
- **US1 (P1)**: depende de Foundational
- **US2 (P2)**, **US3 (P2)**: dependen de US1 (editan `layout.component.ts|html|spec.ts`); entre sí son secuenciales por tocar los mismos archivos
- **US4 (P2)**: independiente del layout; puede ir en paralelo con US1–US3 tras Foundational (archivos `styles.css` y `lint-primeng.mjs`)
- **US5 (P3)**: depende de todas las anteriores
- **Polish**: al final

### Dentro de cada historia

- Pruebas primero (deben fallar) → implementación → verificación
- T003 → T006; T006/T007/T009 → T014 → T015 → T016

### Parallel Opportunities

- Foundational: T003, T004, T005, T008 en paralelo; luego T006, T007, T009
- US1: T010, T011, T012 en paralelo; T013 en paralelo con las pruebas
- US4 (T025) en paralelo con cualquier tarea de US1–US3

## Parallel Example: User Story 1

```text
Task: "Crear not-found.component.spec.ts en app/frontend/src/app/core/layout/not-found/"
Task: "Crear layout.component.spec.ts en app/frontend/src/app/core/layout/"
Task: "Crear app.routes.spec.ts en app/frontend/src/app/"
```

## Implementation Strategy

### MVP (solo US1)

1. Setup → Foundational → US1
2. **Parar y validar**: las 9 URL dentro del shell y `**` con `NotFoundComponent`
3. Demostrar

### Entrega incremental

1. + US2 (drawer y `≡`) → validar a 768 px
2. + US3 (contenedor 1280 px / 1.5 rem)
3. + US4 (tipografía y compuertas de lint)
4. + US5 (verificaciones y 6 capturas) → la HU puede pasar a ACTIVE

## Notes

- [P] = archivos distintos, sin dependencias pendientes
- No ejecutar comandos Git transaccionales (el Watcher controla el VCS)
- Escribir todo texto visible en español desde `LAYOUT_TEXTS`
- Detenerse en cada checkpoint para validar la historia
