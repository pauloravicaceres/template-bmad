---
name: zoneless-validator
description: Skill de auto-auditoría estricta para validar que el código Angular cumple con el paradigma Zoneless, Signals, flujos de control modernos y tipado estricto antes del handoff.
type: skill
tags: [frontend, angular, zoneless, auditoria, dev]
---

# Zoneless Code Validator — Auditoría de Calidad Frontend

## Workflow de Auto-Revisión OBLIGATORIO
Antes de escribir `@QA-AUTO:` o `@CODE-REVIEW:` en el tracker, debes ejecutar mentalmente este checklist sobre los componentes y servicios que acabas de escribir. Si algún paso falla, usa `write_file` para corregirlo inmediatamente:

1. **Regla de Control Flow Moderno:** 
   - Abre mentalmente tus archivos `.html`. ¿Usaste `*ngIf` o `*ngFor` en algún lugar? Si es así, cámbialos INMEDIATAMENTE a la sintaxis `@if` y `@for`.
2. **Regla de Inyección Funcional:**
   - Abre mentalmente tus archivos `.ts`. ¿Declaraste el constructor `constructor(private http: HttpClient) {}`? Si es así, cámbialo INMEDIATAMENTE a `private http = inject(HttpClient);`.
3. **Regla de Estado Reactivo (Signals):**
   - ¿Estás usando mutaciones manuales de variables clásicas para actualizar la UI, o utilizaste `signal()` y `computed()`? ¿Resolviste la lectura HTTP con `toSignal()`?
4. **Regla de Tipado Estricto y Formularios:**
   - ¿Hay algún tipo `any` en los modelos o componentes?
   - Si creaste un formulario, ¿está fuertemente tipado usando `FormGroup<MiInterfaz>`?
5. **Regla Standalone:**
   - ¿Tienen todos los componentes el decorador `@Component({ standalone: true, ... })` y sus respectivos imports (`imports: [TableModule, ButtonModule, ...]`) correctos de PrimeNG?

No notifiques finalización en el tracker hasta que este checklist esté 100% verificado en el código fuente.
