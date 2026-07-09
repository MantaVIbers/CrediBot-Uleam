# CrediBot — Desarrollo del Panel Administrativo con Streamlit

## 1. Objetivo del documento

Este documento especifica el desarrollo del **panel administrativo de CrediBot** utilizando **Streamlit** como framework complementario al backend principal desarrollado con **FastAPI** y la base de datos en **Supabase/PostgreSQL**.

El objetivo del panel es permitir que un asesor o administrador visualice, revise y gestione la información generada por el bot conversacional de WhatsApp, sin necesidad de construir un frontend complejo desde cero.

---

## 2. Rol de Streamlit dentro de CrediBot

Streamlit no reemplaza a FastAPI. En este proyecto, **FastAPI seguirá siendo el backend principal**, encargado de recibir mensajes, procesar el flujo conversacional, ejecutar reglas de negocio y conectarse con Supabase.

Streamlit se utilizará como un **panel administrativo interno** para visualizar información registrada por el sistema.

### Distribución de responsabilidades

| Componente | Responsabilidad |
|---|---|
| FastAPI | Recibir webhooks de WhatsApp, procesar mensajes, manejar estados y reglas de negocio |
| Supabase | Guardar usuarios, conversaciones, solicitudes y resultados |
| Streamlit | Mostrar un dashboard administrativo para consultar datos y revisar casos |
| WhatsApp Cloud API / Sandbox | Canal de comunicación entre el cliente y CrediBot |

---

## 3. Justificación del uso de Streamlit

Se selecciona Streamlit porque permite crear interfaces visuales en Python de forma rápida, ideal para un MVP académico o funcional.

Streamlit permite:

- Crear dashboards sin desarrollar frontend con React o Angular.
- Visualizar datos directamente desde Supabase.
- Filtrar solicitudes por estado o resultado.
- Mostrar métricas del sistema.
- Revisar casos derivados a asesor humano.
- Probar rápidamente el comportamiento del MVP.
- Mantener todo el desarrollo principal en Python.

Para CrediBot, Streamlit sirve como una solución práctica para demostrar el funcionamiento del sistema y facilitar la revisión de solicitudes.

---

## 4. Arquitectura general con Streamlit

```text
Cliente por WhatsApp
        ↓
WhatsApp Cloud API / Sandbox
        ↓
Webhook FastAPI
        ↓
Motor conversacional de CrediBot
        ↓
Reglas de precalificación
        ↓
Supabase/PostgreSQL
        ↓
Panel administrativo Streamlit
```

FastAPI escribe los datos en Supabase y Streamlit consulta esos datos para mostrarlos en pantalla.

---

## 5. Alcance del panel administrativo

El panel administrativo en Streamlit permitirá:

1. Visualizar resumen general del sistema.
2. Consultar usuarios registrados.
3. Consultar solicitudes de crédito.
4. Filtrar solicitudes por resultado.
5. Ver casos derivados a asesor humano.
6. Revisar detalle de cada solicitud.
7. Mostrar métricas básicas.
8. Exportar información a CSV.
9. Visualizar el historial básico de conversaciones.
10. Validar que el flujo del bot esté registrando información correctamente.

---

## 6. Funcionalidades principales del panel

## 6.1. Dashboard general

La primera pantalla mostrará indicadores principales del sistema:

| Indicador | Descripción |
|---|---|
| Total de usuarios | Cantidad de usuarios que han interactuado con CrediBot |
| Total de solicitudes | Número total de solicitudes de crédito registradas |
| Solicitudes preaprobadas | Casos que cumplen las reglas básicas |
| Solicitudes observadas | Casos que requieren revisión |
| Solicitudes no aprobadas | Casos que no cumplen condiciones |
| Casos derivados | Solicitudes enviadas a asesor humano |

Ejemplo visual esperado:

```text
Dashboard CrediBot

Usuarios registrados: 35
Solicitudes totales: 28
Preaprobadas: 12
Observadas: 9
No cumplen: 7
Derivadas a asesor: 8
```

---

## 6.2. Vista de solicitudes

Esta sección permitirá revisar las solicitudes de crédito registradas.

Campos sugeridos:

| Campo | Descripción |
|---|---|
| ID | Identificador de la solicitud |
| Cliente | Nombre del usuario |
| Teléfono | Número de WhatsApp |
| Monto | Monto solicitado |
| Plazo | Plazo solicitado |
| Ingreso mensual | Ingreso declarado |
| Cuota estimada | Cálculo generado por el sistema |
| Resultado | Preaprobado, observado o no cumple |
| Derivado | Sí/No |
| Fecha | Fecha de creación |

