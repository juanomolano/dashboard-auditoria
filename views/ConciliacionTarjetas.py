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
def load_data_conciliacion():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSoATpMQSc32B3A3Fkuy-K1ioh0cFchEMWiJcJ-xyzdS1V7bFFecPwyHwDgQJse2qMEbL5-7LR0A0H_/pub?gid=0&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fecha
        if "Fecha Concilia" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["Fecha Concilia"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "Codigo" in df.columns:
            df["Codigo"] = df["Codigo"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_06():
    # ---------------------------------------------------------
    # ENCABEZADO Y TEXTOS DE CONTEXTO
    # ---------------------------------------------------------
    st.title("💳 Conciliación de Pagos con Tarjeta")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Validar el proceso de pago por medio de datáfono en las tiendas, garantizando que los cobros se realicen y facturen dentro del punto de venta correspondiente y previniendo cruces de ventas con otras tiendas.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> Se exige la justificación inmediata de las novedades identificadas y, según la gravedad de la inconsistencia en los datáfonos, se solicita el inicio del proceso disciplinario correspondiente.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos
    df = load_data_conciliacion()
    
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
    total_tiendas = df_filtered["Codigo"].nunique() if "Codigo" in df_filtered.columns else 0
    
    top_regional = (
        df_filtered["REGIONAL"].value_counts().index[0] 
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Registros Conciliados", f"{total_registros:,}")
    kpi2.metric("Tiendas Impactadas", f"{total_tiendas:,}")
    kpi3.metric("Regional con Más Alertas", str(top_regional))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES NUEVAS Y DIFERENCIADAS
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 📍 Concentración de Alertas por Tienda (Top 10)")
        if "TIENDA" in df_filtered.columns and not df_filtered.empty:
            top_tiendas = (
                df_filtered.groupby(["Codigo", "TIENDA"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_tiendas["Etiqueta"] = top_tiendas["Codigo"].astype(str) + " - " + top_tiendas["TIENDA"]
            
            # Gráfico estilo burbuja de dispersión horizontal (Bubble Scatter)
            fig_bubble = px.scatter(
                top_tiendas,
                x="Cantidad",
                y="Etiqueta",
                size="Cantidad",
                color="Cantidad",
                color_continuous_scale="Reds",
                text="Cantidad"
            )
            fig_bubble.update_traces(
                textposition="middle right",
                marker=dict(sizemode="area", sizeref=2 * max(top_tiendas["Cantidad"]) / (30**2) if max(top_tiendas["Cantidad"]) > 0 else 1)
            )
            fig_bubble.update_layout(
                xaxis_title="Nº de Alertas Registradas",
                yaxis_title="",
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(l=0, r=40, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart2:
        st.markdown("##### 🗺️ Participación de Alertas por Regional")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_regional = df_filtered["REGIONAL"].value_counts().reset_index()
            df_regional.columns = ["REGIONAL", "Cantidad"]
            
            # Calcular porcentaje para etiquetas explicativas
            total_casos = df_regional["Cantidad"].sum()
            df_regional["Porcentaje"] = (df_regional["Cantidad"] / total_casos * 100).round(1)
            df_regional["Etiqueta_Pct"] = df_regional["REGIONAL"] + " (" + df_regional["Porcentaje"].astype(str) + "%)"
            
            # Gráfico de Cascada Descendente con gradiente corporativo
            fig_bar = px.bar(
                df_regional,
                x="Cantidad",
                y="Etiqueta_Pct",
                orientation="h",
                text="Cantidad",
                color="Cantidad",
                color_continuous_scale="Blues"
            )
            fig_bar.update_traces(textposition="outside")
            fig_bar.update_layout(
                xaxis_title="Nº de Alertas",
                yaxis_title="",
                coloraxis_showscale=False,
                margin=dict(l=0, r=40, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # ---------------------------------------------------------
    # TENDENCIA TEMPORAL MENSUAL ENFOCADA EN TIPOS DE ALERTA
    # ---------------------------------------------------------
    st.markdown("##### 📈 Comportamiento Mensual por Tipo de Alerta de Datáfono")
    if "AÑO_MES" in df_filtered.columns and "Alerta_Datafono_Optimizado" in df_filtered.columns and not df_filtered.empty:
        # Agrupar por Mes y por Tipo de Alerta
        df_trend_alert = (
            df_filtered.groupby([df_filtered["AÑO_MES"].astype(str), "Alerta_Datafono_Optimizado"])
            .size()
            .reset_index(name="Cantidad")
        )
        df_trend_alert.columns = ["Mes", "Tipo_Alerta", "Cantidad"]
        
        # Gráfico de líneas compuestas por tipo de alerta
        fig_trend = px.line(
            df_trend_alert,
            x="Mes",
            y="Cantidad",
            color="Tipo_Alerta",
            markers=True,
            text="Cantidad",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_trend.update_traces(textposition="top center")
        fig_trend.update_xaxes(type="category")
        fig_trend.update_layout(
            xaxis_title="Mes de Conciliación",
            yaxis_title="Nº de Alertas",
            legend_title="Tipo de Alerta",
            height=340,
            margin=dict(l=0, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Sin datos suficientes para generar la tendencia por alerta.")
    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros de Conciliación")
    st.write("Registros procesados para validación de datáfonos en punto de venta:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["Fecha Concilia"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "Codigo", "TIENDA", "Fecha Concilia", "Alerta_Datafono_Optimizado"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="Fecha Concilia", ascending=False),
        use_container_width=True,
        hide_index=True
    )
