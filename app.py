import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Estilo Chat y Control de Scroll
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }

    .main .block-container {
        max-width: 100% !important;
        padding: 1rem 5% 20px 5% !important;
    }

    /* AREA DE CHAT: Altura fija y scroll */
    .chat-scroll-area {
        height: 45vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 15px;
        background: rgba(255,255,255,0.03);
        border-radius: 15px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }

    /* Burbujas */
    .bubble { padding: 12px; border-radius: 15px; max-width: 85%; animation: fadeIn 0.3s; line-height: 1.3; }
    .bubble-me { background-color: #005C4B; color: #E9EDEF; align-self: flex-start; border-left: 5px solid #00A884; }
    .bubble-ex { background-color: #202C33; color: #E9EDEF; align-self: flex-end; border-right: 5px solid #FF3B30; text-align: right; }

    .trad-text { font-size: 1.1rem; font-weight: 700; display: block; margin-top: 4px; }
    .orig-text { font-size: 0.8rem; opacity: 0.5; display: block; font-style: italic; }

    /* Controles de Micrófono */
    .mic-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding-top: 15px;
        background: #0E1117;
    }
    
    .stButton > button {
        border-radius: 50% !important;
        width: 75px !important;
        height: 75px !important;
        border: none !important;
    }
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .label-tag { font-size: 0.75rem; font-weight: bold; text-align: center; margin-bottom: 8px; }
    
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    </style>
    """, unsafe_allow_html=True)

# 3. Estado de la Sesión
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_audio_processed' not in st.session_state:
    st.session_state.last_audio_processed = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}

# 4. Cabecera
st.markdown("<h3 style='text-align:center; color:white; margin-top:-15px;'>Interprete Digital</h3>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 1])
with c1: 
    idioma_sel = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    # Voz Masculina por defecto
    genero_sel = st.selectbox("", ["Femenina", "Masculina"], index=1, label_visibility="collapsed")
with c3:
    if st.button("🗑️"):
        st.session_state.history = []
        st.session_state.last_audio_processed = None
        st.rerun()

info = config_idiomas[idioma_sel]
voz_id = "onyx" if genero_sel == "Masculina" else "nova"

# 5. Lógica de Procesamiento
def procesar(audio_data, es_yo):
    # Evitar doble procesamiento si el ID es igual
    audio_id = hash(audio_data['bytes'])
    if st.session_state.last_audio_processed == audio_id:
        return

    with st.spinner("..."):
        audio_file = io.BytesIO(audio_data['bytes'])
        audio_file.name = "audio.mp3"
        
        # Transcripción
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        # Traducción
        sys_prompt = f"Translate to {info['prompt']}. Just text." if es_yo else "Traducí al español de Argentina (usá voseo). Solo texto."
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": trans.text}]
        )
        traducido = res.choices[0].message.content
        
        # Voz (TTS)
        audio_res = client.audio.speech.create(model="tts-1", voice=voz_id, input=traducido)
        
        # Guardar
        st.session_state.history.append({
            "es_yo": es_yo,
            "orig": trans.text,
            "trad": traducido,
            "audio_bytes": audio_res.content
        })
        st.session_state.last_audio_processed = audio_id
        st.rerun()

# --- RENDERIZADO ---

# Area de Chat
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

# Reproductor del último mensaje (Permite repetir con Play)
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio_bytes"], autoplay=True)

# Controles de Micrófono
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("<p class='label-tag' style='color:#007AFF;'>🇦🇷 YO</p>", unsafe_allow_html=True)
    audio_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if audio_yo: procesar(audio_yo, True)

with col_r:
    st.markdown(f"<p class='label-tag' style='color:#FF3B30;'>🌐 {info['label']}</p>", unsafe_allow_html=True)
    audio_el = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if audio_el: procesar(audio_el, False)

st.markdown("</div>", unsafe_allow_html=True)