---

## 6.3. Filtros de búsqueda

El panel debe permitir filtrar la información por:

- Resultado de evaluación.
- Estado de derivación.
- Rango de fechas.
- Nombre del cliente.
- Número de teléfono.

Filtros mínimos para el MVP:

```text
Resultado:
- Todos
- Preaprobado
- Observado
- No cumple

Derivación:
- Todos
- Derivados
- No derivados
```

---

## 6.4. Vista de casos derivados

Esta vista estará enfocada en los casos que requieren intervención humana.

Debe mostrar únicamente solicitudes marcadas como derivadas.

Campos importantes:

| Campo | Descripción |
|---|---|
| Cliente | Nombre del cliente |
| Teléfono | Número de WhatsApp |
| Resultado | Resultado de la evaluación |
| Motivo | Razón de la derivación |
| Fecha | Fecha del caso |
| Estado de atención | Pendiente, en revisión o finalizado |

Para el MVP se puede manejar el estado de atención de forma básica.

---

## 6.5. Detalle de solicitud

Cuando el asesor seleccione una solicitud, el panel debe mostrar información detallada:

```text
Nombre: Carlos Ortiz
Teléfono: 0999999999
Monto solicitado: $500
Plazo: 12 meses
Ingreso mensual: $700
Cuota estimada: $41.67
Capacidad de pago: $210.00
Resultado: Preaprobado
Derivado a asesor: No
Fecha: 2026-07-08
```

También puede incluir un resumen del historial conversacional.

---

## 6.6. Exportación de datos

El panel permitirá descargar la información en formato CSV.

Esto puede servir para:

- Presentar evidencia del funcionamiento del MVP.
- Revisar solicitudes fuera del sistema.
- Generar reportes académicos.
- Analizar resultados del flujo conversacional.

---

## 7. Estructura recomendada del proyecto

La estructura del proyecto puede quedar de la siguiente manera:

```text
creditbot/
│
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── webhook.py
│   │   ├── solicitudes.py
│   │   └── usuarios.py
│   ├── services/
│   │   ├── conversation_service.py
│   │   ├── credit_service.py
│   │   └── whatsapp_service.py
│   ├── models/
│   ├── database/
│   │   └── supabase_client.py
│   └── utils/
│
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── 1_Dashboard.py
│   │   ├── 2_Solicitudes.py
│   │   ├── 3_Casos_Derivados.py
│   │   └── 4_Usuarios.py
│   ├── services/
│   │   └── supabase_dashboard.py
│   └── components/
│       └── filters.py
│
├── docs/
│   ├── flujo_conversacional.md
│   ├── reglas_negocio.md
│   └── streamlit_panel.md
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 8. Dependencias necesarias

En el archivo `requirements.txt` se pueden incluir las siguientes dependencias:

```txt
fastapi
uvicorn
python-dotenv
supabase
pydantic
streamlit
pandas
pytest
requests
```

Si se desea agregar gráficos:

```txt
plotly
```

Para el MVP, se puede trabajar con Streamlit y Pandas sin necesidad de usar librerías visuales avanzadas.

---

## 9. Variables de entorno para Streamlit

Streamlit debe conectarse a Supabase usando variables de entorno.

Archivo `.env`:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxxx
ADMIN_DASHBOARD_PASSWORD=clave_admin
```

Importante:

```text
El archivo .env no debe subirse a GitHub.
La clave service_role solo debe usarse en backend o panel interno.
Nunca debe exponerse públicamente.
```

---

## 10. Seguridad del panel Streamlit

Como el panel mostrará información de clientes, no debe quedar abierto públicamente sin protección.

Medidas mínimas:

1. Proteger el acceso con contraseña.
2. No mostrar tokens ni claves.
3. No imprimir datos sensibles en consola.
4. Usar HTTPS si se despliega.
5. Limitar el panel a uso administrativo.
6. No permitir edición peligrosa de datos en el MVP.
7. Usar variables de entorno.
8. No subir `.env` al repositorio.

Ejemplo de protección básica:

```python
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def login():
    st.title("Acceso administrativo")
    password = st.text_input("Contraseña", type="password")

    if st.button("Ingresar"):
        if password == os.getenv("ADMIN_DASHBOARD_PASSWORD"):
            st.session_state["auth"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta")

if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    login()
    st.stop()
```

