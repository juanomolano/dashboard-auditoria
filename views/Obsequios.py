import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa
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
        
        if "FECHAFACTURA" in df.columns:
            df["FECHAFACTURA_DT"] = pd.to_datetime(df["FECHAFACTURA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHAFACTURA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHAFACTURA_DT"].dt.to_period("M").astype(str)
            
        if "CODALMACEN" in df.columns:
            df["CODALMACEN"] = df["CODALMACEN"].astype(str)
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_01():
    # 🎨 Estilos CSS para Métricas y Encabezados
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

    # Encabezado
    st.title("🎁 Seguimiento Entrega de Obsequios Valor $1")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Ejecutar la validación a nivel nacional de los obsequios otorgados a clientes que fueron registrados omitiendo las directrices de la política interna referente al diligenciamiento obligatorio de campos clave en la facturación de productos a $1, específicamente el motivo de la entrega y la identificación del usuario autorizador.
            </p>
        </div>
        <div style="background-color: #FEF3C7; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_ACCENT}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #92400E;">
                <strong>⚡ Acción Correctiva:</strong> Este reporte consolidado se distribuye a las Jefaturas Regionales para su correspondiente revisión, control y debida justificación. Como medida de control interno, de no contar con una justificación válida o soportada, se solicitará la emisión de la nota crédito correspondiente para proceder con la refacturación del producto a la tarifa comercial aplicable, asumiendo el líder o colaborador responsable el valor diferencial generado.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    df = load_data_obsequios()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    # Filtros Interactivos
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
            meses_disponibles = sorted(df["AÑO_MES"].dropna().unique().tolist())
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
        df_filtered = df_filtered[df_filtered["AÑO_MES"].isin(selected_meses)]

    st.markdown("---")

    # KPIs Globales
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
    kpi4.metric("Regional Crítica", str(top_regional_name))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # RESUMEN CONSOLIDADO POR ALMACÉN (% NACIONAL ACUMULADO)
    # ---------------------------------------------------------
    if not df_filtered.empty:
        st.markdown("##### 📊 Consolidado de Novedades de Obsequios por Almacén")
        
        df_calc = df_filtered.copy()
        
        if "AÑO_MES" not in df_calc.columns or df_calc["AÑO_MES"].isna().all():
            df_calc["AÑO_MES"] = "PERIODO_UNICO"

        # 1. Agrupar conteo de novedades por tienda y por cada mes
        df_mensual = (
            df_calc.groupby(["AÑO_MES", "REGIONAL", "CODALMACEN", "ALMACEN"])
            .size()
            .reset_index(name="Novedades_Mes")
        )

        # 2. Calcular el Total Nacional por cada Mes individual
        totales_mes = (
            df_mensual.groupby("AÑO_MES")["Novedades_Mes"]
            .sum()
            .reset_index(name="Total_Nacional_Mes")
        )

        # 3. Cruzar totales nacionales y sacar el % de la tienda en ese mes específico
        df_mensual = pd.merge(df_mensual, totales_mes, on="AÑO_MES", how="left")
        df_mensual["Pct_Nacional_Mes"] = (
            df_mensual["Novedades_Mes"] / df_mensual["Total_Nacional_Mes"]
        ) * 100

        # =========================================================
        # 🧪 BLOQUE DE VALIDACIÓN MES A MES (TIENDA S12 - TITAN)
        # =========================================================
        with st.expander("🔍 VALIDADOR DE CÁLCULO MES A MES (CLICK PARA AUDITAR S12 - TITAN)"):
            st.write("### Desglose Mensual para S12 - CLASSIC CC TITAN L120:")
            df_titan_test = df_mensual[df_mensual["CODALMACEN"].astype(str).str.contains("S12", na=False)].copy()
            
            if not df_titan_test.empty:
                df_titan_test["% Mes Formateado"] = df_titan_test["Pct_Nacional_Mes"].apply(lambda x: f"{x:.2f}%")
                
                st.dataframe(
                    df_titan_test[["AÑO_MES", "Novedades_Mes", "Total_Nacional_Mes", "% Mes Formateado"]],
                    use_container_width=True,
                    hide_index=True
                )
                
                suma_casos = df_titan_test["Novedades_Mes"].sum()
                suma_pct = df_titan_test["Pct_Nacional_Mes"].sum()
                st.info(f"📌 **Suma Total Casos Titán:** {suma_casos} | **Suma Acumulada Porcentajes Mensuales:** {suma_pct:.2f}%")
            else:
                st.warning("No se encontraron registros de la tienda S12 con los filtros seleccionados.")
        # =========================================================

        # 4. Consolidar por Tienda: Sumar novedades totales y la suma de porcentajes mensuales
        df_resumen = (
            df_mensual.groupby(["REGIONAL", "CODALMACEN", "ALMACEN"])
            .agg(
                Novedades_Tienda=("Novedades_Mes", "sum"),
                Pct_Acumulado=("Pct_Nacional_Mes", "sum")
            )
            .reset_index()
            .sort_values(by="Novedades_Tienda", ascending=False)
        )

        # 5. Formatear la columna de porcentaje
        df_resumen_display = df_resumen.copy()
        df_resumen_display["% Participación Nacional"] = (
            df_resumen_display["Pct_Acumulado"].apply(lambda x: f"{x:.2f}%")
        )
        df_resumen_display.rename(columns={"Novedades_Tienda": "Novedades Tienda"}, inplace=True)

        # 6. Añadir Fila Final de TOTAL GENERAL
        total_novedades = df_resumen["Novedades_Tienda"].sum()
        fila_total = pd.DataFrame([{
            "REGIONAL": "TOTAL GENERAL",
            "CODALMACEN": "-",
            "ALMACEN": "NACIONAL",
            "Novedades Tienda": total_novedades,
            "% Participación Nacional": "-"
        }])

        df_final_resumen = pd.concat([
            df_resumen_display[["REGIONAL", "CODALMACEN", "ALMACEN", "Novedades Tienda", "% Participación Nacional"]],
            fila_total
        ], ignore_index=True)

        st.dataframe(
            df_final_resumen,
            column_config={
                "REGIONAL": "REGIONAL",
                "CODALMACEN": "CODALMACEN",
                "ALMACEN": "ALMACEN",
                "Novedades Tienda": st.column_config.NumberColumn("Novedades Tienda", format="%d"),
                "% Participación Nacional": "% Participación Nacional"
            },
            use_container_width=True,
            hide_index=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES Y GRÁFICOS
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

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
            
            max_val = top_almacenes["Cantidad"].max() if not top_almacenes.empty else 10
            
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
                xaxis=dict(range=[0, max_val * 1.18]),
                margin=dict(l=0, r=60, t=20, b=20),
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
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_pie.update_traces(textinfo="percent", textposition="inside")
            fig_pie.update_layout(
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
                height=375,
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
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHAFACTURA"] = df_tabla["FECHA_MOSTRAR"]
        
    cols_display = [col for col in ["REGIONAL", "CODALMACEN", "ALMACEN", "Factura", "FECHAFACTURA", "NOMVENDEDOR"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHAFACTURA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
