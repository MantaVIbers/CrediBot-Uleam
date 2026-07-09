# CrediBot — Plan de Desarrollo por Tareas
## Agente Conversacional de Ventas/Créditos por WhatsApp

**Tecnologías principales:** Python, FastAPI, Supabase y WhatsApp Cloud API/Sandbox.  
**Objetivo del MVP:** construir un agente conversacional estructurado que reciba mensajes por WhatsApp, guíe al usuario, recopile datos, evalúe una solicitud básica de crédito, registre el caso en Supabase y derive a un asesor humano cuando corresponda.

---

# 1. Alcance del desarrollo

El desarrollo se enfocará únicamente en el flujo funcional del MVP. No se construirá un chatbot abierto ni una IA generativa. El bot funcionará mediante una **máquina de estados**, donde cada usuario tendrá un estado actual de conversación y el sistema responderá según la etapa en la que se encuentre.

El MVP debe permitir:

- Recibir mensajes desde WhatsApp mediante un webhook.
- Identificar al usuario por su número de teléfono.
- Mantener el estado de conversación por usuario.
- Solicitar datos paso a paso.
- Validar datos ingresados por el cliente.
- Calcular una precalificación básica.
- Responder con resultado: `preaprobado`, `observado` o `no_cumple`.
- Registrar usuarios, conversaciones, mensajes y solicitudes en Supabase.
- Permitir derivación a asesor humano.
- Tener endpoints de prueba para simular mensajes sin depender siempre de WhatsApp.

---

# 2. Arquitectura general

```text
Cliente WhatsApp
      ↓
WhatsApp Cloud API / Sandbox
      ↓
Webhook FastAPI
      ↓
Controlador de mensajes
      ↓
Motor conversacional por estados
      ↓
Servicios de validación y reglas de negocio
      ↓
Supabase PostgreSQL
      ↓
Respuesta enviada al cliente
```

---

# 3. Estructura recomendada del proyecto

```text
creditbot/
│
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── constants.py
│   │
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_webhook.py
│   │   ├── routes_simulator.py
│   │   └── routes_admin.py
│   │
│   ├── schemas/
│   │   ├── whatsapp.py
│   │   ├── conversation.py
│   │   └── credit.py
│   │
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── credit_service.py
│   │   ├── validation_service.py
│   │   ├── message_service.py
│   │   ├── whatsapp_service.py
│   │   └── handoff_service.py
│   │
│   ├── repositories/
│   │   ├── supabase_client.py
│   │   ├── user_repository.py
│   │   ├── conversation_repository.py
│   │   ├── message_repository.py
│   │   ├── credit_repository.py
│   │   └── handoff_repository.py
│   │
│   └── tests/
│       ├── test_credit_service.py
│       ├── test_validation_service.py
│       └── test_conversation_flow.py
│
├── docs/
│   ├── flujo_conversacional.md
│   ├── reglas_negocio.md
│   └── endpoints.md
│
├── supabase/
│   └── schema.sql
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── pyproject.toml
```

---

# 4. Variables de entorno

Crear un archivo `.env` para desarrollo local y un `.env.example` para documentar las variables necesarias.

## `.env.example`

```env
APP_NAME=CrediBot
APP_ENV=development
APP_DEBUG=true

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

WHATSAPP_VERIFY_TOKEN=creditbot_verify_token
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_API_VERSION=v20.0

DEFAULT_COUNTRY_CODE=593
```

**Nota importante:** `SUPABASE_SERVICE_ROLE_KEY` no debe exponerse en frontend ni subirse al repositorio. Solo debe usarse desde el backend.

---

# 5. Dependencias iniciales

## `requirements.txt`

```txt
fastapi
uvicorn[standard]
python-dotenv
pydantic
pydantic-settings
supabase
httpx
pytest
pytest-asyncio
```

## Instalación

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

En Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

# 6. Estados principales de conversación

La conversación se controlará mediante estados. Cada usuario tendrá un estado actual guardado en Supabase.

