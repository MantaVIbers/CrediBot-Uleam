"""Página del dashboard para listar y buscar usuarios."""
import pandas as pd
import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from services.supabase_dashboard import DashboardConfigError, obtener_usuarios
from styles import apply_dashboard_styles


st.set_page_config(
    page_title="Usuarios - CrediBot",
    page_icon="CB",
    layout="wide",
)

apply_dashboard_styles()
require_auth()
render_sidebar()

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-eyebrow">Base de clientes</div>
      <div class="cb-hero-title">Usuarios</div>
      <p class="cb-hero-subtitle">
        Directorio de clientes que han interactuado con CrediBot.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

st.markdown('<div class="cb-section-title">Búsqueda</div>', unsafe_allow_html=True)
search = st.text_input("Buscar por nombre o telefono").strip().lower()

filtered_df = df.copy()
if search:
    full_name = filtered_df.get("full_name", pd.Series("", index=filtered_df.index))
    phone = filtered_df.get("phone", pd.Series("", index=filtered_df.index))
    mask = full_name.fillna("").str.lower().str.contains(search, na=False)
    mask = mask | phone.fillna("").astype(str).str.lower().str.contains(search, na=False)
    filtered_df = filtered_df[mask]

metric_cols = st.columns(3)
metric_cols[0].metric("Usuarios mostrados", len(filtered_df))
metric_cols[1].metric(
    "Con cédula",
    int(filtered_df["cedula"].notna().sum()) if "cedula" in filtered_df else 0,
)
metric_cols[2].metric(
    "Con consentimiento",
    int(filtered_df["consent_given"].fillna(False).sum())
    if "consent_given" in filtered_df
    else 0,
)

preferred_columns = [
    "id",
    "full_name",
    "phone",
    "created_at",
    "updated_at",
]
visible_columns = [column for column in preferred_columns if column in filtered_df.columns]
extra_columns = [column for column in filtered_df.columns if column not in visible_columns]
display_df = filtered_df[visible_columns + extra_columns]

st.markdown('<div class="cb-section-title">Directorio</div>', unsafe_allow_html=True)
st.dataframe(display_df, width="stretch", hide_index=True)
