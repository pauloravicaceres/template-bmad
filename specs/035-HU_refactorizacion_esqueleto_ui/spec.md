# Feature Specification: Refactorización de Esqueleto UI — Layout de Aplicación y Tipografía Global

**Feature Branch**: `main`

**Created**: 2026-10-05

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/035-HU_refactorizacion_esqueleto_ui.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver todas las pantallas dentro de un esqueleto común (Priority: P1)

Como Usuario Final autenticado, quiero que cada pantalla existente (Registro de Elemento de Backlog, Sprints, Equipo y el diálogo de asignación de elemento a Sprint) se muestre dentro de un esqueleto común con barra superior, navegación lateral colapsable, área de contenido y pie de página, para orientarme y moverme entre Backlog, Sprints y Equipo sin que cada pantalla se vea y se comporte distinto.

**Why this priority**: Es el núcleo de la historia y la directiva de distribución estructural (Skeleton) de la Constitución; todas las historias derivadas (migas de pan, grilla, formularios, verificación visual) dependen de que este esqueleto exista.

**Independent Test**: Navegar a cada una de las rutas existentes con un usuario autenticado y comprobar que siempre se ven la barra superior (perfil y acciones del usuario a la derecha), la navegación lateral izquierda con acceso a Backlog, Sprints y Equipo, el pie de página y el contenido original de la pantalla en el área central, y que cada URL resuelve a la misma pantalla que antes.

**Acceptance Scenarios**:

1. **Given** un usuario autenticado en cualquiera de las rutas existentes, **When** la pantalla se carga, **Then** se muestran siempre una barra superior con el perfil y las acciones del usuario a la derecha, una navegación lateral izquierda colapsable con acceso a Backlog, Sprints y Equipo, un pie de página inferior y el contenido de la pantalla en el área central.
2. **Given** un usuario autenticado, **When** accede a cualquier URL que existía antes de la refactorización, **Then** la URL resuelve a la misma pantalla que antes y su contenido interno no cambia.
3. **Given** un usuario autenticado, **When** navega a una ruta que no existe, **Then** la barra superior, la navegación lateral y el pie de página permanecen visibles y el área central no muestra contenido de otra pantalla.

---

### User Story 2 - Usar el esqueleto con ancho reducido o navegación colapsada (Priority: P2)

Como Usuario Final, quiero que el esqueleto siga siendo usable cuando la ventana es estrecha (768 px) o cuando colapso la navegación lateral, para seguir accediendo a los tres módulos y leer el contenido sin desplazamiento horizontal.

**Why this priority**: Garantiza que el esqueleto no degrade la experiencia en anchos reducidos; depende de que el esqueleto base (Historia 1) exista.

**Independent Test**: Reducir la ventana a 768 px, o colapsar la navegación lateral, y consultar cada módulo: el contenido ocupa el ancho disponible sin desbordar horizontalmente y existe un control visible para expandir la navegación y alcanzar los tres módulos.

**Acceptance Scenarios**:

1. **Given** un usuario con la ventana a 768 px de ancho o con la navegación lateral colapsada, **When** consulta cualquier pantalla, **Then** el contenido ocupa el ancho disponible sin desbordar horizontalmente la ventana y los tres módulos siguen accesibles mediante un control visible para expandir la navegación.

---

### User Story 3 - Contenido con medidas uniformes en todas las pantallas (Priority: P2)

Como Usuario Final, quiero que el área de contenido central tenga el mismo ancho máximo, centrado y espaciado interior en todas las pantallas, para que ninguna pantalla se vea distinta de las demás.

**Why this priority**: Es la consistencia visual que justifica el esqueleto común, pero puede verificarse una vez entregado el esqueleto base.

**Independent Test**: Medir el área de contenido central en cada pantalla del alcance con la ventana a 1920 px: el ancho máximo es 1280 px, está centrada horizontalmente y el espaciado interior es 1.5 rem en los cuatro lados, con el mismo valor en todas las pantallas.

**Acceptance Scenarios**:

1. **Given** una pantalla mostrada en una ventana de 1920 px de ancho, **When** se mide el área de contenido central, **Then** su ancho máximo es 1280 px, está centrada horizontalmente y su espaciado interior es 1.5 rem en los cuatro lados.
2. **Given** todas las pantallas del alcance, **When** se compara el espaciado interior del área de contenido, **Then** es el mismo valor en todas (Pasa si la medición coincide en todas; Falla si alguna difiere).

---

