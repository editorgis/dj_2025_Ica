import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import requests

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema Catastro ICA 2025",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. CONFIGURACIÓN DE ENLACE A GOOGLE DRIVE ---
# IMPORTANTE: Reemplaza este ID por el de tu archivo (está en el enlace de compartir)
ID_ARCHIVO_DRIVE = "1132VqpRNmOG8zQ1g-2xmNBI4OC0GFEkRk" # <-- PEGA AQUÍ TU ID REAL  

def obtener_url_descarga(id_file):
    return f"https://docs.google.com/uc?export=download&id={id_file}"

# --- 3. DICCIONARIO DE COLUMNAS (Configuración de visualización) ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACION JURADA 2025</h1>", unsafe_allow_html=True)
st.write("---")

# --- 4. FUNCIÓN PARA CARGAR DESDE DRIVE (Salta aviso de virus) ---
@st.cache_data(show_spinner="⏳ Conectando con Google Drive y descargando base de datos...")
def cargar_datos_desde_drive(file_id):
    url = obtener_url_descarga(file_id)
    session = requests.Session()
    
    # Intento inicial de descarga
    response = session.get(url, stream=True)
    
    # Si Google Drive envía un aviso de "archivo grande / posible virus", buscamos el token de confirmación
    token = None
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            token = value
            break
            
    if token:
        url = f"{url}&confirm={token}"
        response = session.get(url, stream=True)
    
    try:
        output = io.BytesIO(response.content)
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {}
        for hoja in nombres_hojas:
            df = pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("")
            datos[hoja] = df
        return datos, nombres_hojas
    except Exception as e:
        return None, str(e)

# Ejecución de la carga
archivo_excel, pestanas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)

if archivo_excel is None:
    st.error(f"❌ Error al conectar con Drive: {pestanas}")
    st.info("Asegúrate de que el archivo en Drive esté compartido como 'Cualquier persona con el enlace' en modo Lector.")
    st.stop()
else:
    st.sidebar.success("✅ Conectado a Google Drive")

# --- 5. LÓGICA DE BÚSQUEDA ---
col_op, col_in = st.columns(2)
with col_op:
    opcion = st.radio("**Seleccione criterio:**", ["1. Por CODIGO", "2. Por COD_PRED"])

col_filtro = 'CODIGO' if "1" in opcion else 'COD_PRED'

with col_in:
    valor_busqueda = st.text_input(f"Ingrese {col_filtro}:").strip().lstrip('0')

if valor_busqueda:
    resultados_acumulados = {}
    total = 0

    for nombre in pestanas:
        df_hoja = archivo_excel[nombre]
        col_id = next((c for c in df_hoja.columns if c.upper() == col_filtro.upper()), None)
        
        if col_id:
            mask = df_hoja[col_id].str.strip().str.lstrip('0') == valor_busqueda
            df_res = df_hoja[mask]
            
            if not df_res.empty:
                cols_mostrar = [c for c in columnas_especificas.get(nombre, df_res.columns) if c in df_res.columns]
                resultados_acumulados[nombre] = df_res[cols_mostrar]
                total += len(df_res)

    if total > 0:
        st.success(f"🔎 Se encontraron {total} registros.")
        for hoja, data in resultados_acumulados.items():
            st.markdown(f"### Pestaña: {hoja}")
            st.dataframe(data, use_container_width=True)

        # --- 6. GENERACIÓN DE PDF ---
        if st.button("📄 Descargar Reporte PDF"):
            try:
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE CATASTRAL - ICA 2025", ln=True, align='C')
                pdf.ln(10)

                for hoja, df_pdf in resultados_acumulados.items():
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 8, f" SECCIÓN: {hoja.upper()}", ln=True, fill=True, border=1)
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", 'B', 6)
                    
                    # Calcular anchos de columna
                    anchos = [max(pdf.get_string_width(str(c)) + 4, df_pdf[c].astype(str).map(pdf.get_string_width).max() + 4) for c in df_pdf.columns]
                    factor = (pdf.w - 20) / sum(anchos)
                    anchos_f = [w * factor for w in anchos]

                    # Encabezados
                    pdf.set_fill_color(230, 230, 230)
                    for i, col in enumerate(df_pdf.columns):
                        pdf.cell(anchos_f[i], 6, str(col), border=1, fill=True, align='C')
                    pdf.ln()

                    # Datos
                    pdf.set_font("Helvetica", size=6)
                    for _, fila in df_pdf.iterrows():
                        if pdf.get_y() > 180: pdf.add_page()
                        for i, col in enumerate(df_pdf.columns):
                            pdf.cell(anchos_f[i], 5, str(fila[col])[:40], border=1, align='C')
                        pdf.ln()
                    pdf.ln(5)

                # CORRECCIÓN DE BYTES PARA STREAMLIT CLOUD
                pdf_output = bytes(pdf.output())
                st.download_button(
                    label="⬇️ Confirmar Descarga PDF",
                    data=pdf_output,
                    file_name=f"Reporte_{valor_busqueda}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error generando PDF: {e}")
    else:
        st.warning("No se encontraron resultados.")
