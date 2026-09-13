## 1. HISTORIA DE USUARIO

- **Épica:** Catálogo Digital de Servicios y Especialistas
- **Título de la HU:** Visualización del catálogo podológico y especialistas disponibles

> **Como** Cliente del Spa Podológico
> **Quiero** explorar la vitrina digital de servicios podológicos y conocer a los profesionales de la salud podológica disponibles
> **Para** informarme sobre las duraciones estimadas de los tratamientos y elegir al especialista de mi preferencia para mi atención

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Despliegue del catálogo visual de profesionales de la salud podológica (especialistas).
  - Listado de servicios podológicos disponibles con su información descriptiva.
  - Muestra explícita y exclusiva de la duración promedio de atención de cada servicio podológico.
  - Selección de uno o más servicios y/o especialista desde la vitrina como paso previo o integrado al agendamiento.
  - Diseño responsivo y optimizado bajo enfoque Mobile-First.

- **NO Incluye:**
  - Visualización de precios, tarifas o montos económicos de los servicios (por restricción de negocio, están estrictamente ocultos al público).
  - Funcionalidades de administración o edición del catálogo de servicios o personal (alta/baja/modificación de podólogos o tratamientos).
  - Reserva de horarios o bloqueo de agenda (corresponde a la Épica [P1] Motor de Reservas e Integración de Agenda en Tiempo Real).
  - Filtrado por calificaciones o valoraciones de clientes (no especificado en el alcance del MVP).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Ocultamiento total de precios: Toda ficha o elemento del catálogo público debe omitir de forma estricta cualquier información sobre costos o tarifas del servicio.
- **RN-02:** Visibilidad de duración promedio: Todos los servicios listados deben incluir de forma clara su tiempo estimado/promedio de atención en minutos o horas.
- **RN-03:** Disponibilidad de especialistas: La vitrina solo mostrará podólogos activos y habilitados para la prestación del servicio.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización exitosa del catálogo de servicios sin precios (Happy Path)**
- **Dado** que un cliente ingresa a la plataforma web/móvil del spa
- **Cuando** navega a la sección del catálogo de servicios
- **Entonces** el sistema muestra el listado de servicios podológicos indicando únicamente el nombre, descripción y tiempo promedio de atención de cada uno
- **Y** el sistema no muestra ningún dato relativo a precios o montos en dinero

**Escenario 2: Visualización del catálogo de especialistas/podólogos (Happy Path)**
- **Dado** que un cliente explora la vitrina digital
- **Cuando** accede a la sección de profesionales
- **Entonces** el sistema despliega la lista de especialistas podológicos con su información de perfil y especialidades
- **Y** permite al cliente seleccionar un profesional para iniciar el proceso de reserva

**Escenario 3: Selección de múltiples servicios desde la vitrina (Happy Path)**
- **Dado** que un cliente consulta el catálogo de servicios
- **Cuando** selecciona más de un servicio podológico para su atención
- **Entonces** el sistema acumula los servicios seleccionados y calcula visualmente la suma continua del tiempo total estimado de atención

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Módulo de Administración de Catálogo y Especialistas:** El PRD no especifica cómo ni quién registrará o actualizará la información, imágenes o duraciones de los podólogos y servicios. Se declara como Punto Abierto.
- **Detalle de Ficha del Especialista:** No se especifica en el PRD si el perfil del podólogo requiere información extendida (ej. años de experiencia, biografía o certificados).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización del catálogo podológico y especialistas disponibles está lista en el archivo hu_02_catalogo.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
