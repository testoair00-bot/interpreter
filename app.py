import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Traductor Pro", layout="centered")

# 2. CSS: Subida de elementos y habilitación de scroll vertical
st.markdown("""
    <style>
    /* Reset de fondo y permitir scroll vertical suave */
    .stApp { 
        background-color: #0E1117; 
        overflow-y: auto !important; 
    }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }

    /* Contenedor: Menos padding arriba para ganar espacio */
    .main .block-container {
        max-width: 100% !important;
        padding: 0.5rem 4% 100px 4% !important; /* 100px abajo es suficiente ahora */
    }

    /* Título Ultra Compacto */
    .header-title {
        text-align: center;
        color: #E9EDEF;
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 5px;
        opacity: 0.8;
    }

    /* Burbujas de Chat WhatsApp Style */
    .bubble {
        padding: 10px 14px;
        border-radius: 15px;
        margin-bottom: 5px;
        max-width: 90%;
        line-height: 1.2;
        animation: fadeIn 0.3s ease;
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    .bubble-me { background-color: #005C4B; color: #E9EDEF; border-left: 4px solid #00A884; }
    .bubble-ex { background-color: #202C33; color: #E9EDEF; border-right: 4px solid #FF3B30; }

    .trad-text { font-size: 1rem; font-weight: 600; }
    .orig-text { font-size: 0.7rem; opacity: 0.5; }

    /* Micro-Contenedores de Micrófono */
    .mic-container {
        position: relative;
        height: 70px; /* Reducido de 85px */
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }

    /* Botones más pequeños para mobile */
    .stButton > button {
        border-radius: 50% !important;
        width: 55px !important; /* Reducido para ganar aire */
        height: 55px !important;
        border: none !important;
        position: absolute !important;
        right: 0;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    
    button[key="mic_ar"] { background-color: #00A884 !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .label-tag {
        position: absolute;
        right: 0;
        top: -8px;
        font-size: 0.6rem;
        font-weight: bold;
        opacity: 0.9;
    }

    /* Selectores en una línea para ahorrar espacio vertical */
    div[data-baseweb="select"] { height: 32px !important; font-size: 0.75rem !important; }
    
    /* Ocultar barra de scroll de Streamlit pero permitir desplazamiento */
    ::-webkit-scrollbar { width: 0px; background: transparent; }
    </style>
    """, unsafe_allow_html=True)

# 3. Lógica (Manteniendo tu motor OpenAI)
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}
voces = {"Fem": "nova", "Masc": "onyx"}

st.markdown("<div class='header-title'>Traductor Digital</div>", unsafe_allow_html=True)

# Selectores en columnas para ahorrar 40px de altura
c1, c2 = st.columns(2)
with c1: idioma_sel = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: voz_sel = st.selectbox("", list(voces.keys()), label_visibility="collapsed")

info = config_idiomas[idioma_sel]
voz_id = voces[voz_sel]

def render_chat(audio_bytes, es_yo):
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
    
    css_class = "bubble-me" if es_yo else "bubble-ex"
    st.markdown(f"""
    <div class="bubble {css_class}">
        <span class="orig-text">"{trans.text}"</span><br>
        <span class="trad-text">{trad}</span>
    </div>
    """, unsafe_allow_html=True)
    st.audio(speech.content, autoplay=True)

# --- INTERFAZ COMPACTA ---

# Bloque YO (Subido y achicado)
st.markdown("<div class='mic-container'>", unsafe_allow_html=True)
st.markdown("<span class='label-tag' style='color:#00A884;'>🇦🇷 YO</span>", unsafe_allow_html=True)
audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
st.markdown("<div style='width:80%'>", unsafe_allow_html=True)
if audio_ar: render_chat(audio_ar['bytes'], True)
st.markdown("</div></div>", unsafe_allow_html=True)

st.markdown("<hr style='border:0.1px solid #222; margin: 10px 0;'>", unsafe_allow_html=True)

# Bloque ÉL (Subido para que entre siempre)
st.markdown("<div class='mic-container'>", unsafe_allow_html=True)
st.markdown(f"<span class='label-tag' style='color:#FF3B30;'>🌐 {info['label']}</span>", unsafe_allow_html=True)
audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
st.markdown("<div style='width:80%'>", unsafe_allow_html=True)
if audio_ex: render_chat(audio_ex['bytes'], False)
st.markdown("</div></div>", unsafe_allow_html=True)
