# ESPECIFICACIÓN DE DISEÑO UX

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Agendamiento de cita podológica con cálculo acumulativo de tiempo y bloqueo de disponibilidad
- **Enfoque de Usabilidad:** Se diseñó un flujo visual interactivo enfocado en el cálculo dinámico y acumulativo del tiempo total de atención según los servicios podológicos seleccionados. La parrilla de horarios filtra e inhabilita automáticamente aquellos bloques que no garanticen la disponibilidad continua ininterrumpida del podólogo elegido, ofreciendo además mecanismos visuales claros para situaciones de colisión por concurrencia en tiempo real.

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Agendamiento Exitoso con Cálculo Acumulativo y Bloqueo de Agenda (Happy Path)

**Escenario cubierto:** Escenario 1 - Selección de 2 servicios podológicos (30 min + 45 min = 75 min total) y podólogo preferido. Filtrado de horarios libres de 75 min continuos y bloqueo exitoso de agenda al confirmar.

**Artefacto Visual (Stitch):**
- **Project ID:** `projects/585779985085809414`
- **Screen ID:** `projects/585779985085809414/screens/47557a8f24c7461ca877c43b42d0b717`
- **Título de Pantalla:** Agendar Cita - Motor de Reservas (Happy Path)

**Nota de Interfaz:** El banner/tarjeta de resumen muestra el tiempo total acumulado (75 min). La parrilla de disponibilidad solo habilita horas de inicio donde el profesional cuenta con 75 minutos libres ininterrumpidos. El botón principal "Confirmar Reserva" se habilita únicamente cuando los criterios están satisfechos.

### Estado 2: Descarte de Horarios por Tiempo Continuo Insuficiente (Sad Path)

**Escenario cubierto:** Escenario 2 - Selección de servicios por 60 min. El podólogo elegido cuenta con una cita agendada a las 10:30 AM. El horario de las 10:00 AM es descartado por contar únicamente con un bloque disponible de 30 minutos antes del siguiente compromiso.

**Artefacto Visual (Stitch):**
- **Project ID:** `projects/585779985085809414`
- **Screen ID:** `projects/585779985085809414/screens/a7d7c11aebf644d39f7ef2182ff65be5`
- **Título de Pantalla:** Agendar Cita - Error Tiempo Excedido / Disponibilidad Insuficiente

**Nota de Interfaz:** El horario de las 10:00 AM aparece visible pero en estado deshabilitado (estilo mudo/bloqueado) indicando visualmente que el espacio disponible (30 min) es menor al tiempo total acumulado de la cita (60 min).

### Estado 3: Prevención de Cruces por Concurrencia Simultánea en Tiempo Real (Sad Path)

**Escenario cubierto:** Escenario 3 - Dos clientes intentan reservar el mismo horario y podólogo de manera simultánea. Al confirmar el primer cliente, el bloque se reserva inmediatamente. Al intentar confirmar el segundo cliente, el sistema rechaza la solicitud y muestra la alerta de choque de disponibilidad.

**Artefacto Visual (Stitch):**
- **Project ID:** `projects/585779985085809414`
- **Screen ID:** `projects/585779985085809414/screens/102ee1885ea7407599545d533adba33b`
- **Título de Pantalla:** Agendar Cita - Error Concurrencia Horario

**Nota de Interfaz:** Un mensaje/modal emergente de alerta notifica al usuario: *"El horario seleccionado ya no se encuentra disponible debido a una reserva reciente. Por favor, selecciona un nuevo horario."*. La interfaz preserva los servicios y el podólogo previamente seleccionados para evitar volver a empezar el flujo.

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - **Visibilidad del estado del sistema:** Indicador acumulativo de tiempo total visible en todo momento.
  - **Prevención de errores:** Inhabilitación proactiva de bloques horarios insuficientes para evitar clics infructuosos.
  - **Recuperación eficiente de errores:** Ante fallos de concurrencia simultánea, se mantiene la selección previa de servicios y profesional, reduciendo la fricción del usuario.
- **Bloqueos o Consultas (Si aplican):**
  - **PA-01 (Datos del cliente):** No se diseñó formulario de captura de datos personales por ser un punto abierto pendiente de definición en el Product Brief.
  - **PA-02 (Horarios laborales):** Se asume una grilla de tiempo estándar configurable según los turnos asignados a cada profesional.

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@HUMANO: Los wireframes funcionales para la Historia de Usuario Agendamiento de cita podológica con cálculo acumulativo de tiempo y bloqueo de disponibilidad están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_01_agendamiento.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
