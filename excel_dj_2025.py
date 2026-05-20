import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema de Consulta Rápida Declaracion Jurada 2025 - ICA demo.v1", page_icon="🏛️", layout="wide")
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 2. LÓGICA DE ACCESO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
    password = st.text_input("Ingrese la clave del sistema:", type="password")
    if st.button("Ingresar al Sistema"):
        if password == CLAVE_SISTEMA:
            st.session_state['autenticado'] = True
            st.rerun()
        else: st.error("❌ Clave incorrecta")
    st.stop()

# --- 3. DICCIONARIO DE COLUMNAS ---
columnas_especificas = {
    'Contribuyente': ['CODIGO', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'Vía', 'Junta', 'NUM_MANZ', 'NUM_LOTE', 'SUB_LOTE', 'NUM_CALL', 'NUM_DEPA', 'Condicion Propieda', 'Descripcion Uso', 'NUM_PISOS', 'NUM_CONDO', 'AREA_TERRENO', 'AREA_COMUN', 'PORCEN_PROPIEDAD'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion', 'CATE_MUROS', 'CATE_TECHO', 'CATE_PISOS', 'CATE_PUERT', 'CATE_REVES', 'CATE_BANNO', 'CATE_INSEL', 'AREA_CONST', 'POR_COMUN', 'AREA_COMUN'],
    'Instalaciones': ['CODIGO', 'COD_PRED', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'CANTIDAD', 'VAL_INSTALAC', 'UNI_MEDIDA']
}

# --- 4. CARGA DE DATOS ---
@st.cache_data(show_spinner="⏳ Sincronizando con la Base de Datos en la Nube...")
def cargar_datos_desde_drive(file_id):
    try:
        output = "archivo_local.xlsx"
        gdown.download(f'https://drive.google.com/uc?id={file_id}', output, quiet=True)
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        datos = {h: pd.read_excel(output, sheet_name=h, engine='openpyxl', dtype=str).fillna("") for h in excel_reader.sheet_names}
        return datos, excel_reader.sheet_names
    except Exception as e: return None, str(e)

if 'base_datos' not in st.session_state:
    datos, hojas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)
    if datos:
        st.session_state['base_datos'] = datos
        st.session_state['hojas'] = hojas
    else: st.error(f"🛑 Error: {hojas}"); st.stop()

archivo_excel = st.session_state['base_datos']
nombres_hojas = st.session_state['hojas']

# --- 5. INTERFAZ Y BUSCADOR ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
if st.button("🚪 Salir"): st.session_state['autenticado'] = False; st.rerun()
st.success("✅ Sincronizado correctamente con la Base de Datos en la Nube")
st.write("---")

modo = st.radio("Criterio:", ["1.- POR COD_CONTRIBUYENTE", "2.- POR COD_PREDIO", "3.- POR NOMBRE / RAZÓN SOCIAL", "4.- POR UBICACIÓN URBANA"], horizontal=True)

codigos_amarre = set()
ejecutar_busqueda = False
resultados = {}

if "1.- POR COD_CONTRIBUYENTE" in modo:
    val = st.text_input("Ingrese Código:").strip()
    if val: codigos_amarre.add(val.lstrip('0')); ejecutar_busqueda = True
elif "2.- POR COD_PREDIO" in modo:
    val = st.text_input("Cod. Predio:").strip()
    if val: codigos_amarre.add(val.lstrip('0')); ejecutar_busqueda = True
elif "3.- POR NOMBRE / RAZÓN SOCIAL" in modo:
    val = st.text_input("Nombre / Razón Social:").upper().strip()
    if val:
        df_cont = archivo_excel.get('Contribuyente')
        if df_cont is not None and 'Nombre' in df_cont.columns and 'CODIGO' in df_cont.columns:
            palabras = [p for p in val.split() if p.strip() != ""]
            mask = df_cont['Nombre'].str.upper().apply(lambda x: all(p in str(x) for p in palabras))
            codigos_amarre.update(df_cont[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
            ejecutar_busqueda = True
elif "4.- POR UBICACIÓN URBANA" in modo:
    c1, c2, c3 = st.columns(3)
    urb = c1.text_input("URB:").upper().strip()
    mz = c2.text_input("MZ:").strip()
    lt = c3.text_input("LT:").strip()
    if urb:
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'Junta' in df_pred.columns:
            mask = df_pred['Junta'].str.upper().str.contains(urb, na=False)
            if mz: mask &= (df_pred['NUM_MANZ'].str.lstrip('0') == mz.lstrip('0'))
            if lt: mask &= (df_pred['NUM_LOTE'].str.lstrip('0') == lt.lstrip('0'))
            codigos_amarre.update(df_pred[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
            ejecutar_busqueda = True

# --- 6. PROCESAMIENTO ---
if ejecutar_busqueda:
    for h in nombres_hojas:
        df = archivo_excel[h]
        if 'CODIGO' in df.columns:
            res = df[df['CODIGO'].str.strip().str.lstrip('0').isin(codigos_amarre)]
            if not res.empty:
                cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                resultados[h] = res[cols]
    
    if resultados:
        for h, df_res in resultados.items():
            with st.expander(f"📋 {h}", expanded=True):
                st.dataframe(df_res, use_container_width=True)
    else: st.warning("No se encontraron registros vinculados.")