```text
START
MENU
ASK_NAME
ASK_AMOUNT
ASK_TERM
ASK_INCOME
CONFIRM_DATA
EVALUATE_REQUEST
SHOW_RESULT
HANDOFF_REQUESTED
FINISHED
```

## Descripción de estados

| Estado | Descripción |
|---|---|
| `START` | Inicio de conversación o usuario nuevo |
| `MENU` | El bot muestra opciones principales |
| `ASK_NAME` | Solicita nombre completo |
| `ASK_AMOUNT` | Solicita monto del crédito |
| `ASK_TERM` | Solicita plazo en meses |
| `ASK_INCOME` | Solicita ingreso mensual |
| `CONFIRM_DATA` | Muestra resumen y pide confirmación |
| `EVALUATE_REQUEST` | Ejecuta regla de precalificación |
| `SHOW_RESULT` | Envía resultado al usuario |
| `HANDOFF_REQUESTED` | Deriva a asesor humano |
| `FINISHED` | Cierra conversación |

---

# 7. Flujo conversacional esperado

```text
Usuario: Hola
Bot: Hola, soy CrediBot. ¿Qué deseas hacer?
     1. Precalificar crédito
     2. Información general
     3. Hablar con asesor

Usuario: 1
Bot: Perfecto. Indícame tu nombre completo.

Usuario: Carlos Ortiz
Bot: ¿Qué monto deseas solicitar?

Usuario: 500
Bot: ¿En cuántos meses deseas pagar el crédito?

Usuario: 12
Bot: ¿Cuál es tu ingreso mensual aproximado?

Usuario: 700
Bot: Resumen:
     Nombre: Carlos Ortiz
     Monto: $500
     Plazo: 12 meses
     Ingreso: $700
     ¿Confirmas la información?
     1. Sí
     2. No

Usuario: 1
Bot: Resultado: Preaprobado.
     Un asesor puede continuar con la validación final.
```

---

# 8. Regla de negocio del MVP

La regla de negocio será simple para poder demostrar el flujo completo.

## Fórmula base

```text
cuota_estimada = monto_solicitado / plazo
capacidad_pago = ingreso_mensual * 0.30
```

## Criterios de resultado

| Condición | Resultado |
|---|---|
| `cuota_estimada <= capacidad_pago` | `preaprobado` |
| `cuota_estimada <= capacidad_pago * 1.20` | `observado` |
| `cuota_estimada > capacidad_pago * 1.20` | `no_cumple` |

## Ejemplo

```text
Monto solicitado: 500
Plazo: 12 meses
Ingreso mensual: 700

cuota_estimada = 500 / 12 = 41.67
capacidad_pago = 700 * 0.30 = 210

Resultado: preaprobado
```

---

# 9. Diseño de base de datos en Supabase

Crear el archivo `supabase/schema.sql`.

