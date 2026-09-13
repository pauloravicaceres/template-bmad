## 1. HISTORIA DE USUARIO

- **Épica:** Módulo de Vitrina Digital y Catálogo de Servicios Podológicos
- **Título de la HU:** Visualización pública de vitrina digital, perfiles de podólogos y catálogo de servicios con duraciones estimadas

> **Como** visitante o cliente del spá podológico
> **Quiero** explorar la vitrina digital del spa, los perfiles de los podólogos y el catálogo de servicios con sus duraciones
> **Para** conocer la oferta del spa y seleccionar los servicios y profesionales de mi interés antes de iniciar el agendamiento

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Presentación visual informativa del spa e instalaciones.
  - Exposición de perfiles de los profesionales podólogos que laboran en el spa.
  - Despliegue del catálogo público de servicios podológicos indicando su descripción y tiempo/duración promedio de atención.
  - Mantenimiento estricto del ocultamiento de los precios de todos los servicios podológicos en la vista pública.
- **NO Incluye:**
  - Mostrar o listar precios de los servicios en la interfaz pública (Restricción de Negocio Inquebrantable).
  - Funciones administrativas para crear, modificar o eliminar servicios y profesionales (Punto Abierto / Administración).
  - Selección activa y cálculo de disponibilidad para agendamiento (perteneciente a la Épica P1: Motor Inteligente de Reservas).

## 3. REGLAS DE NEGOCIO

- **RN-01:** Los precios de todos los servicios podológicos deben permanecer 100% ocultos e inaccesibles en la vista pública de la vitrina digital.
- **RN-02:** Cada servicio podológico desplegado en el catálogo debe especificar de forma obligatoria su duración promedio estimada de atención (en minutos).
- **RN-03:** Los perfiles de los podólogos presentados deben mostrar información del profesional habilitado para la atención.
- **RN-04:** La interfaz debe ser ligera, responsiva y adaptable a dispositivos móviles, tablets y computadoras de escritorio.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización del catálogo de servicios con duraciones y precios ocultos (Happy Path)**
- **Dado** que el usuario ingresa a la vitrina digital del spa
- **Cuando** navega por la sección del catálogo de servicios podológicos
- **Entonces** el sistema despliega la lista de servicios ofertados detallando su descripción y duración promedio estimada de atención
- **Y** valida que el precio de cada servicio no se muestre en ningún elemento de la pantalla ni en la vista pública.

**Escenario 2: Exploración de perfiles de profesionales podólogos (Happy Path)**
- **Dado** que el usuario consulta la sección del equipo profesional
- **Cuando** selecciona la vista del equipo del spa
- **Entonces** el sistema presenta los perfiles de los podólogos disponibles indicando su especialidad o información profesional.

**Escenario 3: Verificación de diseño responsivo y sin precios (Sad/Edge Path)**
- **Dado** que un usuario accede a la vitrina digital desde un dispositivo móvil o navegador de escritorio
- **Cuando** inspecciona la vista del catálogo de servicios
- **Entonces** la interfaz se adapta correctamente al tamaño de la pantalla sin desconfigurar el contenido
- **Y** confirma que la información tarifaria permanece completamente oculta en la experiencia visual.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **PA-01 (Módulo de Administración para Gestión de Contenidos):** El PRD / Product Brief no define las pantallas ni permisos administrativos para la alta, baja o edición de servicios podológicos, duraciones o perfiles de podólogos.
- **PA-02 (Fotografías y Material Multimedia del Spa):** No se especifica la disponibilidad de activos digitales (fotografías de instalaciones y podólogos) para el renderizado inicial de la vitrina.

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Visualización pública de vitrina digital, perfiles de podólogos y catálogo de servicios con duraciones estimadas está lista en el archivo hu_04_vitrina_catalogo.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
