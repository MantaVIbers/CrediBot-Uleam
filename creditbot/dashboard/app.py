"""Página principal del panel de administración de CrediBot."""
from html import escape

import pandas as pd
import streamlit as st

from components.auth import require_auth
from components.navigation import render_sidebar
from services.supabase_dashboard import (
    DashboardConfigError,
    obtener_casos_derivados,
    obtener_solicitudes,
    obtener_usuarios,
)
from styles import apply_dashboard_styles


st.set_page_config(
    page_title="CrediBot Dashboard",
    page_icon="CB",
    layout="wide",
)

apply_dashboard_styles()
require_auth()
render_sidebar()

st.markdown(
    """
    <div class="cb-hero">
      <div class="cb-eyebrow">Centro de operaciones</div>
      <div class="cb-hero-title">Panel Administrativo CrediBot</div>
      <p class="cb-hero-subtitle">
        Operación diaria de solicitudes, usuarios y casos derivados a atención humana.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

quick_left, quick_right = st.columns([1, 4])
with quick_left:
    st.page_link(
        "pages/1_Simulador.py",
        label="Probar conversación",
        icon="💬",
        width="stretch",
    )
with quick_right:
    st.caption(
        "Simula el flujo completo con el backend real sin consumir mensajes de WhatsApp."
    )

try:
    usuarios = obtener_usuarios()
    solicitudes = obtener_solicitudes()
    casos_derivados = obtener_casos_derivados()
except DashboardConfigError as exc:
    st.warning(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"No se pudo consultar Supabase: {exc}")
    st.stop()

df_usuarios = pd.DataFrame(usuarios)
df_solicitudes = pd.DataFrame(solicitudes)
df_casos_derivados = pd.DataFrame(casos_derivados)

total_usuarios = len(df_usuarios)
total_solicitudes = len(df_solicitudes)
total_casos_derivados = len(df_casos_derivados)
casos_pendientes = (
    int((df_casos_derivados["status"] == "pending").sum())
    if not df_casos_derivados.empty and "status" in df_casos_derivados
    else 0
)
casos_asignados = (
    int((df_casos_derivados["status"] == "assigned").sum())
    if not df_casos_derivados.empty and "status" in df_casos_derivados
    else 0
)

if df_solicitudes.empty or "result" not in df_solicitudes:
    preaprobadas = 0
    observadas = 0
    no_cumplen = 0
else:
    preaprobadas = int((df_solicitudes["result"] == "preaprobado").sum())
    observadas = int((df_solicitudes["result"] == "observado").sum())
    no_cumplen = int((df_solicitudes["result"] == "no_cumple").sum())

metric_cols = st.columns(4)
metric_cols[0].metric("Usuarios", total_usuarios)
metric_cols[1].metric("Solicitudes", total_solicitudes)
metric_cols[2].metric("Casos abiertos", total_casos_derivados)
metric_cols[3].metric("Pendientes", casos_pendientes)

status_cols = st.columns(4)
status_cols[0].metric("Preaprobadas", preaprobadas)
status_cols[1].metric("Observadas", observadas)
status_cols[2].metric("No cumplen", no_cumplen)
status_cols[3].metric("En atención", casos_asignados)

left, right = st.columns([1.25, 0.75], gap="large")

with left:
    st.markdown('<div class="cb-section-title">Solicitudes recientes</div>', unsafe_allow_html=True)

    if df_solicitudes.empty:
        st.info("No existen solicitudes registradas.")
    else:
        recent_columns = [
            column
            for column in [
                "created_at",
                "cedula",
                "requested_amount",
                "term_months",
                "monthly_income",
                "result",
                "status",
            ]
            if column in df_solicitudes.columns
        ]
        display_df = df_solicitudes[recent_columns].head(12).copy()
        rename_map = {
            "created_at": "Fecha",
            "cedula": "Cédula",
            "requested_amount": "Monto",
            "term_months": "Plazo",
            "monthly_income": "Ingreso",
            "result": "Resultado",
            "status": "Estado",
        }
        display_df = display_df.rename(columns=rename_map)
        st.dataframe(display_df, width="stretch", hide_index=True)

with right:
    st.markdown('<div class="cb-section-title">Atención humana</div>', unsafe_allow_html=True)

    if df_casos_derivados.empty:
        st.info("No hay casos derivados abiertos.")
    else:
        for _, case in df_casos_derivados.head(6).iterrows():
            reason = escape(str(case.get("reason") or "Sin motivo"))
            status = escape(str(case.get("status") or "pending"))
            created_at = escape(str(case.get("created_at") or ""))
            pill_class = "cb-pill-yellow" if status == "pending" else "cb-pill-green"
            st.markdown(
                f"""
                <div class="cb-contact">
                  <div class="cb-contact-name">Caso {escape(str(case.get("id") or ""))[:8]}</div>
                  <div class="cb-contact-meta">{reason}</div>
                  <div style="margin-top:8px;">
                    <span class="cb-pill {pill_class}">{status}</span>
                  </div>
                  <div class="cb-contact-meta" style="margin-top:6px;">{created_at}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown('<div class="cb-section-title">Distribución de resultados</div>', unsafe_allow_html=True)
summary = pd.DataFrame(
    [
        {"Resultado": "preaprobado", "Total": preaprobadas},
        {"Resultado": "observado", "Total": observadas},
        {"Resultado": "no_cumple", "Total": no_cumplen},
    ]
)
st.bar_chart(summary, x="Resultado", y="Total", width="stretch")
