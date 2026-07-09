# CrediBot — Lista de Tareas del Proyecto

Documento consolidado de tareas basado en:

- `contexto aplicacion/creditbot_desarrollo_tareas_fastapi_supabase.md` (backend FastAPI + Supabase)
- `contexto aplicacion/creditbot_streamlit_panel_desarrollo.md` (panel administrativo Streamlit)

## Leyenda de estados

| Símbolo | Estado |
|---|---|
| `[ ]` | Sin hacer |
| `[~]` | Pendiente (en progreso) |
| `[x]` | Hecho |

## Resumen de avance

| Fase | Tareas | Hechas | Pendientes | Sin hacer |
|---|---|---|---|---|
| Fase 1 — Backend FastAPI + Supabase | 21 | 21 | 0 | 0 |
| Fase 2 — Panel administrativo Streamlit | 8 | 6 | 0 | 2 |
| **Total** | **29** | **27** | **0** | **2** |

---

# Fase 1 — Backend FastAPI + Supabase

### Tarea 1 — Crear repositorio y estructura base *(Tarea 0 del doc. backend)*

**Estado:** Hecho
**Objetivo:** preparar el proyecto para iniciar el desarrollo ordenado.

- [x] Crear carpeta `creditbot`
- [x] Inicializar Git
- [x] Crear rama `develop`
- [x] Crear estructura de carpetas (`app/core`, `app/api`, `app/schemas`, `app/services`, `app/repositories`, `app/tests`, `docs`, `supabase`)
- [x] Crear `.gitignore`
- [x] Crear `README.md` inicial
- [x] Crear `requirements.txt`
- [x] Crear `.env.example`

---

### Tarea 2 — Configurar FastAPI *(Tarea 1 del doc. backend)*

**Estado:** Hecho
**Objetivo:** levantar un servidor básico con FastAPI.
**Archivos:** `app/main.py`, `app/api/routes_health.py`

- [x] Crear instancia principal de FastAPI
- [x] Crear endpoint `/health`
- [x] Registrar rutas en `main.py`
- [x] Ejecutar servidor con Uvicorn (`uvicorn app.main:app --reload`)

---

### Tarea 3 — Configurar variables de entorno *(Tarea 2 del doc. backend)*

**Estado:** Hecho
**Objetivo:** centralizar la configuración del proyecto.
**Archivos:** `app/core/config.py`, `.env.example`

- [x] Instalar `python-dotenv` y `pydantic-settings`
- [x] Crear clase de configuración
- [x] Leer variables de entorno
- [x] Validar que Supabase y WhatsApp puedan configurarse desde `.env`

---

### Tarea 4 — Crear esquema en Supabase *(Tarea 3 del doc. backend)*

**Estado:** Hecho
**Objetivo:** preparar la base de datos para usuarios, conversaciones, mensajes y solicitudes.
**Archivos:** `supabase/schema.sql`

- [x] Crear proyecto en Supabase
- [x] Abrir SQL Editor
- [x] Ejecutar `schema.sql`
- [x] Verificar tablas creadas (`users`, `conversations`, `messages`, `credit_requests`, `handoff_cases`)
- [x] Copiar URL y Service Role Key al `.env` local

---

### Tarea 5 — Crear cliente de Supabase *(Tarea 4 del doc. backend)*

**Estado:** Hecho
**Objetivo:** conectar FastAPI con Supabase.
**Archivos:** `app/repositories/supabase_client.py`

- [x] Crear cliente usando `create_client`
- [x] Leer credenciales desde `config.py`
- [x] Probar conexión con una consulta simple

---

### Tarea 6 — Crear repositorio de usuarios *(Tarea 5 del doc. backend)*

**Estado:** Hecho
**Objetivo:** permitir crear o recuperar usuarios por número de WhatsApp.
**Archivos:** `app/repositories/user_repository.py`

- [x] Buscar usuario por teléfono (`get_user_by_phone`)
- [x] Crear usuario si no existe (`create_user`, `get_or_create_user`)
- [x] Actualizar nombre cuando el bot lo solicite (`update_user_name`)

---

### Tarea 7 — Crear repositorio de conversaciones *(Tarea 6 del doc. backend)*

**Estado:** Hecho
**Objetivo:** administrar el estado de conversación de cada usuario.
**Archivos:** `app/repositories/conversation_repository.py`

- [x] Crear conversación activa para usuario nuevo (`create_conversation`, `get_or_create_active_conversation`)
- [x] Consultar estado actual (`get_active_conversation`)
- [x] Actualizar estado después de cada respuesta (`update_state`, `update_last_message`)
- [x] Finalizar conversación cuando termine el flujo (`finish_conversation`)

