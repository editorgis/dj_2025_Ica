# --- 3. LÓGICA DE ACCESO (TU ESTRUCTURA ORIGINAL) ---
if 'autenticado' not in st.session_state:
    st.session_state['autenticado'] = False

if not st.session_state['autenticado']:
    # Título Principal
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏛️ SISTEMA DE CONSULTA DECLARACIÓN JURADA 2025 - ICA</h1>", unsafe_allow_html=True)
    
    # SUBTÍTULO DE AVISO LEGAL
    st.markdown("<p style='text-align: center; color: #1E3A8A; font-weight: bold;'>🚫 AVISO: Este sistema contiene información catastral del Proyecto Ica. Está prohibido el acceso no autorizado bajo denuncia de la Ley No. 29733 Protección de Datos</p>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Pantalla de Bloqueo - CANDADO AMARILLO/DORADO
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
