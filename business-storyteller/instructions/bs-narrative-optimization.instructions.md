---
description: 'Usar para transformar la idea cruda en una narrativa estructurada en primera persona y para dar formato a la salida visual en pantalla para el usuario.'
applyTo: '**'
---

# Estándar de Optimización Narrativa de Negocio

> Metodología de transformación de requerimientos informales en narrativas operativas para BMAD.

---

## 1. Las 4 Transformaciones Obligatorias de Negocio

Al procesar la idea madura del stakeholder, debes aplicar las siguientes 4 transformaciones:

### 1. Inyección del Dolor (Pain Point)
- **Regla:** Si la idea original se limita a listar funciones (*"Quiero una web con reservas y login"*), deduce y explicita el problema operativo, comercial o de fricción de tiempo que motiva la inversión (*"Actualmente gestionamos las citas por teléfono, lo que provoca cruces de horarios y pérdida de clientes"*).

### 2. Clarificación de Actores
- **Regla:** Identifica y nombra explícitamente a todos los actores involucrados en el ecosistema (ej. clientes finales, profesionales de atención, personal de recepción, administradores de negocio).

### 3. Agrupación Modular
- **Regla:** Transforma listas desordenadas o viñetas sueltas en bloques funcionales lógicos y cohesivos (ej. *Vitrina y Catálogo*, *Motor de Reservas*, *Autogestión del Cliente*, *Notificaciones Transaccionales*, *Panel de Gestión Interna*).

### 4. Tono Narrativo en Primera Persona (1st Person Stakeholder)
- **Regla:** Redacta toda la idea simulando la voz de un líder de negocio o stakeholder altamente articulado y estructurado (*"Soy el fundador de...", "Necesitamos resolver...", "Nuestra meta es..."*).

---

## 2. Formato de Salida Visual en Terminal

Tras ejecutar las acciones de guardado MCP, imprime en la consola la revisión completa para el usuario:

```xml
<idea_usuario>
[Redacción narrativa de la idea optimizada en primera persona. 
 Estructura: Contexto y Dolor de Negocio → Actores involucrados → Agrupación modular de capacidades requeridas].
</idea_usuario>
```

### ¿Por qué esta versión es mejor para el agente PA?

1. **[Beneficio para PROBLEMA]:** Explicación de cómo la redacción delimita hechos objetivos frente a inferencias operativas.
2. **[Beneficio para OBJETIVO Y CRITERIOS DE ÉXITO]:** Contexto de negocio que facilitará al PA la extracción de métricas clave.
3. **[Beneficio para ALCANCE Y RESTRICCIONES]:** Cómo la agrupación modular previene el scope creep y simplifica el futuro Backlog del MVP.
4. **[Beneficio Adicional]:** Ventaja analítica o estratégica particular de este caso.

---

## 3. Directiva Condicional para Ecosistemas Preexistentes (Modo Brownfield)

Si existe el archivo `files/context/legacy_ecosystem.md`:
- **Regla de Subordinación de Negocio:** Léelo en su totalidad y subordina tu narrativa a las reglas, dominio de negocio, actores y terminología descritos en dicho archivo, sean cuales sean.
- Enmarca el dolor y la necesidad como una extensión, integración o mejora sobre el sistema preexistente, evitando inventar un modelo de negocio paralelo o desconectado.
- Si dicho archivo no existe o está vacío, optimiza la narrativa libremente en base al requerimiento recibido (Modo Greenfield).
