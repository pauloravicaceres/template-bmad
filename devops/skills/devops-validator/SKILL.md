---
name: devops-validator
description: Skill de auto-auditoría para el agente DevOps. Valida la seguridad, los multi-stage builds y la resiliencia del compose antes del handoff.
type: skill
tags: [devops, docker, ci-cd, auditoria]
---

# Infra & Cloud Native Validator — Auditoría de Despliegue

## Workflow de Auto-Revisión OBLIGATORIO
Antes de reportar éxito y pasar el turno en el tracker, debes ejecutar mentalmente este checklist sobre los archivos que acabas de aprovisionar (Compose, Dockerfile, Pipelines). Si algún paso falla, usa `write_file` para corregirlo:

1. **Regla de Multi-Stage & Rootless:** 
   - Lee tu `Dockerfile`. ¿La imagen base final es el SDK completo o un runtime ligero (`aspnet:8.0-alpine`)? ¿Declaraste `USER [nombre]` antes del comando `ENTRYPOINT`?
2. **Regla de Secretos (Leak Prevention):**
   - Escanea el `docker-compose.yml`. ¿Hay alguna contraseña en texto plano en la sección `environment:`? Si es así, cámbiala a `${VARIABLE}` y documenta que debe ir en el `.env`.
3. **Regla de Sincronización de Arranque:**
   - ¿La API (Backend) depende de PostgreSQL o Keycloak? Verifica que el `depends_on` de la API tenga explícitamente `condition: service_healthy` apuntando a la base de datos, y que la base de datos tenga un bloque `healthcheck` definido.
4. **Regla de Paridad de Entorno:**
   - ¿Aseguraste que las URLs internas (ej. la cadena de conexión de BD o el host de RabbitMQ) apunten a los *nombres de los contenedores* de la red interna de Docker (ej. `Host=eshopdb;` o `amqp://messagebus`) y NO a `localhost`?

No notifiques finalización en el tracker hasta que la infraestructura sea robusta, segura y siga principios de Alta Disponibilidad.