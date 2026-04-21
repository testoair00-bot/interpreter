import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS Avanzado: Botones y etiquetas a la derecha
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; display: none !important; 
    }

    /* Contenedor Principal */
    .main .block-container {
        max-width: 100% !important;
        padding: 1.5rem 6% 180px 6% !important;
    }

    /* Animación de Pulso */
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(255, 255, 255, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
    }

    /* Botones Circulares XXL a la derecha */
    .stButton>button {
        border-radius: 50% !important;
        width: 85px !important;
        height: 85px !important;
        border: none !important;
        color: white !important;
        font-size: 2rem !important;
        animation: pulse 2s infinite;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
        margin-top: 10px;
    }

    /* Colores */
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ar"] { background-color: #007AFF !important; }
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ex"] { background-color: #FF3B30 !important; }

    /* Etiquetas alineadas a la derecha */
    .right-label {
        text-align: right;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 1px;
        margin-bottom: 0px;
    }

    /* Tarjetas de Chat */
    .chat-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 25px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 5px;
    }
    
    .trad-text {
        font-size: 1.6rem !important;
        font-weight: 800;
        line-height: 1.2;
    }

    .stAudio { margin-top: 15px !important; }
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

voces = {"Femenina": "nova", "Masculina": "onyx", "Suave": "shimmer"}

st.markdown("<h2 style='text-align: center; color: white;'>Interprete Digital</h2>", unsafe_allow_html=True)

c_h1, c_h2 = st.columns(2)
with c_h1: idioma_sel = st.selectbox("", list(config_idiomas.keys()))
with c_h2: voz_sel = st.selectbox("", list(voces.keys()))

info = config_idiomas[idioma_sel]
voz_id = voces[voz_sel]

def procesar_v4(audio_bytes, es_a_extranjero=True, card_color="#007AFF"):
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
        <div class="chat-card" style="border-left: 8px solid {card_color};">
            <div style="color: #666; font-size: 0.8rem;">"{trans.text}"</div>
            <div class="trad-text" style="color: {card_color};">{trad}</div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(speech.content, autoplay=True)

# --- BLOQUES DE INTERFAZ ---

# BLOQUE 1: YO HABLO
col_ar_txt, col_ar_btn = st.columns([2, 1])

with col_ar_btn:
    st.markdown("<p class='right-label' style='color: #007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')

with col_ar_txt:
    if audio_ar:
        procesar_v4(audio_ar['bytes'], True, "#007AFF")
    else:
        st.markdown("<p style='color:#333; margin-top:40px;'>Esperando audio...</p>", unsafe_allow_html=True)

st.divider()

# BLOQUE 2: INTERLOCUTOR
col_ex_txt, col_ex_btn = st.columns([2, 1])

with col_ex_btn:
    st.markdown(f"<p class='right-label' style='color: #FF3B30;'>🌐 ÉL ({info['label'][:3]})</p>", unsafe_allow_html=True)
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')

with col_ex_txt:
    if audio_ex:
        procesar_v4(audio_ex['bytes'], False, "#FF3B30")
    else:
        st.markdown("<p style='color:#333; margin-top:40px;'>Esperando audio...</p>", unsafe_allow_html=True)
