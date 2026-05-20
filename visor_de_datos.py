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
        gdown.download(url, output, quiet=True)
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
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA demo.v1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información reservada. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos</p>", unsafe_allow_html=True)

col_status, _, col_logout = st.columns([2, 5, 1])
with col_status:
    st.success("✅ Base de datos conectada 'Catastro10102025.xlsx' ")
with col_logout:
    if st.button("🚪 Salir"):
        st.session_state['autenticado'] = False
        st.rerun()

st.write("---") 

# --- 8. BUSCADOR INTERACTIVO AVANZADO ---
c1, c2 = st.columns(2)
with c1:
    modo = st.radio(
        "**Seleccione Criterio de Búsqueda:**", 
        [
            "1. Por COD_CONTRIBUYENTE", 
            "2. Por COD_PREDIO", 
            "3. Por Nombre / Razón Social", 
            "4. Por Junta / Urbanización", 
            "5. Por Número de Manzana", 
            "6. Por Número de Lote"
        ]
    )

with c2:
    # Ajustamos dinámicamente el texto de la caja según la opción marcada
    label_input = "Ingrese el dato a buscar:"
    if "1" in modo: label_input = "Ingrese COD_CONTRIBUYENTE (Suelte ceros):"
    elif "2" in modo: label_input = "Ingrese COD_PREDIO (Suelte ceros):"
    elif "3" in modo: label_input = "Ingrese Nombre o Apellido:"
    elif "4" in modo: label_input = "Ingrese Nombre de la Junta / Sector:"
    elif "5" in modo: label_input = "Ingrese Número de Manzana (NUM_MANZ):"
    elif "6" in modo: label_input = "Ingrese Número de Lote (NUM_LOTE):"
    
    valor = st.text_input(label_input).strip()

if valor:
    # Set de llaves cruzadas para recolectar las referencias amarradas
    codigos_contribuyente_encontrados = set()
    codigos_predio_encontrados = set()
    
    valor_upper = valor.upper()
    valor_limpio = valor.lstrip('0')
    
    # --- FASE A: RECOLECCIÓN DE LLAVES (EL AMARRE) ---
    if "1" in modo:
        codigos_contribuyente_encontrados.add(valor_limpio)
        
    elif "2" in modo:
        codigos_predio_encontrados.add(valor_limpio)
        
    elif "3" in modo:
        # Buscar en la pestaña 'Contribuyente' y extraer su llave ('CODIGO')
        df_cont = archivo_excel.get('Contribuyente')
        if df_cont is not None and 'Nombre' in df_cont.columns and 'CODIGO' in df_cont.columns:
            mask = df_cont['Nombre'].str.upper().str.contains(valor_upper, na=False)
            cods = df_cont[mask]['CODIGO'].str.strip().str.lstrip('0').unique()
            codigos_contribuyente_encontrados.update(cods)

    elif "4" in modo:
        # 'Junta' puede estar en Contribuyente o en Predios, barremos ambos para amarrar todo
        df_cont = archivo_excel.get('Contribuyente')
        if df_cont is not None and 'Junta' in df_cont.columns and 'CODIGO' in df_cont.columns:
            mask = df_cont['Junta'].str.upper().str.contains(valor_upper, na=False)
            codigos_contribuyente_encontrados.update(df_cont[mask]['CODIGO'].str.strip().str.lstrip('0').unique())
        
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'Junta' in df_pred.columns and 'COD_PRED' in df_pred.columns:
            mask = df_pred['Junta'].str.upper().str.contains(valor_upper, na=False)
            codigos_predio_encontrados.update(df_pred[mask]['COD_PRED'].str.strip().str.lstrip('0').unique())

    elif "5" in modo:
        # Buscar en la pestaña 'Predios' y extraer su llave ('COD_PRED')
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'NUM_MANZ' in df_pred.columns and 'COD_PRED' in df_pred.columns:
            mask = df_pred['NUM_MANZ'].str.strip().str.lstrip('0') == valor_limpio
            codigos_predio_encontrados.update(df_pred[mask]['COD_PRED'].str.strip().str.lstrip('0').unique())

    elif "6" in modo:
        # Buscar en la pestaña 'Predios' y extraer su llave ('COD_PRED')
        df_pred = archivo_excel.get('Predios')
        if df_pred is not None and 'NUM_LOTE' in df_pred.columns and 'COD_PRED' in df_pred.columns:
            mask = df_pred['NUM_LOTE'].str.strip().str.lstrip('0') == valor_limpio
            codigos_predio_encontrados.update(df_pred[mask]['COD_PRED'].str.strip().str.lstrip('0').unique())

    # --- FASE B: EXTRACCIÓN Y CRUCE MULTI-PESTAÑA ---
    resultados = {}
    total = 0
    
    if codigos_contribuyente_encontrados or codigos_predio_encontrados:
        for h in nombres_hojas:
            df = archivo_excel[h]
            
            # Detectamos si la pestaña actual responde a clave de Contribuyente o de Predio
            col_id_contribuyente = next((c for c in df.columns if c.upper() == 'CODIGO'), None)
            col_id_predio = next((c for c in df.columns if c.upper() == 'COD_PRED'), None)
            
            # Inicializamos máscara en Falso
            mask_final = pd.Series(False, index=df.index)
            
            if col_id_contribuyente and codigos_contribuyente_encontrados:
                mask_final |= df[col_id_contribuyente].str.strip().str.lstrip('0').isin(codigos_contribuyente_encontrados)
                
            if col_id_predio and codigos_predio_encontrados:
                mask_final |= df[col_id_predio].str.strip().str.lstrip('0').isin(codigos_predio_encontrados)
            
            res = df[mask_final]
            if not res.empty:
                cols = [c for c in columnas_especificas.get(h, res.columns) if c in res.columns]
                resultados[h] = res[cols]
                total += len(res)

    # --- FASE C: MOSTRAR RESULTADOS ---
    if total > 0:
        st.success(f"🔎 Cruce de datos exitoso. Registros encontrados en cascada: {total}")
        
        # Bloque informativo para saber qué códigos amarró el sistema detrás de escena
        if codigos_contribuyente_encontrados and "1" not in modo:
            st.info(f"🔑 **Contribuyentes vinculados:** {', '.join(list(codigos_contribuyente_encontrados)[:10])} {'...' if len(codigos_contribuyente_encontrados) > 10 else ''}")
        if codigos_predio_encontrados and "2" not in modo:
            st.info(f"🏠 **Predios vinculados:** {', '.join(list(codigos_predio_encontrados)[:10])} {'...' if len(codigos_predio_encontrados) > 10 else ''}")

        for h, d in resultados.items():
            with st.expander(f"📋 Pestaña: {h}", expanded=True):
                st.dataframe(d, use_container_width=True)
        
        # --- DESCARGA SEGURA DE REPORTE PDF (Corregido) ---
        try:
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, "REPORTE DECLARACION JURADA 2025 - ICA", ln=True, align='C')
            pdf_output = pdf.output(dest='S')
            pdf_bytes = pdf_output.encode('latin-1') if isinstance(pdf_output, str) else bytes(pdf_output)
            
            st.write("")  # Espacio estético
            st.download_button(
                label="⬇️ Descargar Reporte PDF", 
                data=pdf_bytes, 
                file_name=f"Reporte_{valor.replace(' ', '_')}.pdf", 
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Error en PDF: {e}")
    else:
        st.warning("⚠️ No se tienen registros vinculados para el criterio ingresado.")