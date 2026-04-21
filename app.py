import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Scroll Real y Estilo WhatsApp
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }

    /* Contenedor principal compacto */
    .main .block-container {
        max-width: 100% !important;
        padding: 0.5rem 4% 20px 4% !important;
    }

    /* AREA DE CHAT CON SCROLL REAL */
    .chat-scroll-area {
        height: 350px; /* Altura fija para forzar scroll */
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 10px;
        background: rgba(255,255,255,0.02);
        border-radius: 15px;
        margin-bottom: 15px;
        border: 1px solid #222;
    }

    /* Burbujas */
    .bubble {
        padding: 10px 14px;
        border-radius: 15px;
        max-width: 85%;
        line-height: 1.2;
    }
    .bubble-me { background-color: #005C4B; color: #E9EDEF; align-self: flex-start; border-left: 4px solid #00A884; }
    .bubble-ex { background-color: #202C33; color: #E9EDEF; align-self: flex-end; border-right: 4px solid #FF3B30; text-align: right; }

    .trad-text { font-size: 1rem; font-weight: 600; display: block; }
    .orig-text { font-size: 0.7rem; opacity: 0.5; display: block; }

    /* Controles de Micrófono */
    .mic-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 10px;
        position: relative;
    }
    .mic-wrap { position: relative; width: 70px; height: 70px; }
    
    .stButton > button {
        border-radius: 50% !important;
        width: 65px !important;
        height: 65px !important;
        border: none !important;
    }
    button[key="mic_ar"] { background-color: #00A884 !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .label-tag { font-size: 0.6rem; font-weight: bold; position: absolute; top: -12px; width: 100px; }

    /* Ocultar barra de scroll estéticamente */
    .chat-scroll-area::-webkit-scrollbar { width: 4px; }
    .chat-scroll-area::-webkit-scrollbar-thumb { background: #333; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Lógica de Persistencia
if 'history' not in st.session_state:
    st.session_state.history = []

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}

# 4. Header y Selectores
st.markdown("<div style='text-align:center; color:#E9EDEF; font-weight:600;'>Traductor Digital</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 1])
with c1: 
    idioma_sel = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    genero_sel = st.selectbox("", ["Voz Fem.", "Voz Masc."], index=0, label_visibility="collapsed")
with c3:
    if st.button("🗑️ Borrar"):
        st.session_state.history = []
        st.rerun()

info = config_idiomas[idioma_sel]
voz_id = "nova" if "Fem" in genero_sel else "onyx"

def procesar_y_guardar(audio_bytes, es_yo):
    if not audio_bytes: return
    audio_file = io.BytesIO(audio_bytes); audio_file.name = "audio.mp3"
    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    sys_msg = f"Translate to {info['prompt']}" if es_yo else "Traducí al español de Argentina (voseo)."
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"{sys_msg}. Solo texto."}, {"role": "user", "content": trans.text}]
    )
    trad = res.choices[0].message.content
    speech = client.audio.speech.create(model="tts-1", voice=voz_id, input=trad)
    
    # Guardar en historial
    st.session_state.history.append({
        "es_yo": es_yo,
        "orig": trans.text,
        "trad": trad,
        "audio": speech.content
    })

# --- RENDERIZADO DE INTERFAZ ---

# Area de Chat (Scrollable)
chat_html = '<div class="chat-scroll-area">'
for msg in st.session_state.history:
    side_class = "bubble-me" if msg["es_yo"] else "bubble-ex"
    chat_html += f'''
    <div class="bubble {side_class}">
        <span class="orig-text">"{msg["orig"]}"</span>
        <span class="trad-text">{msg["trad"]}</span>
    </div>
    '''
chat_html += '</div>'
st.markdown(chat_html, unsafe_allow_html=True)

# Auto-reproducir el último audio si existe
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio"], autoplay=True)

# Controles de Micrófono (Fijos abajo)
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)

# Botón YO (Izquierda)
with st.container():
    st.markdown("<div class='mic-wrap'><span class='label-tag' style='color:#00A884; left:0;'>🇦🇷 YO (ES)</span>", unsafe_allow_html=True)
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    st.markdown("</div>", unsafe_allow_html=True)

# Botón ÉL (Derecha)
with st.container():
    st.markdown(f"<div class='mic-wrap'><span class='label-tag' style='color:#FF3B30; right:0; text-align:right;'>🌐 {info['label']}</span>", unsafe_allow_html=True)
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Procesamiento después del render para evitar lags
if audio_ar: 
    procesar_y_guardar(audio_ar['bytes'], True)
    st.rerun()
if audio_ex: 
    procesar_y_guardar(audio_ex['bytes'], False)
    st.rerun()
