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
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQNB6Y3yTcF0o7QFhFoLMOULPZXcVl84MahhUPvHcWyxDjEgQbWKeGTqqi0Y5WymQ/pub?gid=646635232&single=true&output=csv"
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
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
    
    # Cajas HTML sin indentación interna para evitar fallos de renderizado
    html_banner = f"""
    <div style="background-color: {COLOR_BG_CARD}; padding: 15px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px; color: {COLOR_NEUTRAL_DARK}; font-size: 14px;">
        <strong>📌 Objetivo:</strong> Auditar la calidad e integridad de la base de datos de clientes mediante la identificación de inconsistencias, tipologías de documentos erróneas o registros incompletos realizados durante el proceso de facturación en las tiendas.
    </div>
    <div style="background-color: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px; color: #92400E; font-size: 14px;">
        <strong>⚡ Acción Correctiva:</strong> Este reporte consolidado se distribuye a las Jefaturas Regionales para proceder con la depuración y corrección de los datos maestros en el sistema. Asimismo, a los líderes de tienda se les genera un reporte semanal cada lunes para proceder con la debida depuración.
    </div>
    """
    st.markdown(html_banner, unsafe_allow_html=True)
    
    df = load_data_documentos()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    # Filtros
    st.subheader("🔍 Filtros de Auditoría")
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        regional_disponibles = sorted(df["REGIONAL"].dropna().unique().tolist()) if "REGIONAL" in df.columns else []
        selected_regional = st.multiselect("Filtrar por Regional", options=regional_disponibles, placeholder="Todas las Regionales")
        
    df_filtered = df.copy()
    if selected_regional:
        df_filtered = df_filtered[df_filtered["REGIONAL"].isin(selected_regional)]

    with col_f2:
        almacenes_disponibles = sorted(df_filtered["ALMACEN"].dropna().unique().tolist()) if "ALMACEN" in df_filtered.columns else []
        selected_almacen = st.multiselect("Filtrar por Almacén", options=almacenes_disponibles, placeholder="Todos los Almacenes")
        
    if selected_almacen:
        df_filtered = df_filtered[df_filtered["ALMACEN"].isin(selected_almacen)]

    with col_f3:
        if "AÑO_MES" in df_filtered.columns and not df_filtered["AÑO_MES"].isna().all():
            meses_disponibles = sorted(df_filtered["AÑO_MES"].dropna().unique().astype(str).tolist())
            selected_meses = st.multiselect("Filtrar por Meses", options=meses_disponibles, placeholder="Todos los Meses")
            if selected_meses:
                df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    st.markdown("---")

    # KPIs
    total_casos = len(df_filtered)
    top_doc_error = df_filtered["DOCUMENTO"].value_counts().index[0] if "DOCUMENTO" in df_filtered.columns and not df_filtered.empty else "N/A"
    top_regional = df_filtered["REGIONAL"].value_counts().index[0] if "REGIONAL" in df_filtered.columns and not df_filtered.empty else "N/A"
    top_almacen = df_filtered["ALMACEN"].value_counts().index[0] if "ALMACEN" in df_filtered.columns and not df_filtered.empty else "N/A"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Facturas Auditadas", f"{total_casos:,}")
    kpi2.metric("Tipo Doc. Principal Error", str(top_doc_error))
    kpi3.metric("Regional Crítica", str(top_regional))
    kpi4.metric("Almacén Reincidente", str(top_almacen))

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos 1
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 📍 Top 10 Almacenes Críticos")
        if "ALMACEN" in df_filtered.columns and not df_filtered.empty:
            top_almacenes = (
                df_filtered.groupby(["CODALMACEN", "ALMACEN"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_almacenes["Etiqueta"] = top_almacenes["CODALMACEN"].astype(str) + " - " + top_almacenes["ALMACEN"]
            
            fig_dot = px.scatter(
                top_almacenes, x="Cantidad", y="Etiqueta", text="Cantidad",
                size="Cantidad", color_discrete_sequence=[COLOR_PRIMARY]
            )
            fig_dot.update_traces(marker=dict(size=16), textposition="middle right")
            
            for _, row in top_almacenes.iterrows():
                fig_dot.add_shape(
                    type="line", x0=0, y0=row["Etiqueta"], x1=row["Cantidad"], y1=row["Etiqueta"],
                    line=dict(color="#CBD5E1", width=1, dash="dot")
                )

            fig_dot.update_layout(
                xaxis_title="Cantidad de Registros", yaxis_title="",
                margin=dict(l=0, r=40, t=20, b=20), height=380,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_dot, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart2:
        st.markdown("##### 🔻 Concentración por Regional")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_regional = df_filtered["REGIONAL"].value_counts().reset_index()
            df_regional.columns = ["REGIONAL", "Cantidad"]
            
            fig_funnel = px.funnel(
                df_regional, x="Cantidad", y="REGIONAL",
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_funnel.update_layout(
                showlegend=False, margin=dict(l=10, r=10, t=20, b=20),
                height=380, paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_funnel, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # Gráficos 2
    col_chart3, col_chart4 = st.columns([0.8, 1.2])

    with col_chart3:
        st.markdown("##### 🪪 Distribución por Tipo de Documento")
        if "DOCUMENTO" in df_filtered.columns and not df_filtered.empty:
            df_doc = df_filtered["DOCUMENTO"].value_counts().reset_index()
            df_doc.columns = ["DOCUMENTO", "Cantidad"]
            
            fig_pie = px.pie(
                df_doc, names="DOCUMENTO", values="Cantidad", hole=0.45,
                color_discrete_sequence=px.colors.sequential.Tealgrn_r
            )
            fig_pie.update_traces(textinfo="percent+label")
            fig_pie.update_layout(
                showlegend=False, margin=dict(l=10, r=10, t=20, b=20),
                height=300, paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart4:
        st.markdown("##### 📈 Comportamiento Mensual de Inconsistencias")
        if "AÑO_MES" in df_filtered.columns and not df_filtered.empty:
            df_trend = df_filtered.groupby("AÑO_MES").size().reset_index(name="Cantidad")
            df_trend["AÑO_MES_STR"] = df_trend["AÑO_MES"].astype(str)
            
            fig_area = px.area(
                df_trend, x="AÑO_MES_STR", y="Cantidad", markers=True,
                text="Cantidad", color_discrete_sequence=[COLOR_SECONDARY]
            )
            fig_area.update_traces(textposition="top center")
            fig_area.update_layout(
                xaxis_title="Mes", yaxis_title="Nº de Casos", height=300,
                margin=dict(l=0, r=20, t=30, b=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_area, use_container_width=True)

    # Tabla
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    st.write("Facturas registradas con posible inconsistencia de tipo de documento:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHAFACTURA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "ALMACEN", "FECHAFACTURA", "Factura", "DOCUMENTO", "IDENTIFICACION", "NOMVENDEDOR"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHAFACTURA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
