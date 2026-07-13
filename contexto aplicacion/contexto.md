# CrediBot — Contexto del proyecto (handoff)

Documento de continuidad para retomar el desarrollo en otra computadora.  
**Última actualización:** julio 2026  
**Rama activa de trabajo:** `develop`

---

## 1. Qué es CrediBot

Bot conversacional por **WhatsApp** para **precalificación de crédito**. No usa IA generativa: funciona con una **máquina de estados** que guía al usuario, valida datos, calcula un resultado (`preaprobado`, `observado`, `no_cumple`), guarda todo en **Supabase** y deriva a un asesor humano cuando aplica.

**Stack actual:**
- Backend: Python + FastAPI
- Base de datos: Supabase (PostgreSQL)
- WhatsApp: **Twilio Console** (Sandbox para pruebas)
- Despliegue previsto: **Render** (carpeta `creditbot/`)
- Panel admin: Streamlit (Fase 2, **aún no implementado**)

---

## 2. Repositorio y ramas

| Dato | Valor |
|---|---|
| Repositorio GitHub | https://github.com/Erickelrojo-22/CrediBot-Uleam |
| Rama principal | `main` (solo historia de usuario / story mapping) |
| Rama de desarrollo | `develop` (todo el código del backend) |

### Clonar en otra computadora

```bash
git clone https://github.com/Erickelrojo-22/CrediBot-Uleam.git
cd CrediBot-Uleam
git checkout develop
```

---

## 3. Estructura del proyecto

```text
CrediBot-Uleam/
├── contexto aplicacion/          # Documentación de planificación + este archivo
│   ├── contexto.md
│   ├── creditbot_desarrollo_tareas_fastapi_supabase.md
│   └── creditbot_streamlit_panel_desarrollo.md
├── tareas.md                     # Seguimiento de tareas (21/29 hechas)
├── README.md                     # Story mapping del proyecto
└── creditbot/                    # ← BACKEND (esto se despliega en Render)
    ├── app/
    │   ├── main.py
    │   ├── api/                  # health, simulator, webhook, admin
    │   ├── core/                 # config, constants
    │   ├── schemas/
    │   ├── services/             # conversation, credit, validation, whatsapp, handoff, messages
    │   ├── repositories/         # supabase, users, conversations, messages, credit, handoff
    │   └── tests/
    ├── docs/
    ├── supabase/schema.sql
    ├── .env                      # ⚠️ NO está en Git — copiar manualmente
    ├── .env.example
    ├── requirements.txt
    ├── Procfile
    └── render.yaml
```

---

## 4. Avance de tareas

| Fase | Estado |
|---|---|
| **Fase 1 — Backend FastAPI + Supabase** | ✅ **21/21 completada** |
| **Fase 2 — Panel Streamlit** | ⏳ 0/8 pendiente |
| **Total** | **21/29 tareas** |

Detalle completo en `tareas.md` (raíz del repo).

### Fase 1 — Lo que ya está hecho

1. Estructura base del proyecto
2. FastAPI + `/health`
3. Variables de entorno (`config.py`)
4. Esquema Supabase (`supabase/schema.sql`)
5. Cliente Supabase
6. Repositorios: usuarios, conversaciones, mensajes, crédito, handoff
7. Servicios: validación, reglas de negocio, plantillas de mensajes, motor conversacional
8. Simulador local `POST /simulate/message`
9. Webhook WhatsApp vía **Twilio** `POST /webhook/whatsapp`
10. Servicio de envío Twilio (`send_text_message`)
11. Flujo de derivación humana
12. Endpoints admin
13. Pruebas unitarias (17 tests, `pytest`)
14. Documentación (`README`, `docs/`)
15. Configuración de despliegue Render (`Procfile`, `render.yaml`)

### Fase 2 — Pendiente (Streamlit)

- Tareas 22 a 29: dashboard, conexión Supabase, pantallas, seguridad, ejecución local

---

## 5. Arquitectura

```text
Usuario WhatsApp
      ↓
Twilio Sandbox / WhatsApp
      ↓  POST /webhook/whatsapp
FastAPI (CrediBot)
      ↓
Motor conversacional (máquina de estados)
      ↓
Validación + reglas de negocio
      ↓
Supabase PostgreSQL
      ↓
Respuesta vía Twilio API
```

### Estados de conversación

`START` → `MENU` → `ASK_NAME` → `ASK_AMOUNT` → `ASK_TERM` → `ASK_INCOME` → `CONFIRM_DATA` → `SHOW_RESULT` → `FINISHED`

También: `HANDOFF_REQUESTED` (derivación a asesor)

### Regla de negocio

```text
cuota_estimada = monto / plazo
capacidad_pago = ingreso * 0.30
```

| Condición | Resultado |
|---|---|
| cuota ≤ capacidad | `preaprobado` |
| cuota ≤ capacidad × 1.20 | `observado` |
| cuota > capacidad × 1.20 | `no_cumple` |

---