---

## 11. Conexión de Streamlit con Supabase

Archivo sugerido:

```text
dashboard/services/supabase_dashboard.py
```

Código base:

```python
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_usuarios():
    response = supabase.table("usuarios").select("*").execute()
    return response.data

def obtener_solicitudes():
    response = supabase.table("solicitudes_credito").select("*").execute()
    return response.data

def obtener_casos_derivados():
    response = (
        supabase
        .table("solicitudes_credito")
        .select("*")
        .eq("derivado_asesor", True)
        .execute()
    )
    return response.data
```

---

## 12. Ejemplo de pantalla principal en Streamlit

Archivo:

```text
dashboard/app.py
```

Código base:

```python
import streamlit as st
import pandas as pd
from services.supabase_dashboard import obtener_solicitudes, obtener_usuarios

st.set_page_config(
    page_title="CrediBot Dashboard",
    page_icon="💬",
    layout="wide"
)

st.title("Panel Administrativo CrediBot")

usuarios = obtener_usuarios()
solicitudes = obtener_solicitudes()

df_usuarios = pd.DataFrame(usuarios)
df_solicitudes = pd.DataFrame(solicitudes)

total_usuarios = len(df_usuarios)
total_solicitudes = len(df_solicitudes)

preaprobadas = len(df_solicitudes[df_solicitudes["resultado"] == "preaprobado"])
observadas = len(df_solicitudes[df_solicitudes["resultado"] == "observado"])
no_cumplen = len(df_solicitudes[df_solicitudes["resultado"] == "no_cumple"])
derivadas = len(df_solicitudes[df_solicitudes["derivado_asesor"] == True])

col1, col2, col3 = st.columns(3)
col1.metric("Usuarios registrados", total_usuarios)
col2.metric("Solicitudes totales", total_solicitudes)
col3.metric("Casos derivados", derivadas)

col4, col5, col6 = st.columns(3)
col4.metric("Preaprobadas", preaprobadas)
col5.metric("Observadas", observadas)
col6.metric("No cumplen", no_cumplen)

st.subheader("Solicitudes recientes")
st.dataframe(df_solicitudes, use_container_width=True)
```

---

## 13. Ejemplo de página de solicitudes

Archivo:

```text
dashboard/pages/2_Solicitudes.py
```

Código base:

```python
import streamlit as st
import pandas as pd
from services.supabase_dashboard import obtener_solicitudes

st.title("Solicitudes de crédito")

solicitudes = obtener_solicitudes()
df = pd.DataFrame(solicitudes)

if df.empty:
    st.info("No existen solicitudes registradas.")
    st.stop()

resultado = st.selectbox(
    "Filtrar por resultado",
    ["Todos", "preaprobado", "observado", "no_cumple"]
)

if resultado != "Todos":
    df = df[df["resultado"] == resultado]

derivacion = st.selectbox(
    "Filtrar por derivación",
    ["Todos", "Derivados", "No derivados"]
)

if derivacion == "Derivados":
    df = df[df["derivado_asesor"] == True]
elif derivacion == "No derivados":
    df = df[df["derivado_asesor"] == False]

st.dataframe(df, use_container_width=True)

csv = df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Descargar CSV",
    data=csv,
    file_name="solicitudes_creditbot.csv",
    mime="text/csv"
)
```

---

## 14. Ejemplo de página de casos derivados

Archivo:

```text
dashboard/pages/3_Casos_Derivados.py
```

Código base:

```python
import streamlit as st
import pandas as pd
from services.supabase_dashboard import obtener_casos_derivados

st.title("Casos derivados a asesor")

casos = obtener_casos_derivados()
df = pd.DataFrame(casos)

if df.empty:
    st.success("No existen casos derivados pendientes.")
    st.stop()

st.dataframe(df, use_container_width=True)

st.subheader("Detalle de caso")

ids = df["id_solicitud"].tolist()
seleccion = st.selectbox("Seleccionar solicitud", ids)

caso = df[df["id_solicitud"] == seleccion].iloc[0]

st.write(f"**Cliente:** {caso.get('nombre', 'No registrado')}")
st.write(f"**Teléfono:** {caso.get('telefono', 'No registrado')}")
st.write(f"**Monto solicitado:** ${caso.get('monto', 0)}")
st.write(f"**Plazo:** {caso.get('plazo', 0)} meses")
st.write(f"**Ingreso mensual:** ${caso.get('ingreso_mensual', 0)}")
st.write(f"**Resultado:** {caso.get('resultado', 'No registrado')}")
```

