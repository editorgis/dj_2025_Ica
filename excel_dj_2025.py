import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import gdown
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Catastro ICA 2025", page_icon="🏛️", layout="wide")

# --- 2. CONFIGURACIÓN DE GOOGLE DRIVE ---
# Reemplaza esto con el ID de tu archivo de la imagen que compartiste
ID_ARCHIVO_DRIVE = "TU_ID_AQUI" 

# --- 3. DICCIONARIO DE COLUMNAS ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA CATASTRAL 2025</h1>", unsafe_allow_html=True)

# --- 4. FUNCIÓN PARA CARGAR DESDE DRIVE USANDO GDOWN ---
@st.cache_data(show_spinner="⏳ Descargando base de datos desde Google Drive (34MB)...")
def cargar_datos_gdown(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "database.xlsx"
        
        # gdown descarga el archivo real saltándose avisos de virus
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {hoja: pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("") for hoja in nombres_hojas}
        return datos, nombres_hojas
    except Exception as e:
        return None, str(e)

# Ejecutar carga automática
archivo_excel, resultado_carga = cargar_datos_gdown(ID_ARCHIVO_DRIVE)

if archivo_excel is None:
    st.error(f"❌ Error al conectar: {resultado_carga}")
    st.stop()
else:
    st.sidebar.success("✅ Conectado a Google Drive")

# --- 5. INTERFAZ DE BÚSQUEDA ---
col_1, col_2 = st.columns(2)
with col_1:
    opcion = st.radio("**Criterio:**", ["1. Por CODIGO", "2. Por COD_PRED"])
col_filtro = 'CODIGO' if "1" in opcion else 'COD_PRED'
with col_2:
    valor = st.text_input(f"Ingrese {col_filtro}:").strip().lstrip('0')

if valor:
    resultados = {}
    total = 0
    for nombre in archivo_excel.keys():
        df = archivo_excel[nombre]
        col_id = next((c for c in df.columns if c.upper() == col_filtro.upper()), None)
        if col_id:
            mask = df[col_id].str.strip().str.lstrip('0') == valor
            df_res = df[mask]
            if not df_res.empty:
                cols = [c for c in columnas_especificas.get(nombre, df_res.columns) if c in df_res.columns]
                resultados[nombre] = df_res[cols]
                total += len(df_res)

    if total > 0:
        st.success(f"🔎 Encontrados: {total}")
        for n, d in resultados.items():
            with st.expander(f"📋 Pestaña: {n}", expanded=True):
                st.dataframe(d, use_container_width=True)

        # --- 6. PDF CORREGIDO ---
        if st.button("📄 Generar Reporte PDF"):
            try:
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE CATASTRAL 2025", ln=True, align='C')
                pdf.ln(10)

                for hoja, df_p in resultados.items():
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.set_fill_color(30, 58, 138)
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 8, f" SECCIÓN: {hoja.upper()}", ln=True, fill=True, border=1)
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", size=6)
                    
                    for _, fila in df_p.iterrows():
                        pdf.multi_cell(0, 5, str(fila.to_dict()), border=1)
                        pdf.ln(2)

                # FIX bytearray: Convertimos a bytes puros
                pdf_bytes = bytes(pdf.output())
                st.download_button(label="⬇️ Descargar PDF", data=pdf_bytes, file_name=f"Reporte_{valor}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error en PDF: {e}")
    else:
        st.warning("No hay resultados.")
