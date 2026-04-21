import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Posicionamiento Absoluto para evitar colapsos
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; display: none !important; 
    }

    /* Espacio masivo abajo para el Iframe */
    .main .block-container {
        max-width: 100% !important;
        padding: 1.5rem 5% 350px 5% !important;
    }

    /* Contenedor relativo para posicionar el botón */
    [data-testid="stVerticalBlock"] > div {
        position: relative !important;
        min-height: 100px;
    }

    /* ESTILO DE LOS BOTONES CIRCULARES */
    .stButton>button {
        border-radius: 50% !important;
        width: 80px !important;
        height: 80px !important;
        border: none !important;
        color: white !important;
        font-size: 2rem !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
        position: absolute !important;
        right: 0 !important;
        top: 10px !important;
        z-index: 1000 !important;
    }

    /* Márgenes para que el texto NO colapse ni choque con el botón */
    .text-container {
        margin-right: 100px !important;
        min-height: 90px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Colores por Key */
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .right-label-fix {
        position: absolute;
        right: 5px;
        top: -15px;
        font-size: 0.7rem;
        font-weight: 900;
        letter-spacing: 1px;
    }

    .chat-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 18px;
        padding: 15px;
        border-left: 6px solid #007AFF;
        margin-top: 5px;
    }
    
    .trad-text { font-size: 1.4rem !important; font-weight: 800; line-height: 1.1; }
    hr { border: 0.1px solid #222; margin: 30px 0 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialización
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "INGLÉS"},
    "Chino": {"prompt": "Chinese", "label": "CHINO"},
    "Portugués": {"prompt": "Portuguese", "label": "PORTUGUÉS"},
    "Italiano": {"prompt": "Italian", "label": "ITALIANO"}
}
voces = {"Femenina": "nova", "Masculina": "onyx"}

st.markdown("<h3 style='text-align: center; color: white;'>Interprete Digital</h3>", unsafe_allow_html=True)

c_h1, c_h2 = st.columns(2)
with c_h1: idioma_sel = st.selectbox("", list(config_idiomas.keys()))
with c_h2: voz_sel = st.selectbox("", list(voces.keys()))

info = config_idiomas[idioma_sel]
voz_id = voces[voz_sel]

def procesar_final(audio_bytes, es_a_extranjero=True, card_color="#007AFF"):
    if not audio_bytes: return
    with st.spinner("..."):
        audio_file = io.BytesIO(audio_bytes); audio_file.name = "audio.mp3"
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        sys_msg = f"Translate to {info['prompt']}" if es_a_extranjero else "Traducí al español de Argentina (voseo)."
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"{sys_msg}. Solo texto."}, {"role": "user", "content": trans.text}]
        )
        trad = res.choices[0].message.content
        speech = client.audio.speech.create(model="tts-1", voice=voz_id, input=trad)
        
        st.markdown(f"""
        <div class="chat-card" style="border-left-color: {card_color};">
            <div style="color: #555; font-size: 0.7rem;">"{trans.text}"</div>
            <div class="trad-text" style="color: {card_color};">{trad}</div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(speech.content, autoplay=True)

# --- INTERFAZ SIN COLUMNAS (Para evitar colapsos) ---

# BLOQUE 1: YO
st.markdown(f"<div><span class='right-label-fix' style='color:#007AFF;'>🇦🇷 YO (ES)</span>", unsafe_allow_html=True)
audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
st.markdown("<div class='text-container'>", unsafe_allow_html=True)
if audio_ar:
    procesar_final(audio_ar['bytes'], True, "#007AFF")
else:
    st.markdown("<p style='color:#333;'>Esperando audio propio...</p>", unsafe_allow_html=True)
st.markdown("</div></div><hr>", unsafe_allow_html=True)

# BLOQUE 2: EL
st.markdown(f"<div><span class='right-label-fix' style='color:#FF3B30;'>🌐 EL ({info['label'][:3]})</span>", unsafe_allow_html=True)
audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
st.markdown("<div class='text-container'>", unsafe_allow_html=True)
if audio_ex:
    procesar_final(audio_ex['bytes'], False, "#FF3B30")
else:
    st.markdown(f"<p style='color:#333;'>Esperando audio de {info['label']}...</p>", unsafe_allow_html=True)
st.markdown("</div></div>", unsafe_allow_html=True)
