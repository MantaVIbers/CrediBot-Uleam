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

## Webhook de WhatsApp (Twilio)

### `GET /webhook/whatsapp`

Estado del endpoint para confirmar que la ruta existe.

### `POST /webhook/whatsapp`

Recibe mensajes enviados por Twilio cuando un usuario escribe por WhatsApp.

**Formato esperado:** `application/x-www-form-urlencoded`

Campos principales:

| Campo | Ejemplo |
|---|---|
| `From` | `whatsapp:+593999999999` |
| `Body` | `Hola` |
| `MessageSid` | `SMxxxxxxxx` |

**Configuración en Twilio Console:**

- URL: `https://tu-dominio.com/webhook/whatsapp`
- Método: `POST`

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
