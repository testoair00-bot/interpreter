import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de Página
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Estilo Chat Compacto
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }
    .main .block-container { max-width: 100% !important; padding: 1rem 5% 20px 5% !important; }

    /* Área de Chat con Scroll */
    .chat-scroll-area {
        height: 40vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 15px;
        background: rgba(255,255,255,0.03);
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid #333;
    }

    /* Burbujas */
    .bubble { padding: 12px; border-radius: 15px; max-width: 80%; line-height: 1.3; margin-bottom: 5px; }
    .bubble-me { background-color: #005C4B; color: #E9EDEF; align-self: flex-start; border-left: 5px solid #00A884; }
    .bubble-ex { background-color: #202C33; color: #E9EDEF; align-self: flex-end; border-right: 5px solid #FF3B30; text-align: right; }

    .trad-text { font-size: 1.1rem; font-weight: 700; display: block; margin-top: 2px; }
    .orig-text { font-size: 0.8rem; opacity: 0.5; display: block; font-style: italic; }

    /* Controles de Micrófono */
    .mic-row { display: flex; justify-content: space-around; padding-top: 10px; }
    .stButton > button { border-radius: 50% !important; width: 70px !important; height: 70px !important; }
    
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .label-tag { font-size: 0.75rem; font-weight: bold; text-align: center; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialización de Estados
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_processed_hash' not in st.session_state:
    st.session_state.last_processed_hash = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}

# 4. Cabecera y Configuración
st.markdown("<h3 style='text-align:center; color:white; margin-top:-10px;'>Interprete Digital</h3>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 0.5])
with c1: 
    idioma_sel = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    # Voz Masculina por defecto (index 1)
    genero_sel = st.selectbox("", ["Voz Femenina", "Voz Masculina"], index=1, label_visibility="collapsed")
with c3:
    if st.button("🗑️"):
        st.session_state.history = []
        st.session_state.last_processed_hash = None
        st.rerun()

info = config_idiomas[idioma_sel]
voz_id = "onyx" if "Masc" in genero_sel else "nova"

# 5. Función de Procesamiento Robusta
def procesar_voz(audio_data, es_yo):
    # Validar que sea un audio nuevo
    audio_hash = hash(audio_data['bytes'])
    if st.session_state.last_processed_hash == audio_hash:
        return

    with st.spinner("..."):
        audio_file = io.BytesIO(audio_data['bytes'])
        audio_file.name = "audio.mp3"
        
        # 1. Transcribir lo que se escuchó
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        # 2. Definir Prompts de Traducción (Cruzados correctamente)
        if es_yo:
            # Yo hablo español -> Traducir al idioma extranjero
            sys_msg = f"You are a professional translator. Translate the following Spanish text into {info['prompt']}. Provide only the translation."
        else:
            # El otro habla extranjero -> Traducir al español de Argentina
            sys_msg = f"You are a professional translator. Translate the following {info['prompt']} text into Spanish (Argentina, use 'voseo'). Provide only the translation."
        
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": trans.text}]
        )
        texto_traducido = res.choices[0].message.content
        
        # 3. Generar Audio (TTS)
        audio_res = client.audio.speech.create(model="tts-1", voice=voz_id, input=texto_traducido)
        
        # 4. Guardar en Historial
        st.session_state.history.append({
            "es_yo": es_yo,
            "orig": trans.text,
            "trad": texto_traducido,
            "audio_bytes": audio_res.content
        })
        st.session_state.last_processed_hash = audio_hash
        st.rerun()

# --- RENDERIZADO DE INTERFAZ ---

# Chat Histórico
chat_html = '<div class="chat-scroll-area">'
for msg in st.session_state.history:
    clase = "bubble-me" if msg["es_yo"] else "bubble-ex"
    chat_html += f'''
    <div class="bubble {clase}">
        <span class="orig-text">"{msg["orig"]}"</span>
        <span class="trad-text">{msg["trad"]}</span>
    </div>
    '''
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# Reproductor automático del último mensaje (Permite repetir)
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio_bytes"], autoplay=True)

# Fila de Micrófonos (Abajo)
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("<p class='label-tag' style='color:#007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    audio_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if audio_yo: procesar_voz(audio_yo, True)

with col_r:
    st.markdown(f"<p class='label-tag' style='color:#FF3B30;'>🌐 {info['label']}</p>", unsafe_allow_html=True)
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if audio_ex: procesar_voz(audio_ex, False)