---

## 15. Tareas de desarrollo para Streamlit

## Tarea 01: Crear módulo del dashboard

### Descripción

Crear una carpeta independiente para el panel administrativo dentro del proyecto.

### Actividades

```text
1. Crear carpeta dashboard.
2. Crear archivo app.py.
3. Crear carpeta pages.
4. Crear carpeta services.
5. Crear carpeta components.
6. Verificar que Streamlit pueda ejecutarse.
```

### Criterios de aceptación

```text
- Existe la carpeta dashboard.
- Existe el archivo app.py.
- Streamlit se ejecuta correctamente.
- El dashboard muestra una pantalla inicial.
```

### Commit sugerido

```bash
git commit -m "feat: create streamlit dashboard module"
```

---

## Tarea 02: Configurar conexión de Streamlit con Supabase

### Descripción

Conectar el panel administrativo con Supabase para consultar usuarios y solicitudes.

### Actividades

```text
1. Instalar supabase y python-dotenv.
2. Crear archivo services/supabase_dashboard.py.
3. Cargar variables de entorno.
4. Crear cliente de Supabase.
5. Crear función para obtener usuarios.
6. Crear función para obtener solicitudes.
7. Probar consulta desde Streamlit.
```

### Criterios de aceptación

```text
- Streamlit se conecta correctamente a Supabase.
- Se pueden consultar usuarios.
- Se pueden consultar solicitudes de crédito.
- No existen claves escritas directamente en el código.
```

### Commit sugerido

```bash
git commit -m "feat: connect streamlit dashboard to supabase"
```

---

## Tarea 03: Crear pantalla de dashboard general

### Descripción

Crear la pantalla principal con indicadores generales del sistema.

### Actividades

```text
1. Consultar usuarios y solicitudes.
2. Convertir datos a DataFrame.
3. Calcular total de usuarios.
4. Calcular total de solicitudes.
5. Calcular preaprobadas, observadas y no aprobadas.
6. Calcular casos derivados.
7. Mostrar métricas con st.metric.
8. Mostrar tabla de solicitudes recientes.
```

### Criterios de aceptación

```text
- El panel muestra métricas generales.
- Las métricas corresponden a datos reales de Supabase.
- El panel muestra solicitudes recientes.
- La interfaz es entendible para el asesor.
```

### Commit sugerido

```bash
git commit -m "feat: add dashboard metrics view"
```

---

## Tarea 04: Crear pantalla de solicitudes

### Descripción

Crear una página para consultar y filtrar solicitudes de crédito.

### Actividades

```text
1. Crear archivo pages/2_Solicitudes.py.
2. Consultar solicitudes desde Supabase.
3. Mostrar tabla completa.
4. Agregar filtro por resultado.
5. Agregar filtro por derivación.
6. Agregar botón para descargar CSV.
```

### Criterios de aceptación

```text
- El asesor puede ver todas las solicitudes.
- El asesor puede filtrar por resultado.
- El asesor puede filtrar por derivación.
- El asesor puede descargar los datos en CSV.
```

### Commit sugerido

```bash
git commit -m "feat: add credit requests dashboard page"
```

---

## Tarea 05: Crear pantalla de casos derivados

### Descripción

Crear una página dedicada a los casos que necesitan atención humana.

### Actividades

```text
1. Crear archivo pages/3_Casos_Derivados.py.
2. Consultar solicitudes con derivado_asesor = true.
3. Mostrar tabla de casos derivados.
4. Permitir seleccionar un caso.
5. Mostrar detalle del caso seleccionado.
```

### Criterios de aceptación

```text
- La página muestra únicamente casos derivados.
- El asesor puede seleccionar una solicitud.
- El panel muestra los datos principales del caso.
- El panel ayuda a continuar la atención humana.
```

### Commit sugerido

```bash
git commit -m "feat: add human handoff cases page"
```

---

## Tarea 06: Crear pantalla de usuarios

### Descripción

Crear una página para visualizar los usuarios que han interactuado con CrediBot.

### Actividades

```text
1. Crear archivo pages/4_Usuarios.py.
2. Consultar usuarios desde Supabase.
3. Mostrar nombre, teléfono y fecha de registro.
4. Agregar búsqueda por nombre o teléfono.
```

