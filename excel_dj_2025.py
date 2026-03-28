import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import io

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Sistema Catastro ICA 2025",
    page_icon="🏛️",
    layout="wide"
)

# --- 2. DICCIONARIO DE COLUMNAS (Personalización por pestaña) ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

# Estilo de título
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACION JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
st.write("---")

# --- 3. CARGA DE DATOS ---
st.sidebar.header("Configuración")
archivo_subido = st.sidebar.file_uploader("📂 Suba el archivo Catastro10102025.xlsx", type=["xlsx"])

if archivo_subido:
    @st.cache_data(show_spinner="⏳ Procesando base de datos, por favor espere...")
    def cargar_datos(file):
        excel_reader = pd.ExcelFile(file, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos_completos = {}
        for hoja in nombres_hojas:
            # Cargamos todo como texto y reemplazamos vacíos (NaN) con texto vacío
            df = pd.read_excel(file, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("")
            datos_completos[hoja] = df
        return datos_completos, nombres_hojas

    archivo_excel, pestanas = cargar_datos(archivo_subido)
    st.sidebar.success("✅ Datos cargados correctamente")

    # --- 4. INTERFAZ DE BÚSQUEDA ---
    col_radio, col_input = st.columns([1, 1])
    
    with col_radio:
        opcion = st.radio("**Criterio de búsqueda:**", ["1. Por CODIGO (Contribuyente)", "2. Por COD_PRED (Predio)"])
    
    columna_filtro = 'CODIGO' if "1" in opcion else 'COD_PRED'
    
    with col_input:
        # Quitamos ceros a la izquierda para evitar fallos si el usuario digita 00123 en vez de 123
        valor_busqueda = st.text_input(f"Ingrese el {columna_filtro}:").strip().lstrip('0')

    if valor_busqueda:
        resultados_encontrados = {}
        total_registros = 0

        # Buscamos en todas las pestañas
        for nombre in pestanas:
            df_hoja = archivo_excel[nombre]
            
            # Buscamos la columna sin importar si está en mayúsculas o minúsculas
            col_id = next((c for c in df_hoja.columns if c.upper() == columna_filtro.upper()), None)
            
            if col_id:
                # Filtrado eliminando ceros a la izquierda en la base de datos también
                mask = df_hoja[col_id].str.strip().str.lstrip('0') == valor_busqueda
                df_filtrado = df_hoja[mask]
                
                if not df_filtrado.empty:
                    # Seleccionamos solo las columnas importantes definidas arriba
                    cols_a_mostrar = [c for c in columnas_especificas.get(nombre, df_filtrado.columns) if c in df_filtrado.columns]
                    df_final = df_filtrado[cols_a_mostrar]
                    
                    resultados_encontrados[nombre] = df_final
                    total_registros += len(df_final)

        # --- 5. MOSTRAR RESULTADOS Y PDF ---
        if total_registros > 0:
            st.info(f"🔎 Se encontraron {total_registros} registros asociados al {columna_filtro}: {valor_busqueda}")
            
            for nombre_pestana, datos_tabla in resultados_encontrados.items():
                with st.expander(f"📋 Pestaña: {nombre_pestana}", expanded=True):
                    st.dataframe(datos_tabla, use_container_width=True)

            st.write("---")
            
            # --- 6. GENERACIÓN DE REPORTE PDF ---
            if st.button("📄 Generar Reporte PDF para Descarga"):
                try:
                    # Formato A4 Horizontal (Landscape)
                    pdf = FPDF(orientation='L', unit='mm', format='A4')
                    pdf.set_auto_page_break(auto=True, margin=10)
                    pdf.add_page()
                    
                    # Encabezado
                    pdf.set_font("Helvetica", 'B', 16)
                    pdf.cell(0, 10, "REPORTE DE CATASTRO - ICA 2025", ln=True, align='C')
                    pdf.set_font("Helvetica", '', 10)
                    pdf.cell(0, 8, f"Consulta realizada por {columna_filtro}: {valor_busqueda}", ln=True, align='C')
                    pdf.cell(0, 5, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
                    pdf.ln(10)

                    for hoja, df_datos in resultados_encontrados.items():
                        # Título de Sección
                        pdf.set_font("Helvetica", 'B', 10)
                        pdf.set_fill_color(30, 58, 138) # Azul oscuro
                        pdf.set_text_color(255, 255, 255) # Blanco
                        pdf.cell(0, 8, f" SECCIÓN: {hoja.upper()}", ln=True, fill=True, border=1)
                        pdf.set_text_color(0, 0, 0) # Volver a Negro

                        # Cálculo dinámico de anchos
                        pdf.set_font("Helvetica", 'B', 6)
                        anchos = []
                        for col in df_datos.columns:
                            w_head = pdf.get_string_width(str(col)) + 4
                            w_data = df_datos[col].astype(str).map(pdf.get_string_width).max() + 4
                            anchos.append(max(w_head, w_data))
                        
                        # Ajuste proporcional al ancho de página
                        ancho_pag = pdf.w - 20
                        scale = ancho_pag / sum(anchos)
                        anchos_f = [w * scale for w in anchos]

                        # Cabecera de Tabla
                        pdf.set_fill_color(220, 220, 220)
                        for i, col in enumerate(df_datos.columns):
                            pdf.cell(anchos_f[i], 6, str(col), border=1, align='C', fill=True)
                        pdf.ln()

                        # Cuerpo de Tabla
                        pdf.set_font("Helvetica", size=6)
                        for _, fila in df_datos.iterrows():
                            # Verificar si la fila cabe, si no, nueva página
                            if pdf.get_y() > 180:
                                pdf.add_page()
                            
                            for i, col in enumerate(df_datos.columns):
                                texto_celda = str(fila[col])[:50] # Truncar si es muy largo
                                pdf.cell(anchos_f[i], 5, texto_celda, border=1, align='C')
                            pdf.ln()
                        pdf.ln(8)

                    # --- CORRECCIÓN CRÍTICA PARA STREAMLIT CLOUD ---
                    # Obtenemos el bytearray y lo convertimos a un objeto de bytes puro
                    resultado_pdf = bytes(pdf.output())
                    
                    st.download_button(
                        label="✅ Descargar PDF Ahora",
                        data=resultado_pdf,
                        file_name=f"Reporte_{valor_busqueda}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"Se produjo un error al generar el PDF: {e}")
        else:
            st.warning(f"No se encontró información para el {columna_filtro} ingresado.")
else:
    st.info("👋 Bienvenido. Por favor, cargue el archivo Excel (.xlsx) en el menú lateral para habilitar las consultas.")

# Pie de página
st.markdown("---")
st.caption("Visor Catastral ICA 2025 - Desarrollado para gestión remota.")
