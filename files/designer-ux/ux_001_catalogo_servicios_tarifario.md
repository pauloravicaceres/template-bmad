# ESPECIFICACIÓN DE DISEÑO UX: Catálogo de Servicios y Tarifario Parametrizable

- **Historia de Usuario Fuente:** files/business-analyst/001-HU_catalogo_servicios_tarifario.md
- **Especificación SDD Fuente:** specs/001-HU_catalogo_servicios_tarifario.md
- **Fecha de Diseño:** 02-10-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** `001-HU_catalogo_servicios_tarifario` - Registro y mantenimiento del catálogo reutilizable de servicios, componentes funcionales y tarifas base.
- **Enfoque de Usabilidad:** Interfaz limpia orientada a la gestión de datos maestros. Ofrece una vista principal en tabla paginada con filtros rápidos por categoría y estado, y un panel/modal interactivo de alta y edición con validaciones inmediatas en línea para asegurar la captura limpia de tarifas numéricas positivas y evitar conflictos por duplicidad.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Listado y Consulta del Catálogo de Servicios (Happy Path)
- **Escenario Cubierto:** SC-02 [Happy Path] Consulta y filtrado del catálogo de servicios (FR-004, FR-005)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  [ Cotizador Freelance ]   / Catálogo de Servicios                     [ Admin (v) ] |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  CATÁLOGO DE SERVICIOS Y TARIFARIO BASE                                           |
|  Gestión de componentes funcionales y tarifas configurables para cotizaciones.    |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Buscar: [ API REST............ ]  Categoría: [ Todos (v) ] Estado: [Activos] |  |
|  +-----------------------------------------------------------------------------+  |
|                                                     [ + Registrar Nuevo Servicio ]|
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | CODIGO | NOMBRE SERVICIO       | CATEGORIA | UNIDAD  | TARIFA BASE | ESTADO |  |
|  +--------+-----------------------+-----------+---------+-------------+--------+  |
|  | SRV-01 | Desarrollo API REST   | Web       | Hora    | $50.00 USD  | ACTIVO |  |
|  | SRV-02 | Landing Page Básica   | Web       | Proyecto| $350.00 USD | ACTIVO |  |
|  | SRV-03 | Módulo Autenticación  | Backend   | Módulo  | $200.00 USD | ACTIVO |  |
|  +-----------------------------------------------------------------------------+  |
|  | Mostrando 1-3 de 3 registros                  [ < Previo ] [ 1 ] [ Siguiente > ]|
+-----------------------------------------------------------------------------------+
```
- **Notas de Interfaz:**
  - **Filtros Dinámicos:** La búsqueda por texto aplica sobre `nombre` y `codigo` con debounce de 300ms.
  - **Paginación:** Configurada a 10 ítems por página por defecto (`page=1`, `limit=10`).
  - **Acciones Primarias:** El botón `[ + Registrar Nuevo Servicio ]` desencadena el modal de creación (Estado 2).

---

### Estado 2: Modal de Registro de Nuevo Servicio (Happy Path)
- **Escenario Cubierto:** SC-01 [Happy Path] Registro exitoso de servicio (FR-001, FR-002, FR-007)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  REGISTRAR NUEVO SERVICIO                                                         |
+-----------------------------------------------------------------------------------+
|  Complete los datos del componente funcional y su tarifa base.                    |
|                                                                                   |
|  Nombre del Servicio *:                                                           |
|  [ Desarrollo de API REST                                                       ] |
|                                                                                   |
|  Categoría *:                            Unidad de Medida *:                      |
|  [ Web                               v ] [ Hora                             v ]   |
|                                                                                   |
|  Tarifa Base *:                          Moneda *:                                |
|  [ 50.00                             ] [ USD (Dólares)                      v ]   |
|                                                                                   |
|  Descripción (Opcional):                                                          |
|  [ Servicio de desarrollo de endpoints RESTful documentados con OpenAPI.        ] |
|                                                                                   |
|                                   [ Cancelar ]     [ [✓] Guardar Servicio ]       |
+-----------------------------------------------------------------------------------+
```
- **Notas de Interfaz:**
  - **Valores por Defecto:** Campo Moneda predeterminado en `USD` conforme a la especificación.
  - **Foco:** Auto-focus al abrir el modal en el campo `Nombre del Servicio`.
  - **Validación Frontend Client-Side:** Deshabilita submit si los campos obligatorios (*) están vacíos.

