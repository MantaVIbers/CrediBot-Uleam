# Configuración de WhatsApp con Twilio Console

CrediBot usa **Twilio** como proveedor de WhatsApp. No necesitas configurar la API directa de Meta.

## Qué necesitas conseguir en Twilio

Antes de conectar el bot, reúne estos datos desde [Twilio Console](https://console.twilio.com):

| Dato | Dónde encontrarlo |
|---|---|
| **Account SID** | Dashboard principal de Twilio |
| **Auth Token** | Dashboard principal de Twilio |
| **Número WhatsApp Sandbox** | Messaging > Try it out > Send a WhatsApp message |
| **Código join del Sandbox** | Misma pantalla del Sandbox |

Para desarrollo usamos normalmente el **WhatsApp Sandbox** de Twilio.

## Paso 1: Crear o acceder a tu cuenta Twilio

1. Entra a [https://console.twilio.com](https://console.twilio.com)
2. Copia tu **Account SID**
3. Copia tu **Auth Token**

## Paso 2: Activar WhatsApp Sandbox

1. Ve a **Messaging**
2. Abre **Try it out > Send a WhatsApp message**
3. Twilio mostrará:
   - Un número tipo `+1 415 523 8886`
   - Un mensaje tipo `join <palabra-clave>`
4. Desde tu WhatsApp personal, envía ese mensaje `join ...` al número del Sandbox
5. Twilio confirmará que tu número quedó vinculado

## Paso 3: Configurar variables en `.env`

En `creditbot/.env`:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_VALIDATE_SIGNATURE=false
APP_PUBLIC_URL=https://tu-url-publica.com
```

Notas:

- `TWILIO_WHATSAPP_FROM` debe incluir el prefijo `whatsapp:`
- En Sandbox suele ser `whatsapp:+14155238886`
- En local deja `TWILIO_VALIDATE_SIGNATURE=false`

## Paso 4: Exponer tu backend

Twilio necesita una URL pública para enviar mensajes entrantes.

### Desarrollo local con ngrok

```bash
ngrok http 8000
```

Usa la URL HTTPS que te entregue ngrok, por ejemplo:

```text
https://abcd1234.ngrok-free.app/webhook/whatsapp
```

### Producción

Usa la URL de tu despliegue, por ejemplo:

```text
https://credibot-uleam-gjj2.onrender.com/webhook/whatsapp
```

## Paso 5: Configurar el webhook en Twilio

En la pantalla del **WhatsApp Sandbox Settings**:

| Campo | Valor |
|---|---|
| **When a message comes in** | `https://tu-url-publica/webhook/whatsapp` |
| **Method** | `POST` |

Guarda los cambios.

## Paso 6: Probar

1. Levanta el backend:

```bash
cd creditbot
uvicorn app.main:app --reload
```

2. Verifica salud:

```http
GET /health
```

3. Escribe `Hola` desde tu WhatsApp al número del Sandbox
4. CrediBot debe responder con el menú inicial

## Qué debes enviarme si quieres que lo dejemos funcionando juntos

Para terminar la integración contigo, comparte solo estos valores (por un canal seguro, no en GitHub):

1. `TWILIO_ACCOUNT_SID`
2. `TWILIO_AUTH_TOKEN`
3. Confirmación de que tu número ya envió el `join` al Sandbox
4. La URL pública que usarás:
   - ngrok en local, o
   - dominio de Render/Railway en producción

Opcional pero recomendable:

5. Captura de la pantalla de **WhatsApp Sandbox Settings** con el webhook configurado

## Errores comunes

| Problema | Causa probable |
|---|---|
| Twilio no llama al webhook | URL incorrecta, ngrok cerrado o backend apagado |
| El bot no responde por WhatsApp | Variables Twilio mal configuradas en `.env` |
| Solo funciona con algunos números | El número no se unió al Sandbox |
| Error 403 en producción | `TWILIO_VALIDATE_SIGNATURE=true` sin `APP_PUBLIC_URL` correcta |

## Producción

Cuando pases de Sandbox a un número real de WhatsApp en Twilio:

1. Solicita o activa tu número WhatsApp en Twilio
2. Cambia `TWILIO_WHATSAPP_FROM` al nuevo número
3. Configura el mismo webhook en la configuración del sender de WhatsApp
4. Activa `TWILIO_VALIDATE_SIGNATURE=true`
5. Define `APP_PUBLIC_URL` con tu dominio final
