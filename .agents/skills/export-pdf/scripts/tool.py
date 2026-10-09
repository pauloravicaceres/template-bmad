import sys
from pathlib import Path
try:
    import markdown
    from weasyprint import HTML, CSS
except ImportError:
    print("❌ Faltan dependencias. Ejecuta: pip install markdown weasyprint")
    sys.exit(1)

# ==========================================
# ESTILOS CSS CORPORATIVOS (Profesional & Limpio)
# ==========================================
ESTILO_CORPORATIVO = """
    @page {
        margin: 2.5cm 2cm;
        size: A4;
        @bottom-right {
            content: "Página " counter(page) " de " counter(pages);
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 9pt;
            color: #666;
        }
    }
    
    body {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        line-height: 1.6;
        color: #333333;
        font-size: 11pt;
    }
    
    h1, h2, h3, h4 {
        color: #1a365d; /* Azul corporativo oscuro */
        font-weight: 600;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
    }
    
    h1 { font-size: 24pt; border-bottom: 2px solid #2b6cb0; padding-bottom: 5px; }
    h2 { font-size: 18pt; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
    h3 { font-size: 14pt; }
    
    p, li { margin-bottom: 0.8em; }
    
    /* Formato de Tablas */
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 1.5em 0;
        font-size: 10.5pt;
    }
    th, td {
        border: 1px solid #cbd5e0;
        padding: 10px 12px;
        text-align: left;
    }
    th {
        background-color: #f7fafc;
        color: #2d3748;
        font-weight: bold;
    }
    tr:nth-child(even) { background-color: #f8fafc; }
    
    /* Bloques de Código y Citas */
    pre, code {
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: #f1f5f9;
        border-radius: 4px;
        font-size: 9.5pt;
    }
    pre {
        padding: 12px;
        border: 1px solid #e2e8f0;
        overflow-x: auto;
    }
    blockquote {
        border-left: 4px solid #3182ce;
        margin: 1.5em 0;
        padding: 0.5em 1em;
        background-color: #ebf8ff;
        color: #2c5282;
        font-style: italic;
    }
    
    /* Checklist y Tareas */
    ul { list-style-type: square; }
"""

def convertir_md_a_pdf(ruta_md, ruta_pdf=None):
    ruta_md = Path(ruta_md).resolve()
    
    if not ruta_md.exists():
        print(f"❌ Error: El archivo {ruta_md} no existe.")
        sys.exit(1)
        
    if not ruta_pdf:
        # Generar el PDF en la misma carpeta que el MD, con el mismo nombre
        ruta_pdf = ruta_md.with_suffix('.pdf')
    else:
        ruta_pdf = Path(ruta_pdf).resolve()
        
    print(f"📄 Leyendo archivo Markdown: {ruta_md.name}")
    
    with open(ruta_md, 'r', encoding='utf-8') as f:
        texto_md = f.read()

    # Extensiones activadas para soportar tablas, código, checklists y formato extra
    html_body = markdown.markdown(
        texto_md, 
        extensions=['tables', 'fenced_code', 'sane_lists', 'nl2br']
    )
    
    # Envolver en un HTML completo
    html_completo = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>{ruta_md.stem}</title>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """

    print("🎨 Aplicando estilos corporativos y renderizando PDF...")
    
    try:
        html = HTML(string=html_completo, base_url=str(ruta_md.parent))
        css = CSS(string=ESTILO_CORPORATIVO)
        html.write_pdf(ruta_pdf, stylesheets=[css])
        print(f"✅ PDF generado exitosamente en:\n{ruta_pdf}")
    except Exception as e:
        print(f"❌ Error durante la renderización del PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python tool.py <ruta_archivo.md> [ruta_archivo.pdf]")
        sys.exit(1)
        
    archivo_entrada = sys.argv[1]
    archivo_salida = sys.argv[2] if len(sys.argv) > 2 else None
    
    convertir_md_a_pdf(archivo_entrada, archivo_salida)