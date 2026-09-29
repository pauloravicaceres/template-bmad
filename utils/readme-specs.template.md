# 🗺️ Mapa de Specs (Product State Ledger)

> **Regla de Actualización:** Este archivo es el registro histórico del estado del producto. Las modificaciones a la tabla deben respetar estrictamente el formato Markdown para permitir su parseo automatizado.

### Glosario de Estados Permitidos (Diccionario Finito)
Para mantener el determinismo del *Ledger*, los agentes mutadores y lectores utilizarán estrictamente este conjunto cerrado de estados:
* **`ACTIVE`**: Funcionalidad probada y en producción. Es la fuente de verdad actual.
* **`IN-PROGRESS`**: Spec en diseño activo.
* **`READY-FOR-DEV`**: Diseño técnico aprobado, listo para Fase D.
* **`DRAFT` / `BACKLOG`**: Idea o requerimiento sin refinar; sin diseño técnico ni código asociado.
* **`BLOCKED`**: Avance detenido por falta de definiciones o dependencias externas.
* **`DEPRECATED`**: Funcionalidad completamente obsoleta o reemplazada. Estrictamente prohibido usarla como base.
* **`DEPRECATED-PARTIAL`**: Funcionalidad reemplazada solo parcialmente. Obligatorio consultar las *Notas de Relación* para identificar qué partes siguen vivas.

---

### Registro del Ledger

| N° | Spec / Nombre | HU / Épica Origen | Qué aporta | Estado | Rama |
|----|---------------|-------------------|------------|--------|------|

---

## 🔗 Notas de Relación entre Specs
* (Aún no hay relaciones registradas)

