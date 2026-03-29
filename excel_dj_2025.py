import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Consulta Declaracion Jurada 2025 - ICA", page_icon="🏛️", layout="wide")

# --- 2. ID DE TU ARCHIVO DE DRIVE ---
ID_ARCHIVO_DRIVE = "132VqpRNmOG8zQ1g-2xmNBI4OC0GFEkRk" 

# --- 3. DICCIONARIO DE COLUMNAS ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA CATASTRAL 2025</h1>", unsafe_allow_html=True)
st.write("---")

@st.cache_data(show_spinner="⏳ Sincronizando con Google Drive...")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
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

# --- 5. BUSCADOR ---
c1, c2 = st.columns(2)
with c1:
    modo = st.radio("**Seleccione Criterio:**", ["1. Por COD_CONTRIBUTENTE", "2. Por COD_PREDIO"])
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

        # --- 6. REPORTE PDF REESTRUCTURADO (FORMATO FICHA) ---
        if st.button("📄 Generar Reporte PDF Profesional"):
            try:
                # Usamos vertical (P) porque el formato ficha se lee mejor así
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                
                # Encabezado
                pdf.set_font("Helvetica", 'B', 16)
                pdf.set_text_color(30, 58, 138)
                pdf.cell(0, 10, "REPORTE DE DECLARACIÓN JURADA 2025", ln=True, align='C')
                pdf.set_font("Helvetica", size=10)
                pdf.set_text_color(100, 100, 100)
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                pdf.cell(0, 5, f"ICA, PERÚ | Generado el: {fecha}", ln=True, align='C')
                pdf.cell(0, 5, f"Búsqueda por {col_filtro}: {valor}", ln=True, align='C')
                pdf.ln(10)

                for h, data in resultados.items():
                    # Título de Sección
                    pdf.set_font("Helvetica", 'B', 12)
                    pdf.set_fill_color(30, 58, 138) 
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 9, f"  {h.upper()}", ln=True, fill=True)
                    pdf.ln(2)
                    
                    pdf.set_text_color(0, 0, 0)
                    
                    # Formato Ficha: Cada fila del Excel es un bloque
                    for i, (_, fila) in enumerate(data.iterrows()):
                        pdf.set_font("Helvetica", 'B', 9)
                        pdf.set_fill_color(245, 245, 245)
                        pdf.cell(0, 7, f" Registro N° {i+1}", ln=True, fill=True, border='B')
                        
                        # Imprimir cada campo en dos columnas (Nombre del campo : Valor)
                        pdf.set_font("Helvetica", size=8)
                        
                        items = fila.to_dict().items()
                        # Dividimos los items para que no sea una lista infinita hacia abajo
                        for k, v in items:
                            pdf.set_font("Helvetica", 'B', 8)
                            pdf.cell(45, 6, f"{k}:", border=0)
                            pdf.set_font("Helvetica", size=8)
                            pdf.cell(0, 6, f"{v}", ln=True, border=0)
                        
                        pdf.ln(4) # Espacio entre fichas
                        
                        # Si queda poco espacio en la hoja, saltamos de página
                        if pdf.get_y() > 250:
                            pdf.add_page()

                pdf_output = pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1', 'replace') if isinstance(pdf_output, str) else bytes(pdf_output)

                st.download_button(
                    label="⬇️ Descargar Reporte PDF Legible",
                    data=pdf_bytes,
                    file_name=f"Reporte_Catastro_{valor}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error en PDF: {e}")
    else:
        st.warning("No se hallaron resultados.")
