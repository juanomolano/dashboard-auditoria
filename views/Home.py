import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# IMPORTACIONES SEGURAS DE INFORMES
# ---------------------------------------------------------
from views.Obsequios import load_data_obsequios
from views.Anulaciones import load_data_anulaciones
from views.Documentos import load_data_documentos
from views.Tarifas import load_data_tarifas
from views.AperturasCierres import load_data_aperturas

try:
    from views.ConciliacionTarjetas import load_data_tarjetas as load_data_m6
except ImportError:
    try:
        from views.ConciliacionTarjetas import load_data_conciliacion as load_data_m6
    except ImportError:
        load_data_m6 = lambda: pd.DataFrame()

try:
    from views.ConciliacionLinkPago import load_data_links as load_data_m7
except ImportError:
    try:
        from views.ConciliacionLinkPago import load_data_link_pago as load_data_m7
    except ImportError:
        load_data_m7 = lambda: pd.DataFrame()

from views.ConciliacionAddi import load_data_addi


# ---------------------------------------------------------
# CARGA Y PROCESAMIENTO DE VISITAS BI POR CÓDIGO
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_data_bi_visitas():
    url_bi = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRNYj2gzHu2_4DVxA1bcYQl4i5H1xDetU0OPv0JvjQBVmiZFKNHJFnar8ib6FomdA/pub?gid=985157017&single=true&output=csv"
    try:
        df_bi = pd.read_csv(url_bi, encoding="utf-8")
        df_bi.columns = df_bi.columns.str.strip()
        
        col_pct = [c for c in df_bi.columns if "PORCENTAJE" in c.upper() or "VISITA" in c.upper()]
        col_target = col_pct[0] if col_pct else "Porcentaje"
        
        s_clean = df_bi[col_target].astype(str).str.replace("%", "", regex=False)
        s_clean = s_clean.str.replace(",", ".", regex=False).str.strip()
        df_bi["PCT_NUM"] = pd.to_numeric(s_clean, errors="coerce").fillna(0.0)
        
        if df_bi["PCT_NUM"].max() <= 1.0 and df_bi["PCT_NUM"].max() > 0:
            df_bi["PCT_NUM"] = df_bi["PCT_NUM"] * 100

        col_cod = [c for c in df_bi.columns if "COD" in c.upper()][0] if any("COD" in c.upper() for c in df_bi.columns) else df_bi.columns[1]
        df_bi["CODIGO_CLEAN"] = df_bi[col_cod].astype(str).str.strip().str.upper()
        
        df_promedio = df_bi.groupby("CODIGO_CLEAN")["PCT_NUM"].mean().reset_index()
        df_promedio.columns = ["CODIGO", "PROMEDIO_VISITA_BI"]
        return df_promedio
    except Exception as e:
        return pd.DataFrame(columns=["CODIGO", "PROMEDIO_VISITA_BI"])


