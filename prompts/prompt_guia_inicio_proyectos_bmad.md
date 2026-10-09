# Prompt para agente CLI — Documentación operativa para iniciar proyectos BMAD

## Rol y objetivo

Actúa como ingeniero de software senior, arquitecto de sistemas y technical writer. Trabaja **directamente sobre el repositorio actual** del ecosistema BMAD + SDD + Herdr. Tu misión es **crear o actualizar documentación operativa real, completa y comprobable** para que cualquier desarrollador pueda iniciar un proyecto nuevo reutilizando la instalación única del motor BMAD, sin clonar el ecosistema por cada proyecto.

**Ejecuta las modificaciones**, no te limites a entregar recomendaciones, propuestas, informes o planes. No implementes nuevas funciones de producto ni refactorices el runtime salvo que sea indispensable para corregir un ejemplo documental erróneo; en ese caso prioriza documentar el comportamiento real y señala la limitación al finalizar.

## Contexto funcional que debes verificar, no asumir

El repositorio ha sido modificado para soportar:
- Un motor BMAD compartido y múltiples workspaces/proyectos independientes.
- Proveedores de IA configurables (Claude, Codex y posiblemente Gemini), por agente o fase.
- Opciones de esfuerzo de razonamiento (`effort`) con traducción específica por proveedor.
- Orquestación de agentes con Herdr, watcher, handoffs y artefactos.
- Flujo BMAD + SDD y posiblemente integración con SpecKit.

Estas son **hipótesis a comprobar en el código**. No inventes flags, comandos, nombres de scripts, esquemas JSON, rutas, agentes, dependencias ni funcionalidades que no existan.

## 1. Inspección dirigida y fuente de verdad

Antes de escribir, revisa únicamente lo necesario para reconstruir el flujo vigente:
1. `README.md`, `AGENTS.md`, guías vigentes, archivos de configuración y ejemplos.
2. Entradas CLI, `--help`, scripts de arranque, inicialización y gestión de proyectos/workspaces.
3. Módulos que resuelven rutas y contexto de proyecto, configuran proveedores/modelos/effort, arrancan Herdr, watcher y fases BMAD/SDD.
4. Estructura de carpetas que se crea realmente en un proyecto nuevo, ubicación de artefactos, handoffs, logs y código de la aplicación.
5. Pruebas existentes que confirmen las opciones y el comportamiento.

Usa búsquedas acotadas, sin cargar el repositorio completo ni generar archivos auxiliares de auditoría. Si una capacidad no está implementada, no la documentes como disponible.

## 2. Archivos de documentación que debes modificar

- **Preferencia:** crear o actualizar la guía canónica `SETUP.md` en la raíz (o reutilizar la ubicación documental ya establecida en el repositorio, si existe).
- Actualizar el `README.md` principal con una sección visible **«Iniciar un nuevo proyecto»**: requisitos mínimos, resumen de 3–5 pasos y enlace relativo correcto a `SETUP.md`.
- Si ya hay una guía equivalente, **consolídala**: no crees una segunda guía duplicada. Actualiza los enlaces entrantes y elimina documentos duplicados solo cuando sea seguro.
- No crees carpetas `audit/`, `reports/`, `diagnosticos/`, `temp/` ni documentos históricos o de planificación.
- No uses la frase «Referencia histórica conservada; no usar como instrucciones vigentes». Reescribe o sustituye el contenido obsoleto.

## 3. Contenido obligatorio de la guía

Escribe una guía en **español**, orientada a desarrolladores que usarán principalmente **Windows + PowerShell**, con ejemplos verificados y variables de rutas fáciles de adaptar. Incluye:

### A. Visión general
- Qué es el motor compartido y qué es un workspace/proyecto.
- Qué se comparte entre proyectos y qué debe quedar aislado.
- Diagrama de arquitectura general.

### B. Prerrequisitos
- Versiones y dependencias que realmente exija el repositorio (Python, Herdr, CLI de proveedores, etc.).
- Cómo verificar instalaciones y autenticación, únicamente con comandos reales y seguros.
- Cómo preparar el entorno Python si aplica, distinguiendo dependencias opcionales.

### C. Inicio rápido (camino feliz)
- Pasos **numerados y ejecutables**, desde abrir PowerShell en el motor hasta obtener un proyecto inicializado.
- Cómo elegir la ruta del workspace fuera del motor, si así lo soporta la implementación.
- Comando exacto de inicialización, o procedimiento real si no existe comando único.
- Ejemplo de estructura resultante del workspace, validada contra el código.
- Cómo proporcionar la idea inicial o entrada de negocio; ruta y formato reales.
- Cómo configurar proveedor/modelo/effort con claves que existan en la configuración.
- Cómo iniciar agentes, watcher y/o fases, con el orden correcto y los comandos reales.
- Cómo monitorear progreso, handoffs, documentos y código generado.
- Cómo detener/reanudar de forma segura y evitar ejecuciones duplicadas.
- Cómo comprobar que el proyecto está listo y dónde encontrar resultados.

