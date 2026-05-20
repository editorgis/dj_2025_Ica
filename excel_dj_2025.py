import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Consulta Rápida Declaracion Jurada 2025 - ICA demo.v1", page_icon="🏛️", layout="wide")

# --- 2. CONFIGURACIÓN PROTEGIDA (SECRETS) ---
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 3. LÓGICA DE ACCESO (ESTRUCTURA ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # Título Principal
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
    
    # SUBTÍTULO DE AVISO LEGAL
    st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos.</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Pantalla de Restricción
    st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>🔐 ACCESO RESTRINGIDO</h2>", unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1, 1])
    with col_login:
        password = st.text_input("Ingrese la clave del sistema:", type="password")
        if st.button("Ingresar al Sistema"):
            if password == CLAVE_SISTEMA:
                st.session_state['autenticado'] = True
                st.rerun()
            else:
                st.error("❌ Clave incorrecta")
    st.stop()

# --- 4. DICCIONARIO DE COLUMNAS (FILTROS) ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

# --- 5. FUNCIÓN DE CARGA ---
@st.cache_data(show_spinner="⏳ Sincronizando con la Base de Datos...")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
        gdown.download(url, output, quiet=True)
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        
        datos = {}
        for hoja in nombres_hojas:
            df_hoja = pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("")
            # Estandarización exhaustiva de espacios en blanco
            for col in df_hoja.columns:
                df_hoja[col] = df_hoja[col].astype(str).str.strip()
            datos[hoja] = df_hoja
            
        return datos, nombres_hojas
    except Exception as e:
        return None, str(e)

# --- 6. LÓGICA DE PERSISTENCIA ---
if 'base_datos' not in st.session_state:
    datos, hojas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)
    if datos is not None:
        st.session_state['base_datos'] = datos
        st.session_state['hojas'] = hojas
    else:
        st.error(f"Error de conexión con Google Drive: {hojas}")
        st.stop()

archivo_excel = st.session_state['base_datos']
nombres_hojas = st.session_state['hojas']

# --- 7. INTERFAZ VISUAL PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos</p>", unsafe_allow_html=True)

col_status, _, col_logout = st.columns([3, 4, 1])
with col_status:
    st.success("✅ Sincronizado correctamente con la Base de Datos en la Nube")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

st.write("---") 

# --- 8. BUSCADOR INTERACTIVO CON ENFOQUE DE PRELACIÓN ---
st.markdown("### 🔍 Panel de Consulta de Información Cadastral")

modo = st.radio(
    "Seleccione el criterio de búsqueda requerido:",
    [
        "1.- POR COD_CONTRIBUYENTE", 
        "2.- POR COD_PREDIO", 
        "3.- POR NOMBRE / RAZÓN SOCIAL", 
        "4.- POR UBICACIÓN URBANA"
    ],
    horizontal=True
)

st.markdown("---")

# Estructuras de control para el amarre estricto
codigos_contribuyente_encontrados = set()
codigos_predio_encontrados = set()
ejecutar_busqueda = False
valor_reporte = ""
resultados = {}

# -----------------------------------------------------------------------------
# CRITERIO 1: POR CÓDIGO DE CONTRIBUYENTE
# -----------------------------------------------------------------------------
if "1.- POR COD_CONTRIBUYENTE" in modo:
    valor = st.text_input("Ingrese Código de Contribuyente (Exacto):", placeholder="Ej. 0012345").strip()
    if valor:
        valor_limpio = valor.lstrip('0')
        codigos_contribuyente_encontrados.add(valor_limpio)
        valor_reporte = valor
        ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 2: POR CÓDIGO DE PREDIO
# -----------------------------------------------------------------------------
elif "2.- POR COD_PREDIO" in modo:
    valor = st.text_input("Ingrese Código de Predio (Exacto):", placeholder="Ej. P-009876").strip()
    if valor:
        valor_limpio = valor.lstrip('0')
        codigos_predio_encontrados.add(valor_limpio)
        valor_reporte = valor
        ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 3: POR NOMBRE / RAZÓN SOCIAL
# -----------------------------------------------------------------------------
elif "3.- POR NOMBRE / RAZÓN SOCIAL" in modo:
    valor = st.text_input("Ingrese Nombre, Apellidos o Razón Social (Búsqueda Parcial):", placeholder="Ej. LUIS ALBERTO SANCHEZ").upper().strip()
    if valor:
        df_cont = archivo_excel.get('Contribuyente')
        if df_cont is not None and 'Nombre' in df_cont.columns and 'CODIGO' in df_cont.columns:
            palabras_clave = valor.split()
            mask = df_cont['Nombre'].str.upper().apply(lambda x: all(palabra in str(x) for palabra in palabras_clave))
            cods = df_cont[mask]['CODIGO'].str.strip().str.lstrip('0').unique()
            codigos_contribuyente_encontrados.update(cods)
            valor_reporte = valor
            ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 4: POR UBICACIÓN URBANA (PRELACIÓN DE PREDIO -> FILTRA TODO POR 'CODIGO')