## 6. Endpoints del backend

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/health` | Verificar servidor |
| `POST` | `/simulate/message` | Probar bot sin WhatsApp |
| `GET` | `/webhook/whatsapp` | Estado del webhook Twilio |
| `POST` | `/webhook/whatsapp` | Recibir mensajes de Twilio |
| `GET` | `/admin/requests` | Listar solicitudes de crédito |
| `GET` | `/admin/handoff` | Casos pendientes de asesor |
| `GET` | `/admin/conversations/{phone}` | Historial por teléfono |

Documentación: `creditbot/docs/endpoints.md`

---

## 7. Variables de entorno

Archivo: `creditbot/.env` (crear desde `.env.example` si no existe)

| Variable | Estado actual | Notas |
|---|---|---|
| `TWILIO_ACCOUNT_SID` | ✅ Configurado | Ver `creditbot/.env` (no subir a Git) |
| `TWILIO_AUTH_TOKEN` | ✅ En `.env` local | **No subir a GitHub**. Copiar `.env` manualmente a la otra PC |
| `TWILIO_WHATSAPP_FROM` | ✅ Configurado | `whatsapp:+14155238886` (Sandbox) |
| `TWILIO_VALIDATE_SIGNATURE` | `false` en local | `true` en producción (Render) |
| `APP_PUBLIC_URL` | Pendiente URL real | URL de Render sin barra final |
| `SUPABASE_URL` | ⚠️ Pendiente | Crear proyecto y ejecutar `schema.sql` |
| `SUPABASE_SERVICE_ROLE_KEY` | ⚠️ Pendiente | Copiar desde Supabase Console |
| `DEFAULT_COUNTRY_CODE` | `593` | Ecuador |

### Archivos que NO están en Git (copiar manualmente)

- `creditbot/.env`
- `creditbot/venv/` (recrear en la otra PC con `pip install -r requirements.txt`)

---

## 8. Twilio — Configuración actual

**Proveedor WhatsApp:** Twilio Console (no API directa de Meta)

### Credenciales

- **Account SID:** en `creditbot/.env` (copiar manualmente a otra PC)
- **Auth Token:** en `creditbot/.env` (regenerar si se expuso)

### Pasos pendientes en Twilio

1. **Unir WhatsApp al Sandbox:** Messaging → Try it out → Send a WhatsApp message → enviar `join <palabra>` al número del Sandbox
2. **Configurar webhook** en Sandbox Settings:
   - URL: `https://TU-SERVICIO.onrender.com/webhook/whatsapp`
   - Método: `POST`

Guía completa: `creditbot/docs/twilio_setup.md`

---

## 9. Supabase — Pendiente de configurar

1. Crear proyecto en https://supabase.com
2. SQL Editor → ejecutar `creditbot/supabase/schema.sql`
3. Copiar `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` al `.env`
4. Tablas creadas: `users`, `conversations`, `messages`, `credit_requests`, `handoff_cases`

Sin Supabase configurado, el simulador y el webhook fallarán al persistir datos.

---

## 10. Cómo levantar en otra computadora

### Requisitos

- Python 3.11+
- Git

### Instalación

```bash
git clone https://github.com/Erickelrojo-22/CrediBot-Uleam.git
cd CrediBot-Uleam
git checkout develop
cd creditbot
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

### Configurar entorno

1. Copiar `creditbot/.env` desde la computadora anterior, **o**
2. Copiar `.env.example` a `.env` y completar valores

### Ejecutar

```bash
uvicorn app.main:app --reload
```

- Health: http://localhost:8000/health
- Swagger: http://localhost:8000/docs

### Probar sin WhatsApp

```http
POST http://localhost:8000/simulate/message
Content-Type: application/json

{
  "phone": "593999999999",
  "message": "Hola"
}
```

### Ejecutar pruebas

```bash
pytest
```

Resultado esperado: **17 passed**

---

## 11. Despliegue en Render

**Qué desplegar:** solo la carpeta `creditbot/` (Web Service)

| Campo Render | Valor |
|---|---|
| Root Directory | `creditbot` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/health` |
| Rama | `develop` |

Variables de entorno en Render: ver `creditbot/docs/despliegue.md` y `render.yaml`

Webhook en Twilio:

```text
https://TU-SERVICIO.onrender.com/webhook/whatsapp
```

---

## 12. Commits recientes en `develop`

```text
96cc00c chore: add deployment configuration for Render
bed9d32 docs: add local execution and Twilio setup guides
f9d883f feat: adapt WhatsApp integration for Twilio Console
79eece3 test: add validation and credit service tests
162d5f1 feat: add basic admin query endpoints
a3af474 feat: add human handoff flow
8f3aef6 feat: add WhatsApp webhook routes
e522527 feat: add WhatsApp outbound message service
55c1f7e feat: add local message simulator endpoint
0dff013 feat: implement conversation state machine
... (más commits de Fase 1)
```

---

## 13. Próximos pasos sugeridos

1. **Configurar Supabase** (URL + Service Role Key en `.env`)
2. **Desplegar en Render** y obtener URL pública
3. **Configurar webhook en Twilio** con la URL de Render
4. **Unir número al Sandbox** y probar mensaje real por WhatsApp
5. **Regenerar Auth Token** de Twilio (se compartió en chat)
6. **Iniciar Fase 2:** panel Streamlit (tareas 22–29)

---

## 14. Documentos de referencia

| Archivo | Contenido |
|---|---|
| `tareas.md` | Lista de tareas y avance |
| `contexto aplicacion/creditbot_desarrollo_tareas_fastapi_supabase.md` | Plan detallado backend |
| `contexto aplicacion/creditbot_streamlit_panel_desarrollo.md` | Plan panel Streamlit |
| `creditbot/README.md` | Guía rápida del backend |
| `creditbot/docs/twilio_setup.md` | Configuración Twilio paso a paso |
| `creditbot/docs/despliegue.md` | Despliegue Render/Railway |
| `creditbot/docs/flujo_conversacional.md` | Flujo del bot |
| `creditbot/docs/endpoints.md` | API endpoints |

---

## 15. Convenciones del equipo

- **Un commit por tarea** realizada
- Rama de trabajo: `develop`
- Push a GitHub después de cada bloque de tareas
- **Nunca** commitear `.env` ni claves secretas
- Actualizar `tareas.md` al completar cada tarea

---

## 16. Contacto / datos del proyecto

- Proyecto académico: CrediBot-Uleam
- Usuario Twilio: Carlos Ortiz (`carlosortizluisgarcia@gmail.com`)
- Código país por defecto: Ecuador (`593`)
