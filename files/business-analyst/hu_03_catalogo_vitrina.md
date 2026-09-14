## 1. HISTORIA DE USUARIO

- **Épica:** Catálogo de Servicios y Vitrina del Equipo Profesional
- **Título de la HU:** Exploración del Catálogo Podológico y Selección del Equipo Profesional

> **Como** Cliente del Spa Podológico Ámely  
> **Quiero** consultar la vitrina de profesionales podólogos y explorar el catálogo de servicios con su descripción y duración promedio estimada  
> **Para** conocer al equipo especializado, seleccionar los tratamientos adecuados y dar inicio al flujo de agendamiento sin visualizar precios

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Visualización del perfil y presentación de los profesionales podólogos del spa (Vitrina del Equipo).
  - Consulta del catálogo de servicios podológicos disponibles mostrando únicamente nombre, descripción detallada y duración promedio estimada de atención.
  - Selección de uno o más servicios y/o elección del profesional podólogo preferido para transicionar al Motor de Reservas.
  - Ocultamiento estricto de cualquier tarifa, costo u opción monetaria dentro del catálogo y la vitrina.
- **NO Incluye:**
  - Creación, modificación o eliminación administrativa de servicios o perfiles de profesionales (abarcado en gestión de backend/administración).
  - Consulta de horarios en tiempo real y reserva de citas (abarcado en Épica P1).
  - Envío de notificaciones por WhatsApp (abarcado en Épica P2).
  - Valoraciones, comentarios o reseñas de clientes sobre los podólogos.

## 3. REGLAS DE NEGOCIO

- **RN-01 (Sin Precios en Catálogo):** Todos los servicios exhibidos en el catálogo deben omitir información sobre precios, tarifas o costos de atención.
- **RN-02 (Duración Promedio Explicita):** Cada servicio en el catálogo debe mostrar obligatoriamente su duración promedio estimada de atención (ej. 45 min, 60 min) para permitir el cálculo posterior en la reserva.
- **RN-03 (Navegación Fluida al Agendamiento):** La selección de servicios o de un profesional en este catálogo debe pre-cargar dichos ítems al iniciar el flujo de disponibilidad en el motor de reservas.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Consulta del catálogo de servicios y vitrina de profesionales (Happy Path)**
- **Dado** que el cliente ingresa a la aplicación web responsiva del Spa Ámely
- **Cuando** navega por la sección del catálogo de servicios y la vitrina del equipo profesional
- **Entonces** el sistema despliega la información detallada de cada podólogo
- **Y** muestra el listado de servicios podológicos indicando únicamente su nombre, descripción funcional y duración promedio estimada, sin mostrar información de precios

**Escenario 2: Selección de servicios y profesional para iniciar reserva**
- **Dado** que el cliente se encuentra explorando el catálogo de servicios
- **Cuando** selecciona uno o varios servicios podológicos y elige su profesional de preferencia
- **Entonces** el sistema guarda la selección realizada y redirige al cliente al Motor de Reservas para consultar la disponibilidad en tiempo real

**Escenario 3: Verificación de Prohibición de Precios en el Catálogo**
- **Dado** que el cliente revisa las fichas de los servicios podológicos y del personal profesional
- **Cuando** inspecciona todos los elementos visuales de la interfaz
- **Entonces** se garantiza que no exista ningún campo, etiqueta ni importe numérico asociado a precios o monedas

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Filtros y Categorización):** El PRD no especifica si el catálogo requiere categorización avanzada de tratamientos podológicos o búsqueda por filtros de especialidad.
- **Punto Abierto 2 (Asignación Automática de Profesional):** El PRD no aclara si la selección de un profesional es estrictamente obligatoria o si se permite elegir la opción "Cualquier profesional disponible".
- **Dependencia:** Sirve como punto de entrada previo para alimentar la Épica del Motor Inteligente de Reservas (P1).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Exploración del Catálogo Podológico y Selección del Equipo Profesional está lista en el archivo hu_03_catalogo_vitrina.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
