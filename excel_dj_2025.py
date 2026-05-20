import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Catastral 2025", layout="wide")
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 2. ACCESO ---
if 'autenticado' not in st.session_state: st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.title("🏛️ SISTEMA DE CONSULTA CATASTRAL")
    password = st.text_input("Clave:", type="password")
    if st.button("Ingresar") and password == CLAVE_SISTEMA:
        st.session_state['autenticado'] = True
        st.rerun()
    st.stop()

# --- 3. CARGA DE DATOS ---
@st.cache_data(show_spinner="Sincronizando...")
def cargar_datos(file_id):
    try:
        output = "data.xlsx"
        gdown.download(f'https://drive.google.com/uc?id={file_id}', output, quiet=True)
        if not os.path.exists(output): return None, "Error: Archivo no descargado."
        excel = pd.ExcelFile(output)
        datos = {h: pd.read_excel(output, sheet_name=h, dtype=str).fillna("") for h in excel.sheet_names}
        for h in datos:
            for col in datos[h].columns: datos[h][col] = datos[h][col].str.strip()
        return datos, excel.sheet_names
    except Exception as e: return None, str(e)

if 'base' not in st.session_state:
    datos, hojas = cargar_datos(ID_ARCHIVO_DRIVE)
    if datos:
        st.session_state['base'] = datos
        st.session_state['hojas'] = hojas
    else:
        st.error(f"Error: {hojas}"); st.stop()

# --- 4. BUSCADOR ---
modo = st.radio("Criterio:", ["1.- COD_CONTRIBUYENTE", "2.- COD_PREDIO", "3.- NOMBRE / RAZÓN SOCIAL", "4.- UBICACIÓN URBANA"], horizontal=True)
codigos_amarre = set()
ejecutar = False
valor_reporte = ""

if "1.- COD_CONTRIBUYENTE" in modo:
    val = st.text_input("Código:").strip()
    if val: codigos_amarre.add(val.lstrip('0')); ejecutar = True; valor_reporte = val
elif "2.- COD_PREDIO" in modo:
    val = st.text_input("Cod. Predio:").strip()
    # Lógica específica para Predio si fuera necesario
    ejecutar = True; valor_reporte = val
elif "3.- NOMBRE / RAZÓN SOCIAL" in modo:
    val = st.text_input("Nombre:").upper().strip()
    if val:
        df = st.session_state['base']['Contribuyente']
        mask = df['Nombre'].str.upper().apply(lambda x: all(p in str(x) for p in val.split()))
        codigos_amarre.update(df[mask]['CODIGO'].str.lstrip('0').unique())
        ejecutar = True; valor_reporte = val
elif "4.- UBICACIÓN URBANA" in modo:
    col1, col2, col3 = st.columns(3)
    urb = col1.text_input("URB:").upper().strip()
    mz = col2.text_input("MZ:").strip()
    lt = col3.text_input("LT:").strip()
    if urb:
        df = st.session_state['base']['Predios']
        mask = df['Junta'].str.upper().str.contains(urb)
        if mz: mask &= (df['NUM_MANZ'].str.lstrip('0') == mz.lstrip('0'))
        if lt: mask &= (df['NUM_LOTE'].str.lstrip('0') == lt.lstrip('0'))
        codigos_amarre.update(df[mask]['CODIGO'].str.lstrip('0').unique())
        ejecutar = True; valor_reporte = f"{urb}_{mz}_{lt}"

# --- 5. PROCESAMIENTO Y VISUALIZACIÓN ---
if ejecutar:
    resultados = {}
    for h in st.session_state['hojas']:
        df = st.session_state['base'][h]
        if 'CODIGO' in df.columns and codigos_amarre:
            res = df[df['CODIGO'].str.lstrip('0').isin(codigos_amarre)]
            if not res.empty: resultados[h] = res
    
    if resultados:
        st.success(f"Registros encontrados: {sum(len(v) for v in resultados.values())}")
        for h, df in resultados.items():
            with st.expander(f"📋 {h}", expanded=True):
                st.dataframe(df, use_container_width=True)
    else:
        st.warning("Sin resultados.")
