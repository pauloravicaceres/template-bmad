# Análisis de Flujo GitOps y Metodología BMAD-SDD

## 1. Análisis Metodológico: Desarrollo Horizontal vs. Vertical Slicing

El comportamiento que has observado en el tracker corresponde claramente a un enfoque de **Desarrollo Horizontal** encubierto. En este escenario, el enjambre intenta terminar toda la fase de "Definición y Diseño" (BA, QA, UX) para todas las historias de usuario antes de avanzar a las etapas de arquitectura y desarrollo. 

Este comportamiento rompe el principio de **Vertical Slicing** que defiende la metodología BMAD-SDD. El Vertical Slicing exige que el framework procese una rebanada vertical completa del sistema por cada requerimiento. Es decir, una sola Historia de Usuario (HU) debe atravesar todo el ciclo:
`Negocio (BA) -> Calidad Documental (QA) -> Interfaz (UX) -> Arquitectura Software (SA) -> Arquitectura Datos (DA) -> Contratos (API) -> Compilación Técnica (QT) -> Desarrollo (DEV)`

**Conclusión Metodológica:**
Una HU no está "terminada" desde la perspectiva del flujo de diseño hasta que el QA-Tech (`@QT`) la compila y aprueba cruzando datos y contratos. Volver al `@PM` justo después del `@UX` rompe la cadena de valor asíncrona del sistema, creando un cuello de botella de diseño que no se traduce en arquitectura funcional ni en código.

---

## 2. Análisis de Impacto GitOps (State Hydration y Event-Sourcing)

Permitir que el `@PM` dispare comandos `GITOPS-BRANCH-CREATE` iterativamente (feat/001, feat/002, feat/003) sin que las ramas anteriores hayan alcanzado su clímax y hayan sido fusionadas (`GITOPS-MERGE-CLOSE`) tendrá consecuencias catastróficas para el enjambre:

1. **Fractura del State Ledger (`specs/README.md`):** La gobernanza del framework exige que todo diseño propuesto (`SA`, `DA`) evalúe el Ledger actual para evitar colisiones. Si tenemos 3 ramas abiertas paralelamente, la rama `feat/003` no tendrá visibilidad de las tablas de base de datos ni los componentes creados en `feat/002` o `feat/001`, ya que residen en dimensiones (ramas) aisladas.
2. **Conflictos de Merge Inevitables:** Si múltiples ramas modifican el mismo "bus de datos" o el tracker simultáneamente (al intentar cerrarse), GitOps colapsará en conflictos de resolución manual que el enjambre no podrá sortear.
3. **Pérdida de la Fuente de la Verdad (Zero-Trust):** El sistema de *State Hydration* asume que `main` o `develop` siempre tienen la foto más reciente y consolidada. Al ramificar de un tronco desactualizado, el enjambre alucinará soluciones sobre un contexto obsoleto.

---

## 3. Propuesta de Enrutamiento (Topología Dinámica)

Para corregir la desviación y asegurar que el enjambre opere como un reloj suizo, se debe ajustar el flujo de transferencias (Handoffs) de la siguiente manera:

* **¿A quién debe pasarle el turno el `@UX`?**
  El `@UX` **NUNCA** debe devolver el control al `@PM`. Su rol finaliza su parte del trabajo y debe despachar obligatoriamente al **Arquitecto de Software (`@SA:`)**. El SA tomará los wireframes del UX y las reglas de negocio del BA para comenzar el diseño estructural (`tech-design`). 
  *Flujo correcto: `... -> @UX: Handoff a @SA -> @SA: Handoff a @DA -> ...`*

* **¿Quién es el responsable de despertar al `@PM`?**
  El responsable de devolver el ciclo al `@PM` para la próxima épica debe ser el **QA-Tech (`@QT`)** (si el enjambre está operando solo la Fase A de especificación) o el **SecOps/Tech Lead en Code Review** (si el enjambre incluye ejecución y desarrollo). 
  Solo cuando la rama técnica es validada, compilada, cerrada (`GITOPS-MERGE-CLOSE`) y el `main` es rehidratado con los nuevos artefactos, el `@QT` invoca al `@PM`:
  > *"@PM: HU 002 completada, consolidada en el Ledger y fusionada con éxito. Procede a asignar la siguiente HU."*
