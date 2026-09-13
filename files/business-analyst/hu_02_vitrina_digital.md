## 1. HISTORIA DE USUARIO

- **Épica:** Vitrina Digital de Podólogos y Servicios
- **Título de la HU:** Visualización del catálogo de servicios podológicos y presentación del equipo de podólogos

> **Como** Cliente (Paciente) del spá podológico
> **Quiero** explorar el catálogo de servicios con sus precios y tiempos promedio explicitados, así como conocer la información del equipo de podólogos
> **Para** evaluar y seleccionar informadamente los tratamientos y el profesional de mi preferencia antes de iniciar el agendamiento

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Despliegue visual del catálogo de servicios podológicos disponibles.
  - Presentación explícita para cada servicio de: nombre del tratamiento, descripción funcional, precio visible (en moneda local) y tiempo promedio estimado de atención (en minutos).
  - Sección de presentación del equipo de profesionales podólogos (nombre completo, especialidad/breve perfil).
  - Filtro o navegación clara por servicios y/o por profesional podólogo.
  - Botón o llamada a la acción (CTA) directa desde un servicio o podólogo para iniciar el flujo de agendamiento de reserva.
  - Diseño ligero, moderno y 100% responsivo (adaptable a mobile, tablet y desktop).

- **NO Incluye:**
  - Sistema de valoraciones, opiniones o calificación por estrellas de podólogos (fuera del alcance del MVP).
  - Reserva directa de horario o validación de agenda (pertenece a la Épica P1: Motor Inteligente de Reservas y Disponibilidad).
  - Procesamiento de pagos o carrito de compra e-commerce (fuera del alcance del MVP).
  - Administración dinámica del catálogo (alta/baja de servicios desde un panel administrativo web).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Transparencia de Precios y Tiempos: Todo servicio publicado en el catálogo debe mostrar de forma obligatoria e inmutable su precio explícito y su duración promedio estimada de atención.
- **RN-02:** Presentación Profesional: Cada perfil de podólogo expuesto en la vitrina debe estar asociado a su nombre completo y especialidad médica/podológica.
- **RN-03:** Continuidad de Agendamiento: Al seleccionar un servicio o podólogo desde la vitrina, el sistema debe pre-seleccionar dicha opción y dirigir al cliente de manera fluida hacia el Motor de Reservas.
- **RN-04:** Responsividad Obligatoria: La visualización del catálogo debe ajustarse automáticamente a pantallas móviles, tablets y computadoras sin degradación de la información ni superposición de elementos.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización completa del catálogo de servicios (Happy Path)**
- **Dado** que el cliente ingresa a la vitrina digital del spá podológico
- **Cuando** navega en la sección de servicios podológicos
- **Entonces** el sistema muestra la lista completa de tratamientos disponibles
- **Y** para cada servicio exhibe el nombre, descripción, precio explícito (ej. "$45.00") y el tiempo promedio estimado de atención (ej. "30 min")

**Escenario 2: Visualización del equipo de podólogos**
- **Dado** que el cliente navega en la sección del equipo médico
- **Cuando** selecciona ver los profesionales disponibles
- **Entonces** el sistema despliega las fichas de los podólogos indicando su nombre completo y especialidad podológica

**Escenario 3: Transición directa desde la vitrina hacia el flujo de reserva**
- **Dado** que el cliente está visualizando el servicio "Perfilado Podológico" en la vitrina digital
- **Cuando** selecciona la opción o botón "Reservar Cita" en dicha ficha
- **Entonces** el sistema lo redirige al Motor Inteligente de Reservas manteniendo pre-seleccionado el servicio "Perfilado Podológico"

**Escenario 4: Adaptabilidad responsiva en dispositivos móviles (Sad Path / Edge Path - Degradación UI)**
- **Dado** que el cliente accede a la vitrina digital desde un smartphone con pantalla reducida
- **Cuando** visualiza el catálogo de servicios o las fichas de los podólogos
- **Entonces** el sistema ajusta la maquetación en una sola columna fluida
- **Y** no oculta ni recorta la visibilidad del precio, la duración ni los botones de acción

**Escenario 5: Manejo de servicios o podólogos no disponibles/inactivos (Sad Path)**
- **Dado** que un servicio podológico o podólogo se encuentra deshabilitado temporalmente
- **Cuando** el cliente explora la vitrina digital
- **Entonces** el sistema no muestra dicho servicio/profesional en el catálogo activo o indica claramente su estado no disponible impidiendo la pre-selección para agendamiento

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Contenido Multimedial de Podólogos:** No se ha precisado en el Product Brief si se incluirán fotografías reales o avatares de los podólogos en la vitrina digital. Se tratará como un recurso visual no bloqueante.
- **Estructura Fija de Duraciones:** Las duraciones estimadas se consideran estáticas para el MVP. Si un tratamiento varía de duración según la severidad del paciente, esta lógica deberá abordarse en iteraciones posteriores.
- **Dependencia de Integración:** La pre-selección de servicios redirige directamente al Motor Inteligente de Reservas (Épica P1).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización del catálogo de servicios podológicos y presentación del equipo de podólogos está lista en el archivo hu_02_vitrina_digital.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
