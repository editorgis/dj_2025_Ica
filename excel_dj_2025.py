import streamlit as st
import pandas as pd

# Configuración de la página institucional
st.set_page_config(
    page_title="Sistema de Consulta Rápida - Declaración Jurada 2025",
    page_icon="🔍",
    layout="wide"
)

# =============================================================================
# 1. CONTROL DE ACCESO DE SEGURIDAD (PASSWORD)
# =============================================================================
def check_password():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        if st.session_state["password"] == "Ica2025*":  # <-- Tu clave del sistema
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Limpia la variable de la memoria
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Pantalla de bloqueo inicial
        st.markdown("<h2 style='text-align: center;'>🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA</h2>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>2025 - ICA demo.v1</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: red;'>🛑 AVISO: Este sistema contiene información reservada. Ley No. 29733 Protección de Datos.</p>", unsafe_allow_html=True)
        
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 2, 2])
        with col2:
            st.markdown("#### 🔒 ACCESO RESTRINGIDO")
            st.text_input("Ingrese la clave del sistema:", type="password", on_change=password_entered, key="password")
            if "password_correct" in st.session_state and not st.session_state["password_correct"]:
                st.error("❌ Clave incorrecta. Inténtelo nuevamente.")
        return False
    return True

# Si el usuario no está autenticado, se detiene la ejecución aquí
if not check_password():
    st.stop()

# =============================================================================
# 2. CARGA Y OPTIMIZACIÓN DE LA BASE DE DATOS (EXCEL)
# =============================================================================
@st.cache_data
def cargar_datos():
    # Carga el archivo Excel desde la raíz de tu repositorio
    archivo = "Catastro10102025.xlsx"
    data = pd.read_excel(archivo)
    
    # Estandarización estricta de textos para evitar fallas por minúsculas o espacios huerfanos
    data['NM_CONTR_RAZ_SOC'] = data['NM_CONTR_RAZ_SOC'].fillna('').astype(str).str.upper().str.strip()
    data['NM_URB'] = data['NM_URB'].fillna('').astype(str).str.upper().str.strip()
    data['NU_MANZ'] = data['NU_MANZ'].fillna('').astype(str).str.upper().str.strip()
    data['NU_LOTE'] = data['NU_LOTE'].fillna('').astype(str).str.upper().str.strip()
    
    return data

try:
    df = cargar_datos()
    # Indicador superior de conexión exitosa
    st.sidebar.success(f"✅ Base de datos conectada: 'Catastro10102025.xlsx'")
    if st.sidebar.button("🚪 Salir del Sistema"):
        del st.session_state["password_correct"]
        st.rerun()
except Exception as e:
    st.error(f"❌ Error crítico al cargar el archivo Excel: {e}")
    st.stop()

# =============================================================================
# 3. INTERFAZ PRINCIPAL Y CRITERIOS DE BÚSQUEDA
# =============================================================================
st.markdown("## 🏛️ SISTEMA DE CONSULTA RÁPIDA DECLARACIÓN JURADA 2025 - ICA")
st.markdown("<p style='color: gray;'>Módulo Supervisor - Proyecto de Actualización Catastral</p>", unsafe_allow_html=True)
st.markdown("---")

st.markdown("### 🔍 Panel de Consulta de Información Cadastral")

