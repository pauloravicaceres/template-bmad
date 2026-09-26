---
name: vsa-validator
description: Skill de auto-auditoría estricta para validar que el código generado cumple con Vertical Slice Architecture (VSA), Fluent API y registro de dependencias antes del handoff.
type: skill
tags: [backend, vsa, auditoria, dev, csharp]
---

# VSA Code Validator — Auditoría de Calidad del Código Generado

## Workflow de Auto-Revisión OBLIGATORIO
Antes de escribir `@QA-AUTO:` o `@CODE-REVIEW:` en el tracker, debes ejecutar mentalmente este checklist sobre el código que acabas de escribir. Si algún paso falla, usa `write_file` para corregirlo inmediatamente:

1. **Regla de Co-locación VSA:** 
   - ¿Están el `Endpoint.cs`, `Command.cs`, `Validator.cs` y el `Handler.cs` guardados exactamente en la misma carpeta física de la Feature? Si los separaste en carpetas horizontales (`/Controllers` o `/Services`), corrige las rutas de inmediato.
2. **Regla de Pureza de Dominio (Fluent API):**
   - Si creaste una nueva Entidad/Agregado, verifica que NO tenga decoradores `[Table]`, `[Column]`, `[Key]`. ¿Creaste su respectivo `IEntityTypeConfiguration<T>` en la carpeta `/Data/Configurations/` y lo registraste en el DbContext?
3. **Regla de Registro DI (Dependency Injection):**
   - Si creaste un Decorador (ej. para Redis) o un servicio específico que no se auto-descubre, ¿lo registraste en el método `Add[Modulo]Module()` del archivo `[Modulo]Module.cs`?
4. **Regla de Sintaxis y Excepciones:**
   - ¿Usaste Constructores Primarios (Primary Constructors)?
   - ¿Verificaste no estar lanzando `Exception` genéricas, sino `BadRequestException`, `NotFoundException` o `InternalServerException` de la capa `Shared`?

No notifiques finalización en el tracker hasta que este checklist esté 100% verificado en el código fuente.