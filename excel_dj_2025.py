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

# --- 3. DICCIONARIO DE COLUMNAS (FILTROS) ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACION JURADA 2025</h1>", unsafe_allow_html=True)
st.write("---")

# --- 4. FUNCIÓN DE CARGA DESDE DRIVE ---
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
else:
    st.sidebar.success("✅ Base de datos conectada")

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

        # --- 6. REPORTE PDF MEJORADO ---
        if st.button("📄 Generar Reporte PDF Profesional"):
            try:
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                
                # Encabezado
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE DECLARACION JURADA 2025 - ICA", ln=True, align='C')
                pdf.set_font("Helvetica", size=9)
                fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
                pdf.cell(0, 5, f"Consulta realizada por {col_filtro}: {valor} | Fecha: {fecha_actual}", ln=True, align='C')
                pdf.ln(5)

                for h, data in resultados.items():
                    # Título de Sección
                    pdf.set_font("Helvetica", 'B', 11)
                    pdf.set_fill_color(30, 58, 138) 
                    pdf.set_text_color(255, 255, 255)
                    pdf.cell(0, 8, f" SECCIÓN: {h.upper()}", ln=True, fill=True, border=1)
                    pdf.set_text_color(0, 0, 0)
                    
                    # Lógica de Ancho de Columnas Dinámico
                    pdf.set_font("Helvetica", 'B', 6)
                    cols = data.columns.tolist()
                    ancho_total = 277 # mm disponibles en A4 horizontal
                    
                    # Asignamos más espacio a columnas con mucho texto (como Nombres o Direcciones)
                    anchos = []
                    for c in cols:
                        if c.upper() in ['NOMBRE', 'DIRECCIÓN FISCAL', 'VIA', 'JUNTA', 'DESCRIPCION']:
                            anchos.append(ancho_total * 0.25 if len(cols) < 10 else ancho_total * 0.15)
                        else:
                            # Reparto equitativo del resto
                            anchos.append((ancho_total * 0.5) / (len(cols) - 1) if len(cols) > 1 else ancho_total)
                    
                    # Ajuste proporcional para no pasarse de 277mm
                    factor_ajuste = ancho_total / sum(anchos)
                    anchos = [a * factor_ajuste for a in anchos]

                    # Dibujar Cabeceras
                    pdf.set_fill_color(230, 230, 230)
                    for i, col in enumerate(cols):
                        pdf.cell(anchos[i], 6, str(col)[:12], border=1, align='C', fill=True)
                    pdf.ln()

                    # Dibujar Filas con fuente minificada para que quepa todo
                    pdf.set_font("Helvetica", size=5.5)
                    for _, fila in data.iterrows():
                        for i, col in enumerate(cols):
                            # Truncar texto para evitar superposición
                            contenido = str(fila[col])[:25] 
                            pdf.cell(anchos[i], 5, contenido, border=1, align='C')
                        pdf.ln()
                    pdf.ln(4)

                pdf_output = pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)

                st.download_button(
                    label="⬇️ Descargar Reporte PDF Optimizado",
                    data=pdf_bytes,
                    file_name=f"Reporte_{valor}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error generando el PDF: {e}")
    else:
        st.warning("No se encontraron resultados para esa búsqueda.")
