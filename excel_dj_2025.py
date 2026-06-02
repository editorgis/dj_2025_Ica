import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
import os

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Consulta Rápida Declaracion Jurada 2025 - ICA demo.v2", page_icon="🏛️", layout="wide")

# --- 2. CONFIGURACIÓN PROTEGIDA (SECRETS) ---
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 3. LÓGICA DE ACCESO (ESTRUCTURA ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA demo.v2</h1>", unsafe_allow_html=True)
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

# --- 4. DICCIONARIO DE COLUMNAS ACTUALIZADO (CABECERAS REALES) ---
columnas_especificas = {
    'Contribuyente': ['Codigo', 'Nombre', 'Dirección Fiscal', 'Junta', 'Dni', 'Correo'],
    'Predios': ['CODIGO', 'COD_PRED', 'TipoPredio', 'ANEXO', 'SUB_ANEXO', 'ID_VIA', 'Vía', 'ID_URBA', 'Junta', 'NUM_MANZ'],
    'Pisos': ['CODIGO', 'COD_PRED', 'ANEXO', 'SUB_ANEXO', 'ITEM_PISO', 'NIV_PISO', 'TIPO_NIVEL', 'TipoNivel', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG', 'ID_CLAFICA', 'Clasifica', 'ID_MATERIA', 'Material', 'ID_ESTADOS', 'Conservacion'],
    'Instalaciones': ['CODIGO', 'ITEM_INSTALACION', 'COD_PRED', 'ANEXO', 'SUB_ANEXO', 'ID_INSTALA', 'Descripcion', 'MES_CONS', 'ANO_CONS', 'ANNO_ANTIG']
}

# --- 5. FUNCIÓN DE CARGA CONTROLADA ---
@st.cache_data(show_spinner="⏳ Sincronizando con la Base de Datos")
def cargar_datos_desde_drive(file_id):
    try:
        url = f'https://drive.google.com/uc?id={file_id}'
        output = "archivo_local.xlsx"
        ruta_descarga = gdown.download(url, output, quiet=True)
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        datos = {h: pd.read_excel(output, sheet_name=h, engine='openpyxl', dtype=str).fillna("") for h in excel_reader.sheet_names}
        return datos, excel_reader.sheet_names
    except Exception as e: return None, str(e)

# --- 6. LÓGICA DE PERSISTENCIA REAL ---
if 'base_datos' not in st.session_state:
    datos, hojas = cargar_datos_desde_drive(ID_ARCHIVO_DRIVE)
    if datos is not None:
        st.session_state['base_datos'] = datos
        st.session_state['hojas'] = hojas
    else: st.error("Error al cargar"); st.stop()

archivo_excel = st.session_state['base_datos']
nombres_hojas = st.session_state['hojas']

# --- 7. INTERFAZ VISUAL ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos</p>", unsafe_allow_html=True)

col_status, _, col_logout = st.columns([3, 4, 1])
with col_status:
    st.success("✅ Sincronizado correctamente con la Base de Datos 2025 ")
with col_logout:
    if st.button("🚪 Salir"): st.session_state['autenticado'] = False; st.rerun()

st.write("---") 

# --- 8. BUSCADOR INTERACTIVO ---
st.markdown("### 🔍 Panel de Consulta de Información DJ Municipal")
modo = st.radio("Seleccione el criterio de búsqueda requerido:", ["1.- POR COD_CONTRIBUYENTE", "2.- POR COD_PREDIO", "3.- POR NOMBRE / RAZÓN SOCIAL", "4.- POR UBICACIÓN URBANA"], horizontal=True)
st.markdown("---")

codigos_amarre = set()
ejecutar_busqueda = False
valor_reporte = ""

# Determinar dinámicamente el nombre de la columna llave por pestaña
def obtener_columna_codigo(nombre_hoja):
    return 'Codigo' if nombre_hoja == 'Contribuyente' else 'CODIGO'

if "1.- POR COD_CONTRIBUYENTE" in modo:
    val = st.text_input("Ingrese Código:").strip()
    if val: 
        codigos_amarre.add(val.lstrip('0'))
        ejecutar_busqueda = True
        valor_reporte = val

elif "2.- POR COD_PREDIO" in modo:
    val = st.text_input("Cod. Predio:").strip()
    if val:
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'COD_PRED' in df_pred.columns:
            # Encontramos las filas que correspondan al código de predio buscado
            mask_predio = df_pred['COD_PRED'].str.strip().str.lstrip('0') == val.lstrip('0')
            # Extraemos los códigos de contribuyente vinculados a ese predio físico
            codigos_encontrados = df_pred[mask_predio]['CODIGO'].str.strip().str.lstrip('0').unique()
            if len(codigos_encontrados) > 0:
                codigos_amarre.update(codigos_encontrados)
                ejecutar_busqueda = True
                valor_reporte = val
            else:
                st.warning("⚠️ No se encontró ningún código de contribuyente asociado a ese predio.")

elif "3.- POR NOMBRE / RAZÓN SOCIAL" in modo:
    val = st.text_input("Ingrese Nombre / Razón Social:").upper().strip()
    if val:
        df_cont = archivo_excel.get('Contribuyente')
        if df_cont is not None and 'Nombre' in df_cont.columns:
            palabras = [p for p in val.split() if p.strip() != ""]
            mask = df_cont['Nombre'].str.upper().apply(lambda x: all(p in str(x) for p in palabras))
            # Rescatamos el campo llave dinámico ('Codigo' para Contribuyente)
            codigos_amarre.update(df_cont[mask]['Codigo'].str.strip().str.lstrip('0').unique())
            ejecutar_busqueda = True
            valor_reporte = val

elif "4.- POR UBICACIÓN URBANA" in modo:
    c1, c2, c3 = st.columns([4, 2, 2])
    urb = c1.text_input("URB:").upper().strip()
    mz = c2.text_input("MZ:").strip()
    lt = c3.text_input("LT:").strip()
    if urb or mz or lt:
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'CODIGO' in df_pred.columns:
            mask = pd.Series([True] * len(df_pred))
            # Filtro por urbanización mapeado a la columna real ID_URBA
            if urb and 'ID_URBA' in df_pred.columns: 
                mask &= df_pred['ID_URBA'].str.upper().str.contains(urb, na=False)
            # Filtro por manzana mapeado a la columna real NUM_MANZ
            if mz and 'NUM_MANZ' in df_pred.columns: 
                mask &= (df_pred['NUM_MANZ'].str.strip().str.lstrip('0') == mz.lstrip('0'))
            # Filtro opcional por lote si estuviera más a la derecha
            if lt and 'NUM_LOTE' in df_pred.columns: 
                mask &= (df_pred['NUM_LOTE'].str.strip().str.lstrip('0') == lt.lstrip('0'))
            
            codigos_amarre.update(df_pred[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
            ejecutar_busqueda = True
            valor_reporte = f"{urb}_{mz}_{lt}"

# --- 9. PROCESAMIENTO Y FILTRADO MAESTRO (EL BARRIDO EN CASCADA) ---
if ejecutar_busqueda:
    total = 0
    # Recorremos cada pestaña del Excel de manera integral
    for h in nombres_hojas:
        df = archivo_excel[h]
        col_llave = obtener_columna_codigo(h)
        
        if col_llave in df.columns:
            # El algoritmo realiza el barrido cruzando los códigos del amarre normalizados
            res = df[df[col_llave].str.strip().str.lstrip('0').isin(codigos_amarre)]
            if not res.empty:
                cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                with st.expander(f"📋 Pestaña: {h}", expanded=True):
                    st.dataframe(res[cols], use_container_width=True)
                total += len(res)
                
    if total > 0: 
        st.success(f"🔎 Cruce de datos exitoso. Registros vinculados encontrados a través de la Llave: {total}")
    else: 
        st.warning("⚠️ No se encontraron registros vinculados en las pestañas con los criterios ingresados.")
