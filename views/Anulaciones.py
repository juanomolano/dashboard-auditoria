import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa sobria
COLOR_PRIMARY = "#1E3A8A"      # Azul marino profundo
COLOR_SECONDARY = "#2563EB"    # Azul corporativo
COLOR_ACCENT = "#D97706"       # Ámbar/Naranja sobrio para alertas
COLOR_NEUTRAL_DARK = "#1F2937" # Gris oscuro
COLOR_BG_CARD = "#F9FAFB"      # Fondo claro para tarjetas

@st.cache_data(ttl=60)
def load_data_anulaciones():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV (Base Principal Anulaciones).
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQM4H5MpdtZYBem7pGKx3OszdwLBtFxcPE6c74dMqDRCj45RaZWDCMVW6N6M0VusA/pub?gid=1621055796&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas especificando día primero (DD/MM/YYYY)
        if "FECHA" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "CODALMACEN" in df.columns:
            df["CODALMACEN"] = df["CODALMACEN"].astype(str).str.strip().str.upper()
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_data_totales_nacionales_anulaciones():
    """
    Carga la nueva pestaña con los totales nacionales (MES, TOTAL_NACIONAL) para el cálculo de participación %.
    """
    url_totales = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQM4H5MpdtZYBem7pGKx3OszdwLBtFxcPE6c74dMqDRCj45RaZWDCMVW6N6M0VusA/pub?gid=1716693701&single=true&output=csv"
    try:
        df_totales = pd.read_csv(url_totales, encoding="utf-8")
        df_totales.columns = df_totales.columns.str.strip().str.upper()
        
        # Formatear la columna TOTAL_NACIONAL a numérico
        if "TOTAL_NACIONAL" in df_totales.columns:
            df_totales["TOTAL_NACIONAL"] = (
                df_totales["TOTAL_NACIONAL"]
                .astype(str)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.strip()
            )
            df_totales["TOTAL_NACIONAL"] = pd.to_numeric(df_totales["TOTAL_NACIONAL"], errors="coerce").fillna(0.0)
            
        if "MES" in df_totales.columns:
            df_totales["MES"] = df_totales["MES"].astype(str).str.strip()
            
        return df_totales
    except Exception as e:
        st.error(f"⚠️ No se pudo cargar el total nacional de anulaciones: {e}")
        return pd.DataFrame()


