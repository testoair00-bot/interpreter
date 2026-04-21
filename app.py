import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# Configuración de nivel profesional
st.set_page_config(
    page_title="Interprete Pro | Argentina", 
    layout="wide", 
    page_icon="🇦🇷",
    initial_sidebar_state="collapsed"
)

# Estilos CSS avanzados para Mobile y UX
st.markdown("""
    <style>
    /* 1. Eliminar el ancho máximo y los márgenes laterales de Streamlit */
    .block-container {
        max-width: 100% !important;
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    /* 2. Forzar que el contenedor principal ocupe todo el ancho */
    .stAppViewMain {
        width: 100% !important;
    }

    /* 3. Ajustar el espaciado de las columnas para que los botones queden bien al borde */
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 4. Ocultar la decoración superior (la línea de color que a veces aparece) */
    [data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 5. Si querés fondo negro total como en tu imagen */
    .stApp {
        background-color: #0E1117;
    }
    </style>
    """, unsafe_allow_html=True)

client = OpenAI(api_key="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")

# --- DICCIONARIO DE IDIOMAS PROFESIONAL ---
config_idiomas = {
    "Inglés": {"prompt": "English", "code": "EN", "btn": "Tap to Speak", "label": "English"},
    "Chino": {"prompt": "Chinese (Simplified)", "code": "ZH", "btn": "点击通话", "label": "中文"},
    "Portugués": {"prompt": "Portuguese", "code": "PT", "btn": "Toque para falar", "label": "Português"},
    "Italiano": {"prompt": "Italian", "code": "IT", "btn": "Tocca para parlare", "label": "Italiano"},
    "Francés": {"prompt": "French", "code": "FR", "btn": "Appuyez pour parler", "label": "Français"}
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
        
        # Traducción con instrucción de acento Argentino
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

# --- INTERFAZ MOBILE-FIRST ---

# BLOQUE 1: ARGENTINA
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
    else:
        st.caption("Pulsa el micro para hablar...")

st.write("") # Espaciador
st.divider()

# BLOQUE 2: EXTRANJERO
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
    else:
        st.caption(info['btn'] + "...")

# Barra lateral para ajustes menores
with st.sidebar:
    st.header("Opciones")
    st.write("Asegurate de estar en la misma red WiFi para usar desde el celu.")