### D. Operación multiworkspace
- Cómo crear un segundo proyecto sin clonar el motor.
- Cómo seleccionar el proyecto activo y cómo verificarlo antes de arrancar agentes.
- Qué ocurre con sesiones, identificadores, rutas y estado al alternar proyectos.
- Reglas para evitar contaminación entre workspaces; advertencias sobre procesos concurrentes si no hay soporte probado.

### E. Configuración y resolución de problemas
- Ejemplo mínimo de configuración basado en el esquema real, sin credenciales.
- Tabla con parámetros clave, ubicación, valor de ejemplo y efecto.
- Errores habituales comprobables: ruta inexistente, proveedor no instalado/autenticado, watcher sin tracker, archivo de entrada ausente, permisos de escritura, sesión previa, problemas de Herdr.
- Cómo diagnosticar sin borrar archivos ni desactivar protecciones.

### F. Referencia rápida
- Tabla de comandos reales, cuándo usarlos y desde qué directorio ejecutarlos.
- Checklist final de arranque y enlaces relativos a documentación de arquitectura, configuración y desarrollo.

## 4. Diagramas obligatorios, adaptados al funcionamiento real

Usa bloques Markdown `mermaid` compatibles con la vista previa de GitHub y VS Code. Incluye **todos los diagramas que aporten claridad**, como mínimo cuando el código permita sustentarlos:
1. **Arquitectura**: motor BMAD compartido, configuración, Herdr, watcher, agentes y workspaces independientes.
2. **Flujo de inicio de un proyecto**: prerrequisitos → creación/selección del workspace → configuración → entrada → arranque → verificación.
3. **Diagrama de secuencia**: usuario/CLI → runtime → Herdr/agentes → watcher/handoffs → artefactos/código.
4. **Flujo BMAD + SDD**: fases, roles y artefactos reales, con decisiones y puntos de validación.
5. **Árbol de carpetas** en bloque `text` (más claro que Mermaid para directorios), mostrando motor vs. proyecto.
6. **Ciclo de vida operativo**: iniciar, supervisar, detener y reanudar, solo si hay evidencia de estas capacidades.

Requisitos para diagramas:
- Nombres y rutas fieles a la implementación; no atribuyas funcionalidades hipotéticas.
- Mermaid válido: nodos con identificadores simples, etiquetas legibles y sin sintaxis experimental innecesaria.
- No dupliques diagramas que expliquen exactamente lo mismo.
- Coloca cada diagrama cerca de los pasos que ilustra y explícalo brevemente.

## 5. Validación obligatoria

1. Comprueba que todos los comandos, flags y nombres de archivos de la guía existen; usa `--help` o inspección del parser cuando sea posible, **sin iniciar la flota real**.
2. Comprueba que los fragmentos JSON/TOML/YAML sean sintácticamente válidos y respeten el esquema implementado.
3. Verifica enlaces relativos del README y de la guía.
4. Valida sintaxis de los bloques Mermaid con herramientas disponibles, sin instalar paquetes innecesarios.
5. Ejecuta pruebas focalizadas del runtime/documentación cuando existan; no ejecutes acciones costosas o destructivas.
6. Corrige cualquier discrepancia encontrada antes de terminar.

## 6. Restricciones

- **Sí debes editar y guardar** README y la guía definitiva.
- No generes reportes, diagnósticos, propuestas, archivos de trabajo ni carpetas adicionales.
- No inventes comandos ni simules resultados de pruebas.
- No modifiques datos o artefactos de workspaces existentes.
- No arranques agentes reales, no consumas APIs innecesariamente, no hagas commits y no cambies de rama.
- No incluyas secretos, tokens, credenciales ni rutas privadas innecesarias.
- Si un paso no puede verificarse o una función aún no existe, indícalo explícitamente en la guía como limitación, sin presentar instrucciones ficticias.
- No detengas el trabajo después de inspeccionar: **la tarea termina cuando la documentación está escrita y validada**.

## 7. Criterios de aceptación

La tarea está completa únicamente si:
- [ ] README contiene una sección clara «Iniciar un nuevo proyecto» con enlace funcional.
- [ ] `SETUP.md` es la única guía canónica, completa, actualizada y en español.
- [ ] Un desarrollador puede seguir los pasos de principio a fin sin deducir rutas o comandos.
- [ ] Se explica el uso de múltiples workspaces sin clonar el motor.
- [ ] Se documentan proveedores y effort conforme al código vigente.
- [ ] Diagramas Mermaid describen arquitectura, arranque y coordinación reales.
- [ ] No hay referencias históricas disfrazadas de documentación operativa.
- [ ] Enlaces, ejemplos y comandos han sido contrastados con el repositorio.
- [ ] No se generaron reportes ni archivos auxiliares innecesarios.

## 8. Respuesta final breve

Al terminar, informa únicamente:
- Archivos creados o actualizados.
- Secciones y diagramas incorporados.
- Validaciones realizadas y resultados.
- Limitaciones reales que impidan seguir algún paso.

**Empieza ahora: inspecciona el repositorio, escribe la guía, actualiza el README y valida el resultado.**