### User Story 4 - Tipografía base uniforme (Priority: P2)

Como Usuario Final, quiero que todo el texto de la aplicación use la misma familia sans-serif del sistema y que el cuerpo de la página no tenga márgenes por defecto, para que la interfaz se vea uniforme y no aparezca la fuente serif por defecto del navegador.

**Why this priority**: Resuelve el defecto visible actual (fuente serif) y es independiente del layout, pero de menor impacto estructural.

**Independent Test**: Abrir cualquier pantalla del alcance y verificar que el texto usa una familia sans-serif del sistema, que no se descargan fuentes externas y que el cuerpo no tiene márgenes; revisar el código fuente del frontend y comprobar que existe exactamente una declaración de familia tipográfica y de margen del cuerpo, ubicada en el archivo de estilos globales.

**Acceptance Scenarios**:

1. **Given** cualquier pantalla del alcance, **When** se muestra, **Then** todo el texto usa la misma familia sans-serif del sistema, sin descargar fuentes externas ni definir una marca, y el cuerpo de la página no tiene márgenes por defecto.
2. **Given** el código fuente del frontend tras la refactorización, **When** se busca cualquier declaración de familia tipográfica o de margen del cuerpo de la página, **Then** existe exactamente una, en el archivo de estilos globales; si hay más de una, la historia no se cierra.

---

### User Story 5 - Cierre verificado de la refactorización (Priority: P3)

Como equipo responsable de la entrega, quiero verificar que el layout y la tipografía no rompen la calidad existente y que hay evidencia visual por módulo, para cerrar la historia con respaldo objetivo.

**Why this priority**: Es la compuerta de cierre; solo tiene sentido cuando las demás historias están terminadas.

**Independent Test**: Ejecutar las verificaciones de calidad del frontend (lint de PrimeNG, build y tests) y revisar que se adjunta una captura de una pantalla de cada módulo (Backlog, Sprints, Equipo) a 1920 px y a 768 px.

**Acceptance Scenarios**:

1. **Given** el layout y la tipografía terminados, **When** se ejecutan las verificaciones de calidad definidas, **Then** terminan sin errores, los tests de componentes existentes siguen en verde y se adjunta una captura de una pantalla de cada módulo mostrando barra superior, navegación lateral, contenido y pie de página, a 1920 px y a 768 px de ancho (6 capturas).
2. **Given** que alguna verificación termina con error, o falta una captura de algún módulo o de alguno de los dos anchos, **When** se intenta cerrar la historia, **Then** la historia permanece abierta y no pasa a ACTIVE hasta corregir la causa.

---

### Edge Cases

- Ruta inexistente: el esqueleto permanece visible y el área central no muestra contenido de otra pantalla (el diseño específico de la página de error no está documentado).
- Ancho de 768 px o navegación lateral colapsada: sin desborde horizontal y módulos accesibles mediante un control visible.
- Pantalla con espaciado interior distinto al definido: la verificación de medidas falla.
- Más de una declaración de tipografía o margen global: la historia no se cierra.
- Verificación o captura faltante: la historia no se cierra.
- Pantallas que se abren como diálogo (registro de miembro, asignación de elemento a Sprint): se muestran sobre el esqueleto sin alterarlo ni cambiar su contenido interno.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST mostrar, en todas las rutas existentes para usuarios autenticados, un esqueleto común compuesto por barra superior, navegación lateral izquierda, área de contenido central y pie de página.
- **FR-002**: La barra superior MUST mostrar el perfil y las acciones del usuario a la derecha.
- **FR-003**: La navegación lateral MUST ser colapsable y dar acceso a Backlog, Sprints y Equipo.
- **FR-004**: Todas las URL existentes MUST seguir resolviendo a la misma pantalla que antes, sin cambios en su contenido interno.
- **FR-005**: Ante una ruta inexistente, el sistema MUST mantener visibles la barra superior, la navegación lateral y el pie de página, y el área central MUST NOT mostrar contenido de otra pantalla.
- **FR-006**: Con ancho de ventana de 768 px o navegación colapsada, el contenido MUST ocupar el ancho disponible sin desbordar horizontalmente y MUST existir un control visible para expandir la navegación y acceder a los tres módulos.
- **FR-007**: El área de contenido central MUST tener un ancho máximo de 1280 px, estar centrada horizontalmente y tener un espaciado interior de 1.5 rem en los cuatro lados, con el mismo valor en todas las pantallas del alcance.
- **FR-008**: Todo el texto de las pantallas del alcance MUST usar una única familia sans-serif del sistema, sin descargar fuentes externas ni definir una marca; el cuerpo de la página MUST NOT tener márgenes por defecto.
- **FR-009**: La tipografía base y el reseteo de margen del cuerpo MUST declararse exactamente una vez, en el archivo de estilos globales del frontend.
- **FR-010**: La maquetación MUST apoyarse en el tema neutral y las utilidades de estilo del proyecto, sin estilos personalizados de colores, bordes, sombras o tipografías por componente, sin sobrescrituras forzadas de estilo ni penetración de estilos entre componentes.
- **FR-011**: El sistema MUST NOT reutilizar código, estructuras, selectores, grilla ni estilos de la plantilla antigua `app/template-primeng`; solo es válida como referencia visual de la distribución de zonas.
- **FR-012**: La refactorización MUST NOT modificar ninguna regla de negocio, API ni contrato de datos.
- **FR-013**: Las verificaciones de calidad del frontend (lint de PrimeNG, build y tests) MUST terminar sin errores y los tests de componentes existentes MUST seguir en verde.
- **FR-014**: La historia MUST NOT cerrarse sin una captura de una pantalla de cada módulo (Backlog, Sprints, Equipo) a 1920 px y a 768 px de ancho, mostrando barra superior, navegación lateral, contenido y pie de página.
- **FR-015**: Toda pantalla futura MUST nacer dentro del mismo esqueleto.

