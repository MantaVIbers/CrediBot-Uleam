# Bitácora de desarrollo — CrediBot

Documento de trabajo que resume **qué se ha construido**, **con qué herramientas** y
**por qué se eligió cada una** en el proyecto CrediBot (agente conversacional de
precalificación de crédito por WhatsApp).

> Repositorio: `MantaVIbers/CrediBot-Uleam` · Rama de trabajo: `develop`
> Despliegue: `https://credibot-uleam-gjj2.onrender.com`

---

## 1. Descripción del proyecto

**CrediBot** es un agente conversacional que guía a una persona, paso a paso, para
**precalificar** una solicitud de crédito. El usuario conversa (por WhatsApp o por el
simulador), entrega sus datos, autoriza la consulta de su historial y recibe un
resultado: **preaprobado**, **observado** o **no cumple**, con el monto máximo, la cuota
estimada y la tasa referencial.

La lógica crediticia es **determinista** (reglas de negocio puras), de modo que el
resultado sea explicable y reproducible, no un número inventado. La IA se usa como
capa de redacción: mejora el lenguaje de la respuesta, pero no cambia estados,
montos, tasas, score ni resultados.

---

## 2. Arquitectura por capas

El proyecto separa responsabilidades en capas, lo que facilita las pruebas y el
mantenimiento:

```text
WhatsApp / Simulador
        │
        ▼
  API (FastAPI)  ──►  routes_webhook / routes_simulator / routes_admin / routes_health
        │
        ▼
  Servicios      ──►  conversation_service (flujo), precalificacion_service, validation_service...
        │
        ├─► Agente IA      ──►  openai_agent   (redacción controlada, con fallback)
        ├─► Dominio        ──►  cedula_validator, credit_rules   (lógica pura, sin BD)
        │
        └─► Repositorios   ──►  acceso a Supabase (users, credit_requests, credit_profiles,
                                 tool_audit_logs, ...)
```

- **Dominio**: reglas de negocio puras (validación de cédula y motor de crédito). No
  conoce la base de datos ni el canal. Es 100% testeable.
- **Servicios**: orquestan el flujo de la conversación y combinan dominio + repositorios.
- **Agente IA**: redacta respuestas con OpenAI cuando hay API key; si falla, devuelve
  el texto base para no cortar la conversación.
- **Repositorios**: única capa que habla con Supabase.
- **API**: expone los endpoints HTTP.

---

## 3. Trabajo realizado (paso a paso)

Cada paso se entregó como uno o varios commits con mensajes descriptivos (Conventional
Commits).

### Paso 1 — Esquema de base de datos v2 + datos de prueba
- `supabase/schema.sql`: tablas del modelo v2 (`users` con cédula/consentimiento,
  `credit_profiles`, `credit_history_events`, `tool_audit_logs`, campos v2 en
  `credit_requests`, y tablas RAG preparadas).
- `supabase/seed_credit_profiles.sql`: **21 perfiles crediticios ficticios pero válidos**
  (cédulas que pasan el algoritmo módulo 10), cubriendo las 4 categorías de score y casos
  de mora/lista negra.
- Tests que validan la integridad del seed.
- _Commit:_ `feat(supabase): schema v2 con perfiles crediticios y seed de datos`

### Paso 2 — Dominio: validación de cédula y reglas de crédito
- `app/domain/cedula_validator.py`: valida cédula ecuatoriana (módulo 10) y la enmascara
  para logs (`09******75`).
- `app/domain/credit_rules.py`: categorización de score, elegibilidad, tasa por categoría,
  capacidad de pago, cuota (amortización francesa), monto máximo y precalificación.
- Tests unitarios de ambos módulos.
- _Commit:_ `feat(domain): validador de cedula y motor de reglas de credito`

### Paso 3 — Repositorio de perfiles crediticios
- `app/repositories/credit_profile_repository.py`: lee el perfil por cédula desde
  Supabase (buró simulado). Tests con cliente de Supabase mockeado.
- _Commit:_ `feat(repositories): repositorio de perfiles crediticios por cedula`

### Paso 4 — Servicio de precalificación v2
- `app/services/precalificacion_service.py`: orquesta validar cédula → buscar perfil →
  aplicar reglas. Trata perfiles inexistentes o "thin file" como sin historial. Tests con
  el repositorio mockeado.
- _Commit:_ `feat(services): servicio de precalificacion crediticia v2`

### Paso 5 — Integración al flujo conversacional (cédula + consentimiento)
- Nuevos estados `ASK_CEDULA` y `CONSENT` en `conversation_service.py`.
- Se solicita cédula (validada) y **consentimiento** antes de consultar el buró (RF-08);
  sin autorización la conversación termina.
