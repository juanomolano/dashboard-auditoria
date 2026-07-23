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
def load_data_link_pago():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ58v4TtAkliL4mP70AhXDWLNJSNPOg0SbsNAA2LqTz7vWiQEmosYQILZfT9PU8pQ/pub?gid=847813721&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas especificando día primero (DD/MM/YYYY)
        if "FECHADOCUMENTO" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHADOCUMENTO"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "CODALMACEN" in df.columns:
            df["CODALMACEN"] = df["CODALMACEN"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_07():
    # ---------------------------------------------------------
    # ENCABEZADO Y TEXTOS DE CONTEXTO
    # ---------------------------------------------------------
    st.title("🔗 Conciliación Pagos con Link de Pago (Mercado Pago)")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Validar el proceso de conciliación de las transacciones generadas por medio de links de pago de Mercado Pago en las tiendas, garantizando el cruce correcto de cobros y facturación.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> Se exige la justificación operativa inmediata de las inconsistencias detectadas y, según su impacto y recurrencia, se solicita el inicio del proceso disciplinario respectivo.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos
    df = load_data_link_pago()
    
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
        almacenes_disponibles = sorted(df["ALMACEN"].dropna().unique().tolist()) if "ALMACEN" in df.columns else []
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
        df_filtered = df_filtered[df_filtered["ALMACEN"].isin(selected_almacen)]
        
    if selected_meses and "AÑO_MES" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    st.markdown("---")

    # ---------------------------------------------------------
    # TARJETAS DE KPIS GLOBALES (SIMILAR A TARJETAS)
    # ---------------------------------------------------------
    total_registros = len(df_filtered)
    total_tiendas = df_filtered["CODALMACEN"].nunique() if "CODALMACEN" in df_filtered.columns else 0
    
    top_regional = (
        df_filtered["REGIONAL"].value_counts().index[0] 
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Registros Conciliados", f"{total_registros:,}")
    kpi2.metric("Almacenes Impactados", f"{total_tiendas:,}")
    kpi3.metric("Regional con Más Alertas", str(top_regional))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES (BURBUJAS POR TIENDA Y CASCADA POR REGIONAL)
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 📍 Concentración de Alertas por Almacén (Top 10)")
        if "ALMACEN" in df_filtered.columns and not df_filtered.empty:
            top_almacenes = (
                df_filtered.groupby(["CODALMACEN", "ALMACEN"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_almacenes["Etiqueta"] = top_almacenes["CODALMACEN"].astype(str) + " - " + top_almacenes["ALMACEN"]
            
            # Gráfico estilo burbuja de dispersión horizontal (Bubble Scatter)
            fig_bubble = px.scatter(
                top_almacenes,
                x="Cantidad",
                y="Etiqueta",
                size="Cantidad",
                color="Cantidad",
                color_continuous_scale="Reds",
                text="Cantidad"
            )
            fig_bubble.update_traces(
                textposition="middle right",
                marker=dict(sizemode="area", sizeref=2 * max(top_almacenes["Cantidad"]) / (30**2) if max(top_almacenes["Cantidad"]) > 0 else 1)
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
            
            # Gráfico de Barras Horizontales con Gradiente
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
    # TENDENCIA TEMPORAL MENSUAL POR TIPO DE OPERACIÓN
    # ---------------------------------------------------------
    st.markdown("##### 📈 Comportamiento Mensual por Tipo de Auditoría Mercado Pago")
    if "AÑO_MES" in df_filtered.columns and "Auditoria_Operacion_MP_Optimizado" in df_filtered.columns and not df_filtered.empty:
        df_trend_mp = (
            df_filtered.groupby([df_filtered["AÑO_MES"].astype(str), "Auditoria_Operacion_MP_Optimizado"])
            .size()
            .reset_index(name="Cantidad")
        )
        df_trend_mp.columns = ["Mes", "Tipo_Auditoria", "Cantidad"]
        
        fig_trend = px.line(
            df_trend_mp,
            x="Mes",
            y="Cantidad",
            color="Tipo_Auditoria",
            markers=True,
            text="Cantidad",
            line_shape="spline",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_trend.update_traces(textposition="top center")
        fig_trend.update_xaxes(type="category")
        fig_trend.update_layout(
            xaxis_title="Mes de Conciliación",
            yaxis_title="Nº de Casos",
            legend_title="Tipo Auditoría MP",
            height=340,
            margin=dict(l=0, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros Mercado Pago")
    st.write("Detalle de transacciones por link de pago auditadas:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHADOCUMENTO"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "ALMACEN", "FECHADOCUMENTO", "NUMERO_DOC", "Auditoria_Operacion_MP_Optimizado"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHADOCUMENTO", ascending=False),
        use_container_width=True,
        hide_index=True
    )
