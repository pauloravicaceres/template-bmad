---
description: 'Política estricta de Cero Alucinación para el agente Backend Developer. Prohíbe código bloqueante, falta de tipado y el uso de librerías síncronas ajenas a FastAPI.'
applyTo: '**'
---

# Zero Hallucination Policy — Backend (FastAPI / Python)

## 1. Fronteras Estrictas de Implementación
- **Cero Placeholders y Funciones Vacías:** Tienes PROHIBIDO dejar rutas o funciones con `pass` o `raise NotImplementedError`. Todo endpoint o listener debe estar 100% implementado.
- **Cero Bloqueo del Event Loop:** Tienes estrictamente PROHIBIDO usar funciones síncronas bloqueantes (ej. `time.sleep()`, `requests.get()`, leer archivos enormes con `open()` síncrono en rutas de alto tráfico) en un bloque `async def`. Usa alternativas asíncronas (`asyncio.sleep()`, `httpx`, `aiofiles`) o transpórtalas con `run_in_executor()`.
- **Cero Tipo Dinámico No Controlado:** Prohibido el uso de la cláusula global `Any` de forma arbitraria para evitar pensar. Todo payload HTTP y todo evento de WebSocket DEBE estar fuertemente tipado usando modelos de `pydantic`.
- **Librerías Fantasma Prohibidas:** 
  - 🚫 Usa `FastAPI` y `Uvicorn`, NUNCA `Flask` o `Django`.
  - 🚫 Usa `httpx` para peticiones, NUNCA `requests` bloqueante en el flujo asíncrono.

## 2. Fidelidad Absoluta al Contrato
- Los nombres de los atributos en los modelos Pydantic (`BaseModel`) deben ser **copias exactas** de los JSON requeridos en el `tech-design_*.md`. Si la API demanda camelCase, usa configuración en Pydantic (`alias_generator`, `populate_by_name`), pero no rompas el contrato hacia el cliente.

## 3. Protocolo Anti-Confirmación Fantasma
1. Ejecuta `write_file` para generar el código `.py`.
2. Obligatorio: Ejecuta `read_file` sobre la ruta exacta recién escrita para verificar que el archivo existe y no está truncado.
3. Solo tras validar físicamente el archivo, notifica la finalización en el tracker.

[IMPORT_SKILL: skills/fastapi-validator/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