- El resultado final usa la precalificación v2 (score real, categoría, monto máximo, TEA,
  cuota) y persiste los campos v2 en `credit_requests` y la cédula/consentimiento en
  `users`.
- _Commit:_ `feat(conversation): integrar cedula, consentimiento y precalificacion v2 al flujo`

### Paso 6 — Auditoría de tools con cédula enmascarada
- `app/repositories/audit_repository.py`: registra cada invocación de la "tool" de
  precalificación en `tool_audit_logs` (entrada/salida, éxito, latencia, conversación),
  con la **cédula enmascarada** (RNF-04). Es *best-effort*: si falla el registro, no rompe
  la conversación.
- _Commit:_ `feat(audit): auditoria de tools con cedula enmascarada (tool_audit_logs)`

### Paso 7 — Agente IA con OpenAI
- `app/agent/openai_agent.py`: integra OpenAI mediante `client.responses.create`.
  Recibe una respuesta base ya validada por el backend y la redacta en tono natural
  para WhatsApp.
- La IA no decide el crédito: conserva opciones, montos, plazos, score, categoría y
  resultado. Si no existe `OPENAI_API_KEY` o la API falla, el bot responde con el
  texto base.
- El agente recibe contexto seguro: estado anterior, estado objetivo, paso pendiente
  y fragmentos RAG permitidos. Esto evita que el modelo pierda el flujo o invente
  condiciones.
- Tests cubren el fallback sin API key, el flag de desactivación y la llamada mockeada
  a OpenAI.
- _Commits:_ `agrega agente de ia`, `mejora contexto de ia`

### Paso 8 — Intención natural y destino del crédito
- `app/services/intent_service.py`: permite detectar intención del usuario sin obligarlo
  a escribir solo números (`quiero un crédito`, `información`, `hablar con asesor`).
- El flujo ahora recopila el destino o producto de interés antes del monto, por ejemplo
  estudios, negocio, consumo o emergencia.
- La opción de asesor queda visible durante el flujo con un recordatorio permanente.
- _Commits:_ `mejora intencion del flujo`, `agrega destino del credito`

### Paso 9 — RAG básico de políticas
- `docs/policies/credito_mvp.md`: documento fuente para requisitos, documentos, montos,
  plazos, tasas referenciales y derivación humana.
- `app/services/rag_service.py`: recupera secciones relevantes por coincidencia léxica
  y construye una respuesta informativa con fuente local.
- El flujo responde dudas de políticas sin cambiar el estado actual; luego recuerda qué
  dato falta para continuar.
- _Commits:_ `agrega rag de politicas`, `conecta rag al flujo`

### Paso 10 — Handoff con resumen y transcript
- Cada mensaje entrante y saliente se guarda en `messages` con `conversation_id`, de modo
  que el historial puede consultarse después.
- Los casos de `handoff_cases` ahora guardan `handoff_summary` y `transcript` con los
  últimos mensajes relevantes para que el asesor humano retome el caso con contexto.
- El resumen indica el motivo de derivación y el último mensaje del cliente.
- _Commit:_ `guarda resumen de handoff`

### DevOps — CI/CD y contenerización
- `.github/workflows/ci.yml`: pipeline de **GitHub Actions** que instala dependencias y
  corre las pruebas en cada push/PR a `main` y `develop`.
- `creditbot/Dockerfile` + `.dockerignore`: imagen del backend para desplegarlo como
  contenedor.
- _Commit:_ `ci: pipeline de GitHub Actions (build + tests) y contenerizacion Docker`

### Integración con Supabase y despliegue
- Configuración del archivo `.env` con las credenciales de Supabase (no se versiona).
- Despliegue del backend en **Render** desde la rama `develop`.
- Verificación end-to-end en la URL pública: lectura de perfiles, cálculo, persistencia
  de solicitud, consentimiento y auditoría.

### Corrección detectada en producción
- `fix(conversation): persistir consentimiento leyendo la cedula de la solicitud`:
  el consentimiento no se guardaba en `users` porque la cédula se leía de un objeto en
  memoria que se recargaba en cada mensaje; ahora se lee de la solicitud ya persistida.

**Estado de pruebas:** 90 pruebas automatizadas, todas en verde.

---

## 4. Herramientas y tecnologías: qué son y por qué se usan aquí

### Lenguaje y framework

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **Python 3.12+** | Lenguaje de programación | Ecosistema maduro para back-end y datos; sintaxis clara para lógica de negocio. |
| **FastAPI** | Framework web para APIs | Define los endpoints (webhook de WhatsApp, simulador, salud, admin) con validación automática y documentación `/docs` incluida. |
| **Uvicorn** | Servidor ASGI | Ejecuta la aplicación FastAPI en local y en producción. |
| **Pydantic / pydantic-settings** | Validación de datos y configuración | Valida los cuerpos de las peticiones y carga la configuración desde variables de entorno (`.env`). |