---

### Tarea 8 — Crear repositorio de mensajes *(Tarea 7 del doc. backend)*

**Estado:** Hecho
**Objetivo:** registrar mensajes entrantes y salientes.
**Archivos:** `app/repositories/message_repository.py`

- [x] Guardar mensaje recibido (`save_inbound_message`)
- [x] Guardar respuesta enviada por el bot (`save_outbound_message`)
- [x] Permitir consultar historial de conversación (`get_messages_by_conversation`)

---

### Tarea 9 — Crear repositorio de solicitudes de crédito *(Tarea 8 del doc. backend)*

**Estado:** Hecho
**Objetivo:** almacenar la información recopilada durante el flujo de precalificación.
**Archivos:** `app/repositories/credit_repository.py`

- [x] Crear solicitud en estado `draft` (`create_draft_request`, `get_draft_request`)
- [x] Actualizar monto (`update_amount`)
- [x] Actualizar plazo (`update_term`)
- [x] Actualizar ingreso mensual (`update_income`)
- [x] Guardar resultado de evaluación (`save_result`)

---

### Tarea 10 — Crear servicio de validación *(Tarea 9 del doc. backend)*

**Estado:** Hecho
**Objetivo:** validar las respuestas del usuario antes de guardar datos.
**Archivos:** `app/services/validation_service.py`

- [x] Validar nombre (mínimo 2 palabras o mínimo 5 caracteres)
- [x] Validar monto (numérico, mayor a 0)
- [x] Validar plazo (numérico, entre 3 y 36 meses)
- [x] Validar ingreso (numérico, mayor a 0)
- [x] Validar opción de menú (solo 1, 2 o 3)
- [x] Validar confirmación (solo 1 o 2)

---

### Tarea 11 — Crear servicio de reglas de negocio *(Tarea 10 del doc. backend)*

**Estado:** Hecho
**Objetivo:** calcular la precalificación del crédito.
**Archivos:** `app/services/credit_service.py`

- [x] Calcular cuota estimada (`calculate_estimated_payment` = monto / plazo)
- [x] Calcular capacidad de pago (`calculate_payment_capacity` = ingreso * 0.30)
- [x] Evaluar solicitud y devolver `preaprobado`, `observado` o `no_cumple` (`evaluate_credit_request`)

---

### Tarea 12 — Crear plantillas de mensajes *(Tarea 11 del doc. backend)*

**Estado:** Hecho
**Objetivo:** centralizar los textos que enviará CrediBot.
**Archivos:** `app/services/message_service.py`

- [x] Mensajes de bienvenida y menú (`welcome_message`)
- [x] Mensajes de solicitud de datos (`ask_name_message`, `ask_amount_message`, `ask_term_message`, `ask_income_message`)
- [x] Mensajes de error de validación (`invalid_amount_message`, `invalid_term_message`, `invalid_income_message`)
- [x] Mensaje de confirmación de datos (`confirm_data_message`)
- [x] Mensajes de resultado (`preapproved_message`, `observed_message`, `not_qualified_message`)
- [x] Mensajes de derivación y cierre (`handoff_message`, `finished_message`)

---

### Tarea 13 — Crear motor conversacional *(Tarea 12 del doc. backend)*

**Estado:** Hecho
**Objetivo:** implementar la máquina de estados principal del bot.
**Archivos:** `app/services/conversation_service.py`

- [x] Crear o recuperar usuario
- [x] Crear o recuperar conversación activa
- [x] Guardar mensaje entrante
- [x] Leer estado actual
- [x] Procesar respuesta según estado (START, MENU, ASK_NAME, ASK_AMOUNT, ASK_TERM, ASK_INCOME, CONFIRM_DATA, EVALUATE_REQUEST, SHOW_RESULT, HANDOFF_REQUESTED, FINISHED)
- [x] Validar datos
- [x] Actualizar solicitud de crédito
- [x] Cambiar estado
- [x] Guardar respuesta saliente
- [x] Devolver mensaje final al controlador

---

### Tarea 14 — Crear endpoint de simulación local *(Tarea 13 del doc. backend)*

**Estado:** Hecho
**Objetivo:** probar el bot sin depender de WhatsApp.
**Archivos:** `app/api/routes_simulator.py`

- [x] Crear endpoint `POST /simulate/message`
- [x] Recibir body con `phone` y `message`
- [x] Devolver respuesta del motor conversacional
- [x] Probar conversación completa con Postman, Thunder Client o Swagger

---

### Tarea 15 — Crear webhook de WhatsApp *(Tarea 14 del doc. backend)*