def render_home():
    if "categoria_activa" not in st.session_state:
        st.session_state.categoria_activa = "TODAS"

    # 🎨 ESTILOS CSS COMPACTOS Y EXCLUSIVOS PARA TARJETAS BOTÓN
    st.markdown(
        """
        <style>
            h1 {
                font-size: 1.8rem !important;
                padding-bottom: 0px !important;
                margin-bottom: 10px !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.1rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
            }
            div[data-testid="stMetric"] {
                background-color: #F8FAFC;
                padding: 10px 14px;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
            }
            
            /* Estilo compacto para los botones del filtro */
            div.row-widget.stButton > button {
                width: 100%;
                border-radius: 8px;
                padding: 6px 8px !important;
                font-size: 0.82rem !important;
                font-weight: bold;
                border: 1px solid #CBD5E1;
                color: white !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                min-height: 55px !important;
                line-height: 1.2 !important;
            }
            
            /* Colores compactos específicos */
            div.btn-todas > button { background-color: #1E3A8A !important; }
            div.btn-bajo > button { background-color: #10B981 !important; }
            div.btn-medio > button { background-color: #F59E0B !important; }
            div.btn-alto > button { background-color: #EF4444 !important; }

            div.row-widget.stButton > button:hover {
                filter: brightness(0.92);
                transform: translateY(-1px);
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🏠 Tablero Consolidado General de Auditoría")
    
    st.markdown(
        """
        <div style="background-color: #F9FAFB; padding: 12px 18px; border-radius: 8px; border-left: 4px solid #1E3A8A; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 13px; color: #1F2937;">
                📊 <strong>Centro de Control de Auditoría Interna:</strong> Vista consolidada en tiempo real con matriz de riesgo y penalización operativa.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ---------------------------------------------------------
    # CARGA DE DATOS MULTI-MÓDULO
    # ---------------------------------------------------------
    with st.spinner("Consolidando métricas e informes de auditoría..."):
        df_m1 = load_data_obsequios()
        df_m2 = load_data_anulaciones()
        df_m3 = load_data_documentos()
        df_m4 = load_data_tarifas()
        df_m5 = load_data_aperturas()
        df_m6 = load_data_m6()
        df_m7 = load_data_m7()
        df_m8 = load_data_addi()
        df_bi_promedio = load_data_bi_visitas()

    volumenes = {
        "Obsequios $1": len(df_m1) if isinstance(df_m1, pd.DataFrame) else 0,
        "Anulaciones Forma Pago": len(df_m2) if isinstance(df_m2, pd.DataFrame) else 0,
        "Tipo Documento": len(df_m3) if isinstance(df_m3, pd.DataFrame) else 0,
        "Uso de Tarifas": len(df_m4) if isinstance(df_m4, pd.DataFrame) else 0,
        "Apertura/Cierre Tiendas": len(df_m5) if isinstance(df_m5, pd.DataFrame) else 0,
        "Datáfonos Tarjetas": len(df_m6) if isinstance(df_m6, pd.DataFrame) else 0,
        "Links Mercado Pago": len(df_m7) if isinstance(df_m7, pd.DataFrame) else 0,
        "Créditos Addi": len(df_m8) if isinstance(df_m8, pd.DataFrame) else 0
    }
    
    total_inconsistencias = sum(volumenes.values())
    saldo_tarifas = df_m4["SALDO_NUMERICO"].sum() if isinstance(df_m4, pd.DataFrame) and "SALDO_NUMERICO" in df_m4.columns and not df_m4.empty else 0

    # Consolidador de Regionales
    reg_list = []
    for name, df_mod in [
        ("Obsequios", df_m1), ("Anulaciones", df_m2), ("Documentos", df_m3),
        ("Tarifas", df_m4), ("Aperturas", df_m5), ("Conciliacion", df_m6),
        ("LinkPago", df_m7), ("Addi", df_m8)
    ]:
        if isinstance(df_mod, pd.DataFrame) and not df_mod.empty and "REGIONAL" in df_mod.columns:
            temp = df_mod[["REGIONAL"]].dropna().copy()
            temp["Modulo"] = name
            reg_list.append(temp)
            
    df_reg_all = pd.concat(reg_list, ignore_index=True) if reg_list else pd.DataFrame()
    top_regional_global = df_reg_all["REGIONAL"].value_counts().index[0] if not df_reg_all.empty else "N/A"

    # Consolidador de Almacenes (Código + Nombre)
    alm_pairs = []
    for df_mod in [df_m1, df_m2, df_m3, df_m4, df_m5, df_m6, df_m7, df_m8]:
        if isinstance(df_mod, pd.DataFrame) and not df_mod.empty:
            col_cod = [c for c in df_mod.columns if "COD" in c.upper() or "CODIGO" in c.upper()]
            col_alm = [c for c in df_mod.columns if "ALMACEN" in c.upper() or "TIENDA" in c.upper()]
            
            if col_cod and col_alm:
                temp_df = df_mod[[col_cod[0], col_alm[0]]].dropna().copy()
                temp_df.columns = ["CODIGO", "ALMACEN"]
                temp_df["CODIGO"] = temp_df["CODIGO"].astype(str).str.strip().str.upper()
                alm_pairs.append(temp_df)

    if alm_pairs:
        df_all_pairs = pd.concat(alm_pairs, ignore_index=True)
        top_almacen_global = df_all_pairs["ALMACEN"].value_counts().index[0] if not df_all_pairs.empty else "N/A"
    else:
        df_all_pairs = pd.DataFrame(columns=["CODIGO", "ALMACEN"])
        top_almacen_global = "N/A"

    # ---------------------------------------------------------
    # TARJETAS DE KPIS CONSOLIDADOS
    # ---------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Hallazgos Auditados", f"{total_inconsistencias:,}")
    kpi2.metric("Saldo Recuperado", f"$ {saldo_tarifas:,.0f}")
    kpi3.metric("Regional Crítica", str(top_regional_global))
    kpi4.metric("Almacén Reincidente", str(top_almacen_global))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES PRINCIPALES
    # ---------------------------------------------------------
    col_chart1, col_chart2 = st.columns([1.1, 0.9])

    with col_chart1:
        st.markdown("##### 📌 Volumen de Hallazgos por Módulo Auditado")
        df_vol = pd.DataFrame(list(volumenes.items()), columns=["Módulo", "Cantidad"]).sort_values(by="Cantidad", ascending=True)
        
        fig_bar_mod = px.bar(
            df_vol,
            x="Cantidad",
            y="Módulo",
            orientation="h",
            text="Cantidad",
            color="Cantidad",
            color_continuous_scale="Blues"
        )
        fig_bar_mod.update_traces(textposition="outside")
        fig_bar_mod.update_layout(
            xaxis_title="Cantidad de Eventos",
            yaxis_title="",
            coloraxis_showscale=False,
            margin=dict(l=0, r=40, t=20, b=20),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_bar_mod, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🗺️ Mapa de Calor: Hallazgos por Regional y Módulo")
        if not df_reg_all.empty:
            df_matrix = pd.crosstab(df_reg_all["REGIONAL"], df_reg_all["Modulo"])
            
            fig_heatmap = px.imshow(
                df_matrix,
                labels=dict(x="Módulo de Control", y="Regional", color="Hallazgos"),
                x=df_matrix.columns,
                y=df_matrix.index,
                color_continuous_scale="Blues",
                text_auto=True
            )
            fig_heatmap.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                coloraxis_showscale=False,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Sin datos para generar el mapa zonal.")

    # ---------------------------------------------------------
    # MATRIZ DE RIESGO
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 Matriz de Riesgo")

    if not df_all_pairs.empty:
        df_tiendas_count = (
            df_all_pairs.groupby("CODIGO")
            .agg(ALMACEN=("ALMACEN", "first"), Total_Hallazgos=("ALMACEN", "count"))
            .reset_index()
        )

        # Cruce con datos de Visitas BI (0.0% si aún no tiene visita presencial)
        if not df_bi_promedio.empty:
            df_merged = pd.merge(df_tiendas_count, df_bi_promedio, on="CODIGO", how="left")
            df_merged["PROMEDIO_VISITA_BI"] = df_merged["PROMEDIO_VISITA_BI"].fillna(0.0)
        else:
            df_merged = df_tiendas_count.copy()
            df_merged["PROMEDIO_VISITA_BI"] = 0.0

        # Cálculo de Penalización y Nota Ajustada (Permite valores negativos si no se ha visitado)
        df_merged["Descuento_Pct"] = df_merged["Total_Hallazgos"] * 0.5
        df_merged["Nota_Ajustada"] = df_merged["PROMEDIO_VISITA_BI"] - df_merged["Descuento_Pct"]

        # Clasificación por Nivel de Riesgo
        def clasificar_riesgo(nota):
            if nota >= 85.0:
                return "🟢 RIESGO BAJO"
            elif nota >= 70.0:
                return "🟡 RIESGO MEDIO"
            else:
                return "🔴 RIESGO ALTO"

        df_merged["Clasificacion"] = df_merged["Nota_Ajustada"].apply(clasificar_riesgo)

        c_bajo = len(df_merged[df_merged["Clasificacion"] == "🟢 RIESGO BAJO"])
        c_medio = len(df_merged[df_merged["Clasificacion"] == "🟡 RIESGO MEDIO"])
        c_alto = len(df_merged[df_merged["Clasificacion"] == "🔴 RIESGO ALTO"])

        # 🎛️ FILTROS/BOTONES COMPACTOS DE RIESGO
        b1, b2, b3, b4 = st.columns(4)

        with b1:
            st.markdown('<div class="btn-todas">', unsafe_allow_html=True)
            if st.button(f"🌐 TODAS ({len(df_merged)})", key="btn_todas"):
                st.session_state.categoria_activa = "TODAS"
            st.markdown('</div>', unsafe_allow_html=True)

        with b2:
            st.markdown('<div class="btn-bajo">', unsafe_allow_html=True)
            if st.button(f"🟢 RIESGO BAJO ({c_bajo})", key="btn_bajo"):
                st.session_state.categoria_activa = "🟢 RIESGO BAJO"
            st.markdown('</div>', unsafe_allow_html=True)

        with b3:
            st.markdown('<div class="btn-medio">', unsafe_allow_html=True)
            if st.button(f"🟡 RIESGO MEDIO ({c_medio})", key="btn_medio"):
                st.session_state.categoria_activa = "🟡 RIESGO MEDIO"
            st.markdown('</div>', unsafe_allow_html=True)

        with b4:
            st.markdown('<div class="btn-alto">', unsafe_allow_html=True)
            if st.button(f"🔴 RIESGO ALTO ({c_alto})", key="btn_alto"):
                st.session_state.categoria_activa = "🔴 RIESGO ALTO"
            st.markdown('</div>', unsafe_allow_html=True)

        st.caption(f"Filtro activo: **{st.session_state.categoria_activa}**")

        # Aplicar el filtro según la selección
        if st.session_state.categoria_activa != "TODAS":
            df_filtrada = df_merged[df_merged["Clasificacion"] == st.session_state.categoria_activa].copy()
        else:
            df_filtrada = df_merged.copy()

        # Formatear columnas
        df_filtrada["Porcentaje Visita (BI)"] = df_filtrada["PROMEDIO_VISITA_BI"].apply(
            lambda x: f"{x:.1f}%" if x > 0 else "0.0% (Sin Visita)"
        )
        df_filtrada["Porcentaje Final Ajustado"] = df_filtrada["Nota_Ajustada"].apply(lambda x: f"{x:.1f}%")
        df_filtrada["Total Hallazgos Auditados"] = df_filtrada["Total_Hallazgos"]

        cols_finales = ["CODIGO", "ALMACEN", "Total Hallazgos Auditados", "Porcentaje Visita (BI)", "Porcentaje Final Ajustado", "Clasificacion"]

        st.dataframe(
            df_filtrada[cols_finales].sort_values(by="Total Hallazgos Auditados", ascending=False),
            use_container_width=True,
            hide_index=True
        )

    # ---------------------------------------------------------
    # RESUMEN EJECUTIVO DE PROCESOS AUDITADOS
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Estado Operativo de los 8 Módulos de Control")
    st.write("Estatus general de los procesos bajo supervisión:")

    m_col1, m_col2 = st.columns(2)

    with m_col1:
        st.markdown(f"🎁 **Obsequios Valor $1:** `{volumenes['Obsequios $1']:,}` registros analizados.")
        st.markdown(f"💳 **Anulaciones Forma de Pago:** `{volumenes['Anulaciones Forma Pago']:,}` eventos detectados.")
        st.markdown(f"🪪 **Tipo de Documento:** `{volumenes['Tipo Documento']:,}` inconsistencias en clientes.")
        st.markdown(f"🏷️ **Uso de Tarifas:** `{volumenes['Uso de Tarifas']:,}` casos ($ {saldo_tarifas:,.0f} saldo en contra).")

    with m_col2:
        st.markdown(f"⏰ **Apertura y Cierre Tiendas:** `{volumenes['Apertura/Cierre Tiendas']:,}` novedades de horario.")
        st.markdown(f"💳 **Datáfonos Tarjetas:** `{volumenes['Datáfonos Tarjetas']:,}` alertas en datáfono.")
        st.markdown(f"🔗 **Links Mercado Pago:** `{volumenes['Links Mercado Pago']:,}` transacciones auditadas.")
        st.markdown(f"⚡ **Créditos Addi:** `{volumenes['Créditos Addi']:,}` registros conciliados.")