criterio = st.radio(
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

# Contenedores lógicos del filtro
df_filtrado = pd.DataFrame()
ejecutar_busqueda = False

# -----------------------------------------------------------------------------
# CRITERIO 1: POR CÓDIGO DE CONTRIBUYENTE
# -----------------------------------------------------------------------------
if "1.- POR COD_CONTRIBUYENTE" in criterio:
    cod_contr = st.text_input("Ingrese Código de Contribuyente (Exacto):", placeholder="Ej. 0012345").strip()
    if cod_contr:
        df_filtrado = df[df['COD_CONTRIBUYENTE'].astype(str).str.strip() == cod_contr]
        ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 2: POR CÓDIGO DE PREDIO
# -----------------------------------------------------------------------------
elif "2.- POR COD_PREDIO" in criterio:
    cod_predio = st.text_input("Ingrese Código de Predio (Exacto):", placeholder="Ej. P-009876").strip()
    if cod_predio:
        df_filtrado = df[df['COD_PREDIO'].astype(str).str.strip() == cod_predio]
        ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 3: POR NOMBRE / RAZÓN SOCIAL (Coincidencias múltiples por palabras)
# -----------------------------------------------------------------------------
elif "3.- POR NOMBRE / RAZÓN SOCIAL" in criterio:
    nombre_buscar = st.text_input("Ingrese Nombre, Apellidos o Razón Social (Búsqueda Parcial):", placeholder="Ej. LUIS ALBERTO SANCHEZ").upper().strip()
    if nombre_buscar:
        palabras_clave = nombre_buscar.split()
        # Filtra registros que contengan todas las palabras escritas independientemente del orden
        condicion_nombre = df['NM_CONTR_RAZ_SOC'].apply(lambda x: all(palabra in x for palabra in palabras_clave))
        df_filtrado = df[condicion_nombre]
        ejecutar_busqueda = True

# -----------------------------------------------------------------------------
# CRITERIO 4: POR UBICACIÓN URBANA (Menú unificado con 3 entradas de texto)
# -----------------------------------------------------------------------------
elif "4.- POR UBICACIÓN URBANA" in criterio:
    st.markdown("##### 📍 Ingrese los parámetros de Ubicación Territorial")
    
    # Grid estructurado y proporcional
    col_urb, col_mz, col_lt = st.columns([4, 2, 2])
    
    with col_urb:
        urb_ingresada = st.text_input("URB (JUNTA / URBANIZACIÓN):", placeholder="Ej. SAN ISIDRO").upper().strip()
    with col_mz:
        mz_ingresada = st.text_input("MZ (MANZANA):", placeholder="Ej. A").upper().strip()
    with col_lt:
        lote_ingresado = st.text_input("LOTE:", placeholder="Ej. 15").upper().strip()
        
    if urb_ingresada:
        # Filtro base obligatorio (Búsqueda parcial en urbanización para flexibilidad del operador)
        condicion_geo = df['NM_URB'].str.contains(urb_ingresada, na=False, regex=False)
        
        # Filtros acumulativos condicionales si el usuario decide precisar Mz y Lote
        if mz_ingresada:
            condicion_geo = condicion_geo & (df['NU_MANZ'] == mz_ingresada)
        if lote_ingresado:
            condicion_geo = condicion_geo & (df['NU_LOTE'] == lote_ingresado)
            
        df_filtrado = df[condicion_geo]
        ejecutar_busqueda = True
    else:
        st.info("💡 Por favor, ingrese al menos el nombre de la **Urbanización / Junta** para delimitar el ámbito geográfico de búsqueda.")

# =============================================================================
# 4. DESPLIEGUE EJECUTIVO DE RESULTADOS
# =============================================================================
if ejecutar_busqueda:
    st.markdown("---")
    if not df_filtrado.empty:
        cant_registros = len(df_filtrado)
        
        # Indicador de rendimiento / volumen de datos hallados
        st.metric(label="Registros Coincidentes Encontrados", value=f"{cant_registros} UUCC")
        
        # Visualización de datos corporativa
        st.dataframe(
            df_filtrado, 
            use_container_width=True,
            column_config={
                "COD_CONTRIBUYENTE": "Cód. Contribuyente",
                "COD_PREDIO": "Cód. Predio",
                "NM_CONTR_RAZ_SOC": "Contribuyente / Razón Social",
                "NM_URB": "Habilitación / Urbanización",
                "NU_MANZ": "Mz.",
                "NU_LOTE": "Lt."
            }
        )
    else:
        st.warning("⚠️ No se encontraron registros catastrales que coincidan con los parámetros ingresados. Verifique la ortografía o códigos.")