```sql
create extension if not exists "uuid-ossp";

create table if not exists users (
    id uuid primary key default uuid_generate_v4(),
    phone text not null unique,
    full_name text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists conversations (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    current_state text not null default 'START',
    is_active boolean not null default true,
    last_message text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists messages (
    id uuid primary key default uuid_generate_v4(),
    conversation_id uuid not null references conversations(id) on delete cascade,
    user_id uuid not null references users(id) on delete cascade,
    direction text not null check (direction in ('inbound', 'outbound')),
    content text not null,
    raw_payload jsonb,
    created_at timestamptz not null default now()
);

create table if not exists credit_requests (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    requested_amount numeric(12, 2),
    term_months integer,
    monthly_income numeric(12, 2),
    estimated_payment numeric(12, 2),
    payment_capacity numeric(12, 2),
    result text check (result in ('preaprobado', 'observado', 'no_cumple')),
    status text not null default 'draft',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists handoff_cases (
    id uuid primary key default uuid_generate_v4(),
    user_id uuid not null references users(id) on delete cascade,
    conversation_id uuid not null references conversations(id) on delete cascade,
    credit_request_id uuid references credit_requests(id) on delete set null,
    reason text not null,
    status text not null default 'pending' check (status in ('pending', 'assigned', 'closed')),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

---

# 10. Endpoints del backend

| Método | Endpoint | Uso |
|---|---|---|
| `GET` | `/health` | Verificar que el servidor esté activo |
| `GET` | `/webhook/whatsapp` | Validar webhook de WhatsApp |
| `POST` | `/webhook/whatsapp` | Recibir mensajes reales de WhatsApp |
| `POST` | `/simulate/message` | Simular mensajes para pruebas locales |
| `GET` | `/admin/requests` | Consultar solicitudes de crédito |
| `GET` | `/admin/handoff` | Consultar casos derivados a asesor |
| `GET` | `/admin/conversations/{phone}` | Ver conversación por número |

---

# 11. Desarrollo por tareas

## Tarea 0 — Crear repositorio y estructura base

**Objetivo:** preparar el proyecto para iniciar el desarrollo ordenado.

### Actividades

- [ ] Crear carpeta `creditbot`.
- [ ] Inicializar Git.
- [ ] Crear rama `develop`.
- [ ] Crear estructura de carpetas.
- [ ] Crear `.gitignore`.
- [ ] Crear `README.md` inicial.
- [ ] Crear `requirements.txt`.
- [ ] Crear `.env.example`.

### Comandos sugeridos

```bash
mkdir creditbot
cd creditbot
git init
git checkout -b develop
mkdir -p app/core app/api app/schemas app/services app/repositories app/tests docs supabase
touch README.md requirements.txt .env.example .gitignore
```

### Criterio de aceptación

El proyecto debe tener la estructura base creada y lista para instalar dependencias.

### Commit sugerido

```bash
git add .
git commit -m "chore: initialize creditbot project structure"
```

---

## Tarea 1 — Configurar FastAPI

**Objetivo:** levantar un servidor básico con FastAPI.

### Archivos involucrados

```text
app/main.py
app/api/routes_health.py
```

### Actividades

- [ ] Crear instancia principal de FastAPI.
- [ ] Crear endpoint `/health`.
- [ ] Registrar rutas en `main.py`.
- [ ] Ejecutar servidor con Uvicorn.

### Ejemplo esperado de respuesta

```json
{
  "status": "ok",
  "app": "CrediBot"
}
```

### Comando para ejecutar

```bash
uvicorn app.main:app --reload
```

### Criterio de aceptación

Al abrir `http://localhost:8000/health`, el servidor debe responder correctamente.

### Commit sugerido

```bash
git add .
git commit -m "feat: add FastAPI health endpoint"
```

---

## Tarea 2 — Configurar variables de entorno

**Objetivo:** centralizar la configuración del proyecto.

### Archivos involucrados

```text
app/core/config.py
.env.example
```

### Actividades

- [ ] Instalar `python-dotenv` y `pydantic-settings`.
- [ ] Crear clase de configuración.
- [ ] Leer variables de entorno.
- [ ] Validar que Supabase y WhatsApp puedan configurarse desde `.env`.

### Variables mínimas

```env
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
```

### Criterio de aceptación

La aplicación debe poder leer variables sin escribir claves directamente en el código.

### Commit sugerido

```bash
git add .
git commit -m "chore: configure environment settings"
```

---

## Tarea 3 — Crear esquema en Supabase

**Objetivo:** preparar la base de datos para usuarios, conversaciones, mensajes y solicitudes.

### Archivos involucrados

```text
supabase/schema.sql
```

### Actividades

- [ ] Crear proyecto en Supabase.
- [ ] Abrir SQL Editor.
- [ ] Ejecutar `schema.sql`.
- [ ] Verificar tablas creadas.
- [ ] Copiar URL y Service Role Key al `.env` local.

### Tablas necesarias

- `users`
- `conversations`
- `messages`
- `credit_requests`
- `handoff_cases`