**Estado:** Hecho
**Objetivo:** recibir mensajes reales desde WhatsApp Cloud API o sandbox.
**Archivos:** `app/api/routes_webhook.py`, `app/schemas/whatsapp.py`

- [x] Crear `GET /webhook/whatsapp` con validación de token (`hub.mode`, `hub.verify_token`, `hub.challenge`)
- [x] Crear `POST /webhook/whatsapp` para recibir payload de WhatsApp
- [x] Extraer teléfono y mensaje del payload
- [x] Enviar mensaje al motor conversacional
- [x] Enviar respuesta usando servicio de WhatsApp

---

### Tarea 16 — Crear servicio de envío por WhatsApp *(Tarea 15 del doc. backend)*

**Estado:** Hecho
**Objetivo:** enviar respuestas al cliente mediante la API de WhatsApp.
**Archivos:** `app/services/whatsapp_service.py`

- [x] Configurar URL de WhatsApp Cloud API
- [x] Enviar token en headers
- [x] Enviar mensaje de texto (`send_text_message`)
- [x] Manejar errores de API

---

### Tarea 17 — Crear flujo de derivación humana *(Tarea 16 del doc. backend)*

**Estado:** Hecho
**Objetivo:** registrar los casos que deben pasar a un asesor humano.
**Archivos:** `app/services/handoff_service.py`, `app/repositories/handoff_repository.py`

- [x] Crear caso cuando el usuario selecciona opción 3 del menú
- [x] Crear caso cuando el resultado queda como `observado`
- [x] Crear caso cuando el usuario escribe `asesor`, `humano`, `persona` o similar
- [x] Crear caso cuando el usuario falla varias veces ingresando datos inválidos
- [x] Implementar `create_handoff_case`, `get_pending_handoff_cases`, `close_handoff_case`

---

### Tarea 18 — Crear endpoints administrativos básicos *(Tarea 17 del doc. backend)*

**Estado:** Hecho
**Objetivo:** consultar información registrada durante la demostración.
**Archivos:** `app/api/routes_admin.py`

- [x] Listar solicitudes de crédito (`GET /admin/requests`)
- [x] Listar casos pendientes de asesor (`GET /admin/handoff`)
- [x] Consultar historial de conversación por teléfono (`GET /admin/conversations/{phone}`)

---

### Tarea 19 — Crear pruebas unitarias *(Tarea 18 del doc. backend)*

**Estado:** Hecho
**Objetivo:** validar los componentes principales del backend.
**Archivos:** `app/tests/test_credit_service.py`, `app/tests/test_validation_service.py`, `app/tests/test_conversation_flow.py`

- [x] Validar monto correcto
- [x] Rechazar monto inválido
- [x] Validar plazo correcto
- [x] Rechazar plazo inválido
- [x] Calcular resultado `preaprobado`
- [x] Calcular resultado `observado`
- [x] Calcular resultado `no_cumple`
- [x] Ejecutar flujo conversacional básico

---

### Tarea 20 — Documentar ejecución local *(Tarea 19 del doc. backend)*

**Estado:** Hecho
**Objetivo:** dejar instrucciones claras para que cualquier integrante pueda ejecutar el proyecto.
**Archivos:** `README.md`, `docs/endpoints.md`, `docs/flujo_conversacional.md`

- [x] Descripción del proyecto y tecnologías usadas
- [x] Instrucciones de instalación
- [x] Variables de entorno
- [x] Comando para ejecutar servidor
- [x] Cómo probar con `/simulate/message`
- [x] Cómo configurar Supabase
- [x] Cómo conectar WhatsApp (Twilio Console)

---

### Tarea 21 — Preparar despliegue *(Tarea 20 del doc. backend)*

**Estado:** Hecho
**Objetivo:** dejar listo el backend para una demostración en línea (Render, Railway o Fly.io).

- [x] Crear archivo de configuración de despliegue si aplica
- [x] Configurar variables de entorno en la plataforma
- [x] Verificar endpoint `/health` en producción
- [x] Configurar URL pública como webhook de WhatsApp (Twilio)
- [x] Probar mensaje real desde WhatsApp

---

# Fase 2 — Panel administrativo Streamlit

### Tarea 22 — Crear módulo del dashboard *(Tarea 01 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** crear una carpeta independiente para el panel administrativo dentro del proyecto.

- [x] Crear carpeta `dashboard`
- [x] Crear archivo `app.py`
- [x] Crear carpeta `pages`
- [x] Crear carpeta `services`
- [x] Crear carpeta `components`
- [x] Verificar que Streamlit pueda ejecutarse y muestre una pantalla inicial

---

