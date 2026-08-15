import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa
COLOR_PRIMARY = "#1E3A8A"
COLOR_SECONDARY = "#2563EB"
COLOR_ACCENT = "#D97706"
COLOR_NEUTRAL_DARK = "#1F2937"
COLOR_BG_CARD = "#F9FAFB"

@st.cache_data(ttl=60)
def load_data_documentos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNB6Y3yTcF0o7QFhFoLMOULPZXcVl84MahhUPvHcWyxDjEgQbWKeGTqqi0Y5WymQ/pub?gid=1260662215&single=true&output=csv"
    try:
        # Intentamos leer con separador estándar, asegurando UTF-8
        df = pd.read_csv(url, encoding="utf-8")
        
        # Limpieza profunda de los nombres de columnas (quita espacios invisibles y mayúsculas/minúsculas raras)
        df.columns = df.columns.astype(str).str.strip()
        
        # Procesamiento de fechas exacto según tu imagen ("FECHAFACTURA")
        if "FECHAFACTURA" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHAFACTURA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M").astype(str)
            
        # Limpieza de IDs por si tienen decimales molestos
        for col in ["CODALMACEN", "IDENTIFICACION"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(".0", "", regex=False)
                
        return df
    except Exception as e:
        st.error(f"⚠️ Error al cargar datos: {e}")
        return pd.DataFrame()

def render_informe_03():
    st.title("🪪 Control Creación Tipo de Documento")
    df = load_data_documentos()
    
    if df.empty:
        st.warning("No se encontraron registros en el archivo.")
        return

    # Filtros Dinámicos
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        reg = st.multiselect("Filtrar por Regional", options=df["REGIONAL"].unique() if "REGIONAL" in df.columns else [])
    with col_f2:
        alm = st.multiselect("Filtrar por Almacén", options=df["ALMACEN"].unique() if "ALMACEN" in df.columns else [])
    with col_f3:
        mes = st.multiselect("Filtrar por Mes", options=df["AÑO_MES"].unique() if "AÑO_MES" in df.columns else [])

    # Aplicar Filtros
    dff = df.copy()
    if reg: dff = dff[dff["REGIONAL"].isin(reg)]
    if alm: dff = dff[dff["ALMACEN"].isin(alm)]
    if mes: dff = dff[dff["AÑO_MES"].isin(mes)]

    # KPIs
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Registros", f"{len(dff):,}")
    kpi2.metric("Tipo Doc. Principal", dff["DOCUMENTO"].mode()[0] if not dff.empty and "DOCUMENTO" in dff.columns else "N/A")
    kpi3.metric("Regional Crítica", dff["REGIONAL"].mode()[0] if not dff.empty and "REGIONAL" in dff.columns else "N/A")
    kpi4.metric("Almacén Crítico", dff["ALMACEN"].mode()[0] if not dff.empty and "ALMACEN" in dff.columns else "N/A")

    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE (Blindada contra el KeyError)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    
    df_tabla = dff.copy()
    
    # Definimos exactamente las columnas que se ven en tu imagen
    cols_posibles = ["REGIONAL", "CODALMACEN", "ALMACEN", "FECHAFACTURA", "Factura", "IDENTIFICACION", "DOCUMENTO", "NOMVENDEDOR"]
    cols_display = [col for col in cols_posibles if col in df_tabla.columns]
    
    # Ordenamiento seguro usando FECHA_DT (la fecha real en formato fecha)
    if "FECHA_DT" in df_tabla.columns:
        df_tabla = df_tabla.sort_values(by="FECHA_DT", ascending=False)
    
    st.dataframe(
        df_tabla[cols_display],
        use_container_width=True,
        hide_index=True
    )
