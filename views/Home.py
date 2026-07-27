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
# CARGA Y PROCESAMIENTO DE VISITAS BI (COLUMNAS EXACTAS)
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

        col_cod = "CODIGO" if "CODIGO" in df_bi.columns else df_bi.columns[0]
        col_alm = "ALMACEN" if "ALMACEN" in df_bi.columns else df_bi.columns[1]
        
        df_bi["CODIGO_CLEAN"] = df_bi[col_cod].astype(str).str.strip().str.upper()
        df_bi["ALMACEN_NOMBRE"] = df_bi[col_alm].astype(str).str.strip()
        
        df_promedio = df_bi.groupby("CODIGO_CLEAN").agg(
            PROMEDIO_VISITA_BI=("PCT_NUM", "mean"),
            ALMACEN_BI=("ALMACEN_NOMBRE", "first")
        ).reset_index()
        
        df_promedio.columns = ["CODIGO", "PROMEDIO_VISITA_BI", "ALMACEN_BI"]
        return df_promedio
    except Exception as e:
        return pd.DataFrame(columns=["CODIGO", "PROMEDIO_VISITA_BI", "ALMACEN_BI"])


def render_home():
    if "categoria_activa" not in st.session_state:
        st.session_state.categoria_activa = "TODAS"

    # 🎨 ESTILOS CSS CON INYECCIÓN DIRECTA PARA TARJETAS Y KPIS
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
            
            div.btn-todas button[data-testid="stBaseButton-secondary"] {
                background-color: #1E3A8A !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: bold !important;
            }
            div.btn-bajo button[data-testid="stBaseButton-secondary"] {
                background-color: #10B981 !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: bold !important;
            }
            div.btn-medio button[data-testid="stBaseButton-secondary"] {
                background-color: #F59E0B !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: bold !important;
            }
            div.btn-alto button[data-testid="stBaseButton-secondary"] {
                background-color: #EF4444 !important;
                color: #FFFFFF !important;
                border: none !important;
                font-weight: bold !important;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("🏠 Tablero Consolidado General de Auditoría")

    # ---------------------------------------------------------
    # CARGA DE DATOS Y ESTANDARIZACIÓN
    # ---------------------------------------------------------
    with st.spinner("Consolidando métricas e informes de auditoría con mapa exacto..."):
        df_m1 = load_data_obsequios()
        df_m2 = load_data_anulaciones()
        df_m3 = load_data_documentos()
        df_m4 = load_data_tarifas()
        df_m5 = load_data_aperturas()
        df_m6 = load_data_m6()
        df_m7 = load_data_m7()
        df_m8 = load_data_addi()
        df_bi_promedio = load_data_bi_visitas()

    def estandarizar_informe_exacto(df_input, col_cod_nombre, col_alm_nombre, col_reg_nombre, modulo_nombre):
        if isinstance(df_input, pd.DataFrame) and not df_input.empty:
            temp = df_input.copy()
            temp.columns = temp.columns.str.strip()
            
            c_cod = col_cod_nombre if col_cod_nombre in temp.columns else [c for c in temp.columns if "COD" in c.upper()][0]
            c_alm = col_alm_nombre if col_alm_nombre in temp.columns else [c for c in temp.columns if "ALM" in c.upper() or "TIENDA" in c.upper()][0]
            c_reg = col_reg_nombre if col_reg_nombre in temp.columns else [c for c in temp.columns if "REG" in c.upper()][0]
            
            temp["CODIGO_STD"] = temp[c_cod].astype(str).str.strip().str.upper()
            temp["ALMACEN_STD"] = temp[c_alm].astype(str).str.strip()
            temp["REGIONAL_STD"] = temp[c_reg].astype(str).str.strip().str.upper()
            temp["Modulo"] = modulo_nombre
            return temp
        return pd.DataFrame()

    list_df_std = [
        estandarizar_informe_exacto(df_m1, "CODALMACEN", "ALMACEN", "REGIONAL", "Obsequios"),
        estandarizar_informe_exacto(df_m2, "CODALMACEN", "NOMBRE_ALMACEN", "REGIONAL", "Anulaciones"),
        estandarizar_informe_exacto(df_m3, "CODALMACEN", "ALMACEN", "REGIONAL", "Documentos"),
        estandarizar_informe_exacto(df_m4, "COD", "ALMACEN", "REGIONAL", "Tarifas"),
        estandarizar_informe_exacto(df_m5, "CODIGO", "TIENDA", "REGIONAL", "Aperturas"),
        estandarizar_informe_exacto(df_m6, "Codigo", "TIENDA", "REGIONAL", "Conciliacion"),
        estandarizar_informe_exacto(df_m7, "CODALMACEN", "ALMACEN", "REGIONAL", "LinkPago"),
        estandarizar_informe_exacto(df_m8, "CODALMACEN", "ALMACEN", "REGIONAL", "Addi")
    ]

    df_consolidado_all = pd.concat([d for d in list_df_std if not d.empty], ignore_index=True) if any(not d.empty for d in list_df_std) else pd.DataFrame()

    # ---------------------------------------------------------
    # ENRIQUECIMIENTO DE NOMBRES CON HOJA OFICIAL DE BI
    # ---------------------------------------------------------
    if not df_consolidado_all.empty and not df_bi_promedio.empty:
        df_consolidado_all = pd.merge(
            df_consolidado_all,
            df_bi_promedio[["CODIGO", "ALMACEN_BI"]],
            left_on="CODIGO_STD",
            right_on="CODIGO",
            how="left"
        )
        # Priorizar el nombre proveniente del BI si existe
        df_consolidado_all["ALMACEN_STD"] = df_consolidado_all["ALMACEN_BI"].fillna(df_consolidado_all["ALMACEN_STD"])

    # ---------------------------------------------------------
    # 🎛️ FILTROS EJECUTIVOS SUPERIORES (REGIONAL Y ALMACÉN)
    # ---------------------------------------------------------
    st.markdown(
        """
        <div style="background-color: #F8FAFC; padding: 12px 16px; border-radius: 8px; border: 1px solid #CBD5E1; margin-bottom: 15px;">
            <p style="margin: 0; font-size: 13px; color: #1E3A8A; font-weight: bold;">
                🎛️ Centro de Control Interactivo: Filtra todo el tablero por Regional y/o Almacén Específico.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    f_col1, f_col2 = st.columns(2)

    # 1. Selector de Regional
    regionales_disponibles = ["TODAS"] + sorted([r for r in df_consolidado_all["REGIONAL_STD"].unique() if r != "SIN REGIONAL"]) if not df_consolidado_all.empty else ["TODAS"]
    sel_regional = f_col1.selectbox("🏢 Regional a consultar:", regionales_disponibles, key="sel_regional_main")

    if sel_regional != "TODAS":
        df_sub_reg = df_consolidado_all[df_consolidado_all["REGIONAL_STD"] == sel_regional]
    else:
        df_sub_reg = df_consolidado_all.copy()

    # 2. Selector de Almacén Dinámico (Obteniendo el nombre más largo/descriptivo por código único)
    if not df_sub_reg.empty:
        # Extraer para cada CODIGO_STD el nombre más completo
        almacenes_unicos = (
            df_sub_reg.groupby("CODIGO_STD")
            .agg(ALMACEN_BEST=("ALMACEN_STD", lambda x: max(x, key=len)))
            .reset_index()
        )
        almacenes_unicos["DISPLAY"] = almacenes_unicos["CODIGO_STD"] + " - " + almacenes_unicos["ALMACEN_BEST"]
        opciones_almacen = ["TODOS"] + sorted(almacenes_unicos["DISPLAY"].tolist())
    else:
        opciones_almacen = ["TODOS"]

    sel_almacen_display = f_col2.selectbox("🏪 Almacén a consultar:", opciones_almacen, key="sel_almacen_main")

    # Aplicar filtrado al dataset general
    if sel_almacen_display != "TODOS":
        cod_sel = sel_almacen_display.split(" - ")[0]
        df_filtrado_final = df_consolidado_all[df_consolidado_all["CODIGO_STD"] == cod_sel]
    else:
        df_filtrado_final = df_sub_reg.copy()

    # Recálculo de volúmenes filtrados
    def contar_modulo(mod_name):
        return len(df_filtrado_final[df_filtrado_final["Modulo"] == mod_name]) if not df_filtrado_final.empty else 0

    volumenes = {
        "Obsequios $1": contar_modulo("Obsequios"),
        "Anulaciones Forma Pago": contar_modulo("Anulaciones"),
        "Tipo Documento": contar_modulo("Documentos"),
        "Uso de Tarifas": contar_modulo("Tarifas"),
        "Apertura/Cierre Tiendas": contar_modulo("Aperturas"),
        "Datáfonos Tarjetas": contar_modulo("Conciliacion"),
        "Links Mercado Pago": contar_modulo("LinkPago"),
        "Créditos Addi": contar_modulo("Addi")
    }

    df_tarifas_filt = df_filtrado_final[df_filtrado_final["Modulo"] == "Tarifas"] if not df_filtrado_final.empty else pd.DataFrame()
    saldo_tarifas = df_tarifas_filt["SALDO_NUMERICO"].sum() if not df_tarifas_filt.empty and "SALDO_NUMERICO" in df_tarifas_filt.columns else 0

    top_regional_global = df_filtrado_final["REGIONAL_STD"].value_counts().index[0] if not df_filtrado_final.empty else "N/A"
    top_almacen_global = df_filtrado_final["ALMACEN_STD"].value_counts().index[0] if not df_filtrado_final.empty else "N/A"

    # ---------------------------------------------------------
    # 📌 TARJETAS KPIS SUPERIORES (REGIONAL Y TIENDA CON MÁS CASOS)
    # ---------------------------------------------------------
    kpi_col1, kpi_col2 = st.columns(2)
    kpi_col1.metric("Regional Crítica (Más Casos)", str(top_regional_global))
    kpi_col2.metric("Tienda Reincidente (Más Casos)", str(top_almacen_global))

    # ---------------------------------------------------------
    # 1. 🎯 MATRIZ DE RIESGO
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 Matriz de Riesgo")

    if not df_filtrado_final.empty:
        df_tiendas_count = (
            df_filtrado_final.groupby("CODIGO_STD")
            .agg(
                ALMACEN_FALLBACK=("ALMACEN_STD", lambda x: max(x, key=len)),
                Total_Hallazgos=("ALMACEN_STD", "count")
            )
            .reset_index()
        )
        df_tiendas_count.rename(columns={"CODIGO_STD": "CODIGO"}, inplace=True)

        if not df_bi_promedio.empty:
            df_merged = pd.merge(df_tiendas_count, df_bi_promedio, on="CODIGO", how="left")
            df_merged["PROMEDIO_VISITA_BI"] = df_merged["PROMEDIO_VISITA_BI"].fillna(0.0)
            df_merged["ALMACEN"] = df_merged["ALMACEN_BI"].fillna(df_merged["ALMACEN_FALLBACK"])
        else:
            df_merged = df_tiendas_count.copy()
            df_merged["PROMEDIO_VISITA_BI"] = 0.0
            df_merged["ALMACEN"] = df_merged["ALMACEN_FALLBACK"]

        df_merged["Descuento_Pct"] = df_merged["Total_Hallazgos"] * 0.5
        df_merged["Nota_Ajustada"] = df_merged["PROMEDIO_VISITA_BI"] - df_merged["Descuento_Pct"]

        def clasificar_riesgo(nota):
            if nota >= 85.0:
                return "🟢 RIESGO BAJO"
            elif nota >= 70.0:
                return "🟡 RIESGO MEDIO"
            else:
                return "🔴 RIESGO ALTO"

        df_merged["Riesgo"] = df_merged["Nota_Ajustada"].apply(clasificar_riesgo)

        c_bajo = len(df_merged[df_merged["Riesgo"] == "🟢 RIESGO BAJO"])
        c_medio = len(df_merged[df_merged["Riesgo"] == "🟡 RIESGO MEDIO"])
        c_alto = len(df_merged[df_merged["Riesgo"] == "🔴 RIESGO ALTO"])

        # Tarjetas de filtro de color
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

        if st.session_state.categoria_activa != "TODAS":
            df_filtrada = df_merged[df_merged["Riesgo"] == st.session_state.categoria_activa].copy()
        else:
            df_filtrada = df_merged.copy()

        df_filtrada = df_filtrada.sort_values(by="Total_Hallazgos", ascending=False)

        df_filtrada["Total Hallazgos Informes"] = df_filtrada.apply(
            lambda row: f"{row['Total_Hallazgos']} (-{row['Descuento_Pct']:.1f}%)", axis=1
        )
        
        df_filtrada["Porcentaje Visita"] = df_filtrada["PROMEDIO_VISITA_BI"].apply(
            lambda x: f"{x:.1f}%" if x > 0 else "0.0% (Sin Visita)"
        )
        df_filtrada["Porcentaje Final"] = df_filtrada["Nota_Ajustada"].apply(lambda x: f"{x:.1f}%")

        cols_finales = ["CODIGO", "ALMACEN", "Total Hallazgos Informes", "Porcentaje Visita", "Porcentaje Final", "Riesgo"]

        st.dataframe(
            df_filtrada[cols_finales],
            use_container_width=True,
            hide_index=True
        )

    # ---------------------------------------------------------
    # 2. 📋 ESTADO OPERATIVO DE LOS 8 MÓDULOS DE CONTROL
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Estado Operativo de los 8 Módulos de Control")
    st.write(f"Estatus general de los procesos bajo supervisión ({'Filtro Global' if sel_regional == 'TODAS' else sel_regional}):")

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

    # ---------------------------------------------------------
    # 3. 📌 VOLUMEN Y 4. 🗺️ MAPA DE CALOR
    # ---------------------------------------------------------
    st.markdown("---")
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
            xaxis_title="",
            yaxis_title="",
            coloraxis_showscale=False,
            margin=dict(l=0, r=90, t=20, b=20),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        max_val = df_vol["Cantidad"].max() if not df_vol.empty and df_vol["Cantidad"].max() > 0 else 10
        fig_bar_mod.update_xaxes(range=[0, max_val * 1.25])

        st.plotly_chart(fig_bar_mod, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🗺️ Mapa de Calor: Hallazgos por Regional y Módulo")
        if not df_filtrado_final.empty:
            df_matrix = pd.crosstab(df_filtrado_final["REGIONAL_STD"], df_filtrado_final["Modulo"])
            
            # Escala semáforo térmico (Verde -> Amarillo -> Rojo)
            fig_heatmap = px.imshow(
                df_matrix,
                labels=dict(x="Módulo de Control", y="Regional", color="Hallazgos"),
                x=df_matrix.columns,
                y=df_matrix.index,
                color_continuous_scale=[[0.0, "#10B981"], [0.5, "#F59E0B"], [1.0, "#EF4444"]],
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
            st.info("Sin datos para generar el mapa zonal con la selección actual.")
