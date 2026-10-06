# Quickstart: validación del Esqueleto UI

Guía de validación de extremo a extremo. Detalles en [contracts/ui-shell-contract.md](./contracts/ui-shell-contract.md) y [data-model.md](./data-model.md).

## Prerrequisitos

- Node con dependencias instaladas en `app/frontend` (`npm install`).
- Backend y Keycloak levantados con `docker-compose` (como hoy) para ver las pantallas con sesión.
- Rama `feat/035-HU_refactorizacion_esqueleto_ui`.

## 1. Línea base (antes de cambiar código)

```powershell
cd app/frontend
npm test
npm run build
```

Esperado: ambos en verde; esa es la referencia para FR-013 / SC-007.

## 2. Verificaciones automáticas (después de implementar)

```powershell
cd app/frontend
npm run lint:primeng
npm run build
npm test
```

Esperado: cero errores; las specs existentes siguen en verde; el lint falla si hay más de una `font-family` o margen de `body`, `::ng-deep`, `!important` o `ed-grid`.

## 3. Verificación de política (SC-006, SC-002)

- Buscar `font-family` en `app/frontend/src`: exactamente una coincidencia, en `styles.css`.
- `git diff --stat` no debe incluir `app/frontend/src/app/features/**`, `app/template-primeng/**` ni `app/backend/**`.

## 4. Verificación manual con `npm start` (`app/frontend`)

| Escenario | Pasos | Resultado esperado |
|---|---|---|
| Esqueleto en todas las rutas (US1, SC-001) | Visitar las 9 URL del contrato de rutas con sesión | Barra superior, navegación, contenido y pie visibles; misma pantalla que antes |
| Ruta inexistente (FR-005) | Ir a `/zzz` | Shell visible, mensaje informativo, ninguna entrada activa, URL sin reescribir |
| Navegación (SC-003) | Desde cualquier pantalla ir a los 3 módulos | Un clic (dos con la navegación colapsada) |
| Ancho 768 px (US2, SC-004) | Reducir la ventana | Navegación colapsada, control `≡` visible, sin desplazamiento horizontal; `≡` abre `p-drawer` |
| Ancho 1920 px (US3, SC-005) | Ventana a 1920 px | Contenido ≤ 1280 px, centrado, padding 1.5 rem, igual en todas las pantallas |
| Tipografía (US4) | Inspeccionar texto y `body` | Sans-serif del sistema, sin descargas de fuentes, `margin: 0` |
| Foco (ADR-004) | Abrir/cerrar el drawer con teclado | Foco a la primera entrada al abrir; vuelve a `≡` al cerrar |
| Diálogos (CB-06) | Abrir registro de miembro y asignación a Sprint | Se muestran sobre el shell sin alterarlo |

## 5. Evidencia de cierre (FR-014, SC-008)

Guardar 6 capturas en `specs/035-HU_refactorizacion_esqueleto_ui/evidence/` con nombre `{modulo}-{ancho}.png` (`backlog`, `sprints`, `equipo` × `1920`, `768`): 1920 px con la navegación expandida y 768 px con la navegación colapsada. Sin las 6 capturas la historia no pasa a ACTIVE.