def render_informe_02():
    # 🎨 ESTILOS CSS
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

    # ---------------------------------------------------------
    # ENCABEZADO Y TEXTOS DE CONTEXTO
    # ---------------------------------------------------------
    st.title("💳 Control Anulaciones Forma de Pago")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Supervisar y auditar la totalidad de los cambios y anulaciones en las formas de pago registradas en las transacciones comerciales a nivel nacional, garantizando que todo ajuste cumpla con los protocolos de autorización, trazabilidad documental y soporte de caja requeridos.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> Se remitirá el informe detallado a la gestión regional y administradores de tienda para la verificación inmediata de soportes físicos y digitales. De identificar inconsistencias, omisiones injustificadas o faltantes en el flujo de dinero, se solicitará el descargue formal del responsable y la aplicación del cobro o reajuste financiero según la norma disciplinaria y de control interno.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos principales y totales nacionales
    df = load_data_anulaciones()
    df_totales_nacionales = load_data_totales_nacionales_anulaciones()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    # ---------------------------------------------------------
    # FILTROS INTERACTIVOS LIMPIOS
    # ---------------------------------------------------------
    st.subheader("🔍 Filtros de Auditoría")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        regional_disponibles = sorted(df["REGIONAL"].dropna().unique().tolist()) if "REGIONAL" in df.columns else []
        selected_regional = st.multiselect("Filtrar por Regional", options=regional_disponibles, placeholder="Todas las Regionales")
        
    with col_f2:
        almacenes_disponibles = sorted(df["NOMBRE_ALMACEN"].dropna().unique().tolist()) if "NOMBRE_ALMACEN" in df.columns else []
        selected_almacen = st.multiselect("Filtrar por Almacén", options=almacenes_disponibles, placeholder="Todos los Almacenes")
        
    with col_f3:
        if "AÑO_MES" in df.columns and not df["AÑO_MES"].isna().all():
            meses_disponibles = sorted(df["AÑO_MES"].dropna().unique().astype(str).tolist())
            selected_meses = st.multiselect("Filtrar por Meses", options=meses_disponibles, placeholder="Todos los Meses")
        else:
            selected_meses = []

    # Aplicación de Filtros
    df_filtered = df.copy()
    
    if selected_regional:
        df_filtered = df_filtered[df_filtered["REGIONAL"].isin(selected_regional)]
        
    if selected_almacen:
        df_filtered = df_filtered[df_filtered["NOMBRE_ALMACEN"].isin(selected_almacen)]
        
    if selected_meses and "AÑO_MES" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    # ---------------------------------------------------------
    # 🧮 CÁLCULO DE PARTICIPACIÓN % Y GUARDADO EN SESSION STATE
    # ---------------------------------------------------------
    if not df_totales_nacionales.empty and "TOTAL_NACIONAL" in df_totales_nacionales.columns:
        if selected_meses and "MES" in df_totales_nacionales.columns:
            total_nacional_base = df_totales_nacionales[df_totales_nacionales["MES"].isin(selected_meses)]["TOTAL_NACIONAL"].sum()
        else:
            total_nacional_base = df_totales_nacionales["TOTAL_NACIONAL"].sum()
    else:
        total_nacional_base = len(df) # Fallback en caso de que falle la carga

    if not df.empty and "CODALMACEN" in df.columns:
        if total_nacional_base > 0:
            tienda_counts = df_filtered.groupby("CODALMACEN").size()
            dict_pct_anulaciones = (tienda_counts / total_nacional_base * 100).to_dict()
            st.session_state["pct_anulaciones_tiendas"] = dict_pct_anulaciones
        else:
            st.session_state["pct_anulaciones_tiendas"] = {}
    else:
        st.session_state["pct_anulaciones_tiendas"] = {}

    st.markdown("---")

    # ---------------------------------------------------------
    # TARJETAS DE KPIS GLOBALES
    # ---------------------------------------------------------
    total_anulaciones = len(df_filtered)
    total_almacenes = df_filtered["CODALMACEN"].nunique() if "CODALMACEN" in df_filtered.columns else 0
    
    top_regional = (
        df_filtered["REGIONAL"].value_counts().index[0] 
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    top_almacen = (
        df_filtered["NOMBRE_ALMACEN"].value_counts().index[0] 
        if "NOMBRE_ALMACEN" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Anulaciones", f"{total_anulaciones:,}")
    kpi2.metric("Almacenes Afectados", f"{total_almacenes:,}")
    kpi3.metric("Regional Crítica", str(top_regional))
    kpi4.metric("Almacén Reincidente", str(top_almacen))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TABLA CONSOLIDADORA POR TIENDA (Novedades + % Participación)
    # ---------------------------------------------------------
    st.markdown("##### 📊 Resumen por Tienda y Participación Nacional")
    if not df_filtered.empty:
        df_resumen_tiendas = (
            df_filtered.groupby(["REGIONAL", "CODALMACEN", "NOMBRE_ALMACEN"])
            .size()
            .reset_index(name="Novedades Tienda")
        )
        df_resumen_tiendas.rename(columns={"NOMBRE_ALMACEN": "ALMACEN"}, inplace=True)
        
        # Cálculo de % Participación Nacional individual por tienda
        if total_nacional_base > 0:
            df_resumen_tiendas["% Participación Nacional"] = (
                (df_resumen_tiendas["Novedades Tienda"] / total_nacional_base) * 100
            ).apply(lambda x: f"{x:.2f}%")
        else:
            df_resumen_tiendas["% Participación Nacional"] = "0.00%"

        df_resumen_tiendas = df_resumen_tiendas.sort_values(by="Novedades Tienda", ascending=False)

        st.dataframe(
            df_resumen_tiendas[["REGIONAL", "CODALMACEN", "ALMACEN", "Novedades Tienda", "% Participación Nacional"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Sin registros para generar el resumen por tienda.")

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES (TOP 10 ALMACENES Y REGIONAL RADIAL)
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 🏪 Top 10 Almacenes con Mayor Número de Casos")
        if "NOMBRE_ALMACEN" in df_filtered.columns and not df_filtered.empty:
            top_almacenes = (
                df_filtered.groupby(["CODALMACEN", "NOMBRE_ALMACEN"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_almacenes["Etiqueta"] = top_almacenes["CODALMACEN"].astype(str) + " - " + top_almacenes["NOMBRE_ALMACEN"]
            
            fig_bar = px.bar(
                top_almacenes,
                x="Cantidad",
                y="Etiqueta",
                orientation="h",
                text="Cantidad",
                color_discrete_sequence=[COLOR_PRIMARY]
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                xaxis_title="Cantidad de Registros",
                yaxis_title="",
                margin=dict(l=0, r=20, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart2:
        st.markdown("##### 🗺️ Participación por Regional (Distribución Radial)")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_regional = df_filtered["REGIONAL"].value_counts().reset_index()
            df_regional.columns = ["REGIONAL", "Cantidad"]
            
            total_casos = df_regional["Cantidad"].sum()
            df_regional["Porcentaje"] = (df_regional["Cantidad"] / total_casos * 100).round(1)
            df_regional["Etiqueta_Pct"] = df_regional["REGIONAL"] + " (" + df_regional["Porcentaje"].astype(str) + "%)"
            
            fig_radial = px.bar_polar(
                df_regional,
                r="Cantidad",
                theta="Etiqueta_Pct",
                color="REGIONAL",
                color_discrete_sequence=px.colors.sequential.Blues_r,
                template="plotly_white"
            )
            fig_radial.update_layout(
                showlegend=False,
                margin=dict(l=30, r=30, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                polar=dict(
                    radialaxis=dict(showticklabels=False, ticks=""),
                    angularaxis=dict(tickfont=dict(size=10, color=COLOR_NEUTRAL_DARK))
                )
            )
            st.plotly_chart(fig_radial, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # ---------------------------------------------------------
    # TENDENCIA TEMPORAL MENSUAL
    # ---------------------------------------------------------
    st.markdown("##### 📈 Comportamiento Mensual de Anulaciones")
    if "AÑO_MES" in df_filtered.columns and not df_filtered.empty:
        df_trend = (
            df_filtered.groupby(df_filtered["AÑO_MES"].astype(str))
            .size()
            .reset_index(name="Cantidad")
        )
        df_trend.columns = ["Mes", "Cantidad"]
        
        fig_area = px.area(
            df_trend,
            x="Mes",
            y="Cantidad",
            markers=True,
            text="Cantidad",
            color_discrete_sequence=[COLOR_SECONDARY]
        )
        fig_area.update_traces(textposition="top center")
        fig_area.update_xaxes(type="category")
        fig_area.update_layout(
            xaxis_title="Mes de Facturación",
            yaxis_title="Nº de Anulaciones",
            height=300,
            margin=dict(l=0, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_area, use_container_width=True)

    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    st.write("Registros de anulaciones auditados:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "NOMBRE_ALMACEN", "FECHA", "Anulacion", "DESCRIPCION"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
