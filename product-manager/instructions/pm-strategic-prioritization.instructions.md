---
description: 'Usar al estructurar el Backlog Inicial del MVP y al seleccionar la siguiente épica en ciclos de iteración. Define la metodología de Ruta Crítica Desacoplada y la escala de prelación P1 a P5.'
applyTo: '**'
---

# Metodología de Priorización Estratégica (Ruta Crítica)

> Algoritmo de decisión agnóstico para ordenar el Backlog del MVP en el framework BMAD.

---

## 1. Principio de la Ruta Crítica Desacoplada
El Producto Mínimo Viable (MVP) no es una versión reducida de todo el sistema; es el **camino transaccional más corto que entrega el valor principal del producto al usuario**.

Al analizar el Product Brief, desglosa el alcance aplicando estrictamente la jerarquía **P1 → P5**:

```
┌────────────────────────────────────────────────────────┐
│  [P1] CORE TRANSACCIONAL (El motor principal)         │
├────────────────────────────────────────────────────────┤
│  [P2] DEPENDENCIAS Y ALIMENTACIÓN (Datos maestros/UI) │
├────────────────────────────────────────────────────────┤
│  [P3] AUTOGESTIÓN Y EXCEPCIONES (Autonomía de actor)   │
├────────────────────────────────────────────────────────┤
│  [P4] AUTOMATIZACIONES EXTERNAS (Canales/Terceros)    │
├────────────────────────────────────────────────────────┤
│  [P5] GESTIÓN INTERNA Y BACKOFFICE (Supervisión)      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Definición Canónica de Niveles de Prioridad

### [P1] — Funcionalidad Core (Núcleo Rector)
- **Definición:** La transacción primaria sin la cual el producto pierde completamente su razón de ser.
- **Prueba de Fuego:** Si eliminas esta funcionalidad, ¿el usuario aún puede obtener el beneficio principal del producto? Si la respuesta es NO, es P1.
- **Regla:** Solo puede existir **UNA** Épica catalogada como P1 en el backlog inicial.

### [P2] — Dependencias de Datos y Vitrina/Consulta
- **Definición:** Las vistas de consulta, catálogos o entidades de información que sustentan o alimentan al flujo P1.
- **Ejemplo:** En un sistema de reservas, el catálogo de servicios y profesionales; en un ecommerce, el catálogo de productos.

### [P3] — Autogestión del Usuario y Manejo de Excepciones
- **Definición:** Capacidades que permiten al usuario final gestionar, modificar o cancelar de forma autónoma el resultado del Core.
- **Ejemplo:** Módulo de cancelación de citas, reprogramación, consulta de estado de pedidos.

### [P4] — Automatizaciones Asíncronas y Notificaciones Externas
- **Definición:** Disparadores de eventos secundarios hacia canales externos o terceros.
- **Ejemplo:** Notificaciones transaccionales vía mensajería, alertas automáticas, integraciones de correo.

### [P5] — Paneles Privados, Backoffice y Gestión Operativa
- **Definición:** Herramientas de visualización y control interno para los administradores o colaboradores.
- **Ejemplo:** Panel de agenda para el profesional, reportes de recepción, gestión de disponibilidad.

---

## 3. Heurística de Selección en Ciclos de Iteración
Cuando el Diseñador UX finaliza una HU y el PM es invocado en el tracker:
1. Inspecciona el tracker para verificar cuál fue la última Épica delegada que completó el circuito (`@UX:` aprobado).
2. Lee el archivo `mvp_[nombre_corto].md` y localiza el Backlog Inicial.
3. Selecciona la Épica inmediata con menor número de prioridad que **aún no haya sido inyectada** en el tracker (ej. si P1 fue aprobada, toma P2; luego P3; y así sucesivamente).
4. Si todas las Épicas del backlog han completado su ciclo, activa el **Stage-Gate de Cierre (`@HUMANO:`)**.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