### Key Entities *(include if feature involves data)*

- **Esqueleto de aplicación**: Estructura común que envuelve las pantallas autenticadas; zonas: barra superior, navegación lateral, área de contenido, pie de página.
- **Entrada de navegación**: Acceso a un módulo (Backlog, Sprints, Equipo) desde la navegación lateral.
- **Evidencia de cierre**: Conjunto de capturas por módulo y ancho (6) y resultados de las verificaciones de calidad.

No se introducen entidades de negocio ni datos persistentes nuevos.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de las pantallas del alcance (Backlog, Sprints —listado, formulario, detalle y elementos asignados—, Equipo —página y diálogo— y asignación de elemento a Sprint) se muestran dentro del esqueleto común con sus cuatro zonas visibles.
- **SC-002**: El 100 % de las URL existentes resuelve a la misma pantalla que antes de la refactorización; cero regresiones en rutas.
- **SC-003**: Un usuario alcanza cualquiera de los tres módulos desde cualquier pantalla en un solo clic (o dos, si la navegación está colapsada).
- **SC-004**: A 768 px de ancho, cero pantallas del alcance presentan desplazamiento horizontal de la ventana.
- **SC-005**: A 1920 px, el área de contenido mide 1280 px como máximo, está centrada y tiene 1.5 rem de espaciado interior en el 100 % de las pantallas del alcance.
- **SC-006**: Existe exactamente una declaración de familia tipográfica y de margen del cuerpo en todo el código fuente del frontend.
- **SC-007**: Las tres verificaciones de calidad terminan con cero errores y la suite de tests existente mantiene el 100 % de sus casos en verde.
- **SC-008**: Existen las 6 capturas de cierre (3 módulos × 2 anchos).

## Assumptions

- El usuario ya está autenticado para las rutas del esqueleto; esta historia no cambia el mecanismo de autenticación (el origen de perfil y acciones del usuario en la barra superior se resuelve con lo ya existente).
- Tailwind CSS v4 y el tema neutral ya están configurados en el proyecto; no se reintroduce PrimeFlex.
- Los valores de 1280 px de ancho máximo y 1.5 rem de espaciado interior son una propuesta del analista de negocio pendiente de confirmación humana; se adoptan como valores vigentes de la especificación.
- El comportamiento específico de la página de error ante ruta inexistente no está documentado; el alcance se limita a mantener el esqueleto visible sin mostrar contenido de otra pantalla.
- La reducción de la captura a una pantalla por módulo (en lugar de una por cada pantalla) es consecuencia de la partición aprobada; el requisito completo corresponde a la historia derivada de verificación visual.
- Fuera de alcance (historias derivadas): título y migas de pan por pantalla, contenedores y jerarquía de formularios, grilla responsiva y tablas, patrón de formularios y acciones, y verificación visual por cada pantalla (8 pantallas × 2 anchos).
- La decisión del componente concreto de navegación lateral colapsable se toma en la fase de arquitectura/plan.
- Las restricciones técnicas trazables (RT-01 a RT-09) de la historia fuente se aplican en la fase de plan.