---

### Estado 3: Validaciones de Formulario Faltantes / Tarifa Inválida (Sad Path)
- **Escenario Cubierto:** SC-03 [Sad Path] Formulario con datos faltantes o tarifa <= 0 (CB-01, CB-02)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  REGISTRAR NUEVO SERVICIO                                                         |
+-----------------------------------------------------------------------------------+
|  +-----------------------------------------------------------------------------+  |
|  | ⚠ HTTP 400 Bad Request: Error de validación en los datos ingresados.         |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  Nombre del Servicio *:                                                           |
|  [                                                                              ] |
|  * Error: El nombre del servicio es obligatorio.                                  |
|                                                                                   |
|  Tarifa Base *:                          Moneda *:                                |
|  [ -10.00                            ] [ USD (Dólares)                      v ]   |
|  * Error: La tarifa base debe ser un valor numérico estrictamente positivo (> 0). |
|                                                                                   |
|                                   [ Cancelar ]     [ (X) Guardar Servicio ]       |
+-----------------------------------------------------------------------------------+
```
- **Notas de Interfaz:**
  - **Retroalimentación Visual:** Borde rojo en campos con fallas y mensaje inline debajo del input.
  - **Bloqueo:** Botón de submit deshabilitado hasta corregir los valores erróneos.

---

### Estado 4: Alerta por Nombre de Servicio Duplicado (Sad Path)
- **Escenario Cubierto:** SC-04 [Sad Path] Registro con nombre duplicado (CB-03)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  REGISTRAR NUEVO SERVICIO                                                         |
+-----------------------------------------------------------------------------------+
|  +-----------------------------------------------------------------------------+  |
|  | ⛔ HTTP 409 Conflict: Ya existe un servicio registrado con el nombre         |  |
|  |   "Landing Page Básica" en la categoría "Web".                                 |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  Nombre del Servicio *:                                                           |
|  [ Landing Page Básica                                                          ] |
|  * Error: Nombre duplicado dentro de la categoría seleccionada.                   |
|                                                                                   |
|                                   [ Cancelar ]     [ [✓] Guardar Servicio ]       |
+-----------------------------------------------------------------------------------+
```
- **Notas de Interfaz:**
  - **Manejo de Excepción 409:** Muestra banner de alerta en la parte superior del modal manteniendo los datos ingresados por el usuario para facilitar su corrección sin perder información.

---

### Estado 5: Vista de Catálogo Vacío / Sin Coincidencias (Sad Path)
- **Escenario Cubierto:** CB-04 / Vista sin registros iniciales o sin resultados de búsqueda
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------------------+
|  CATÁLOGO DE SERVICIOS Y TARIFARIO BASE                                           |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Buscar: [ Servicio Inexistente ] Categoría: [ Todas ] Estado: [ Todos ]      |  |
|  +-----------------------------------------------------------------------------+  |
|                                                     [ + Registrar Nuevo Servicio ]|
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                                                                             |  |
|  |                        🔍 No se encontraron servicios                        |  |
|  |      No hay componentes o servicios registrados con los filtros aplicados. |  |
|  |                                                                             |  |
|  |                             [ Limpiar Filtros ]                             |  |
|  |                                                                             |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```
- **Notas de Interfaz:**
  - **Empty State Constructivo:** Botón para restablecer los filtros aplicados y acción rápida para abrir el formulario de nuevo servicio.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - La visualización en tabla privilegia la densidad de información limpia para un administrador de cotizaciones.
  - La moneda por defecto es `USD`, ofreciendo selector extensible para `PEN` u otros códigos ISO.
  - Los formularios modales evitan la pérdida de contexto de la pantalla principal.
- **Bloqueos de UX / Consultas para BA:**
  - Ninguno. La especificación técnica de la HU `001-HU_catalogo_servicios_tarifario.md` y la spec SDD `specs/001-HU_catalogo_servicios_tarifario.md` están completamente cerradas y alineadas.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
`@SA: El diseño visual de la Historia de Usuario 001-HU_catalogo_servicios_tarifario está listo en files/designer-ux/ux_001_catalogo_servicios_tarifario.md. Procede con el diseño de arquitectura técnica (tech-design).`
