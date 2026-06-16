from weasyprint import HTML, CSS
from datetime import datetime

def generar_pdf_auditoria(contenido_ia, nombre_archivo="Informe_Auditoria_Nivexa.pdf"):
    """
    Genera un PDF profesional con branding Nivexa.
    """
    html_template = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 20mm; }}
            body {{ font-family: 'Arial', sans-serif; line-height: 1.6; color: #333; }}
            .header {{ background-color: #0f172a; color: white; padding: 20px; text-align: center; }}
            h1 {{ font-size: 24px; }}
            .content {{ margin-top: 30px; }}
            .footer {{ font-size: 10px; color: #666; text-align: center; margin-top: 50px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AUDITORÍA FORENSE NIVEXA QUANTUM</h1>
            <p>{datetime.now().strftime('%d/%m/%Y')}</p>
        </div>
        <div class="content">
            {contenido_ia.replace(chr(10), '<br>')}
        </div>
        <div class="footer">Documento privado generado por Nivexa Systems.</div>
    </body>
    </html>
    """
    # Convierte el HTML en PDF
    HTML(string=html_template).write_pdf(nombre_archivo)
    return nombre_archivo