### Criterio de aceptación

Las tablas deben estar creadas correctamente en Supabase.

### Commit sugerido

```bash
git add .
git commit -m "feat: add Supabase database schema"
```

---

## Tarea 4 — Crear cliente de Supabase

**Objetivo:** conectar FastAPI con Supabase.

### Archivos involucrados

```text
app/repositories/supabase_client.py
```

### Actividades

- [ ] Crear cliente usando `create_client`.
- [ ] Leer credenciales desde `config.py`.
- [ ] Probar conexión con una consulta simple.

### Criterio de aceptación

El backend debe poder conectarse a Supabase sin errores.

### Commit sugerido

```bash
git add .
git commit -m "feat: configure Supabase client"
```

---

## Tarea 5 — Crear repositorio de usuarios

**Objetivo:** permitir crear o recuperar usuarios por número de WhatsApp.

### Archivos involucrados

```text
app/repositories/user_repository.py
```

### Funciones necesarias

```text
get_user_by_phone(phone)
create_user(phone, full_name=None)
get_or_create_user(phone)
update_user_name(user_id, full_name)
```

### Actividades

- [ ] Buscar usuario por teléfono.
- [ ] Crear usuario si no existe.
- [ ] Actualizar nombre cuando el bot lo solicite.

### Criterio de aceptación

Cuando un número escribe por primera vez, debe crearse un registro en `users`.

### Commit sugerido

```bash
git add .
git commit -m "feat: add user repository"
```

---

## Tarea 6 — Crear repositorio de conversaciones

**Objetivo:** administrar el estado de conversación de cada usuario.

### Archivos involucrados

```text
app/repositories/conversation_repository.py
```

### Funciones necesarias

```text
get_active_conversation(user_id)
create_conversation(user_id)
get_or_create_active_conversation(user_id)
update_state(conversation_id, new_state)
update_last_message(conversation_id, message)
finish_conversation(conversation_id)
```

### Actividades

- [ ] Crear conversación activa para usuario nuevo.
- [ ] Consultar estado actual.
- [ ] Actualizar estado después de cada respuesta.
- [ ] Finalizar conversación cuando termine el flujo.

### Criterio de aceptación

Cada usuario debe conservar su propio estado sin mezclarse con otros clientes.

### Commit sugerido

```bash
git add .
git commit -m "feat: add conversation repository"
```

---

## Tarea 7 — Crear repositorio de mensajes

**Objetivo:** registrar mensajes entrantes y salientes.

### Archivos involucrados

```text
app/repositories/message_repository.py
```

### Funciones necesarias

```text
save_inbound_message(conversation_id, user_id, content, raw_payload=None)
save_outbound_message(conversation_id, user_id, content, raw_payload=None)
get_messages_by_conversation(conversation_id)
```

### Actividades

- [ ] Guardar mensaje recibido.
- [ ] Guardar respuesta enviada por el bot.
- [ ] Permitir consultar historial de conversación.

### Criterio de aceptación

Cada mensaje procesado debe quedar registrado en Supabase.

### Commit sugerido

```bash
git add .
git commit -m "feat: add message repository"
```

---

## Tarea 8 — Crear repositorio de solicitudes de crédito

**Objetivo:** almacenar la información recopilada durante el flujo de precalificación.

### Archivos involucrados

```text
app/repositories/credit_repository.py
```

### Funciones necesarias

```text
create_draft_request(user_id, conversation_id)
get_draft_request(conversation_id)
update_amount(request_id, amount)
update_term(request_id, term_months)
update_income(request_id, monthly_income)
save_result(request_id, estimated_payment, payment_capacity, result)
```

### Actividades

- [ ] Crear solicitud en estado `draft`.
- [ ] Actualizar monto.
- [ ] Actualizar plazo.
- [ ] Actualizar ingreso mensual.
- [ ] Guardar resultado de evaluación.

### Criterio de aceptación

