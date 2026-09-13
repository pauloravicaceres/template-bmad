## 1. HISTORIA DE USUARIO

- **Épica:** Vitrina Digital e Identidad del Spá
- **Título de la HU:** Presentación del Equipo Podológico y Catálogo Interactivo de Servicios con Tiempos Estimados sin Precios

> **Como** visitante o cliente del Spá Podológico  
> **Quiero** explorar la vitrina digital de la plataforma con los perfiles del equipo de podólogos y el catálogo de servicios indicando los tiempos estimados de atención  
> **Para** conocer la oferta profesional del spá e iniciar el proceso de reserva con información clara de duraciones sin exposición de precios.

## 2. ALCANCE ESPECÍFICO (SCOPE)

- **Incluye:**
  - Sección pública de presentación del equipo podológico (fotografías, nombres, especialidades y perfiles profesionales).
  - Catálogo interactivo de servicios podológicos ofertados.
  - Indicación visible del tiempo promedio estimado de atención para cada servicio en el catálogo.
  - Integración o enlace directo desde la vitrina digital hacia el inicio del flujo del motor de reservas.
  - Diseño responsivo adaptado a dispositivos móviles, tablets y computadoras de escritorio.
- **NO Incluye:**
  - Mantenimiento o administración de precios (restricción estricta de ocultación de precios en todas las vistas públicas).
  - Gestión dinámica de catálogo o carga de archivos multimedia desde un panel de administración en el MVP (contenido precargado/estático en esta fase).
  - Sistema de calificaciones o reseñas públicas de podólogos por parte de clientes.

## 3. REGLAS DE NEGOCIO

- **RN-01:** Todos los servicios mostrados en el catálogo público deben incluir obligatoriamente su tiempo promedio estimado de atención expresado en minutos.
- **RN-02:** En ninguna vista, sección o elemento de la vitrina digital se deben mostrar o hacer referencia a precios, costos o tarifas de servicios.
- **RN-03:** Cada perfil de podólogo presentado debe mostrar su fotografía, nombre completo y especialidad médica/podológica.
- **RN-04:** La interfaz debe ser 100% responsiva y adaptarse a cualquier tamaño de pantalla de dispositivo.

## 4. CRITERIOS DE ACEPTACIÓN (Gherkin BDD)

**Escenario 1: Visualización del catálogo de servicios y perfiles del equipo (Happy Path)**
- **Dado** que un usuario ingresa a la plataforma web del Spá Podológico
- **Cuando** navega por la sección de vitrina digital
- **Entonces** el sistema despliega el catálogo de servicios detallando la descripción y el tiempo promedio estimado de atención de cada uno sin mostrar precios
- **Y** presenta los perfiles del equipo podológico con sus fotografías, nombres y especialidades
- **Y** ofrece una acción clara para iniciar la reserva con el servicio o podólogo de su elección.

**Escenario 2: Navegación responsiva desde dispositivo móvil (Happy Path / Responsividad)**
- **Dado** que un usuario accede a la vitrina digital desde un dispositivo móvil o smartphone
- **Cuando** visualiza las secciones del equipo podológico y catálogo de servicios
- **Entonces** el sistema adapta el diseño del contenido de manera fluida y legible
- **Y** mantiene oculta cualquier información referente a precios en todas las secciones.

**Escenario 3: Intento de consulta de precios o tarifas en el catálogo (Sad Path / Restricción Negocio)**
- **Dado** que el usuario explora el detalle de un servicio en la vitrina digital
- **Cuando** inspecciona la información del servicio seleccionado
- **Entonces** el sistema muestra la información descriptiva y el tiempo estimado de atención
- **Y** no muestra ningún campo, etiqueta ni valor numérico correspondiente a precios o tarifas.

## 5. PUNTOS ABIERTOS / DEPENDENCIAS

- **Punto Abierto 1 (Actualización de Catálogo y Perfiles):** En el PRD no se define un módulo CMS para que el administrador actualice fotos o servicios, por lo que para el MVP la vitrina manejará datos precargados o estáticos.
- **Dependencia:** Esta historia actúa como punto de entrada hacia el Motor de Reservas Inteligente (Épica P1, hu_01_reserva_citas.md).

## 6. ORDEN DE DELEGACIÓN PARA EL QA

@QA: La Historia de Usuario Presentación del Equipo Podológico y Catálogo Interactivo de Servicios con Tiempos Estimados sin Precios está lista en el archivo hu_04_vitrina_digital.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
