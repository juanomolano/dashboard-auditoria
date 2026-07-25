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
def load_data_aperturas():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSZEU8vmCuxlgdHjobI8ObOFaiwwuLPxCa3k0HP1n5zZmNl144YdCKK4Pe2zEf0WDTwBLujQnchaX8-/pub?gid=0&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas especificando día primero (DD/MM/YYYY)
        if "FECHA" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "CODIGO" in df.columns:
            df["CODIGO"] = df["CODIGO"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_05():
    # 🎨 ESTILOS CSS PARA EVITAR TEXTOS CORTADOS Y PROPORCIONAR METRICAS
    st.markdown(
        """
        <style>
            h1 {
                font-size: 1.8rem !important;
                padding-bottom: 0px !important;
                margin-bottom: 10px !important;
            }
            /* Permite salto de línea en las etiquetas de métricas sin poner puntos suspensivos (...) */
            [data-testid="stMetricLabel"] {
                font-size: 0.8rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
                overflow: visible !important;
                text-overflow: clip !important;
                line-height: 1.2 !important;
            }
            /* Permite que valores largos (ej: BOGOTA SUR) quepan completos */
            [data-testid="stMetricValue"] {
                font-size: 1.05rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
            }
            /* Caja contenedora para las tarjetas de KPIs */
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
    st.title("⏰ Control Apertura y Cierre de Tiendas")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Validar el reporte enviado por Prosegur de las aperturas y cierres de las tiendas que cuentan con la activación de alarmas de seguridad.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> A las tiendas que incurren en estas novedades se les genera un proceso disciplinario debido a la repercusión operativa y faltas a los horarios de apertura/cierre.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos
    df = load_data_aperturas()
    
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
        tiendas_disponibles = sorted(df["TIENDA"].dropna().unique().tolist()) if "TIENDA" in df.columns else []
        selected_tienda = st.multiselect("Filtrar por Tienda", options=tiendas_disponibles, placeholder="Todas las Tiendas")
        
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
        
    if selected_tienda:
        df_filtered = df_filtered[df_filtered["TIENDA"].isin(selected_tienda)]
        
    if selected_meses and "AÑO_MES" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    st.markdown("---")

    # ---------------------------------------------------------
    # TARJETAS DE KPIS GLOBALES
    # ---------------------------------------------------------
    total_registros = len(df_filtered)
    
    total_nov_apertura = df_filtered["NOVEDAD APERTURA"].dropna().apply(lambda x: str(x).strip() != "" and str(x).upper() != "SIN NOVEDAD").sum() if "NOVEDAD APERTURA" in df_filtered.columns else 0
    total_nov_cierre = df_filtered["NOVEDAD CIERRE"].dropna().apply(lambda x: str(x).strip() != "" and str(x).upper() != "SIN NOVEDAD").sum() if "NOVEDAD CIERRE" in df_filtered.columns else 0
    
    top_regional = (
        df_filtered["REGIONAL"].value_counts().index[0] 
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Días Auditados", f"{total_registros:,}")
    kpi2.metric("Novedades en Apertura", f"{total_nov_apertura:,}")
    kpi3.metric("Novedades en Cierre", f"{total_nov_cierre:,}")
    kpi4.metric("Regional Crítica", str(top_regional))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES (DISPERSIÓN Y DONA MULTICOLOR)
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 🎯 Top 10 Tiendas con Mayor Incumplimiento Horario")
        if "TIENDA" in df_filtered.columns and not df_filtered.empty:
            top_tiendas = (
                df_filtered.groupby(["CODIGO", "TIENDA"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_tiendas["Etiqueta"] = top_tiendas["CODIGO"].astype(str) + " - " + top_tiendas["TIENDA"]
            
            # Margen dinámico para el eje X
            max_val = top_tiendas["Cantidad"].max() if not top_tiendas.empty else 10
            
            fig_dot = px.scatter(
                top_tiendas,
                x="Cantidad",
                y="Etiqueta",
                text="Cantidad",
                size="Cantidad",
                color_discrete_sequence=[COLOR_PRIMARY]
            )
            fig_dot.update_traces(
                marker=dict(size=15),
                textposition="middle right"
            )
            
            for _, row in top_tiendas.iterrows():
                fig_dot.add_shape(
                    type="line",
                    x0=0, y0=row["Etiqueta"],
                    x1=row["Cantidad"], y1=row["Etiqueta"],
                    line=dict(color="#CBD5E1", width=1.5, dash="dot")
                )

            fig_dot.update_layout(
                xaxis_title="Cantidad de Eventos",
                yaxis_title="",
                xaxis=dict(range=[0, max_val * 1.2]), # 🛠️ Da espacio para que el número al lado de la bola no tape nada
                margin=dict(l=0, r=50, t=20, b=20),
                height=350, # 🛠️ Tamaño un poco más compacto
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_dot, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart2:
        st.markdown("##### 🗺️ Distribución de Eventos por Regional")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_regional = df_filtered["REGIONAL"].value_counts().reset_index()
            df_regional.columns = ["REGIONAL", "Cantidad"]
            
            # 🎨 Gráfico de Dona Mediana-Grande Multicolor con Leyenda Lateral
            fig_donut = px.pie(
                df_regional,
                names="REGIONAL",
                values="Cantidad",
                hole=0.48,
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_donut.update_traces(
                textinfo="percent",
                textposition="inside",
                marker=dict(line=dict(color="#FFFFFF", width=2))
            )
            fig_donut.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=11, color=COLOR_NEUTRAL_DARK)
                ),
                margin=dict(l=10, r=10, t=10, b=10),
                height=370, # 🛠️ Tamaño Mediano-Grande perfecto
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # ---------------------------------------------------------
    # SEGUNDA FILA: TENDENCIA MENSUAL
    # ---------------------------------------------------------
    st.markdown("##### 📈 Comportamiento Mensual de Novedades de Horario")
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
            xaxis_title="Mes de Registro",
            yaxis_title="Nº de Registros",
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
    st.subheader("📋 Detalle Auditable de Registros Prosegur")
    st.write("Registros detallados de aperturas y cierres de tiendas:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODIGO", "TIENDA", "FECHA", "HORA APERTURA", "NOVEDAD APERTURA", "HORA CIERRE", "NOVEDAD CIERRE"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
