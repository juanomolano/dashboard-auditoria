import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa sobria
COLOR_PRIMARY = "#1E3A8A"      # Azul marino profundo
COLOR_SECONDARY = "#3B82F6"    # Azul corporativo
COLOR_ACCENT = "#D97706"       # Ámbar/Naranja sobrio para alertas
COLOR_NEUTRAL_DARK = "#1F2937" # Gris oscuro
COLOR_BG_CARD = "#F9FAFB"      # Fondo claro para tarjetas

@st.cache_data(ttl=60)
def load_data_obsequios():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQFE4HoACCEcqz8lU5SNHk2DFdFu_ZCjIITexvEJHVEzy65ClESgYik6T5thCe-zQ/pub?output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas especificando que el DÍA va primero (DD/MM/YYYY)
        if "FECHAFACTURA" in df.columns:
            df["FECHAFACTURA_DT"] = pd.to_datetime(df["FECHAFACTURA"], dayfirst=True, errors="coerce")
            
            # Crear columna formateada sin la hora (DD/MM/YYYY) para la tabla
            df["FECHA_MOSTRAR"] = df["FECHAFACTURA_DT"].dt.strftime("%d/%m/%Y")
            
            # Crear columna Año-Mes para agrupaciones mensuales (YYYY-MM)
            df["AÑO_MES"] = df["FECHAFACTURA_DT"].dt.to_period("M")
            
        # Asegurar tipos de datos adecuados
        if "CODALMACEN" in df.columns:
            df["CODALMACEN"] = df["CODALMACEN"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_01():
    # ---------------------------------------------------------
    # ENCABEZADO Y TEXTOS DE OBJETIVO Y ACCIÓN
    # ---------------------------------------------------------
    st.title("🎁 Seguimiento Entrega de Obsequios Valor $1")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Ejecutar la validación a nivel nacional de los obsequios otorgados a clientes que fueron registrados omitiendo las directrices de la política de obsequios referente al diligenciamiento de los campos obligatorios en la facturación de productos a $1, específicamente el motivo y la persona que autoriza. Este reporte consolidado se distribuye a las Jefaturas Regionales para su correspondiente revisión, control y debida justificación.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> Como medida correctiva y de control interno, se solicita la aplicación de la nota crédito correspondiente para dichos obsequios, procediendo con su posterior refacturación bajo la tarifa mensual aplicable según el caso.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos
    df = load_data_obsequios()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    # ---------------------------------------------------------
    # FILTROS INTERACTIVOS
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
    # TARJETAS DE KPIS GLOBALES
    # ---------------------------------------------------------
    total_incumplimientos = len(df_filtered)
    total_almacenes = df_filtered["CODALMACEN"].nunique() if "CODALMACEN" in df_filtered.columns else 0
    total_facturas = df_filtered["Factura"].nunique() if "Factura" in df_filtered.columns else 0
    top_regional_name = (
        df_filtered["REGIONAL"].value_counts().index[0] 
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Obsequios Registrados", f"{total_incumplimientos:,}")
    kpi2.metric("Total Facturas Auditadas", f"{total_facturas:,}")
    kpi3.metric("Almacenes con Registro", f"{total_almacenes:,}")
    kpi4.metric("Regional Máximo Incumplimiento", top_regional_name)

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES Y GRÁFICOS
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.2, 0.8])

    with col_chart1:
        st.markdown("##### 🏪 Top 10 Almacenes con Mayor Número de Casos")
        if "ALMACEN" in df_filtered.columns and not df_filtered.empty:
            top_almacenes = (
                df_filtered.groupby(["CODALMACEN", "ALMACEN"])
                .size()
                .reset_index(name="Cantidad")
                .sort_values(by="Cantidad", ascending=True)
                .tail(10)
            )
            top_almacenes["Etiqueta"] = top_almacenes["CODALMACEN"].astype(str) + " - " + top_almacenes["ALMACEN"]
            
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
        st.markdown("##### 🗺️ Participación por Regional")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_regional = df_filtered["REGIONAL"].value_counts().reset_index()
            df_regional.columns = ["REGIONAL", "Cantidad"]
            
            fig_pie = px.pie(
                df_regional,
                names="REGIONAL",
                values="Cantidad",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_pie.update_traces(textinfo="percent+label")
            fig_pie.update_layout(
                showlegend=False,
                margin=dict(l=10, r=10, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # ---------------------------------------------------------
    # TENDENCIA TEMPORAL MENSUAL
    # ---------------------------------------------------------
    st.markdown("##### 📈 Tendencia Mensual de Incumplimiento por Fecha de Factura")
    if "AÑO_MES" in df_filtered.columns and not df_filtered.empty:
        df_trend = (
            df_filtered.groupby("AÑO_MES")
            .size()
            .reset_index(name="Cantidad")
        )
        df_trend["AÑO_MES_STR"] = df_trend["AÑO_MES"].astype(str)
        
        fig_trend = px.line(
            df_trend,
            x="AÑO_MES_STR",
            y="Cantidad",
            markers=True,
            text="Cantidad",
            line_shape="spline",
            color_discrete_sequence=[COLOR_ACCENT]
        )
        fig_trend.update_traces(textposition="top center")
        fig_trend.update_layout(
            xaxis_title="Mes de Facturación",
            yaxis_title="Nº de Casos Registrados",
            height=320,
            margin=dict(l=0, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    st.write("Filtra y exporta los casos para enviar a las Jefaturas Regionales:")
    
    # Preparación de la vista reemplazando la columna interna por la limpia
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHAFACTURA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "ALMACEN", "Factura", "FECHAFACTURA", "NOMVENDEDOR"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHAFACTURA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