### Criterios de aceptación

```text
- El asesor puede ver usuarios registrados.
- El asesor puede buscar por nombre.
- El asesor puede buscar por número de teléfono.
```

### Commit sugerido

```bash
git commit -m "feat: add users dashboard page"
```

---

## Tarea 07: Implementar seguridad básica del panel

### Descripción

Proteger el acceso al dashboard administrativo con una contraseña básica para el MVP.

### Actividades

```text
1. Crear variable ADMIN_DASHBOARD_PASSWORD en .env.
2. Crear pantalla de login.
3. Guardar autenticación en st.session_state.
4. Evitar acceso al dashboard sin contraseña.
5. Mostrar error si la contraseña es incorrecta.
```

### Criterios de aceptación

```text
- El panel solicita contraseña al iniciar.
- El usuario no puede ver datos sin autenticarse.
- La contraseña no está escrita directamente en el código.
```

### Commit sugerido

```bash
git commit -m "feat: protect streamlit dashboard with password"
```

---

## Tarea 08: Preparar ejecución local del panel

### Descripción

Documentar y probar cómo ejecutar el dashboard localmente.

### Actividades

```text
1. Instalar dependencias.
2. Configurar .env.
3. Ejecutar Streamlit.
4. Verificar conexión a Supabase.
5. Probar filtros y vistas.
```

### Comando de ejecución

```bash
streamlit run dashboard/app.py
```

### Criterios de aceptación

```text
- El panel se levanta correctamente.
- El panel conecta con Supabase.
- El asesor puede navegar entre páginas.
```

### Commit sugerido

```bash
git commit -m "docs: add streamlit dashboard run instructions"
```

---

## 16. Flujo de uso del asesor

```text
1. El asesor ingresa al panel Streamlit.
2. El sistema solicita contraseña.
3. El asesor accede al dashboard.
4. Revisa métricas generales.
5. Consulta solicitudes de crédito.
6. Filtra casos observados o no aprobados.
7. Ingresa a la sección de casos derivados.
8. Selecciona una solicitud.
9. Revisa los datos del cliente.
10. Continúa la atención humana fuera del sistema o registra seguimiento en una futura versión.
```

---

## 17. Reglas para el MVP

Para mantener el alcance controlado, en la primera versión Streamlit solo debe:

```text
- Leer datos desde Supabase.
- Mostrar métricas.
- Mostrar tablas.
- Filtrar información.
- Descargar CSV.
- Proteger acceso con contraseña básica.
```

No se recomienda en el MVP:

```text
- Editar solicitudes directamente.
- Eliminar registros.
- Manejar roles complejos.
- Enviar mensajes de WhatsApp desde Streamlit.
- Administrar usuarios avanzados.
```

Estas funciones pueden dejarse como mejoras futuras.

---

## 18. Mejoras futuras

Después del MVP, se pueden agregar:

1. Login con Supabase Auth.
2. Roles de usuario: administrador y asesor.
3. Cambio de estado de atención.
4. Registro de observaciones del asesor.
5. Envío de mensajes al cliente desde el panel.
6. Gráficos avanzados.
7. Reportes PDF.
8. Auditoría de acciones.
9. Integración con CRM.
10. Notificaciones internas.

---

## 19. Definición final para el documento principal

Se puede agregar al documento general de CrediBot la siguiente descripción:

```text
Además del backend desarrollado con FastAPI, se implementará un panel administrativo con Streamlit. Este panel permitirá visualizar los usuarios registrados, solicitudes de crédito, resultados de precalificación y casos derivados a asesor humano. Streamlit será utilizado como framework complementario para construir una interfaz rápida en Python, adecuada para la demostración y gestión básica del MVP.
```

---

## 20. Conclusión

Streamlit será utilizado en CrediBot como un framework complementario orientado al panel administrativo del MVP. Su función será facilitar la visualización de datos, el seguimiento de solicitudes y la revisión de casos derivados, manteniendo el desarrollo en Python y evitando la construcción de un frontend complejo.

Con esta integración, el proyecto queda organizado de la siguiente manera:

```text
FastAPI = backend principal y lógica del sistema
Supabase = almacenamiento y seguridad de datos
Streamlit = panel administrativo para visualización y revisión
WhatsApp = canal conversacional del cliente
```

Esta arquitectura permite presentar un MVP funcional, claro y escalable para el desarrollo de CrediBot.
