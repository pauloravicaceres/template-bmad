# Data Model: Refactorización de Esqueleto UI

No se introducen entidades de negocio, datos persistentes ni cambios de esquema (FR-012). Lo siguiente es el modelo de **estado y tipos de cliente**, todo efímero y en memoria.

## Entidades

### Esqueleto de aplicación (`LayoutComponent`)

| Campo | Tipo | Origen | Notas |
|---|---|---|---|
| `navOpen` | `WritableSignal<boolean>` | Inicial: `viewport.isWide()` | Se escribe solo desde el control `≡`, selección de entrada en modo capa, cierre del drawer y cruce del umbral. No se persiste |
| `activeModule` | `Signal<NavModuleId \| null>` (`computed`) | Primer segmento de la URL del `Router` | `null` para rutas desconocidas |
| `userName` | `Signal<string \| null>` | `AuthService.userName` | Si es `null` se muestra `LAYOUT_TEXTS.profileFallback` |

### Entrada de navegación (`NAV_ITEMS: MenuItem[]`)

| Módulo (`id`) | Etiqueta (`LAYOUT_TEXTS`) | `routerLink` | Activa cuando el primer segmento es |
|---|---|---|---|
| `backlog` | Backlog | `/backlog/nuevo` | `backlog` |
| `sprints` | Sprints | `/sprints` | `sprints` |
| `equipos` | Equipo | `/equipos` | `equipos` |

Regla: exactamente 3 entradas; no se crean rutas nuevas.

### Estado de ancho (`ViewportService`)

| Campo | Tipo | Regla |
|---|---|---|
| `isWide` | `Signal<boolean>` | `matchMedia('(min-width: 1024px)').matches`; escucha `change`, limpia en `DestroyRef`; sin `matchMedia` ⇒ `true` |

### Perfil de usuario (ampliación de `AuthService`)

| Miembro | Tipo | Regla |
|---|---|---|
| `userName` | `WritableSignal<string \| null>` (readonly en la API pública) | `init()` lo carga desde `tokenParsed`: `name` ⇒ `preferred_username` ⇒ `null` |
| `logout()` | `Promise<void>` | `keycloak.logout({ redirectUri: window.location.origin })` |

### Evidencia de cierre

6 archivos `specs/035-HU_refactorizacion_esqueleto_ui/evidence/{modulo}-{ancho}.png` (`backlog|sprints|equipo` × `1920|768`) y resultado de `lint:primeng`, `build` y `test`.

## Transiciones de estado de `navOpen`

```text
Carga (ancho ≥ 1024) ──> abierta (aside acoplado)
Carga (ancho < 1024) ──> cerrada (sin drawer visible)
cerrada ──[control ≡]──> abierta        abierta ──[control ≡ en modo acoplado]──> cerrada
abierta (capa) ──[entrada | máscara | Escape | botón de cierre]──> cerrada
cualquier estado ──[cruce del umbral 1024 px]──> navOpen = isWide (la elección manual se descarta)
```

## Validaciones

- Una sola declaración de `font-family` y de margen de `body` en `src/` (compuerta de lint).
- El contenedor de contenido lleva `max-w-7xl mx-auto p-6` una sola vez, en el shell.
