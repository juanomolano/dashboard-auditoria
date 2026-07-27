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
        col_alm = [c for c in df_bi.columns if "ALMACEN" in c.upper() or "TIENDA" in c.upper()][0] if any("ALMACEN" in c.upper() for c in df_bi.columns) else df_bi.columns[3]
        
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
    # 🎨 ESTILOS CSS GENERALES Y PARA CÁPSULAS DE FILTRO SOBRIAS
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
            
            /* Cápsulas sobrias para el radio button */
            div[data-testid="stRadio"] div[role="radiogroup"] label div:first-child {
                display: none !important;
            }
            
            div[data-testid="stRadio"] div[role="radiogroup"] label {
                border-radius: 8px !important;
                padding: 8px 16px !important;
                margin-right: 8px !important;
                font-weight: 500 !important;
                color: #334155 !important;
                background-color: #FFFFFF !important;
                border: 1px solid #CBD5E1 !important;
                text-align: center !important;
                cursor: pointer !important;
                box-shadow: 0 1px 2px rgba(0,0,0,0.03) !important;
                transition: all 0.15s ease !important;
            }
            
            div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
                border-color: #94A3B8 !important;
                background-color: #F8FAFC !important;
            }

            div[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
                border-color: #1E3A8A !important;
                background-color: #EFF6FF !important;
                color: #1E3A8A !important;
                font-weight: bold !important;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
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

    # Función helper para estandarizar dataframes con REGIONAL, CODIGO y ALMACEN
    def estandarizar_df(df_input, modulo_nombre):
        if isinstance(df_input, pd.DataFrame) and not df_input.empty:
            temp = df_input.copy()
            col_reg = [c for c in temp.columns if "REGIONAL" in c.upper()]
            col_cod = [c for c in temp.columns if "COD" in c.upper() or "CODIGO" in c.upper()]
            col_alm = [c for c in temp.columns if "ALMACEN" in c.upper() or "TIENDA" in c.upper()]
            
            temp["REGIONAL_STD"] = temp[col_reg[0]].astype(str).str.strip().str.upper() if col_reg else "SIN REGIONAL"
            temp["CODIGO_STD"] = temp[col_cod[0]].astype(str).str.strip().str.upper() if col_cod else "S/C"
            temp["ALMACEN_STD"] = temp[col_alm[0]].astype(str).str.strip() if col_alm else temp["CODIGO_STD"]
            temp["Modulo"] = modulo_nombre
            return temp
        return pd.DataFrame()

    list_df_std = [
        estandarizar_df(df_m1, "Obsequios"),
        estandarizar_df(df_m2, "Anulaciones"),
        estandarizar_df(df_m3, "Documentos"),
        estandarizar_df(df_m4, "Tarifas"),
        estandarizar_df(df_m5, "Aperturas"),
        estandarizar_df(df_m6, "Conciliacion"),
        estandarizar_df(df_m7, "LinkPago"),
        estandarizar_df(df_m8, "Addi")
    ]

    df_consolidado_all = pd.concat([d for d in list_df_std if not d.empty], ignore_index=True) if any(not d.empty for d in list_df_std) else pd.DataFrame()

    # ---------------------------------------------------------
    # CONTROLES Y FILTROS EJECUTIVOS DINÁMICOS
    # ---------------------------------------------------------
    st.markdown("##### 🎛️ Filtros de Control Operativo")
    f_col1, f_col2 = st.columns(2)

    # 1. Filtro de Regional
    regionales_disponibles = ["TODAS"] + sorted([r for r in df_consolidado_all["REGIONAL_STD"].unique() if r != "SIN REGIONAL"]) if not df_consolidado_all.empty else ["TODAS"]
    sel_regional = f_col1.selectbox("🏢 Seleccionar Regional:", opciones := regionales_disponibles)

    # Filtrar data por regional para actualizar los almacenes del combo
    if sel_regional != "TODAS":
        df_sub_reg = df_consolidado_all[df_consolidado_all["REGIONAL_STD"] == sel_regional]
    else:
        df_sub_reg = df_consolidado_all.copy()

    # 2. Filtro de Almacén (solo muestra almacenes de la regional elegida)
    if not df_sub_reg.empty:
        almacenes_unicos = df_sub_reg[["CODIGO_STD", "ALMACEN_STD"]].drop_duplicates()
        almacenes_unicos["DISPLAY"] = almacenes_unicos["CODIGO_STD"] + " - " + almacenes_unicos["ALMACEN_STD"]
        opciones_almacen = ["TODOS"] + sorted(almacenes_unicos["DISPLAY"].tolist())
    else:
        opciones_almacen = ["TODOS"]

    sel_almacen_display = f_col2.selectbox("🏪 Seleccionar Almacén Especifico:", opciones_almacen)

    # Aplicar filtrado definitivo a los dataframes
    if sel_almacen_display != "TODOS":
        cod_sel = sel_almacen_display.split(" - ")[0]
        df_filtrado_final = df_consolidado_all[df_consolidado_all["CODIGO_STD"] == cod_sel]
    else:
        df_filtrado_final = df_sub_reg.copy()

    # Recálculo de Volúmenes Filtrados
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

    total_inconsistencias = sum(volumenes.values())
    
    # Saldo Recuperado Filtrado
    df_tarifas_filt = df_filtrado_final[df_filtrado_final["Modulo"] == "Tarifas"] if not df_filtrado_final.empty else pd.DataFrame()
    saldo_tarifas = df_tarifas_filt["SALDO_NUMERICO"].sum() if not df_tarifas_filt.empty and "SALDO_NUMERICO" in df_tarifas_filt.columns else 0

    # Top Regional y Almacén Reincidente Dinámico
    top_regional_global = df_filtrado_final["REGIONAL_STD"].value_counts().index[0] if not df_filtrado_final.empty else "N/A"
    top_almacen_global = df_filtrado_final["ALMACEN_STD"].value_counts().index[0] if not df_filtrado_final.empty else "N/A"

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # TARJETAS DE KPIS CONSOLIDADOS (ACTUALIZADOS EN TIEMPO REAL)
    # ---------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Hallazgos Auditados", f"{total_inconsistencias:,}")
    kpi2.metric("Saldo Recuperado", f"$ {saldo_tarifas:,.0f}")
    kpi3.metric("Regional Dominante", str(top_regional_global))
    kpi4.metric("Almacén Reincidente", str(top_almacen_global))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES PRINCIPALES CON SEMÁFORO EN MAPA DE CALOR
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
        if not df_filtrado_final.empty:
            df_matrix = pd.crosstab(df_filtrado_final["REGIONAL_STD"], df_filtrado_final["Modulo"])
            
            # 🎨 MAPA DE CALOR CON ESCALA DE SEMÁFORO TÉRMICO (Verde -> Amarillo -> Rojo)
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

    # ---------------------------------------------------------
    # MATRIZ DE RIESGO
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

        # Cruce con datos de Visitas BI
        if not df_bi_promedio.empty:
            df_merged = pd.merge(df_tiendas_count, df_bi_promedio, on="CODIGO", how="left")
            df_merged["PROMEDIO_VISITA_BI"] = df_merged["PROMEDIO_VISITA_BI"].fillna(0.0)
            df_merged["ALMACEN"] = df_merged["ALMACEN_BI"].fillna(df_merged["ALMACEN_FALLBACK"])
        else:
            df_merged = df_tiendas_count.copy()
            df_merged["PROMEDIO_VISITA_BI"] = 0.0
            df_merged["ALMACEN"] = df_merged["ALMACEN_FALLBACK"]

        # Cálculo de Penalización (0.5% por hallazgo) y Nota Ajustada
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

        df_merged["Riesgo"] = df_merged["Nota_Ajustada"].apply(clasificar_riesgo)

        c_bajo = len(df_merged[df_merged["Riesgo"] == "🟢 RIESGO BAJO"])
        c_medio = len(df_merged[df_merged["Riesgo"] == "🟡 RIESGO MEDIO"])
        c_alto = len(df_merged[df_merged["Riesgo"] == "🔴 RIESGO ALTO"])

        # 🎛️ CÁPSULAS DE FILTRO POR NIVEL DE RIESGO
        opciones_tarjeta = {
            f"🌐 TODAS ({len(df_merged)})": "TODAS",
            f"🟢 RIESGO BAJO ({c_bajo})": "🟢 RIESGO BAJO",
            f"🟡 RIESGO MEDIO ({c_medio})": "🟡 RIESGO MEDIO",
            f"🔴 RIESGO ALTO ({c_alto})": "🔴 RIESGO ALTO"
        }

        seleccion_riesgo = st.radio(
            "Filtro de Riesgo",
            options=list(opciones_tarjeta.keys()),
            horizontal=True,
            label_visibility="collapsed"
        )

        filtro_activo = opciones_tarjeta[seleccion_riesgo]

        if filtro_activo != "TODAS":
            df_tabla_final = df_merged[df_merged["Riesgo"] == filtro_activo].copy()
        else:
            df_tabla_final = df_merged.copy()

        # Ordenar primero por Total_Hallazgos
        df_tabla_final = df_tabla_final.sort_values(by="Total_Hallazgos", ascending=False)

        # Formatear columnas para la tabla
        df_tabla_final["Total Hallazgos Informes"] = df_tabla_final.apply(
            lambda row: f"{row['Total_Hallazgos']} (-{row['Descuento_Pct']:.1f}%)", axis=1
        )
        
        df_tabla_final["Porcentaje Visita"] = df_tabla_final["PROMEDIO_VISITA_BI"].apply(
            lambda x: f"{x:.1f}%" if x > 0 else "0.0% (Sin Visita)"
        )
        df_tabla_final["Porcentaje Final"] = df_tabla_final["Nota_Ajustada"].apply(lambda x: f"{x:.1f}%")

        cols_tabla = ["CODIGO", "ALMACEN", "Total Hallazgos Informes", "Porcentaje Visita", "Porcentaje Final", "Riesgo"]

        st.dataframe(
            df_tabla_final[cols_tabla],
            use_container_width=True,
            hide_index=True
        )

    # ---------------------------------------------------------
    # RESUMEN EJECUTIVO DE PROCESOS AUDITADOS (DINÁMICO)
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Estado Operativo de los 8 Módulos de Control")
    st.write(f"Estatus de los procesos bajo supervisión ({'Global' if sel_regional == 'TODAS' else sel_regional}):")

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
