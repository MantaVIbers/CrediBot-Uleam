"""Página del dashboard para listar y buscar usuarios."""
import pandas as pd
import streamlit as st

from components.auth import require_auth
from services.supabase_dashboard import DashboardConfigError, obtener_usuarios


st.set_page_config(
    page_title="Usuarios - CrediBot",
    page_icon="CB",
    layout="wide",
)

require_auth()

st.title("Usuarios")

try:
    usuarios = obtener_usuarios()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

df = pd.DataFrame(usuarios)

if df.empty:
    st.info("No existen usuarios registrados.")
    st.stop()

search = st.text_input("Buscar por nombre o telefono").strip().lower()

filtered_df = df.copy()
if search:
    full_name = filtered_df.get("full_name", pd.Series("", index=filtered_df.index))
    phone = filtered_df.get("phone", pd.Series("", index=filtered_df.index))
    mask = full_name.fillna("").str.lower().str.contains(search, na=False)
    mask = mask | phone.fillna("").astype(str).str.lower().str.contains(search, na=False)
    filtered_df = filtered_df[mask]

st.metric("Usuarios mostrados", len(filtered_df))

preferred_columns = [
    "id",
    "full_name",
    "phone",
    "cedula",
    "consent_given",
    "consent_at",
    "created_at",
    "updated_at",
]
visible_columns = [column for column in preferred_columns if column in filtered_df.columns]
extra_columns = [column for column in filtered_df.columns if column not in visible_columns]
display_df = filtered_df[visible_columns + extra_columns]

st.dataframe(display_df, use_container_width=True, hide_index=True)
