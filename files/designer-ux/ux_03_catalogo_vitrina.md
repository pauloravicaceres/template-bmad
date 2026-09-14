## 1. RESUMEN DE DISEÑO

- **Historia Base:** Exploración del Catálogo Podológico y Selección del Equipo Profesional (`hu_03_catalogo_vitrina.md`)
- **Enfoque de Usabilidad:** Se implementó una vitrina institucional elegante que combina la presentación del equipo podológico colegiado con un catálogo estructurado por especialidades clínicas. La interfaz permite explorar y seleccionar tratamientos podológicos visualizando su descripción anatómica y duración estimada, conectando dinámicamente con la barra flotante de agendamiento sin exhibir información de precios.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Exploración del Catálogo Podológico y Vitrina del Equipo (Happy Path)

**Escenario cubierto:** Escenario 1: Consulta del catálogo de servicios y vitrina de profesionales (Happy Path)

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/71a835e6d1de4ced94a896ce846f4f81`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** La vitrina presenta las fichas del personal colegiado (Dra. Elena Ramos, Dr. Marcos Valdés, Lic. Sofía Méndez) con sus gabinetes asignados y especialidades. El catálogo despliega tarjetas interactivas organizadas por categorías clínicas (Quiropodia, Biomecánica, Terapias Láser), destacando en badges visibles la duración promedio estimada (ej: 45 min, 30 min, 40 min). Todas las fichas omiten montos monetarios.

### Estado 2: Selección de Tratamientos y Transición al Agendamiento

**Escenario cubierto:** Escenario 2: Selección de servicios y profesional para iniciar reserva

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/71a835e6d1de4ced94a896ce846f4f81`
- **Proyecto Stitch:** `projects/13539032631391197448` (Motor de Reservas Spa Amely)

**Nota de Interfaz:** Al marcar uno o varios servicios en el catálogo (ej: Quiropodia Integral 45 min + Tratamiento de Uñero 30 min), la barra flotante inferior (Sticky Dock) se activa inmediatamente, calculando la suma acumulada de tiempo (75 min) y ofreciendo el botón principal `Continuar a Agendamiento de Horario →` que precarga la selección en el motor de reservas.

### Estado 3: Verificación de Restricción Inquebrantable (No Precios)

**Escenario cubierto:** Escenario 3: Verificación de Prohibición de Precios en el Catálogo

- **ID de Pantalla en Stitch:** `projects/13539032631391197448/screens/71a835e6d1de4ced94a896ce846f4f81`

**Nota de Interfaz:** Se realiza la verificación estricta en el catálogo, tarjetas de tratamiento, vitrina de profesionales y barra flotante de resumen. Se garantiza que ningún elemento gráfico o textual despliegue símbolos de moneda ($), tarifas o costos.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - *Reconocimiento antes que recuerdo (Heurística 6):* Tarjetas de tratamiento visualmente descriptivas con etiquetas de categoría y lista de beneficios clínicos para facilitar la elección del cliente.
  - *Visibilidad del Estado del Sistema (Heurística 1):* Barra flotante inferior fija (Sticky Dock) que indica en todo momento la cantidad de servicios marcados y la suma acumulada de minutos.
  - *Consistencia y Estándares (Heurística 4):* Integración del lenguaje visual *Serene Podiatric Sanctuary* en tonos verde salvia (`#3E6B5C`), superficies sanitarias blancas y tipografía clínica Newsreader/Manrope.
- **Bloqueos o Consultas:**
  - *Consulta para el BA / Product Owner:* Se confirma que el catálogo incluye el filtro "Cualquier profesional disponible" para acelerar la reserva cuando el cliente no requiere un especialista específico (Punto Abierto 2 de la HU).

# 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@PM: Los wireframes para la HU Exploración del Catálogo Podológico y Selección del Equipo Profesional están listos en D:\Paulo\Cursos\DMC\template-bmad\files\designer-ux\ux_03_catalogo_vitrina.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
