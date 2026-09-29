---
name: fastapi-validator
description: Skill de auto-auditoría estricta para validar que el código de FastAPI sea no-bloqueante, esté tipado con Pydantic y registre correctamente los WebSockets y Routers.
type: skill
tags: [backend, fastapi, python, websockets, auditoria]
---

# FastAPI Code Validator — Auditoría de Calidad del Código Generado

## Workflow de Auto-Revisión OBLIGATORIO
Antes de escribir `@QA-AUTO:` o `@CODE-REVIEW:` en el tracker, debes ejecutar mentalmente este checklist sobre el código que acabas de escribir. Si algún paso falla, usa `write_file` para corregirlo inmediatamente:

1. **Regla Asíncrona (Event Loop Safe):** 
   - ¿Definiste los endpoints y handlers de WebSockets con `async def`? 
   - Revisa mentalmente si llamaste a `time.sleep()` o a alguna lectura pesada en un hilo bloqueante. Cámbialo a `await asyncio.sleep()` o usa llamadas asíncronas para no ahogar Uvicorn.
2. **Regla de Pydantic y Tipado:**
   - ¿Los parámetros del Request Body usan clases hijas de `BaseModel`? 
   - ¿Especificaste el `response_model` en el decorador del endpoint (ej. `@router.get("/", response_model=MyResponse)`)?
3. **Regla de Modularidad (APIRouter):**
   - ¿Tus nuevas rutas fueron metidas directamente en el `main.py` engordándolo? Si es así, sácalas a un archivo separado, usa `APIRouter` y haz `app.include_router(router)` en el `main.py`.
4. **Regla de WebSockets y Watchdog:**
   - Si creaste un proceso de `watchdog`, ¿verificaste que emite los eventos hacia la cola asyncio sin colisionar los hilos de SO?
   - ¿Verificaste que la desconexión del WebSocket (`WebSocketDisconnect`) esté envuelta en un bloque `try-except` para retirar limpiamente la conexión del gestor?

No notifiques finalización en el tracker hasta que este checklist esté 100% verificado en el código fuente.