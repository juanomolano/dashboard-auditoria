import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa sobria
COLOR_PRIMARY = "#1E3A8A"     # Azul marino profundo
COLOR_SECONDARY = "#2563EB"    # Azul corporativo
COLOR_ACCENT = "#D97706"       # Ámbar/Naranja sobrio para alertas
COLOR_NEUTRAL_DARK = "#1F2937" # Gris oscuro
COLOR_BG_CARD = "#F9FAFB"      # Fondo claro para tarjetas

@st.cache_data(ttl=60)
def load_data_documentos():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNB6Y3yTcF0o7QFhFoLMOULPZXcVl84MahhUPvHcWyxDjEgQbWKeGTqqi0Y5WymQ/pub?gid=646635232&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas especificando día primero (DD/MM/YYYY)
        if "FECHAFACTURA" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHAFACTURA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "CODALMACEN" in df.columns:
            df["CODALMACEN"] = df["CODALMACEN"].astype(str)
            
        if "IDENTIFICACION" in df.columns:
            df["IDENTIFICACION"] = df["IDENTIFICACION"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_03():
    # 🎨 ESTILOS CSS PARA EVITAR TEXTOS CORTADOS Y PROPORCIONAR METRICAS
    st.markdown(
        """
        <style>
            h1 {
                font-size: 1.8rem !important;
                padding-bottom: 0px !important;
                margin-bottom: 10px !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.8rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                text-overflow: clip !important;
                line-height: 1.2 !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.05rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
            }
            div[data-testid="stMetric"] {
                background-color: #F8FAFC;
                padding: 10px 12px;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
                min-height: 90px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🪪 Control Creación Tipo de Documento")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Auditar la calidad e integridad de la base de datos de clientes.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    df = load_data_documentos()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    st.subheader("🔍 Filtros de Auditoría")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        regional_disponibles = sorted(df["REGIONAL"].dropna().unique().tolist()) if "REGIONAL" in df.columns else []
        selected_regional = st.multiselect("Filtrar por Regional", options=regional_disponibles)
    with col_f2:
        almacenes_disponibles = sorted(df["ALMACEN"].dropna().unique().tolist()) if "ALMACEN" in df.columns else []
        selected_almacen = st.multiselect("Filtrar por Almacén", options=almacenes_disponibles)
    with col_f3:
        if "AÑO_MES" in df.columns:
            meses_disponibles = sorted(df["AÑO_MES"].dropna().unique().astype(str).tolist())
            selected_meses = st.multiselect("Filtrar por Meses", options=meses_disponibles)
        else:
            selected_meses = []

    df_filtered = df.copy()
    if selected_regional: df_filtered = df_filtered[df_filtered["REGIONAL"].isin(selected_regional)]
    if selected_almacen: df_filtered = df_filtered[df_filtered["ALMACEN"].isin(selected_almacen)]
    if selected_meses: df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    st.markdown("---")
    
    # KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Facturas Auditadas", f"{len(df_filtered):,}")
    kpi2.metric("Tipo Doc. Principal", str(df_filtered["DOCUMENTO"].mode()[0] if not df_filtered.empty else "N/A"))
    kpi3.metric("Regional Crítica", str(df_filtered["REGIONAL"].mode()[0] if not df_filtered.empty else "N/A"))
    kpi4.metric("Almacén Reincidente", str(df_filtered["ALMACEN"].mode()[0] if not df_filtered.empty else "N/A"))

    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    
    df_tabla = df_filtered.copy()
    
    # CORRECCIÓN: Ordenamos por FECHA_DT (la fecha real) en lugar de FECHAFACTURA
    if "FECHA_DT" in df_tabla.columns:
        df_tabla = df_tabla.sort_values(by="FECHA_DT", ascending=False)
        
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHAFACTURA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "ALMACEN", "FECHAFACTURA", "Factura", "DOCUMENTO", "IDENTIFICACION", "NOMVENDEDOR"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display],
        use_container_width=True,
        hide_index=True
    )
