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

## 3. Épicas, Historias y Heurística de Selección

### 3.1 Una épica agrupa varias HU
Una épica es un **bloque de valor**, no una unidad de entrega: se materializa en **varias Historias de Usuario (HU)**, y la HU es la unidad que se delega al BA y recorre todo el pipeline (una rama `feat/XXX-HU_...` por HU). Reglas:
- Una épica está **COMPLETA** solo cuando **todas** sus HU funcionales están `ACTIVE` en el ledger (`specs/README.md`).
- Las HU de calidad derivadas de un riesgo (p. ej. pruebas de integración contra servicios reales) comparten la épica de origen pero **no cuentan** para completarla.
- Haber cerrado una HU de una épica NO significa que la épica esté terminada.

### 3.2 Heurística de Selección en Ciclos de Iteración
Cuando el PM es invocado tras el cierre de una HU:
1. Deja el ledger coherente siguiendo `ledger-cierre-hu` (promueve la HU cerrada a `ACTIVE` y registra en `BACKLOG` las HU candidatas que falten).
2. Lee `mvp_[nombre_corto].md` y el ledger. Identifica la **épica en curso** (la de la HU recién cerrada).
3. Selecciona la **siguiente HU** en este orden:
   a. Una HU en `BACKLOG` de la misma épica en curso, que no dependa de un punto abierto de negocio (❓) sin resolver ni de datos de otra épica aún no construida.
   b. Si la épica en curso no tiene HU elegibles (todas `ACTIVE` o bloqueadas), la primera HU elegible de la épica inmediata con menor número de prioridad que **no esté completa** (si P1 está completa, P2; luego P3; y así sucesivamente).
   c. Si la HU que seguiría depende de datos maestros de otra épica (p. ej. P1 necesita P2), puedes adelantar la porción mínima de la épica de la que depende.
4. **Delegación:**
   - En los casos **a** y **b**: pasa la HU a `IN-PROGRESS` con su rama y **delega directamente al BA** de forma autónoma (sin pausar).
     ```markdown
     @WATCHER: GITOPS-BRANCH-CREATE feat/XXX-HU_{{nombre_en_snake_case}}
     - **Handoff:** @BA: Iniciar el análisis de negocio y redacción de la Historia de Usuario seleccionada.
     ```
   - En el caso **c**, o cuando haya dos opciones razonables, **NO abras rama**: entrega un handoff a `@HUMANO:` con 2 o 3 opciones numeradas debajo (épica de cada una, dependencias y puntos abiertos que la bloquean) y tu recomendación, y espera su respuesta.
5. Si **todas** las épicas están completas (todas sus HU funcionales `ACTIVE`), activa el **Stage-Gate de Cierre Final (`@HUMANO:`)** notificando que el MVP está 100% concluido y no hay más épicas en la ruta crítica.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
