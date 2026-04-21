import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de página
st.set_page_config(
    page_title="Interprete Pro | Argentina", 
    layout="wide", 
    page_icon="🇦🇷",
    initial_sidebar_state="collapsed"
)

# 2. Estilos CSS (Corregidos con las burbujas que faltaban)
st.markdown("""
    <style>
    /* Ocultar marca Streamlit */
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    button[title="View fullscreen"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}

    /* Fondo y Contenedor */
    .stApp { background-color: #0E1117; }
    .block-container {
        max-width: 100% !important;
        padding: 1rem !important;
    }

    /* Forzar botones a la derecha en Mobile */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
    }
    
    .stButton>button { 
        width: 70px !important; 
        height: 70px !important; 
        border-radius: 50% !important;
        background-color: #007AFF !important;
        color: white !important;
        border: none !important;
    }

    /* BURBUJAS DE CHAT (Añadidas) */
    .chat-bubble {
        padding: 15px 20px;
        border-radius: 20px;
        margin-bottom: 8px;
        font-family: sans-serif;
    }
    .user-text { background-color: #1C1C1E; color: #E5E5EA; }
    .trans-text { background-color: #007AFF; color: white; font-weight: bold; font-size: 1.1rem; }
    
    .lang-label { 
        font-size: 0.8rem; color: #8E8E93; 
        text-transform: uppercase; letter-spacing: 1px; 
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialización Segura de OpenAI
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except Exception as e:
    st.error("Error cargando la API Key. Revisá los Secrets en Streamlit Cloud.")
    st.stop()

# --- CONFIGURACIÓN IDIOMAS ---
config_idiomas = {
    "Inglés": {"prompt": "English", "code": "EN", "btn": "Tap to Speak", "label": "English"},
    "Chino": {"prompt": "Chinese (Simplified)", "code": "ZH", "btn": "点击通话", "label": "中文"},
    "Portugués": {"prompt": "Portuguese", "code": "PT", "btn": "Toque para falar", "label": "Português"},
    "Italiano": {"prompt": "Italian", "code": "IT", "btn": "Tocca para parlare", "label": "Italiano"},
    "Francés": {"prompt": "French", "code": "FR", "btn": "Appuyez para parler", "label": "Français"}
}

idioma_sel = st.selectbox("Seleccionar Idioma:", list(config_idiomas.keys()), index=0)
info = config_idiomas[idioma_sel]

def procesar(audio_bytes, es_a_extranjero=True):
    if not audio_bytes: return None
    
    with st.spinner("..."):
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.mp3"
        
        # Transcripción
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        # Traducción
        if es_a_extranjero:
            sys_msg = f"Translate from Argentine Spanish to {info['prompt']}. Output only the translation."
        else:
            sys_msg = "Traducí al español de Argentina (usá voseo: che, querés, tenés, etc.). Solo devolvé la traducción."
            
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": trans.text}]
        )
        trad = res.choices[0].message.content
        
        # Voz
        speech = client.audio.speech.create(model="tts-1", voice="nova", input=trad)
        return trans.text, trad, speech.content

# --- INTERFAZ ---

# ARGENTINA
st.markdown('<p class="lang-label">🇦🇷 ESPAÑOL ARGENTINO</p>', unsafe_allow_html=True)
col_ar_txt, col_ar_btn = st.columns([4, 1])
with col_ar_btn:
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
with col_ar_txt:
    if audio_ar:
        orig, trad, voice = procesar(audio_ar['bytes'], True)
        st.markdown(f'<div class="chat-bubble user-text">{orig}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble trans-text">{trad}</div>', unsafe_allow_html=True)
        st.audio(voice, autoplay=True)

st.divider()

# EXTRANJERO
st.markdown(f'<p class="lang-label">🌐 {info["label"]}</p>', unsafe_allow_html=True)
col_ex_txt, col_ex_btn = st.columns([4, 1])
with col_ex_btn:
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
with col_ex_txt:
    if audio_ex:
        orig, trad, voice = procesar(audio_ex['bytes'], False)
        st.markdown(f'<div class="chat-bubble user-text">{orig}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="chat-bubble trans-text">{trad}</div>', unsafe_allow_html=True)
        st.audio(voice, autoplay=True)
