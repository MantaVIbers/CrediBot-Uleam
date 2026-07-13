# Panel administrativo Streamlit

El panel administrativo permite consultar la informacion registrada por CrediBot en Supabase: metricas generales, solicitudes de credito, casos derivados y usuarios.

La vista de casos derivados funciona como bandeja de atención humana: muestra el
motivo, resumen para asesor, últimos mensajes del transcript y permite cerrar el
caso cuando ya fue atendido.

## Requisitos

- Python 3.11+
- Dependencias instaladas desde `requirements.txt`
- Proyecto Supabase con el esquema de `supabase/schema.sql`
- Archivo `.env` configurado en la carpeta `creditbot`

## Instalacion

Desde la carpeta `creditbot`:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

En Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Variables necesarias

Edita `creditbot/.env` y configura:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
ADMIN_DASHBOARD_PASSWORD=tu_clave_admin
```

La clave `SUPABASE_SERVICE_ROLE_KEY` solo debe usarse en backend o panel interno. No debe exponerse en un frontend publico.

## Ejecutar el panel

Desde la carpeta `creditbot`:

```bash
streamlit run dashboard/app.py
```

Streamlit abrira el panel en una URL local, normalmente:

```text
http://localhost:8501
```

## Despliegue en Render

El panel se despliega como un **segundo Web Service** separado del backend del bot.

| Campo Render | Valor |
|---|---|
| **Name** | `creditbot-dashboard` |
| **Root Directory** | `creditbot` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `streamlit run dashboard/app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false` |
| **Health Check Path** | `/_stcore/health` |

Variables de entorno en Render:

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
ADMIN_DASHBOARD_PASSWORD=tu_clave_admin
```

Al abrir la URL de Render, ingresa la contraseña configurada en `ADMIN_DASHBOARD_PASSWORD`.

## Despliegue en Streamlit Community Cloud

Tambien puedes desplegar solo el dashboard en Streamlit Cloud.

En `https://share.streamlit.io`, usa estos valores:

| Campo | Valor |
|---|---|
| **Repository** | `MantaVIbers/CrediBot-Uleam` |
| **Branch** | `main` |
| **Main file path** | `creditbot/dashboard/app.py` |
| **App URL** | `credibot-dashboard` o el nombre disponible que prefieras |

En **Advanced settings**, pega los secretos en formato TOML:

```toml
SUPABASE_URL = "https://tu-proyecto.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "tu-service-role-key"
ADMIN_DASHBOARD_PASSWORD = "tu_clave_admin"
```

El archivo `dashboard/requirements.txt` contiene las dependencias minimas para que
Streamlit Cloud instale el panel desde esa subcarpeta.

## Flujo de prueba

1. Abre la URL local de Streamlit.
2. Ingresa la clave configurada en `ADMIN_DASHBOARD_PASSWORD`.
3. Revisa la pagina principal con metricas generales.
4. Abre `Solicitudes` y prueba los filtros por resultado y derivacion.
5. Descarga el CSV desde la pagina de solicitudes.
6. Abre `Casos Derivados` y selecciona un caso para revisar motivo, resumen y transcript.
7. Usa `Cerrar caso` cuando el asesor haya atendido la derivación.
8. Abre `Usuarios` y prueba la busqueda por nombre o telefono.

## Problemas comunes

| Problema | Causa probable | Solucion |
|---|---|---|
| El panel pide configurar `ADMIN_DASHBOARD_PASSWORD` | Falta la variable en `.env` | Agrega la variable y reinicia Streamlit |
| No se pudo consultar Supabase | URL o Service Role Key incorrectas | Revisa `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` |
| Las tablas aparecen vacias | Aun no hay datos registrados | Simula conversaciones o revisa el esquema en Supabase |
| Streamlit no inicia | Faltan dependencias | Ejecuta `pip install -r requirements.txt` |
