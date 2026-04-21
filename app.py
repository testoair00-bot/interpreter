import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Traductor Pro", layout="centered")

# 2. CSS: Estilo WhatsApp, Compacto y Animado
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }

    /* Contenedor Ultra Compacto */
    .main .block-container {
        max-width: 100% !important;
        padding: 0.5rem 4% 20px 4% !important;
    }

    /* Título reducido y pegado arriba */
    .header-title {
        text-align: center;
        color: #E9EDEF;
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 10px;
    }

    /* Burbujas de Chat Animadas */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .bubble {
        padding: 12px 16px;
        border-radius: 18px;
        margin-bottom: 8px;
        max-width: 85%;
        animation: slideIn 0.3s ease-out;
        position: relative;
        line-height: 1.3;
    }

    .bubble-me {
        background-color: #005C4B; /* Verde WhatsApp Dark */
        color: #E9EDEF;
        border-bottom-left-radius: 4px;
        border-left: 4px solid #00A884;
    }

    .bubble-ex {
        background-color: #202C33; /* Gris WhatsApp Dark */
        color: #E9EDEF;
        border-bottom-right-radius: 4px;
        border-right: 4px solid #FF3B30;
    }

    .trad-text { font-size: 1.1rem; font-weight: 600; display: block; }
    .orig-text { font-size: 0.75rem; opacity: 0.6; display: block; margin-bottom: 4px; }

    /* Controles Flotantes a la Derecha */
    .mic-container {
        position: relative;
        height: 85px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }

    .stButton > button {
        border-radius: 50% !important;
        width: 65px !important;
        height: 65px !important;
        border: none !important;
        position: absolute !important;
        right: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        transition: transform 0.2s;
    }
    
    .stButton > button:active { transform: scale(0.9); }

    button[key="mic_ar"] { background-color: #00A884 !important; } /* Verde */
    button[key="mic_ex"] { background-color: #FF3B30 !important; } /* Rojo */

    .label-tag {
        position: absolute;
        right: 0;
        top: -5px;
        font-size: 0.65rem;
        font-weight: bold;
        text-transform: uppercase;
    }

    /* Selectores más pequeños */
    .stSelectbox { margin-bottom: -15px; }
    div[data-baseweb="select"] { height: 35px !important; font-size: 0.8rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Lógica
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}
voces = {"Fem": "nova", "Masc": "onyx"}

st.markdown("<div class='header-title'>Traductor Digital</div>", unsafe_allow_html=True)

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
        <span class="orig-text">"{trans.text}"</span>
        <span class="trad-text">{trad}</span>
    </div>
    """, unsafe_allow_html=True)
    st.audio(speech.content, autoplay=True)

# --- INTERFAZ COMPACTA ---

# Bloque YO
st.markdown("<div class='mic-container'>", unsafe_allow_html=True)
st.markdown("<span class='label-tag' style='color:#00A884;'>TU VOZ (ES)</span>", unsafe_allow_html=True)
audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
st.markdown("<div style='width:75%'>", unsafe_allow_html=True)
if audio_ar: render_chat(audio_ar['bytes'], True)
st.markdown("</div></div>", unsafe_allow_html=True)

# Bloque ÉL
st.markdown("<div class='mic-container'>", unsafe_allow_html=True)
st.markdown(f"<span class='label-tag' style='color:#FF3B30;'>{info['label']}</span>", unsafe_allow_html=True)
audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
st.markdown("<div style='width:75%'>", unsafe_allow_html=True)
if audio_ex: render_chat(audio_ex['bytes'], False)
st.markdown("</div></div>", unsafe_allow_html=True)