La solicitud debe ir completándose paso a paso durante la conversación.

### Commit sugerido

```bash
git add .
git commit -m "feat: add credit request repository"
```

---

## Tarea 9 — Crear servicio de validación

**Objetivo:** validar las respuestas del usuario antes de guardar datos.

### Archivos involucrados

```text
app/services/validation_service.py
```

### Validaciones requeridas

```text
validate_name(value)
validate_amount(value)
validate_term(value)
validate_income(value)
validate_menu_option(value)
validate_confirmation(value)
```

### Reglas sugeridas

| Dato | Regla |
|---|---|
| Nombre | Mínimo 2 palabras o mínimo 5 caracteres |
| Monto | Numérico, mayor a 0 |
| Plazo | Numérico, entre 3 y 36 meses |
| Ingreso | Numérico, mayor a 0 |
| Menú | Solo opciones 1, 2 o 3 |
| Confirmación | Solo 1 o 2 |

### Criterio de aceptación

Si el usuario ingresa un dato inválido, el bot debe pedir corrección sin avanzar al siguiente estado.

### Commit sugerido

```bash
git add .
git commit -m "feat: add user input validation service"
```

---

## Tarea 10 — Crear servicio de reglas de negocio

**Objetivo:** calcular la precalificación del crédito.

### Archivos involucrados

```text
app/services/credit_service.py
```

### Funciones necesarias

```text
calculate_estimated_payment(amount, term_months)
calculate_payment_capacity(monthly_income)
evaluate_credit_request(amount, term_months, monthly_income)
```

### Salida esperada

```json
{
  "estimated_payment": 41.67,
  "payment_capacity": 210.00,
  "result": "preaprobado"
}
```

### Criterio de aceptación

El servicio debe devolver un resultado correcto según la regla de negocio definida.

### Commit sugerido

```bash
git add .
git commit -m "feat: add credit evaluation service"
```

---

## Tarea 11 — Crear plantillas de mensajes

**Objetivo:** centralizar los textos que enviará CrediBot.

### Archivos involucrados

```text
app/services/message_service.py
```

### Mensajes necesarios

```text
welcome_message()
ask_name_message()
ask_amount_message(name=None)
ask_term_message()
ask_income_message()
invalid_amount_message()
invalid_term_message()
invalid_income_message()
confirm_data_message(data)
preapproved_message(data)
observed_message(data)
not_qualified_message(data)
handoff_message()
finished_message()
```

### Criterio de aceptación

Los mensajes deben estar separados de la lógica del flujo para que sea fácil editarlos.

### Commit sugerido

```bash
git add .
git commit -m "feat: add bot message templates"
```

---

## Tarea 12 — Crear motor conversacional

**Objetivo:** implementar la máquina de estados principal del bot.

### Archivos involucrados

```text
app/services/conversation_service.py
```

### Función principal

```text
process_message(phone, text, raw_payload=None)
```

### Responsabilidades

- [ ] Crear o recuperar usuario.
- [ ] Crear o recuperar conversación activa.
- [ ] Guardar mensaje entrante.
- [ ] Leer estado actual.
- [ ] Procesar respuesta según estado.
- [ ] Validar datos.
- [ ] Actualizar solicitud de crédito.
- [ ] Cambiar estado.
- [ ] Guardar respuesta saliente.
- [ ] Devolver mensaje final al controlador.

### Pseudoflujo

```text
process_message(phone, text):
    user = get_or_create_user(phone)
    conversation = get_or_create_active_conversation(user.id)
    save_inbound_message(conversation.id, user.id, text)

    state = conversation.current_state

    if state == START:
        response = welcome_message()
        update_state(MENU)

    elif state == MENU:
        procesar opción del usuario

    elif state == ASK_NAME:
        validar nombre
        guardar nombre
        avanzar a ASK_AMOUNT

    elif state == ASK_AMOUNT:
        validar monto
        guardar monto
        avanzar a ASK_TERM

    elif state == ASK_TERM:
        validar plazo
        guardar plazo
        avanzar a ASK_INCOME

    elif state == ASK_INCOME:
        validar ingreso
        guardar ingreso
        avanzar a CONFIRM_DATA

    elif state == CONFIRM_DATA:
        confirmar o corregir

    save_outbound_message(conversation.id, user.id, response)
    return response
```

