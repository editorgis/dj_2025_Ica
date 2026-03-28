import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io
import gdown
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Catastro ICA 2025", page_icon="🏛️", layout="wide")

# --- 2. ID DE TU ARCHIVO DE DRIVE ---
ID_ARCHIVO_DRIVE = "132VqpRNmOG8zQ1g-2xmNBI4OC0GFEkRk" 

# --- 3. DICCIONARIO DE COLUMNAS ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA CATASTRAL 2025 - ICA</h1>", unsafe_allow_html=True)

# --- 4. FUNCIÓN DE CARGA ROBUSTA CON GDOWN ---
@st.cache_data(show_spinner="⏳ Sincronizando con Google Drive (34MB)...")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
        
        # Descarga forzada del archivo real
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        # Lectura del archivo descargado
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {hoja: pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("") for hoja in nombres_hojas}
        return datos, nombres_hojas
    except Exception as e:
        return None, str(e)

# Ejecución
archivo_excel, nombres_hojas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)

if archivo_excel is None:
    st.error(f"❌ Error crítico: {nombres_hojas}")
    st.stop()
else:
    st.sidebar.success("✅ Base de datos conectada")

# --- 5. BUSCADOR ---
c1, c2 = st.columns(2)
with c1:
    modo = st.radio("**Criterio:**", ["1. Por CODIGO", "2. Por COD_PRED"])
col_filtro = 'CODIGO' if "1" in modo else 'COD_PRED'
with c2:
    valor = st.text_input(f"Ingrese {col_filtro}:").strip().lstrip('0')

if valor:
    resultados = {}
    total = 0
    for h in nombres_hojas:
        df = archivo_excel[h]
        col_id = next((c for c in df.columns if c.upper() == col_filtro.upper()), None)
        if col_id:
            mask = df[col_id].str.strip().str.lstrip('0') == valor
            res = df[mask]
            if not res.empty:
                cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                resultados[h] = res[cols]
                total += len(res)

    if total > 0:
        st.success(f"🔎 Registros encontrados: {total}")
        for h, d in resultados.items():
            with st.expander(f"📋 Pestaña: {h}", expanded=True):
                st.dataframe(d, use_container_width=True)

        # --- 6. REPORTE PDF SEGURO ---
        if st.button("📄 Descargar Reporte PDF"):
            try:
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE CATASTRAL 2025", ln=True, align='C')
                pdf.ln(5)

                for h, data in resultados.items():
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.set_fill_color(230, 230, 230)
                    pdf.cell(0, 8, f" SECCIÓN: {h.upper()}", ln=True, fill=True, border=1)
                    
                    pdf.set_font("Helvetica", size=7)
                    for _, fila in data.iterrows():
                        info = " | ".join([f"{k}: {v}" for k, v in fila.to_dict().items()])
                        pdf.multi_cell(0, 5, info, border=1)
                        pdf.ln(1)
                
                # Conversión segura a bytes para la nube
                pdf_output = pdf.output(dest='S')
                if isinstance(pdf_output, str):
                    pdf_output = pdf_output.encode('latin-1')
                
                st.download_button(
                    label="⬇️ Descargar Archivo PDF",
                    data=pdf_output,
                    file_name=f"Reporte_{valor}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error PDF: {e}")
    else:
        st.warning("No se hallaron coincidencias.")
