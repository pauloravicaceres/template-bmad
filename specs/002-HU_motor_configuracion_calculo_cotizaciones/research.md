# Investigación Técnica: Motor de Cálculo de Cotizaciones

- **ID Feature:** 001-HU_configurador_y_calculo_cotizaciones
- **Fecha:** 2026-10-02

## 1. Evaluación de Alternativas para el Motor de Cómputo

| Criterio | Opción A: Cómputo Server-Side (API REST) | Opción B: Motor Puramente Funcional Client-Side (Elegida) | Opción C: WebSockets Síncronos |
|---|---|---|---|
| Latencia de Recálculo | High (~100-300ms por keystroke) | Immediate (<1ms) | Medium (~50-100ms) |
| Experiencia de Usuario (UX) | Sensación de retardo en la UI | Feedback reactivo instantáneo | Feedback fluido pero dependiente de red |
| Carga en el Servidor | Alta (peticiones por cada cambio) | Nula durante la edición | Alta por conexiones activas |
| Tolerancia a Fallos de Red | Requiere estar 100% online | Funciona offline/localmente | Requiere conexión persistente |

## 2. Decisión Arquitectónica

Se adopta la **Opción B (Motor Puramente Funcional Client-Side)** implementado en TypeScript (`app/frontend/src/engine/calculationEngine.ts`). 
El backend re-validará la estructura antes de la persistencia final en PostgreSQL como mecanismo de seguridad (Defense in Depth).