### Criterio de aceptación

El flujo completo debe poder ejecutarse usando un endpoint de simulación local.

### Commit sugerido

```bash
git add .
git commit -m "feat: implement conversation state machine"
```

---

## Tarea 13 — Crear endpoint de simulación local

**Objetivo:** probar el bot sin depender de WhatsApp.

### Archivos involucrados

```text
app/api/routes_simulator.py
```

### Endpoint

```http
POST /simulate/message
```

### Body de prueba

```json
{
  "phone": "593999999999",
  "message": "Hola"
}
```

### Respuesta esperada

```json
{
  "phone": "593999999999",
  "reply": "Hola, soy CrediBot..."
}
```

### Criterio de aceptación

Se debe poder probar toda la conversación usando Postman, Thunder Client o Swagger.

### Commit sugerido

```bash
git add .
git commit -m "feat: add local message simulator endpoint"
```

---

## Tarea 14 — Crear webhook de WhatsApp

**Objetivo:** recibir mensajes reales desde WhatsApp Cloud API o sandbox.

### Archivos involucrados

```text
app/api/routes_webhook.py
app/schemas/whatsapp.py
```

### Endpoints

```http
GET /webhook/whatsapp
POST /webhook/whatsapp
```

### GET webhook

Debe validar el token de verificación enviado por WhatsApp.

Parámetros esperados:

```text
hub.mode
hub.verify_token
hub.challenge
```

### POST webhook

Debe:

- [ ] Recibir payload de WhatsApp.
- [ ] Extraer teléfono.
- [ ] Extraer mensaje.
- [ ] Enviar mensaje al motor conversacional.
- [ ] Enviar respuesta usando servicio de WhatsApp.

### Criterio de aceptación

WhatsApp debe poder verificar el webhook y enviar mensajes al backend.

### Commit sugerido

```bash
git add .
git commit -m "feat: add WhatsApp webhook routes"
```

---

## Tarea 15 — Crear servicio de envío por WhatsApp

**Objetivo:** enviar respuestas al cliente mediante la API de WhatsApp.

### Archivos involucrados

```text
app/services/whatsapp_service.py
```

### Funciones necesarias

```text
send_text_message(to_phone, message)
```

### Actividades

- [ ] Configurar URL de WhatsApp Cloud API.
- [ ] Enviar token en headers.
- [ ] Enviar mensaje de texto.
- [ ] Manejar errores de API.

### Criterio de aceptación

El backend debe poder enviar una respuesta al número que escribió.

### Commit sugerido

```bash
git add .
git commit -m "feat: add WhatsApp outbound message service"
```

---

## Tarea 16 — Crear flujo de derivación humana

**Objetivo:** registrar los casos que deben pasar a un asesor humano.

### Archivos involucrados

```text
app/services/handoff_service.py
app/repositories/handoff_repository.py
```

### Casos de derivación

- Usuario selecciona opción 3.
- Resultado queda como `observado`.
- Usuario escribe `asesor`, `humano`, `persona` o similar.
- Usuario falla varias veces ingresando datos inválidos.

### Funciones necesarias

```text
create_handoff_case(user_id, conversation_id, credit_request_id=None, reason="")
get_pending_handoff_cases()
close_handoff_case(case_id)
```

### Criterio de aceptación

Cuando un caso requiera asesor, debe crearse un registro en `handoff_cases`.

### Commit sugerido

```bash
git add .
git commit -m "feat: add human handoff flow"
```

---

## Tarea 17 — Crear endpoints administrativos básicos

**Objetivo:** consultar información registrada durante la demostración.

### Archivos involucrados