### Base de datos

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **Supabase** | Plataforma sobre PostgreSQL (BD + API + panel) | Almacena usuarios, conversaciones, mensajes, solicitudes, perfiles crediticios y auditoría. Gratis, rápido de montar y con SQL Editor para cargar el esquema. |
| **PostgreSQL** | Motor de base de datos relacional | Es la BD que corre bajo Supabase; da integridad referencial y restricciones (checks). |
| **supabase-py** | Cliente oficial de Supabase para Python | Permite leer/escribir en las tablas desde los repositorios. |

### Mensajería (WhatsApp)

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **Twilio (WhatsApp)** | Proveedor de mensajería en la nube | Conecta el bot con WhatsApp mediante un webhook, sin integrar directamente la API de Meta. En desarrollo se usa el **Sandbox**. |
| **Simulador propio** (`/simulate/message`) | Endpoint interno de pruebas | Permite probar TODO el flujo conversacional **sin depender de Twilio**, ideal para demos y pruebas automáticas. |

### Pruebas y calidad

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **pytest** | Framework de pruebas | Verifica el dominio, los servicios y el flujo conversacional. Da confianza para refactorizar. |
| **unittest.mock / monkeypatch** | Utilidades de simulación | Aíslan la lógica de la base de datos (se "mockea" Supabase), para probar sin una BD real. |

### DevOps

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **Git** | Control de versiones | Historial del proyecto y trabajo por ramas. |
| **GitHub** | Alojamiento del repositorio | Repositorio público, revisión por Pull Requests y hospedaje del pipeline. |
| **GitHub Actions** | Integración continua (CI) | En cada push/PR instala dependencias y corre las pruebas automáticamente (build + tests). |
| **Docker** | Contenedores | Empaqueta la app con sus dependencias para ejecutarla igual en cualquier entorno; opción de despliegue portable. |
| **Render** | Plataforma de despliegue (PaaS) | Publica el backend con una URL pública accesible, con despliegue automático desde la rama de Git. |

### Panel administrativo (complementario)

| Herramienta | Qué es | Por qué se usa en CrediBot |
|---|---|---|
| **Streamlit** | Framework de apps de datos | Panel interno para revisar métricas, solicitudes, casos derivados y usuarios. Es una app separada del backend. |
| **pandas** | Análisis de datos | Da soporte a las tablas y métricas del panel Streamlit. |

---

## 5. Estrategia de ramas (Git)

- **`main`**: rama estable; representa lo que se despliega/demuestra.
- **`develop`**: rama de integración donde se juntan los avances (rama de trabajo actual).
- **`feature/*`** (opcional): una rama por funcionalidad, que luego se integra a `develop`.

Flujo: `feature/* → develop → main`. El despliegue en Render sigue, por ahora, a
`develop` para pruebas; se cambiará a `main` una vez validado.

---

## 6. Cómo ejecutar el proyecto

### Local
```bash
cd creditbot
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env         # y completar credenciales de Supabase
uvicorn app.main:app --reload
```
Documentación interactiva: `http://localhost:8000/docs`

### Pruebas
```bash
cd creditbot
pytest -v
```

### Docker
```bash
cd creditbot
docker build -t credibot .
docker run --rm -p 8000:8000 --env-file .env credibot
```

---

## 7. Variables de entorno

| Variable | Descripción |
|---|---|
| `SUPABASE_URL` | URL base del proyecto Supabase (sin `/rest/v1/`). |
| `SUPABASE_SERVICE_ROLE_KEY` | Clave secreta (server-side) de Supabase. |
| `DEFAULT_COUNTRY_CODE` | Código de país por defecto (`593`). |
| `TWILIO_VALIDATE_SIGNATURE` | `true` en producción con Twilio, `false` en local. |
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_WHATSAPP_FROM` | Credenciales de Twilio (para WhatsApp real). |
| `ADMIN_DASHBOARD_PASSWORD` | Clave del panel Streamlit (solo panel, no el backend). |

> El archivo `.env` **no se versiona** (está en `.gitignore`) porque contiene secretos.

---

## 8. Próximos pasos

1. Configurar **Twilio** para probar desde WhatsApp real (webhook →
   `/webhook/whatsapp`).
2. Fusionar `develop → main` y apuntar Render a `main`.
3. (Futuro) Agente IA con tools + RAG sobre políticas de crédito (tablas ya previstas en
   el esquema).
