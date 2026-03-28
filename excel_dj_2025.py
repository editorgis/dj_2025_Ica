import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Catastro ICA 2025", layout="wide")

# --- DICCIONARIO DE CABECERAS ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

st.title("🏛️ SISTEMA DE CONSULTA DECLARACION JURADA 2025 - ICA")

# --- CARGA DE DATOS ---
archivo_subido = st.sidebar.file_uploader("📂 Seleccione el archivo Catastro10102025.xlsx", type=["xlsx"])

if archivo_subido:
    @st.cache_data(show_spinner="⏳ CARGANDO BASE DE DATOS...")
    def cargar_excel(file):
        excel_reader = pd.ExcelFile(file, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        archivo_excel = {}
        for hoja in nombres_hojas:
            archivo_excel[hoja] = pd.read_excel(file, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("")
        return archivo_excel, nombres_hojas

    archivo_excel, pestanas = cargar_excel(archivo_subido)
    st.sidebar.success("✅ Base de datos cargada")

    # --- BÚSQUEDA ---
    col_op1, col_op2 = st.columns(2)
    with col_op1:
        opcion = st.radio("Seleccione una opción:", ["1. Buscar por CODIGO", "2. Buscar por COD_PRED"])
    
    columna_objetivo = 'CODIGO' if "1" in opcion else 'COD_PRED'
    
    with col_op2:
        entrada_usuario = st.text_input(f"Ingrese el {columna_objetivo}:").strip().lstrip('0')

    if entrada_usuario:
        encontrado_total = 0
        resultados_acumulados = {}

        for nombre in pestanas:
            df_temp = archivo_excel[nombre]
            col_id = next((c for c in df_temp.columns if c.upper() == columna_objetivo.upper()), None)
            
            if col_id:
                mask = df_temp[col_id].str.strip().str.lstrip('0') == entrada_usuario
                resultado = df_temp[mask]
                
                if not resultado.empty:
                    st.markdown(f"### Pestaña: **{nombre}**")
                    cols = [c for c in columnas_especificas.get(nombre, resultado.columns) if c in resultado.columns]
                    df_ver = resultado[cols]
                    resultados_acumulados[nombre] = df_ver
                    st.dataframe(df_ver, use_container_width=True)
                    encontrado_total += len(resultado)

        if encontrado_total > 0:
            st.success(f"Se encontraron {encontrado_total} registros.")
            
            # --- GENERACIÓN DE PDF CORREGIDA ---
            if st.button("📄 Generar Reporte PDF"):
                try:
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    pdf.set_margins(8, 8, 8)
                    pdf.add_page()
                    
                    pdf.set_font("Helvetica", 'B', 14) # Cambiado a Helvetica para evitar líos de fuentes
                    pdf.cell(0, 10, "DISTRITO DE ICA - PADRON 2025", ln=True, align='C')
                    pdf.ln(5)

                    for pestana, datos in resultados_acumulados.items():
                        pdf.set_font("Helvetica", 'B', 8)
                        pdf.set_fill_color(180, 180, 180) 
                        pdf.cell(0, 6, f"SECCIÓN: {pestana.upper()}", ln=True, fill=True, border=1, align='C')
                        
                        # Cálculo de anchos
                        pdf.set_font("Helvetica", 'B', 5)
                        anchos_requeridos = []
                        for col in datos.columns:
                            w_header = pdf.get_string_width(str(col)) + 4
                            w_content = datos[col].astype(str).map(pdf.get_string_width).max() + 3
                            anchos_requeridos.append(max(w_header, w_content))
                        
                        ancho_total_disponible = pdf.w - 16
                        coeficiente = ancho_total_disponible / sum(anchos_requeridos)
                        anchos_finales = [w * coeficiente for w in anchos_requeridos]

                        # Cabeceras
                        pdf.set_font("Helvetica", 'B', 5.5) 
                        pdf.set_fill_color(240, 240, 240) 
                        for i, col in enumerate(datos.columns):
                            pdf.cell(anchos_finales[i], 5, str(col), border=1, align='C', fill=True)
                        pdf.ln()

                        # Filas
                        pdf.set_font("Helvetica", size=5)
                        for _, fila in datos.iterrows():
                            for i, col in enumerate(datos.columns):
                                contenido = str(fila[col])[:45] 
                                pdf.cell(anchos_finales[i], 4, contenido, border=1, align='C')
                            pdf.ln()
                        pdf.ln(6) 

                    # EXTRACCIÓN DE BYTES (Corrección para fpdf2 en Streamlit)
                    pdf_output = pdf.output() 
                    
                    st.download_button(
                        label="⬇️ Descargar Reporte PDF",
                        data=pdf_output,
                        file_name=f"Reporte_{entrada_usuario}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error al generar PDF: {e}")
        else:
            st.warning("No se encontraron registros.")
else:
    st.info("👋 Por favor, suba el archivo Excel en la barra lateral.")
