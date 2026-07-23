import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de paleta corporativa sobria (Azules, Rojo/Ámbar Financiero y Grises)
COLOR_PRIMARY = "#1E3A8A"      # Azul marino profundo
COLOR_SECONDARY = "#2563EB"    # Azul corporativo
COLOR_DANGER = "#DC2626"       # Rojo corporativo para Saldos en Contra
COLOR_ACCENT = "#D97706"       # Ámbar sobrio
COLOR_NEUTRAL_DARK = "#1F2937" # Gris oscuro
COLOR_BG_CARD = "#F9FAFB"      # Fondo claro para tarjetas

@st.cache_data(ttl=60)
def load_data_tarifas():
    """
    Carga dinámicamente la hoja pública de Google Sheets en formato CSV.
    """
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTCJzHEb2QpcFckHDlKJlEFRRlbhnwYxyswXUm4ZTjSQMZXwUZrMl_4MPi5lqS5mQ/pub?gid=825387403&single=true&output=csv"
    
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df.columns = df.columns.str.strip()
        
        # Conversión de fechas (DD/MM/YYYY)
        if "FECHA" in df.columns:
            df["FECHA_DT"] = pd.to_datetime(df["FECHA"], dayfirst=True, errors="coerce")
            df["FECHA_MOSTRAR"] = df["FECHA_DT"].dt.strftime("%d/%m/%Y")
            df["AÑO_MES"] = df["FECHA_DT"].dt.to_period("M")
            
        if "COD" in df.columns:
            df["COD"] = df["COD"].astype(str)
            
        # Limpieza y conversión numérica del SALDO EN CONTRA
        if "SALDO EN CONTRA" in df.columns:
            # Convertir a texto primero para limpiar símbolos $ o comas
            s_clean = df["SALDO EN CONTRA"].astype(str).str.replace("$", "", regex=False)
            s_clean = s_clean.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
            df["SALDO_NUMERICO"] = pd.to_numeric(s_clean, errors="coerce").fillna(0)
        else:
            df["SALDO_NUMERICO"] = 0
            
        return df
    except Exception as e:
        st.error(f"⚠️ No se pudo conectar al archivo de Google Sheets: {e}")
        return pd.DataFrame()

