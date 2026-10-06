# Contrato de UI: Esqueleto de aplicación

Sin contratos HTTP ni de datos (FR-012). El feature expone **contratos de interfaz** hacia el usuario y hacia las pantallas futuras.

## 1. Contrato de rutas

El shell es la ruta padre `path: ''`, `canActivateChild: [authGuard]`. La redirección de la raíz queda fuera del shell, declarada antes.

| URL | Componente (sin cambios) | Dentro del shell |
|---|---|---|
| `''` | redirige a `backlog/nuevo` | n/a |
| `/backlog/nuevo` | `CreateBacklogItemComponent` | Sí |
| `/sprints` | `SprintListComponent` | Sí |
| `/sprints/nuevo` | `SprintFormComponent` | Sí |
| `/sprints/:id/elementos` | `SprintAssignedItemsComponent` | Sí |
| `/sprints/:id` | `SprintDetailComponent` | Sí |
| `/equipos`, `/equipos/roles`, `/equipos/responsables`, `/equipos/responsables/miembro` | `TeamPageComponent` (con su `data`) | Sí |
| cualquier otra | `NotFoundComponent` (sin redirección) | Sí |

Invariantes: mismos `path`, `data`, `providers` (`MessageService` en `sprints` y `equipos`) y `loadComponent` que antes; `/sprints/:id/elementos` se declara antes que `/sprints/:id`.

## 2. Contrato de zonas del shell

| Zona | Elemento | Contenido | Accesibilidad |
|---|---|---|---|
| Barra superior | `<header>` con `p-menubar` | Control `≡` (siempre visible), nombre de la app, perfil y menú emergente con **Cerrar sesión** a la derecha | `≡` con `aria-label` de `LAYOUT_TEXTS` |
| Navegación | `<nav aria-label>` con `p-menu` en `<aside w-64>` (≥ 1024 px, si `navOpen`) o `p-drawer` (< 1024 px) | Exactamente 3 entradas (`NAV_ITEMS`), entrada activa marcada | Escape, máscara y trampa de foco por `p-drawer` |
| Contenido | `<main class="max-w-7xl mx-auto p-6">` con `<router-outlet />` | Pantalla actual | Orden de foco: barra, navegación, contenido, pie |
| Pie | `<footer>` | Texto de `LAYOUT_TEXTS` | n/a |

Comportamiento: a 768 px la navegación arranca colapsada y el contenido ocupa el ancho sin desborde horizontal; a 1920 px el contenido mide ≤ 1280 px, centrado, con 1.5 rem de padding.

## 3. Contrato de extensión (FR-015)

Una pantalla nueva se agrega como **hija** del shell en `app.routes.ts` y, si es un módulo, una entrada más en `NAV_ITEMS`. No importa ni envuelve el layout, ni declara `max-w-*`, `mx-auto` o padding de página en su raíz.

## 4. Contrato de `AuthService` (aditivo)

```ts
readonly userName: Signal<string | null>;
logout(): Promise<void>;
```

Los miembros existentes (`isAuthenticated`, `token`, `login`, `reauthenticate`, `refreshToken`, `init`) no cambian.

## 5. Contrato de estilos globales

Única declaración permitida en `app/frontend/src/styles.css`: `body { margin: 0; font-family: var(--font-sans); }`. Prohibido en `src/`: otra `font-family`, otro margen de `body`, `::ng-deep`, `!important`, `ed-grid`, `primeng/dropdown`, `primeng/calendar`.