# -----------------------------------------------------------------------------
elif "4.- POR UBICACIÓN URBANA" in modo:
    st.markdown("##### 📍 Ingrese los parámetros de Ubicación Territorial")
    col_urb, col_mz, col_lt = st.columns([4, 2, 2])
    
    with col_urb:
        urb_ingresada = st.text_input("URB (JUNTA / URBANIZACIÓN):", placeholder="Ej. CERCADO DE ICA").upper().strip()
    with col_mz:
        mz_ingresada = st.text_input("MZ (MANZANA):", placeholder="Ej. D").upper().strip()
    with col_lt:
        lote_ingresado = st.text_input("LOTE:", placeholder="Ej. 11").upper().strip()
        
    if urb_ingresada:
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None:
            # PASO 1: Filtrar EXCLUSIVAMENTE en la pestaña de Predios
            mask_pred = df_pred['Junta'].str.upper().str.contains(urb_ingresada, na=False)
            if mz_ingresada:
                mask_pred = mask_pred & (df_pred['NUM_MANZ'].str.lstrip('0') == mz_ingresada.lstrip('0'))
            if lote_ingresado:
                mask_pred = mask_pred & (df_pred['NUM_LOTE'].str.lstrip('0') == lote_ingresado.lstrip('0'))
            
            df_pred_filtrado = df_pred[mask_pred]
            
            if not df_pred_filtrado.empty:
                # PASO 2: Extraer de manera obligatoria el campo 'CODIGO' de la fila de Predio encontrada
                if 'CODIGO' in df_pred_filtrado.columns:
                    cods_c = df_pred_filtrado['CODIGO'].str.strip().str.lstrip('0').unique()
                    cods_c = [c for c in cods_c if c != ""]
                    
                    # Guardamos este registro como el único AMARRE para las demás pestañas
                    codigos_contribuyente_encontrados.update(cods_c)
        
        valor_reporte = f"{urb_ingresada}_MZ_{mz_ingresada}_LT_{lote_ingresado}"
        ejecutar_busqueda = True
    else:
        st.info("💡 Por favor, ingrese al menos el nombre de la **Urbanización / Junta** para delimitar el ámbito geográfico.")

# =============================================================================
# --- FASE DE PROCESAMIENTO GENERAL CON FILTRADO EN CASCADA ---
# =============================================================================
if ejecutar_busqueda:
    total = 0
    
    # Si logramos extraer la llave de amarre ('CODIGO'), esta comanda la prelación en TODAS las pestañas
    if codigos_contribuyente_encontrados:
        for h in nombres_hojas:
            df = archivo_excel[h]
            col_id_contribuyente = next((c for c in df.columns if c.upper() == 'CODIGO'), None)
            
            if col_id_contribuyente:
                # Se filtra cada pestaña obligatoriamente por el 'CODIGO' derivado del predio
                mask_final = df[col_id_contribuyente].str.strip().str.lstrip('0').isin(codigos_contribuyente_encontrados)
                res = df[mask_final]
                
                if not res.empty:
                    cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                    resultados[h] = res[cols]
                    total += len(res)
                    
    # Lógica de contingencia secundaria en caso se busque directamente por Código de Predio (Criterio 2)
    elif codigos_predio_encontrados:
        for h in nombres_hojas:
            df = archivo_excel[h]
            col_id_predio = next((c for c in df.columns if c.upper() == 'COD_PRED'), None)
            
            if col_id_predio:
                mask_final = df[col_id_predio].str.strip().str.lstrip('0').isin(codigos_predio_encontrados)
                res = df[mask_final]
                
                if not res.empty:
                    cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                    resultados[h] = res[cols]
                    total += len(res)

    # --- DESPLIEGUE FINAL DE TABLAS EN PANTALLA ---
    if total > 0:
        st.success(f"🔎 Cruce de datos exitoso. Registros vinculados en cascada: {total}")
        
        # Despliegue ordenado respetando la prelación natural de la base de datos catastral
        for h in nombres_hojas:
            if h in resultados:
                with st.expander(f"📋 Pestaña: {h}", expanded=True):
                    st.dataframe(resultados[h], use_container_width=True)
        
        # --- GENERACIÓN COMPATIBLE DE REPORTE PDF ---
        try:
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, "REPORTE DECLARACION JURADA 2025 - ICA", ln=True, align='C')
            pdf_output = pdf.output(dest='S')
            pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)
            
            st.write("") 
            st.download_button(
                label="⬇️ Descargar Reporte PDF", 
                data=pdf_bytes, 
                file_name=f"Reporte_{valor_reporte.replace(' ', '_')}.pdf", 
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error al generar el reporte PDF: {e}")
    else:
        st.warning("⚠️ No se tienen registros vinculados para el criterio ingresado. Revise los parámetros.")
