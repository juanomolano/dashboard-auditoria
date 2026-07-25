import streamlit as st
import streamlit.components.v1 as components

def render_gestion_retail():
    st.title("📊 Gestión de Auditorías en Tiendas Retail")
    
    st.markdown(
        """
        <div style="background-color: #F9FAFB; padding: 18px; border-radius: 8px; border-left: 5px solid #1E3A8A; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 14px; color: #1F2937;">
                <strong>📌 Control Consolidado de Calificación de Riesgo:</strong> Monitoreo interactivo de hallazgos, evaluaciones por regional y calificaciones por tienda integrado desde Power BI.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # URL de tu reporte seguro de Power BI
    powerbi_url = "https://app.powerbi.com/reportEmbed?reportId=36c41fe2-4cd0-4214-9f9a-2941b9d0c442&autoAuth=true&ctid=9a1892f1-89d9-4e33-97be-4e1d96ddced8"
    
    # Renderizado interactivo ajustado a 620px de altura para eliminar espacios en blanco
    components.iframe(src=powerbi_url, width=1250, height=620, scrolling=True)
