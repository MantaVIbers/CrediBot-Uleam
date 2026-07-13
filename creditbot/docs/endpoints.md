# Endpoints de CrediBot

## Salud

### `GET /health`

Verifica que el servidor esté activo.

**Respuesta:**

```json
{
  "status": "ok",
  "app": "CrediBot"
}
```

### `GET /health/ai`

Verifica si la capa de IA está habilitada y configurada sin exponer la API key.

**Respuesta:**

```json
{
  "status": "ok",
  "enabled": true,
  "configured": true,
  "model": "gpt-5.5"
}
```

### `GET /health/whatsapp`

Indica si Twilio/Meta está configurado (sin exponer secretos).

**Respuesta (ejemplo):**

```json
{
  "status": "ok",
  "provider": "twilio",
  "configured": true,
  "missing_env": [],
  "app_public_url_set": true,
  "twilio_validate_signature": true,
  "redis_configured": false,
  "webhook_path": "/webhook/whatsapp"
}
```

## Simulador local

### `POST /simulate/message`

Permite probar el bot sin Twilio.

**Body:**

```json
{
  "phone": "593999999999",
  "message": "Hola"
}
```

**Respuesta:**

```json
{
  "phone": "593999999999",
  "reply": "Hola, soy CrediBot..."
}
```

## Webhook de WhatsApp (Twilio / Meta)

### `GET /webhook/whatsapp`

- Sin query: estado del endpoint y proveedor activo (`WHATSAPP_PROVIDER`).
- Con `hub.mode=subscribe` + `hub.verify_token` + `hub.challenge`: verificación de Meta Cloud API.

### `POST /webhook/whatsapp`

**Twilio** — `application/x-www-form-urlencoded`

Campos principales:

| Campo | Ejemplo |
|---|---|
| `From` | `whatsapp:+593999999999` |
| `Body` | `Hola` |
| `MessageSid` | `SMxxxxxxxx` |

**Meta** — `application/json` (payload estándar de WhatsApp Cloud API).

Si `META_WHATSAPP_APP_SECRET` está definido, se valida `X-Hub-Signature-256`.

**Configuración:**

- URL: `https://tu-dominio.com/webhook/whatsapp`
- Método: `POST` (y verificación GET para Meta)


## Administración

### `GET /admin/requests`

Lista solicitudes de crédito registradas.

### `GET /admin/handoff`

Lista casos pendientes de derivación a asesor.

### `GET /admin/conversations/{phone}`

Devuelve usuario, conversación e historial de mensajes por teléfono.

**Ejemplo:**

```http
GET /admin/conversations/593999999999
```

## Documentación interactiva

Con el servidor levantado:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
