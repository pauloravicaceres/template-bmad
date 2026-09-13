# 1. HISTORIA DE USUARIO

- **Épica:** Catálogo Digital de Servicios y Especialistas
- **Título de la HU:** Visualización del catálogo podológico y especialistas disponibles

> **Como** Cliente de Ámely Spá Podológico  
> **Quiero** explorar la lista de servicios podológicos ofertados y el equipo de especialistas con sus respectivos tiempos de atención  
> **Para** informarme sobre las opciones disponibles y seleccionar los servicios o el especialista adecuado antes de iniciar el agendamiento  

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Despliegue de la lista completa de servicios podológicos disponibles.
  - Muestra del tiempo promedio de atención estimado para cada servicio.
  - Presentación del perfil o lista de podólogos/especialistas que integran el equipo del spá.
  - Interfaz web adaptable a diferentes dispositivos (móviles, tablets, laptops y computadoras de escritorio).
- **NO Incluye:**
  - Despliegue o visualización de precios de los servicios.
  - Reserva directa de citas o selección de fechas/horarios desde esta vista (pertenece al Motor de Reservas).
  - Gestión o administración (alta, baja o edición) de servicios o especialistas por parte del staff.

## 3. REGLAS DE NEGOCIO

- **RN-01:** Bajo ninguna circunstancia se deben mostrar precios o valores monetarios asociadas a los servicios podológicos en el catálogo.
- **RN-02:** Todo servicio desplegado debe exhibir de forma transparente su duración/tiempo promedio estimado de atención.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Consulta del catálogo de servicios y especialistas (Happy Path)**
- **Dado** que el cliente ingresa a la aplicación web del spá
- **Cuando** navega a la sección del catálogo digital
- **Entonces** el sistema despliega la oferta de servicios podológicos indicando para cada uno su tiempo promedio de atención
- **Y** muestra el listado del equipo de profesionales podólogos de la clínica
- **Y** no muestra en ninguna parte de la interfaz precios o tarifas monetarias.

**Escenario 2: Visualización adaptativa en dispositivos móviles o pantallas pequeñas (Flujo Alternativo)**
- **Dado** que el cliente accede al catálogo digital desde un dispositivo móvil o tablet
- **Cuando** interactúa con la pantalla de servicios y especialistas
- **Entonces** el sistema ajusta dinámicamente la disposición visual manteniendo la visibilidad del catálogo y la duración estimada de cada atención
- **Y** omite la presentación de precios.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Detalles del perfil del especialista:** No se especifica si los especialistas deben mostrar información adicional (ej. especialidad concreta, foto o reseña profesional) o únicamente su nombre.
- **Categorización de servicios:** No se especifica si la oferta de servicios debe estar agrupada en categorías o listada en una sola vista plana.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización del catálogo podológico y especialistas disponibles está lista en el archivo hu_02_catalogo.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
