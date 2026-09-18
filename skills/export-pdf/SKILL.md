---
name: export-pdf
description: Exporta documentos Markdown (.md) a formato PDF con un diseño profesional, corporativo y listo para presentación a stakeholders.
type: skill
tags: [export, pdf, reporting, python, herramientas]
---

# Export PDF — Generador de Documentos Corporativos

## Goal
Convertir los entregables finales aprobados (Product Briefs, Historias de Usuario, Reportes) de su formato nativo Markdown a un documento PDF profesional y presentable, utilizando el motor de conversión interno.

## Input
- **Ruta del archivo Markdown original:** (ej. `files/product-analyst/pb_amely_spa.md`)
- **Ruta de destino del PDF (opcional):** Si no se provee, se guardará en la misma carpeta con la extensión `.pdf`.

## Workflow

1. **Validación de Estado:**
   - Verifica que el documento `.md` que vas a convertir tenga el estado de "Aprobado" (ya sea por el QA Documental o por el Aprobador Humano).
   - No generes PDFs de borradores incompletos.

2. **Ejecución de la Herramienta Técnica:**
   - Abre la terminal o utiliza tu capacidad de ejecución de comandos.
   - Dispara el script de conversión pasándole la ruta absoluta o relativa del archivo `.md`.
   - **Comando base:** `python skills/export-pdf/scripts/tool.py "ruta/al/archivo.md"`

3. **Confirmación y Registro:**
   - Verifica en la salida de la terminal que el PDF se generó con éxito.
   - Si estás registrando un avance en el `tracker_bmad.md`, menciona que la versión PDF está disponible.

## Notas
- El script de Python ya maneja internamente la inyección de estilos CSS corporativos, la paginación y la renderización de tablas. No necesitas modificar el contenido del Markdown para que se vea bien en el PDF.
- Si el comando arroja un error de dependencias, informa al usuario que debe ejecutar `pip install markdown weasyprint`.