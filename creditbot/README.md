# CrediBot

Agente conversacional de precalificación de crédito por WhatsApp.

**Stack:** Python, FastAPI, Supabase, OpenAI y Twilio WhatsApp.

CrediBot guía al usuario paso a paso, valida datos, calcula una precalificación (`preaprobado`, `observado`, `no_cumple`), redacta respuestas con IA cuando OpenAI está configurado, registra la información en Supabase y deriva a un asesor humano cuando corresponde.

También incluye un RAG básico sobre políticas internas en Markdown para responder
dudas de requisitos, documentos, plazos, tasas y condiciones sin inventar datos.
Cuando el cliente pide un asesor, el sistema conserva el historial en `messages` y
crea un caso con resumen y transcript para seguimiento humano.

## Estructura del proyecto

```text
creditbot/
├── app/
│   ├── main.py
│   ├── core/
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   └── tests/
├── docs/
├── supabase/
├── requirements.txt
├── .env.example
├── Procfile
└── render.yaml
```

## Requisitos

- Python 3.11+
- Proyecto en [Supabase](https://supabase.com)
- API key de OpenAI para activar la redacción con IA
- Cuenta en [Twilio Console](https://console.twilio.com) con WhatsApp Sandbox o número aprobado

## Instalación

```bash
cd creditbot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

En Linux/macOS:

```bash
cp .env.example .env
```

## Variables de entorno

Edita `creditbot/.env`:

| Variable | Descripción |
|---|---|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Service Role Key de Supabase |
| `OPENAI_API_KEY` | API key usada por la capa de IA |
| `OPENAI_MODEL` | Modelo de OpenAI para redactar respuestas |
| `OPENAI_ENABLE_AI` | `true` para usar IA, `false` para usar solo fallback determinista |
| `TWILIO_ACCOUNT_SID` | Account SID de Twilio Console |
| `TWILIO_AUTH_TOKEN` | Auth Token de Twilio Console |
| `TWILIO_WHATSAPP_FROM` | Número remitente, ej. `whatsapp:+14155238886` |
| `APP_PUBLIC_URL` | URL pública del backend en producción |
| `TWILIO_VALIDATE_SIGNATURE` | `true` en producción, `false` en local |
| `DEFAULT_COUNTRY_CODE` | Código de país por defecto, ej. `593` |
| `ADMIN_DASHBOARD_PASSWORD` | Contraseña del panel administrativo Streamlit |

## Activar IA conversacional

La IA no decide la precalificación. El backend mantiene la máquina de estados,
valida los datos y calcula el resultado con reglas deterministas. OpenAI solo
redacta la respuesta final a partir de una respuesta base segura.

Configura estas variables en local o Render:

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5.5
OPENAI_ENABLE_AI=true
```

Si `OPENAI_API_KEY` está vacío o la API falla, CrediBot responde con el texto
base del flujo para no interrumpir la conversación.

## RAG de políticas

Las respuestas informativas usan documentos locales como fuente de verdad:

```text
docs/policies/
└── credito_mvp.md
```

Ejemplos que activan RAG:

```text
qué requisitos necesito?
qué documentos piden?
cuáles son los plazos?
```

Si el usuario pregunta esto en medio del flujo, CrediBot responde la duda y luego
le recuerda el dato pendiente para continuar.

## Configurar Supabase

1. Crea un proyecto en Supabase.
2. Abre **SQL Editor**.
3. Ejecuta el contenido de `supabase/schema.sql`.
4. Copia `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` al `.env`.

## Ejecución local

```bash
uvicorn app.main:app --reload
```

Servidor disponible en `http://localhost:8000`.

Documentación interactiva: `http://localhost:8000/docs`

## Panel administrativo Streamlit

El proyecto incluye un panel interno en Streamlit para revisar metricas, solicitudes, casos derivados y usuarios.

Configura en `creditbot/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_DASHBOARD_PASSWORD=tu_clave_admin
```

Ejecuta el panel desde `creditbot`:

```bash
streamlit run dashboard/app.py
```

Guia detallada: [`docs/streamlit_dashboard.md`](docs/streamlit_dashboard.md)

## Probar sin WhatsApp

Usa el simulador local:

```http
POST /simulate/message
Content-Type: application/json

{
  "phone": "593999999999",
  "message": "Hola"
}
```

También puedes probar el flujo completo desde Swagger.

## Conectar WhatsApp con Twilio

La integración usa **Twilio Console**, no la API directa de Meta.

Guía detallada: [`docs/twilio_setup.md`](docs/twilio_setup.md)

Resumen:

1. Obtén `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`.
2. Entra a **Messaging > Try it out > Send a WhatsApp message**.
3. Une tu WhatsApp al Sandbox enviando el código que muestra Twilio.
4. Configura el webhook entrante:
   - Local: usa ngrok, por ejemplo `https://xxxx.ngrok-free.app/webhook/whatsapp`
   - Producción: `https://tu-dominio.com/webhook/whatsapp`
5. Método del webhook: `POST`
6. Coloca las variables Twilio en `.env`.

## Pruebas

```bash
pytest
```

## Despliegue

El proyecto incluye configuración base para Render:

- `render.yaml`
- `Procfile`

Guía: [`docs/despliegue.md`](docs/despliegue.md)

## Documentación adicional

- [`docs/endpoints.md`](docs/endpoints.md)
- [`docs/flujo_conversacional.md`](docs/flujo_conversacional.md)
- [`docs/twilio_setup.md`](docs/twilio_setup.md)
- [`docs/streamlit_dashboard.md`](docs/streamlit_dashboard.md)