```text
app/api/routes_admin.py
```

### Endpoints mínimos

```http
GET /admin/requests
GET /admin/handoff
GET /admin/conversations/{phone}
```

### Actividades

- [ ] Listar solicitudes de crédito.
- [ ] Listar casos pendientes de asesor.
- [ ] Consultar historial de conversación por teléfono.

### Criterio de aceptación

El equipo debe poder demostrar que los datos quedaron registrados en Supabase.

### Commit sugerido

```bash
git add .
git commit -m "feat: add basic admin query endpoints"
```

---

## Tarea 18 — Crear pruebas unitarias

**Objetivo:** validar los componentes principales del backend.

### Archivos involucrados

```text
app/tests/test_credit_service.py
app/tests/test_validation_service.py
app/tests/test_conversation_flow.py
```

### Pruebas mínimas

- [ ] Validar monto correcto.
- [ ] Rechazar monto inválido.
- [ ] Validar plazo correcto.
- [ ] Rechazar plazo inválido.
- [ ] Calcular resultado `preaprobado`.
- [ ] Calcular resultado `observado`.
- [ ] Calcular resultado `no_cumple`.
- [ ] Ejecutar flujo conversacional básico.

### Comando

```bash
pytest
```

### Criterio de aceptación

Las pruebas principales deben ejecutarse sin errores.

### Commit sugerido

```bash
git add .
git commit -m "test: add validation and credit service tests"
```

---

## Tarea 19 — Documentar ejecución local

**Objetivo:** dejar instrucciones claras para que cualquier integrante pueda ejecutar el proyecto.

### Archivos involucrados

```text
README.md
docs/endpoints.md
docs/flujo_conversacional.md
```

### README debe incluir

- Descripción del proyecto.
- Tecnologías usadas.
- Instalación.
- Variables de entorno.
- Comando para ejecutar servidor.
- Cómo probar con `/simulate/message`.
- Cómo configurar Supabase.
- Cómo conectar WhatsApp.

### Criterio de aceptación

Un integrante nuevo debe poder levantar el proyecto siguiendo el README.

### Commit sugerido

```bash
git add .
git commit -m "docs: add local setup and API usage guide"
```

---

## Tarea 20 — Preparar despliegue

**Objetivo:** dejar listo el backend para una demostración en línea.

### Opciones sugeridas

- Render
- Railway
- Fly.io
- Vercel Serverless no recomendado para este caso si se requiere backend persistente

### Actividades

- [ ] Crear archivo de configuración de despliegue si aplica.
- [ ] Configurar variables de entorno en la plataforma.
- [ ] Verificar endpoint `/health` en producción.
- [ ] Configurar URL pública como webhook de WhatsApp.
- [ ] Probar mensaje real desde WhatsApp.

### Criterio de aceptación

El backend debe estar disponible públicamente para recibir eventos de WhatsApp.

### Commit sugerido

```bash
git add .
git commit -m "chore: prepare backend deployment configuration"
```

---

# 12. Flujo de ramas recomendado

```text
main
  └── develop
        ├── feature/project-setup
        ├── feature/fastapi-config
        ├── feature/supabase-schema
        ├── feature/repositories
        ├── feature/conversation-engine
        ├── feature/whatsapp-webhook
        ├── feature/human-handoff
        ├── feature/admin-endpoints
        └── feature/tests
```

## Reglas de trabajo

- `main`: solo versión estable.
- `develop`: integración del MVP.
- `feature/*`: una rama por funcionalidad.
- Cada commit debe representar un avance claro.
- No subir `.env`.
- No subir claves de Supabase ni WhatsApp.

---

# 13. Convención de commits

```text
feat: nueva funcionalidad
fix: corrección de error
chore: configuración o mantenimiento
docs: documentación
test: pruebas
refactor: mejora interna sin cambiar funcionalidad
```

## Ejemplos

