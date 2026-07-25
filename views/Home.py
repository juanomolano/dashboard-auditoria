import streamlit as st
import pandas as pd
import plotly.express as px

# 1. IMPORTAR LAS FUNCIONES DE CARGA DE DATOS DE LOS OTROS MÓDULOS
from views.Obsequios import load_data_obsequios
# (Si usas otras funciones en Home, impórtalas también aquí, por ejemplo:)
# from views.Anulaciones import load_data_anulaciones 

def render_home():
    # Estilos CSS para compactar títulos y métricas
    st.markdown(
        """
        <style>
            h1 {
                font-size: 1.8rem !important;
                padding-bottom: 0px !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 1.2rem !important;
                white-space: normal !important;
                word-wrap: break-word !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 0.85rem !important;
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
                📊 <strong>Centro de Control de Auditoría Interna:</strong> Vista consolidada en tiempo real de los 8 frentes de control operativo y financiero.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )


    # ---------------------------------------------------------
    # CARGA Y CONSOLIDACIÓN DE DATOS MULTI-MÓDULO
    # ---------------------------------------------------------
    with st.spinner("Consolidando métricas generales..."):
        df_m1 = load_data_obsequios()
        df_m2 = load_data_anulaciones()
        df_m3 = load_data_documentos()
        df_m4 = load_data_tarifas()
        df_m5 = load_data_aperturas()
        df_m6 = load_data_conciliacion()
        df_m7 = load_data_link_pago()
        df_m8 = load_data_addi()

    # Recuento por Módulo
    volumenes = {
        "Obsequios $1": len(df_m1),
        "Anulaciones Forma Pago": len(df_m2),
        "Tipo Documento": len(df_m3),
        "Uso de Tarifas": len(df_m4),
        "Apertura/Cierre Tiendas": len(df_m5),
        "Datáfonos Tarjetas": len(df_m6),
        "Links Mercado Pago": len(df_m7),
        "Créditos Addi": len(df_m8)
    }
    
    total_inconsistencias = sum(volumenes.values())
    
    # Impacto Financiero
    saldo_tarifas = df_m4["SALDO_NUMERICO"].sum() if "SALDO_NUMERICO" in df_m4.columns and not df_m4.empty else 0

    # Consolidador de Regionales
    reg_list = []
    for name, df_mod in [
        ("Obsequios", df_m1), ("Anulaciones", df_m2), ("Documentos", df_m3),
        ("Tarifas", df_m4), ("Aperturas", df_m5), ("Conciliacion", df_m6),
        ("LinkPago", df_m7), ("Addi", df_m8)
    ]:
        if not df_mod.empty and "REGIONAL" in df_mod.columns:
            temp = df_mod[["REGIONAL"]].dropna().copy()
            temp["Modulo"] = name
            reg_list.append(temp)
            
    df_reg_all = pd.concat(reg_list, ignore_index=True) if reg_list else pd.DataFrame()
    
    top_regional_global = df_reg_all["REGIONAL"].value_counts().index[0] if not df_reg_all.empty else "N/A"

    # Consolidador de Almacenes
    alm_list = []
    for df_mod in [df_m1, df_m2, df_m3, df_m4, df_m5, df_m6, df_m7, df_m8]:
        col_alm = "ALMACEN" if "ALMACEN" in df_mod.columns else ("TIENDA" if "TIENDA" in df_mod.columns else None)
        if not df_mod.empty and col_alm:
            alm_list.append(df_mod[col_alm].dropna())
            
    df_alm_all = pd.concat(alm_list, ignore_index=True) if alm_list else pd.Series()
    top_almacen_global = df_alm_all.value_counts().index[0] if not df_alm_all.empty else "N/A"

    # ---------------------------------------------------------
    # TARJETAS DE KPIS CONSOLIDADOS
    # ---------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Hallazgos Auditados", f"{total_inconsistencias:,}")
    kpi2.metric("Saldo en Contra Recuperable", f"$ {saldo_tarifas:,.0f}")
    kpi3.metric("Regional de Mayor Atención", str(top_regional_global))
    kpi4.metric("Almacén Más Reincidente", str(top_almacen_global)[:22] + "..." if len(str(top_almacen_global)) > 22 else str(top_almacen_global))

    st.markdown("<br>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # VISUALIZACIONES PRINCIPALES DE CONTROL
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
            # Crear matriz cruzada de Regional vs Módulo
            df_matrix = pd.crosstab(df_reg_all["REGIONAL"], df_reg_all["Modulo"])
            
            fig_heatmap = px.imshow(
                df_matrix,
                labels=dict(x="Módulo de Control", y="Regional", color="Hallazgos"),
                x=df_matrix.columns,
                y=df_matrix.index,
                color_continuous_scale="Blues",
                text_auto=True  # Muestra el número exacto dentro de cada casilla
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
