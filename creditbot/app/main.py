"""Punto de entrada de la aplicación FastAPI."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes_admin import router as admin_router
from app.api.routes_health import router as health_router
from app.api.routes_simulator import router as simulator_router
from app.api.routes_webhook import router as webhook_router

# Crear la instancia principal de FastAPI
app = FastAPI(title="CrediBot", version="0.1.0")


@app.get("/", response_class=HTMLResponse)
def root():
    """Pantalla inicial para probar y presentar el backend."""
    return """
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>CrediBot</title>
        <style>
          :root {
            color-scheme: light;
            --bg: #f4f7fb;
            --ink: #101828;
            --muted: #475467;
            --line: #d7dde8;
            --brand: #0f766e;
            --brand-dark: #115e59;
            --accent: #1d4ed8;
            --panel: #ffffff;
            --soft: #eef6f4;
          }
          * {
            box-sizing: border-box;
          }
          body {
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background: var(--bg);
            color: var(--ink);
          }
          main {
            max-width: 1040px;
            margin: 0 auto;
            padding: 42px 20px 52px;
          }
          h1 {
            margin: 8px 0 10px;
            font-size: 40px;
            line-height: 1.1;
          }
          h2 {
            margin: 0 0 10px;
            font-size: 22px;
          }
          h3 {
            margin: 0 0 8px;
            font-size: 16px;
          }
          p {
            margin: 0;
            line-height: 1.5;
            color: var(--muted);
          }
          code, pre {
            font-family: Consolas, Monaco, monospace;
          }
          pre {
            margin: 14px 0 0;
            overflow-x: auto;
            border-radius: 8px;
            background: #111827;
            color: #e5e7eb;
            padding: 14px;
            line-height: 1.45;
          }
          code {
            background: #eef2f7;
            padding: 2px 5px;
            border-radius: 4px;
            color: #344054;
          }
          .hero {
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 22px;
            align-items: stretch;
          }
          .hero-card,
          .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 14px 36px rgba(16, 24, 40, 0.06);
          }
          .hero-card {
            padding: 28px;
          }
          .status-card {
            padding: 22px;
            background: #102a43;
            color: #ffffff;
          }
          .status-card p {
            color: #dbeafe;
          }
          .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: #34d399;
            display: inline-block;
            margin-right: 8px;
          }
          .badge {
            display: inline-flex;
            align-items: center;
            width: fit-content;
            border-radius: 999px;
            padding: 6px 10px;
            background: var(--soft);
            color: var(--brand-dark);
            font-size: 13px;
            font-weight: 700;
          }
          .actions {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 22px;
          }
          a {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 10px 14px;
            border-radius: 6px;
            background: var(--accent);
            color: white;
            text-decoration: none;
            font-weight: 700;
          }
          a.secondary {
            background: #ffffff;
            color: #1f2937;
            border: 1px solid var(--line);
          }
          .grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 18px;
            margin-top: 22px;
          }
          .panel {
            padding: 22px;
          }
          .mini-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin-top: 16px;
          }
          .mini {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px;
            background: #fbfcfe;
          }
          ol {
            margin: 14px 0 0;
            padding-left: 20px;
            color: var(--muted);
            line-height: 1.65;
          }
          li strong {
            color: var(--ink);
          }
          .routes {
            display: grid;
            gap: 10px;
            margin-top: 14px;
          }
          .route {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 12px;
            background: #fbfcfe;
          }
          .route span {
            color: var(--muted);
            text-align: right;
          }
          footer {
            margin-top: 24px;
            color: var(--muted);
            font-size: 13px;
          }
          @media (max-width: 780px) {
            main {
              padding-top: 24px;
            }
            .hero,
            .grid,
            .mini-grid {
              grid-template-columns: 1fr;
            }
            h1 {
              font-size: 32px;
            }
            .route {
              display: block;
            }
            .route span {
              display: block;
              margin-top: 6px;
              text-align: left;
            }
          }
        </style>
      </head>
      <body>
        <main>
          <section class="hero">
            <div class="hero-card">
              <span class="badge">Consola de demo</span>
              <h1>CrediBot</h1>
              <p>
                Agente conversacional para precalificar créditos por WhatsApp con
                flujo guiado, reglas de negocio, IA, RAG, historial por cliente y
                derivación a asesor humano.
              </p>
              <div class="actions">
                <a href="/docs">Abrir Swagger</a>
                <a class="secondary" href="http://localhost:8501">Dashboard local</a>
                <a class="secondary" href="/health">Health</a>
                <a class="secondary" href="/health/ai">Estado IA</a>
              </div>
            </div>
            <aside class="status-card">
              <h2><span class="status-dot"></span>Backend activo</h2>
              <p>
                Usa esta pantalla para presentar el proyecto sin depender de mensajes
                reales de WhatsApp ni gastar pruebas de Twilio.
              </p>
              <div class="routes">
                <div class="route"><strong>Webhook</strong><span>/webhook/whatsapp</span></div>
                <div class="route"><strong>Simulador</strong><span>/simulate/message</span></div>
                <div class="route"><strong>Handoff</strong><span>/admin/handoff</span></div>
              </div>
            </aside>
          </section>

          <section class="grid">
            <div class="panel">
              <h2>Prueba rápida</h2>
              <p>
                Desde Swagger ejecuta <code>POST /simulate/message</code> con un
                teléfono de prueba. Ese número mantiene su propio estado de conversación.
              </p>
              <pre>{
  "phone": "593999000111",
  "message": "Hola"
}</pre>
            </div>
            <div class="panel">
              <h2>Flujo sugerido</h2>
              <ol>
                <li><strong>Hola</strong></li>
                <li><strong>Quiero un crédito</strong></li>
                <li>Enviar nombre, cédula ficticia, autorización, destino, monto y plazo.</li>
                <li>Escribir <strong>asesor</strong> para probar transferencia humana.</li>
              </ol>
            </div>
          </section>

          <section class="panel">
            <h2>Lo que demuestra el MVP</h2>
            <div class="mini-grid">
              <div class="mini">
                <h3>Reglas</h3>
                <p>Evalúa datos y devuelve preaprobado, observado o rechazado.</p>
              </div>
              <div class="mini">
                <h3>IA controlada</h3>
                <p>Responde con contexto del flujo y evita inventar condiciones.</p>
              </div>
              <div class="mini">
                <h3>Handoff</h3>
                <p>Guarda resumen, motivo y transcript para que un asesor continúe.</p>
              </div>
            </div>
          </section>
          <footer>
            Para producción, configura el webhook de WhatsApp Cloud API apuntando a
            <code>/webhook/whatsapp</code>. Para clases, el simulador permite mostrar
            el recorrido completo sin costo de mensajería.
          </footer>
        </main>
      </body>
    </html>
    """

# Registro de routers
app.include_router(health_router)
app.include_router(simulator_router)
app.include_router(webhook_router)
app.include_router(admin_router)
