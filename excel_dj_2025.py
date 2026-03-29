import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Catastro ICA 2025", page_icon="🏛️", layout="wide")

# --- 2. ID DE TU ARCHIVO DE DRIVE ---
ID_ARCHIVO_DRIVE = "132VqpRNmOG8zQ1g-2xmNBI4OC0GFEkRk" 

# --- 3. DICCIONARIO DE COLUMNAS (FILTROS) ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA CATASTRAL 2025</h1>", unsafe_allow_html=True)
st.write("---")

# --- 4. FUNCIÓN DE CARGA DESDE DRIVE ---
@st.cache_data(show_spinner="⏳ Sincronizando con Google Drive (34MB)...")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
        
        # Descarga el archivo usando gdown (Requiere permisos de lectura activados en Drive)
        gdown.download(url, output, quiet=False, fuzzy=True)
        
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {hoja: pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("") for hoja in nombres_hojas}
        return datos, nombres_hojas
    except Exception as e:
        return None, str(e)

archivo_excel, nombres_hojas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)

if archivo_excel is None:
    st.error(f"❌ Error crítico: {nombres_hojas}")
    st.stop()
else:
    st.sidebar.success("✅ Base de datos conectada")

# --- 5. BUSCADOR ---
c1, c2 = st.columns(2)
with c1:
    modo = st.radio("**Seleccione Criterio:**", ["1. Por CODIGO", "2. Por COD_PRED"])
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

        # --- 6. REPORTE PDF PROFESIONAL (TABLAS ALINEADAS) ---
        if st.button("📄 Generar Reporte PDF"):
            try:
                # Orientación Landscape (L) para que las tablas quepan mejor
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                
                # Título
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE CATASTRAL - ICA 2025", ln=True, align='C')
                pdf.set_font("Helvetica", size=10)
                pdf.cell(0, 7, f"Consulta: {col_filtro} {valor}", ln=True, align='C')
                pdf.ln(5)

                for h, data in resultados.items():
                    # Título de Sección con fondo azul
                    pdf.set_font("Helvetica", 'B', 11)
                    pdf.set_fill_color(30, 58, 138) 
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 8, f" SECCIÓN: {h.upper()}", ln=True, fill=True, border=1)
                    
                    # Configuración de Columnas
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Helvetica", 'B', 7)
                    columnas = data.columns.tolist()
                    ancho_col = 277 / len(columnas) # Reparte el ancho de la hoja A4 (277mm útiles)

                    # Dibujar Cabeceras de Tabla
                    pdf.set_fill_color(240, 240, 240)
                    for col in columnas:
                        pdf.cell(ancho_col, 6, str(col), border=1, align='C', fill=True)
                    pdf.ln()

                    # Dibujar Filas
                    pdf.set_font("Helvetica", size=6)
                    for _, fila in data.iterrows():
                        for col in columnas:
                            # Recortamos texto largo para que no rompa la celda
                            contenido = str(fila[col])[:20] 
                            pdf.cell(ancho_col, 5, contenido, border=1, align='C')
                        pdf.ln()
                    pdf.ln(5)

                # Solución para el error de bytearray en la nube
                pdf_output = pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)

                st.download_button(
                    label="⬇️ Descargar Reporte PDF Ordenado",
                    data=pdf_bytes,
                    file_name=f"Reporte_{valor}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error generando el PDF: {e}")
    else:
        st.warning("No se encontraron resultados para esa búsqueda.")