def render_informe_04():
    # ---------------------------------------------------------
    # ENCABEZADO Y TEXTOS DE CONTEXTO
    # ---------------------------------------------------------
    st.title("🏷️ Control Uso de Tarifas")
    
    st.markdown(
        f"""
        <div style="background-color: {COLOR_BG_CARD}; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_PRIMARY}; margin-bottom: 12px;">
            <p style="margin: 0; font-size: 14px; color: {COLOR_NEUTRAL_DARK};">
                <strong>📌 Objetivo:</strong> Validar las tarifas usadas y su correcto uso (T. 900, General Outlet, Liquidación, Venta de bodega y Venta empleados) en la facturación de puntos de venta.
            </p>
        </div>
        <div style="background-color: #FEF2F2; padding: 18px; border-radius: 8px; border-left: 5px solid {COLOR_DANGER}; margin-bottom: 25px;">
            <p style="margin: 0; font-size: 14px; color: #991B1B;">
                <strong>⚡ Acción Correctiva:</strong> El mal uso de esta tarifa implica el cobro de la diferencia que se dejó de otorgar al líder que generó dicho error, así como el inicio del proceso disciplinario correspondiente.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Carga de datos
    df = load_data_tarifas()
    
    if df.empty:
        st.warning("No se encontraron registros para mostrar.")
        return

    # ---------------------------------------------------------
    # FILTROS INTERACTIVOS LIMPIOS
    # ---------------------------------------------------------
    st.subheader("🔍 Filtros de Auditoría")
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    
    with col_f1:
        regional_disponibles = sorted(df["REGIONAL"].dropna().unique().tolist()) if "REGIONAL" in df.columns else []
        selected_regional = st.multiselect("Filtrar por Regional", options=regional_disponibles, placeholder="Todas")
        
    with col_f2:
        tarifas_disponibles = sorted(df["TARIFA"].dropna().unique().tolist()) if "TARIFA" in df.columns else []
        selected_tarifa = st.multiselect("Filtrar por Tarifa", options=tarifas_disponibles, placeholder="Todas")
        
    with col_f3:
        almacenes_disponibles = sorted(df["ALMACEN"].dropna().unique().tolist()) if "ALMACEN" in df.columns else []
        selected_almacen = st.multiselect("Filtrar por Almacén", options=almacenes_disponibles, placeholder="Todos")
        
    with col_f4:
        if "AÑO_MES" in df.columns and not df["AÑO_MES"].isna().all():
            meses_disponibles = sorted(df["AÑO_MES"].dropna().unique().astype(str).tolist())
            selected_meses = st.multiselect("Filtrar por Meses", options=meses_disponibles, placeholder="Todos")
        else:
            selected_meses = []

    # Aplicación de Filtros
    df_filtered = df.copy()
    
    if selected_regional:
        df_filtered = df_filtered[df_filtered["REGIONAL"].isin(selected_regional)]
        
    if selected_tarifa:
        df_filtered = df_filtered[df_filtered["TARIFA"].isin(selected_tarifa)]
        
    if selected_almacen:
        df_filtered = df_filtered[df_filtered["ALMACEN"].isin(selected_almacen)]
        
    if selected_meses and "AÑO_MES" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["AÑO_MES"].astype(str).isin(selected_meses)]

    st.markdown("---")

    # ---------------------------------------------------------
    # TARJETAS DE KPIS GLOBALES FINANCIEROS (REORGANIZADO A 3 COLUMNAS)
    # ---------------------------------------------------------
    total_casos = len(df_filtered)
    saldo_total = df_filtered["SALDO_NUMERICO"].sum()
    
    top_tarifa_error = (
        df_filtered["TARIFA"].value_counts().index[0] 
        if "TARIFA" in df_filtered.columns and not df_filtered.empty 
        else "N/A"
    )

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Registros Novedad", f"{total_casos:,}")
    kpi2.metric("Saldo en Contra Total", f"$ {saldo_total:,.0f}")
    kpi3.metric("Tarifa con Más Casos", str(top_tarifa_error))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES FINANCIERAS ÚNICAS
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 💵 Saldo en Contra ($) por Tipo de Tarifa")
        if "TARIFA" in df_filtered.columns and not df_filtered.empty:
            df_tarifa_saldo = (
                df_filtered.groupby("TARIFA")["SALDO_NUMERICO"]
                .sum()
                .reset_index()
                .sort_values(by="SALDO_NUMERICO", ascending=True)
            )
            
            fig_bar_saldo = px.bar(
                df_tarifa_saldo,
                x="SALDO_NUMERICO",
                y="TARIFA",
                orientation="h",
                text="SALDO_NUMERICO",
                color_discrete_sequence=[COLOR_PRIMARY]
            )
            fig_bar_saldo.update_traces(
                texttemplate="$ %{x:,.0f}",
                textposition="outside"
            )
            fig_bar_saldo.update_layout(
                xaxis_title="Monto Acumulado ($)",
                yaxis_title="",
                margin=dict(l=0, r=60, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bar_saldo, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    with col_chart2:
        st.markdown("##### 🟣 Matriz Riesgo: Casos vs. Saldo en Contra por Regional")
        if "REGIONAL" in df_filtered.columns and not df_filtered.empty:
            df_bubble = (
                df_filtered.groupby("REGIONAL")
                .agg(
                    Casos=("SALDO_NUMERICO", "count"),
                    SaldoTotal=("SALDO_NUMERICO", "sum")
                )
                .reset_index()
            )
            
            # Scatter / Bubble Chart (Relación Casos vs Impacto Económico)
            fig_bubble = px.scatter(
                df_bubble,
                x="Casos",
                y="SaldoTotal",
                size="SaldoTotal",
                color="REGIONAL",
                text="REGIONAL",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            fig_bubble.update_traces(
                textposition="top center",
                marker=dict(sizemode="diameter", sizeref=df_bubble["SaldoTotal"].max() / 40 if df_bubble["SaldoTotal"].max() > 0 else 1)
            )
            fig_bubble.update_layout(
                xaxis_title="Nº de Casos Ocurridos",
                yaxis_title="Saldo en Contra Total ($)",
                showlegend=False,
                margin=dict(l=10, r=10, t=20, b=20),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig_bubble, use_container_width=True)
        else:
            st.info("Sin datos para generar la gráfica.")

    # ---------------------------------------------------------
    # SEGUNDA FILA: TENDENCIA MENSUAL DEL SALDO EN CONTRA
    # ---------------------------------------------------------
    st.markdown("##### 📈 Comportamiento Mensual del Saldo en Contra ($)")
    if "AÑO_MES" in df_filtered.columns and not df_filtered.empty:
        df_trend = (
            df_filtered.groupby("AÑO_MES")["SALDO_NUMERICO"]
            .sum()
            .reset_index()
        )
        df_trend["AÑO_MES_STR"] = df_trend["AÑO_MES"].astype(str)
        
        fig_line = px.line(
            df_trend,
            x="AÑO_MES_STR",
            y="SALDO_NUMERICO",
            markers=True,
            text="SALDO_NUMERICO",
            color_discrete_sequence=[COLOR_DANGER]
        )
        fig_line.update_traces(
            texttemplate="$ %{y:,.0f}",
            textposition="top center"
        )
        fig_line.update_layout(
            xaxis_title="Mes",
            yaxis_title="Saldo en Contra ($)",
            height=320,
            margin=dict(l=0, r=20, t=30, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    # ---------------------------------------------------------
    # TABLA DE DETALLE AUDITABLE CON FORMATO MONEDA
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Detalle Auditable de Registros")
    st.write("Facturas con inconsistencia en tarifa y saldo en contra atribuible:")
    
    df_tabla = df_filtered.copy()
    if "FECHA_MOSTRAR" in df_tabla.columns:
        df_tabla["FECHA"] = df_tabla["FECHA_MOSTRAR"]
        
    # Formatear la columna monetaria para la vista tabular
    df_tabla["SALDO_FORMATO"] = df_tabla["SALDO_NUMERICO"].apply(lambda x: f"$ {x:,.0f}")
    
    cols_display = [col for col in ["REGIONAL", "COD", "ALMACEN", "FECHA", "Factura", "TARIFA", "VENDEDOR", "SALDO_FORMATO"] if col in df_tabla.columns]
    
    st.dataframe(
        df_tabla[cols_display].sort_values(by="FECHA", ascending=False),
        use_container_width=True,
        hide_index=True
    )
