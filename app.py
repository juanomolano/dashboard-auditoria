# app.py
import streamlit as st
from views.Home import render_home
from views.Obsequios import render_informe_01
from views.Anulaciones import render_informe_02
from views.Documentos import render_informe_03
from views.Tarifas import render_informe_04
from views.AperturasCierres import render_informe_05
from views.ConciliacionTarjetas import render_informe_06
from views.ConciliacionLinkPago import render_informe_07
from views.ConciliacionAddi import render_informe_08
from views.GestionRetailBI import render_gestion_retail  # <--- NUEVA IMPORTACIÓN

# Configuración principal de la página
st.set_page_config(
    page_title="Dashboard Consolidado de Auditoría Interna",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menú lateral de navegación
st.sidebar.title("🏢 Auditoría Interna")
st.sidebar.markdown("---")

opcion_menu = st.sidebar.radio(
    "Módulo de Auditoría:",
    [
        "🏠 Consolidado General",
        "🎁 Seguimiento Obsequios Valor $1",
        "💳 Control Anulaciones Forma de Pago",
        "🪪 Control Creación Tipo de Documento",
        "🏷️ Control Uso de Tarifas",
        "⏰ Control Apertura y Cierre Tiendas",
        "💳 Conciliación de Pagos con Tarjeta",
        "🔗 Conciliación Pagos con Link de Pago",
        "⚡ Conciliación de Pagos con Addi",
        "📊 Gestión Auditorías Retail (Power BI)",  # <--- NUEVA OPCIÓN
    ]
)

st.sidebar.markdown("---")

# Botón para forzar la recarga de datos
if st.sidebar.button("🔄 Recargar Datos", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Enrutamiento de las vistas
if opcion_menu == "🏠 Consolidado General":
    render_home()
elif opcion_menu == "🎁 Seguimiento Obsequios Valor $1":
    render_informe_01()
elif opcion_menu == "💳 Control Anulaciones Forma de Pago":
    render_informe_02()
elif opcion_menu == "🪪 Control Creación Tipo de Documento":
    render_informe_03()
elif opcion_menu == "🏷️ Control Uso de Tarifas":
    render_informe_04()
elif opcion_menu == "⏰ Control Apertura y Cierre Tiendas":
    render_informe_05()
elif opcion_menu == "💳 Conciliación de Pagos con Tarjeta":
    render_informe_06()
elif opcion_menu == "🔗 Conciliación Pagos con Link de Pago":
    render_informe_07()
elif opcion_menu == "⚡ Conciliación de Pagos con Addi":
    render_informe_08()
elif opcion_menu == "📊 Gestión Auditorías Retail (Power BI)":
    render_gestion_retail()  # <--- NUEVA RUTA
