import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

async def send_workflow_report(to_email: str, workflow_name: str, report_content: str):
    """Sends a professional HTML workflow completion report via email."""
    if not settings.SMTP_USER or not settings.SMTP_PASS:
        logger.warning("SMTP_USER or SMTP_PASS not configured. Skipping email sent.")
        return False

    try:
        import markdown2
        # Convert markdown to HTML
        body_html = markdown2.markdown(report_content, extras=["tables", "fenced-code-blocks", "break-on-newline"])
        
        msg = MIMEMultipart()
        # Branded sender
        msg['From'] = f"AgentsRichard <{settings.SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = f"🚀 Workflow Completado: {workflow_name}"

        # HTML Template with modern CSS
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1a1a1a; margin: 0; padding: 0; background-color: #f8fafc; }}
                .container {{ max-width: 600px; margin: 20px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0; }}
                .header {{ background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); color: white; padding: 32px 24px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.025em; }}
                .content {{ padding: 32px 24px; }}
                .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 9999px; background-color: #dcfce7; color: #166534; font-size: 14px; font-weight: 600; margin-bottom: 24px; }}
                .report-box {{ background-color: #f1f5f9; padding: 24px; border-radius: 8px; border: 1px solid #e2e8f0; color: #334155; font-size: 15px; }}
                .report-box h1, .report-box h2, .report-box h3 {{ color: #1e293b; margin-top: 24px; border-bottom: none; text-decoration: none; }}
                .report-box h2 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
                .report-box pre {{ background: #1e293b; color: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; }}
                .report-box code {{ font-family: 'Consolas', 'Monaco', 'Andale Mono', 'Ubuntu Mono', monospace; font-size: 0.9em; padding: 2px 4px; background: #e2e8f0; border-radius: 4px; }}
                .footer {{ text-align: center; padding: 24px; color: #64748b; font-size: 12px; border-top: 1px solid #f1f5f9; }}
                .footer p {{ margin: 4px 0; }}
                table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
                th {{ background-color: #f8fafc; font-weight: 600; color: #475569; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AgentsRichard</h1>
                    <p style="margin-top: 8px; opacity: 0.9;">Reporte de Ejecución Inteligente</p>
                </div>
                <div class="content">
                    <div class="status-badge">✓ Ejecución Exitosa</div>
                    <p style="margin-bottom: 24px;">El workflow <strong>{workflow_name}</strong> ha finalizado sus tareas. Aquí tienes los resultados:</p>
                    
                    <div class="report-box">
                        {body_html}
                    </div>
                </div>
                <div class="footer">
                    <p>Este es un reporte automático generado por tu instancia de <strong>AgentsRichard</strong>.</p>
                    <p>&copy; {datetime.now().year} AgentsRichard Dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            import re
            clean_pass = re.sub(r'[^a-zA-Z]', '', settings.SMTP_PASS)
            server.login(settings.SMTP_USER.strip(), clean_pass)
            server.send_message(msg)
        
        logger.info(f"HTML email report sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send HTML email: {str(e)}")
        return False
