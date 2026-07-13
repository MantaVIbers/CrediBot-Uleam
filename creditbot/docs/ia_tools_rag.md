# CrediBot — IA, tools, RAG y cálculos

Documento de referencia para la evaluación del proyecto. Resume **cómo se calculan**
los resultados, **qué tools existen**, **cómo funciona el RAG** y **dónde queda
documentada** cada invocación.

---

## 1. Arquitectura en la nube

```text
WhatsApp (Twilio Sandbox)
        │ POST /webhook/whatsapp
        ▼
Render — FastAPI (rama develop)
        │
        ├── Supabase (PostgreSQL): users, credit_requests, credit_profiles, tool_audit_logs, rag_*
        ├── OpenAI API: normalización de texto, RAG, asistente conversacional
        └── GitHub Actions (CI): pytest en cada push/PR
```

| Componente | Servicio | Rol |
|---|---|---|
| Backend | Render | API FastAPI, webhook WhatsApp |
| Base de datos | Supabase | Persistencia y buró simulado |
| Mensajería | Twilio | Canal WhatsApp |
| IA | OpenAI | Interpretación de lenguaje natural + RAG |
| CI | GitHub Actions | Tests automáticos |
| CD | Render (auto-deploy) | Despliegue al hacer push a `develop` |
| Panel admin | Render (Streamlit) | Métricas, solicitudes, auditoría IA |

---

## 2. Cálculos crediticios (deterministas)

Los **montos, cuotas, tasas y resultados no los inventa el LLM**. Los calcula el
dominio puro en `app/domain/credit_rules.py`, invocado por la tool
`precalificar_por_cedula`.

### Entradas

- Score y perfil del buró simulado (`credit_profiles`)
- Ingreso mensual neto del usuario
- Plazo en meses (3–36)
- Monto solicitado (opcional, para evaluar cuota)

### Pasos del cálculo

1. **Categorizar score** (escala Ecuador 1–999):
   - Excelente: 750–999
   - Aceptable: 550–749
   - Regular: 349–549
   - Alto riesgo: 1–348

2. **Verificar elegibilidad**: lista negra, mora > 30 días, alto riesgo → no cumple.

3. **Capacidad de pago** = 35% del ingreso − cuotas vigentes del buró.

4. **TEA referencial** por categoría (excelente 14.5%, aceptable 16%, regular 16.5%).

5. **Monto máximo** = múltiplo del ingreso según categoría × reglas de cuota (amortización francesa).

6. **Resultado**:
   - **Preaprobado**: cuota ≤ capacidad de pago
   - **Observado**: cuota ≤ 115% de la capacidad
   - **No cumple**: resto de casos

### Código

- Motor: `app/domain/credit_rules.py`
- Orquestación: `app/services/precalificacion_service.py`
- Tests: `app/tests/test_credit_rules.py`, `app/tests/test_precalificacion_service.py`

---

## 3. Tools del agente

Cada “tool” es una función de negocio auditable. Toda invocación se registra en
`tool_audit_logs` (RNF-04) con entrada/salida, latencia y éxito. La cédula viaja
**enmascarada** en los payloads.

| Tool | Archivo | Cuándo se usa |
|---|---|---|
| `precalificar_por_cedula` | `precalificacion_service.py` | Al confirmar datos en el flujo de precalificación |
| `normalizar_entrada_usuario` | `ai_input_service.py` | En cada paso del flujo (monto, plazo, sí/no, menú…) |
| `consultar_politica_credito` | `ai_assistant_service.py` | Modo información (opción 2) y agente IA |
| `agente_openai_tools` | `agent_service.py` | Preguntas complejas en modo IA con function calling |

### Ejemplo de auditoría (Supabase)

```sql
SELECT tool_name, success, latency_ms, input_payload, output_payload, created_at
FROM tool_audit_logs
ORDER BY created_at DESC
LIMIT 20;
```

También visible en el panel Streamlit → **Auditoría IA**.

---

## 4. RAG (Retrieval-Augmented Generation)

### Objetivo (RF-07)

Responder preguntas sobre **políticas de crédito** usando contexto recuperado, sin
inventar reglas.

### Fuentes de conocimiento

1. **Documento local**: `creditbot/data/politica_credito.md`
2. **Supabase** (opcional): tablas `rag_documents` y `rag_chunks` — ver `seed_rag_documents.sql`
3. **Indexación**: script `scripts/index_rag.py` genera embeddings OpenAI (`text-embedding-3-small`, 1536 dims)

### Flujo RAG

```text
Pregunta del usuario
      │
      ▼
Embedding de la pregunta (OpenAI)
      │
      ▼
Búsqueda por similitud coseno sobre chunks de política
      │
      ▼
GPT recibe contexto + pregunta → respuesta en español
      │
      ▼
Registro en tool_audit_logs (consultar_politica_credito)
```

### Código

- Recuperación: `app/services/rag_service.py`
- Respuesta: `app/services/ai_assistant_service.py`
- Agente con tools: `app/services/agent_service.py`

---

## 5. IA en todo el flujo conversacional

Además del RAG, OpenAI **normaliza lenguaje natural** antes de validar:

| Usuario escribe | El bot interpreta |
|---|---|
| `un año` | 12 meses |
| `cinco mil` | 5000 |
| `sí, autorizo` | 1 (consentimiento) |
| `precalificar` | opción 1 del menú |

Código: `app/services/ai_input_service.py` (reglas locales + OpenAI como respaldo).

La precalificación sigue siendo **100% determinista** después de normalizar.

---

## 6. CI/CD

### CI (Integración continua)

Archivo: `.github/workflows/ci.yml`

- Dispara en push/PR a `main` y `develop`
- Instala dependencias y ejecuta `pytest -v`

### CD (Despliegue continuo)

- **Render** conectado al repo GitHub, rama `develop`
- Cada push exitoso redeploya el Web Service
- Health check: `GET /health`

Ver detalle en `docs/despliegue.md`.

---

## 7. Cómo demostrar al profesor (checklist)

1. **CI verde**: pestaña Actions en GitHub con workflow CI en verde.
2. **Nube viva**: `GET https://credibot-uleam.onrender.com/health` → OK.
3. **Flujo WhatsApp**: precalificación completa con lenguaje natural.
4. **Cálculo**: resultado con score, TEA, cuota y monto máximo.
5. **Tools**: filas nuevas en `tool_audit_logs` tras la demo.
6. **RAG**: opción 2 del menú → preguntar “¿qué es score excelente?”.
7. **Panel**: Streamlit con solicitudes v2 y página Auditoría IA.

---

## 8. Variables de entorno (IA)

| Variable | Descripción |
|---|---|
| `OPENAI_API_KEY` | Clave de API OpenAI |
| `OPENAI_MODEL` | Modelo chat (default: `gpt-4o-mini`) |

Configurar en Render y en `creditbot/.env` local.