```bash
git commit -m "feat: add credit evaluation service"
git commit -m "fix: validate invalid amount input"
git commit -m "docs: update local setup guide"
git commit -m "test: add preapproval calculation tests"
```

---

# 14. Casos de prueba funcionales del MVP

## Caso 1 — Cliente preaprobado

```text
Hola
1
Carlos Ortiz
500
12
700
1
```

Resultado esperado:

```text
preaprobado
```

---

## Caso 2 — Cliente observado

```text
Hola
1
Juan Pérez
2000
12
600
1
```

Resultado esperado:

```text
observado
```

---

## Caso 3 — Cliente no cumple

```text
Hola
1
María López
5000
6
400
1
```

Resultado esperado:

```text
no_cumple
```

---

## Caso 4 — Dato inválido

```text
Hola
1
Carlos Ortiz
quinientos
```

Resultado esperado:

```text
El monto ingresado no es válido. Por favor escribe solo números.
```

---

## Caso 5 — Derivación humana directa

```text
Hola
3
```

Resultado esperado:

```text
Tu caso será derivado a un asesor humano.
```

Debe registrarse un caso en `handoff_cases`.

---

# 15. Orden recomendado para desarrollar

El orden ideal para construir el MVP es:

```text
1. Estructura del proyecto
2. FastAPI funcionando
3. Configuración de entorno
4. Supabase schema
5. Cliente Supabase
6. Repositorios
7. Validaciones
8. Regla de negocio
9. Plantillas de mensajes
10. Motor conversacional
11. Simulador local
12. Webhook WhatsApp
13. Servicio de envío WhatsApp
14. Derivación humana
15. Endpoints administrativos
16. Pruebas
17. Documentación
18. Despliegue
```

Este orden permite probar primero el flujo completo de forma local antes de depender de WhatsApp.

---

# 16. Criterios de finalización del MVP

El MVP se considera completo cuando:

- [ ] El servidor FastAPI levanta correctamente.
- [ ] Supabase está conectado.
- [ ] Se puede simular una conversación completa.
- [ ] Cada usuario mantiene su propio estado.
- [ ] Los datos se guardan en Supabase.
- [ ] La regla de negocio calcula un resultado.
- [ ] El bot responde con preaprobado, observado o no cumple.
- [ ] Se registra derivación humana si aplica.
- [ ] El webhook de WhatsApp está implementado.
- [ ] Existe documentación para ejecutar y probar.
- [ ] El proyecto está organizado en Git con ramas y commits claros.

---

# 17. Entregable técnico esperado

Al finalizar el desarrollo, el repositorio debe contener:

```text
Código fuente FastAPI
Conexión con Supabase
Schema SQL de base de datos
Motor conversacional por estados
Regla de negocio de precalificación
Webhook de WhatsApp
Endpoint de simulación local
Endpoints administrativos básicos
Pruebas mínimas
README de ejecución
Documentación del flujo
```

---

# 18. Recomendación para la demostración

Para la demostración académica, primero se debe mostrar el flujo usando `/simulate/message`, porque permite comprobar que el backend funciona sin depender de configuraciones externas.

Luego se puede mostrar la integración con WhatsApp Sandbox o WhatsApp Cloud API si ya está configurada.

Orden sugerido de presentación:

```text
1. Mostrar estructura del repositorio.
2. Mostrar FastAPI corriendo.
3. Probar endpoint /health.
4. Probar conversación con /simulate/message.
5. Mostrar datos guardados en Supabase.
6. Mostrar resultado de precalificación.
7. Mostrar caso derivado a asesor.
8. Mostrar webhook de WhatsApp configurado.
```

---

# 19. Resultado final esperado

CrediBot quedará como un backend funcional desarrollado con Python y FastAPI, conectado a Supabase, capaz de manejar conversaciones estructuradas para precalificación de créditos por WhatsApp.

El sistema demostrará un flujo completo desde el primer mensaje del cliente hasta el resultado final de la solicitud, incluyendo validaciones, persistencia de datos y derivación a asesor humano.
