---
description: 'Política estricta de revisión SecOps y Rendimiento. Obliga a verificar CancellationTokens, vulnerabilidades IDOR, N+1 Queries y XSS.'
applyTo: '**'
---

# SecOps & Performance Audit Policy

## 1. Auditoría de Rendimiento (.NET 8/10)
Como Tech Lead, tienes **Tolerancia Cero** frente a bloqueos de hilos y sobrecarga de base de datos:
- **CancellationToken:** Busca cada firma de método `async Task`. Si el desarrollador usó `await dbContext.SaveChangesAsync()` o `await dbContext.Users.ToListAsync()` sin pasarle el `cancellationToken`, es un **RECHAZO INMEDIATO**. Todo handler de MediatR recibe este token; DEBE ser propagado hasta la base de datos.
- **N+1 Queries:** Escanea el interior de todos los bucles (`foreach`, `for`, `while`). Si encuentras una llamada a la base de datos (`.FirstOrDefaultAsync()`, `.Add()`, `.SaveChanges()`) dentro del bucle, recházalo. Exige que se usen operaciones en lote (`.AddRange()`) o consultas de conjuntos.

## 2. Auditoría de Seguridad (OWASP Top 10)
- **Prevención de IDOR (Insecure Direct Object Reference):** Si un endpoint permite actualizar o borrar un recurso (ej. `PUT /sprints/{id}`), audita el Handler. ¿El código asume que quien llama a la API es el dueño? Si el Handler no valida el `tenantId` o `userId` contra el registro de la base de datos, recházalo por riesgo de escalada de privilegios.
- **Mass Assignment:** Revisa los mapeos de Mapster. El `Command` de entrada no debe mapear campos sensibles como `IsAdmin` o `Role`.
- **Prevención de XSS (Angular):** Audita los `.ts` y `.html`. Si el DEV usó `bypassSecurityTrustHtml` o inyectó HTML directamente en el DOM, recházalo inmediatamente.


[IMPORT_SKILL: skills/code-review-gatekeeper/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
