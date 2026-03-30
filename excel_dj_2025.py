import streamlit as st
import pandas as pd
from fpdf import FPDF
import gdown
from datetime import datetime

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema de Consulta Declaracion Jurada 2025 - ICA demo.v1</h1", page_icon="🏛️", layout="wide")

# --- 2. CONFIGURACIÓN PROTEGIDA (SECRETS) ---
CLAVE_SISTEMA = st.secrets["CLAVE_SISTEMA"]
ID_ARCHIVO_DRIVE = st.secrets["ID_ARCHIVO_DRIVE"] 

# --- 3. LÓGICA DE ACCESO (ESTRUCTURA ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # Título Principal
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
    
    # SUBTÍTULO DE AVISO LEGAL
    st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos.</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Pantalla de Bloqueo con CANDADO DORADO
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
        gdown.download(url, output, quiet=True, fuzzy=True)
        excel_reader = pd.ExcelFile(output, engine='openpyxl')
        nombres_hojas = excel_reader.sheet_names
        datos = {hoja: pd.read_excel(output, sheet_name=hoja, engine='openpyxl', dtype=str).fillna("") for hoja in nombres_hojas}
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
        st.error(f"Error de conexión: {hojas}")
        st.stop()

archivo_excel = st.session_state['base_datos']
nombres_hojas = st.session_state['hojas']

# --- 7. INTERFAZ VISUAL (DENTRO DEL SISTEMA) ---
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos</p>", unsafe_allow_html=True)

col_status, _, col_logout = st.columns([2, 5, 1])
with col_status:
    st.success("✅ Base de datos conectada")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

st.write("---") 

# --- 8. BUSCADOR ---
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
        
        if st.button("📄 Generar Reporte PDF"):
            try:
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 16)
                pdf.cell(0, 10, "REPORTE DECLARACION JURADA 2025 - ICA", ln=True, align='C')
                pdf_output = pdf.output(dest='S')
                pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)
                st.download_button(label="⬇️ Descargar Reporte PDF", data=pdf_bytes, file_name=f"Reporte_{valor}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error en PDF: {e}")
    else:
        st.warning("⚠️ No se tiene registro")