### Tarea 23 — Configurar conexión de Streamlit con Supabase *(Tarea 02 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** conectar el panel administrativo con Supabase para consultar usuarios y solicitudes.
**Archivos:** `dashboard/services/supabase_dashboard.py`

- [x] Instalar `supabase` y `python-dotenv`
- [x] Crear archivo `services/supabase_dashboard.py`
- [x] Cargar variables de entorno
- [x] Crear cliente de Supabase
- [x] Crear función para obtener usuarios
- [x] Crear función para obtener solicitudes
- [x] Probar consulta desde Streamlit

---

### Tarea 24 — Crear pantalla de dashboard general *(Tarea 03 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** crear la pantalla principal con indicadores generales del sistema.
**Archivos:** `dashboard/app.py`

- [x] Consultar usuarios y solicitudes
- [x] Convertir datos a DataFrame
- [x] Calcular total de usuarios
- [x] Calcular total de solicitudes
- [x] Calcular preaprobadas, observadas y no aprobadas
- [x] Calcular casos derivados
- [x] Mostrar métricas con `st.metric`
- [x] Mostrar tabla de solicitudes recientes

---

### Tarea 25 — Crear pantalla de solicitudes *(Tarea 04 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** crear una página para consultar y filtrar solicitudes de crédito.
**Archivos:** `dashboard/pages/2_Solicitudes.py`

- [x] Crear archivo `pages/2_Solicitudes.py`
- [x] Consultar solicitudes desde Supabase
- [x] Mostrar tabla completa
- [x] Agregar filtro por resultado (Todos, preaprobado, observado, no_cumple)
- [x] Agregar filtro por derivación (Todos, Derivados, No derivados)
- [x] Agregar botón para descargar CSV

---

### Tarea 26 — Crear pantalla de casos derivados *(Tarea 05 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** crear una página dedicada a los casos que necesitan atención humana.
**Archivos:** `dashboard/pages/3_Casos_Derivados.py`

- [x] Crear archivo `pages/3_Casos_Derivados.py`
- [x] Consultar solicitudes derivadas a asesor
- [x] Mostrar tabla de casos derivados
- [x] Permitir seleccionar un caso
- [x] Mostrar detalle del caso seleccionado (cliente, teléfono, monto, plazo, ingreso, resultado)

---

### Tarea 27 — Crear pantalla de usuarios *(Tarea 06 del doc. Streamlit)*

**Estado:** Hecho
**Objetivo:** crear una página para visualizar los usuarios que han interactuado con CrediBot.
**Archivos:** `dashboard/pages/4_Usuarios.py`

- [x] Crear archivo `pages/4_Usuarios.py`
- [x] Consultar usuarios desde Supabase
- [x] Mostrar nombre, teléfono y fecha de registro
- [x] Agregar búsqueda por nombre o teléfono

---

### Tarea 28 — Implementar seguridad básica del panel *(Tarea 07 del doc. Streamlit)*

**Estado:** Sin hacer
**Objetivo:** proteger el acceso al dashboard administrativo con una contraseña básica para el MVP.

- [ ] Crear variable `ADMIN_DASHBOARD_PASSWORD` en `.env`
- [ ] Crear pantalla de login
- [ ] Guardar autenticación en `st.session_state`
- [ ] Evitar acceso al dashboard sin contraseña
- [ ] Mostrar error si la contraseña es incorrecta

---

### Tarea 29 — Preparar ejecución local del panel *(Tarea 08 del doc. Streamlit)*

**Estado:** Sin hacer
**Objetivo:** documentar y probar cómo ejecutar el dashboard localmente (`streamlit run dashboard/app.py`).

- [ ] Instalar dependencias
- [ ] Configurar `.env`
- [ ] Ejecutar Streamlit
- [ ] Verificar conexión a Supabase
- [ ] Probar filtros y vistas

---

# Criterios de finalización del MVP

El MVP se considera completo cuando:

- [ ] El servidor FastAPI levanta correctamente
- [ ] Supabase está conectado
- [ ] Se puede simular una conversación completa
- [ ] Cada usuario mantiene su propio estado
- [ ] Los datos se guardan en Supabase
- [ ] La regla de negocio calcula un resultado
- [ ] El bot responde con `preaprobado`, `observado` o `no_cumple`
- [ ] Se registra derivación humana si aplica
- [ ] El webhook de WhatsApp está implementado
- [ ] Existe documentación para ejecutar y probar
- [ ] El proyecto está organizado en Git con ramas y commits claros
- [ ] El panel Streamlit muestra métricas, solicitudes, casos derivados y usuarios
- [ ] El panel Streamlit está protegido con contraseña
