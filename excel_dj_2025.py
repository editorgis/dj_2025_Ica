import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Consulta Rápida Declaracion Jurada 2025 - ICA demo.v1", page_icon="🏛️", layout="wide")

# --- 2. CONFIGURACIÓN PROTEGIDA (SECRETS) ---
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 3. LÓGICA DE ACCESO (ESTRUCTURA ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos.</p>", unsafe_allow_html=True)
    st.write("---")
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

# --- 5. FUNCIÓN DE CARGA CONTROLADA ---
@st.cache_data(show_spinner="⏳ Sincronizando con la Base de Datos en la Nube...")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
        ruta_descarga = gdown.download(url, output, quiet=True)
        if not ruta_descarga or not os.path.exists(output):
            return None, "No se pudo descargar el archivo."
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {}
        for hoja in nombres_hojas:
            df_hoja = pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("")
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
        st.error(f"🛑 ERROR: {hojas}")
        st.stop()

archivo_excel = st.session_state['base_datos']
nombres_hojas = st.session_state['hojas']

# --- 7. INTERFAZ VISUAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
if st.button("🚪 Salir"):
    st.session_state['autenticado'] = False
    st.rerun()

st.write("---") 

# --- 8. BUSCADOR INTERACTIVO ---
modo = st.radio("Seleccione el criterio de búsqueda:", ["1.- POR COD_CONTRIBUYENTE", "2.- POR COD_PREDIO", "3.- POR NOMBRE / RAZÓN SOCIAL", "4.- POR UBICACIÓN URBANA"], horizontal=True)

codigos_contribuyente_encontrados = set()
codigos_predio_encontrados = set()
ejecutar_busqueda = False
valor_reporte = ""
resultados = {}

if "1.- POR COD_CONTRIBUYENTE" in modo:
    valor = st.text_input("Ingrese Código:").strip()
    if valor: codigos_contribuyente_encontrados.add(valor.lstrip('0')); ejecutar_busqueda = True; valor_reporte = valor
elif "2.- POR COD_PREDIO" in modo:
    valor = st.text_input("Ingrese Cod. Predio:").strip()
    if valor: codigos_predio_encontrados.add(valor.lstrip('0')); ejecutar_busqueda = True; valor_reporte = valor
elif "3.- POR NOMBRE / RAZÓN SOCIAL" in modo:
    valor = st.text_input("Ingrese Nombre / Razón Social:").upper().strip()
    if valor:
        df_cont = archivo_excel.get('Contribuyente')
        palabras = [p for p in valor.split() if p.strip() != ""]
        mask = df_cont['Nombre'].str.upper().apply(lambda x: all(p in str(x) for p in palabras))
        codigos_contribuyente_encontrados.update(df_cont[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
        ejecutar_busqueda = True; valor_reporte = valor
elif "4.- POR UBICACIÓN URBANA" in modo:
    col1, col2, col3 = st.columns(3)
    urb = col1.text_input("URB:").upper().strip()
    mz = col2.text_input("MZ:").strip()
    lt = col3.text_input("LT:").strip()
    if urb:
        df_pred = archivo_excel.get('Predios')
        mask = df_pred['Junta'].str.upper().str.contains(urb, na=False)
        if mz: mask &= (df_pred['NUM_MANZ'].str.lstrip('0') == mz.lstrip('0'))
        if lt: mask &= (df_pred['NUM_LOTE'].str.lstrip('0') == lt.lstrip('0'))
        codigos_contribuyente_encontrados.update(df_pred[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
        ejecutar_busqueda = True; valor_reporte = f"{urb}_{mz}_{lt}"

# --- 9. FASE DE PROCESAMIENTO Y AMARRE ---
if ejecutar_busqueda:
    for h in nombres_hojas:
        df = archivo_excel[h]
        # Amarre por CODIGO maestro
        if codigos_contribuyente_encontrados and 'CODIGO' in df.columns:
            res = df[df['CODIGO'].str.strip().str.lstrip('0').isin(codigos_contribuyente_encontrados)]
        # Contingencia por COD_PREDIO
        elif codigos_predio_encontrados and 'COD_PRED' in df.columns:
            res = df[df['COD_PRED'].str.strip().str.lstrip('0').isin(codigos_predio_encontrados)]
        else: continue
        
        if not res.empty:
            cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
            resultados[h] = res[cols]

    for h, df_res in resultados.items():
        with st.expander(f"📋 {h}", expanded=True):
            st.dataframe(df_res, use_container_width=True)
