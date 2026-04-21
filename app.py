import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de página (Indispensable al inicio)
st.set_page_config(
    page_title="Interprete Pro | Argentina", 
    layout="wide", 
    page_icon="🇦🇷",
    initial_sidebar_state="collapsed"
)

# 2. Estilos CSS: Limpieza de marca, Full Width y Mobile-First
st.markdown("""
    <style>
    /* Ocultar elementos nativos de Streamlit */
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    button[title="View fullscreen"] {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}

    /* Fondo oscuro y control de ancho */
    .stApp { background-color: #0E1117; }
    .block-container {
        max-width: 100% !important;
        padding-top: 1.5rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }

    /* Forzar botones a la derecha en Mobile (No se apilan) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    [data-testid="column"] {
        width: auto !important;
        flex: 1 1 auto !important;
    }
    
    /* Botones de Micrófono Pro */
    .stButton>button { 
        width: 75px !important; 
        height: 75px !important; 
        border-radius: 50% !important;
        background-color: #007AFF !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0,122,255,0.3);
    }

    /* Burbujas de chat */
    .chat-bubble {
        padding: 12px 18px;
        border-radius: 18px;
        margin-bottom: 6px;
        font-family: 'Segoe UI', sans-serif;
        line-height: 1.4;
    }
    .user-text { background-color: #1C1C1E; color: #E5E5EA; border-bottom-left-radius: 4px; }
    .trans-text { background-color: #007AFF; color: white; font-weight: 600; font-size: 1.1rem; border-top-left-radius: 4px; }
    
    /* Etiquetas de idioma */
    .lang-label { 
        font-size: 0.75rem; color: #8E8E93; 
        text-transform: uppercase; letter-spacing: 1.5px; 
        margin-bottom: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Validación y Conexión Segura con OpenAI
try:
    # Verificamos si existe el secreto antes de llamar a la API
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("Falta la clave en 'Secrets'. Agregala en el panel de Streamlit Cloud.")
        st.stop()
        
    api_key = st.secrets["OPENAI_API_KEY"]
    if not api_key.startswith("sk-"):
        st.error("La API Key en Secrets no parece ser válida (debe empezar con 'sk-').")
        st.stop()
        
    client = OpenAI(api_key=api_key)
except Exception as e:
    st.error(f"Error de inicialización: {str(e)}")
    st.stop()

# --- DICCIONARIO DE IDIOMAS ---
config_idiomas = {
    "Inglés": {"prompt": "English", "btn": "Tap to Speak", "label": "English"},
    "Chino": {"prompt": "Chinese (Simplified)", "btn": "点击通话", "label": "中文"},
    "Portugués": {"prompt": "Portuguese", "btn": "Toque para falar", "label": "Português"},
    "Italiano": {"prompt": "Italian", "btn": "Tocca per parlare", "label": "Italiano"},
    "Francés": {"prompt": "French", "btn": "Appuyez para parler", "label": "Français"}
}

# Selector estilizado
idioma_sel = st.selectbox("Idioma del interlocutor:", list(config_idiomas.keys()), index=0)
info = config_idiomas[idioma_sel]

# 4. Lógica de Procesamiento
def procesar(audio_bytes, es_a_extranjero=True):
    if not audio_bytes: return None
    
    with st.spinner("Procesando..."):
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.mp3"
        
        # 1. Transcripción
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        # 2. Traducción con Sabor Argentino
        if es_a_extranjero:
            sys_msg = f"Translate from Argentine Spanish to {info['prompt']}. Output only the translation."
        else:
            sys_msg = "Traducí al español de Argentina (usá voseo: che, querés, tenés, etc.). Solo devolvé la traducción."
            
        res = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": trans.text}]
        )
        trad = res.choices[0].message.content
        
        # 3. Síntesis de voz (TTS)
        speech = client.audio.speech.create(model="tts-1", voice="nova", input=trad)
        return trans.text, trad, speech.content

# --- INTERFAZ DE USUARIO ---

# BLOQUE ARGENTINA
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
        st.caption("Mantené presionado para hablar...")

st.divider()

# BLOQUE EXTRANJERO
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
        st.caption(f"{info['btn']}...")
