import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Forzar línea única y espacio extra abajo
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; display: none !important; 
    }

    /* 300px de espacio abajo para que el mic flote libre */
    .main .block-container {
        max-width: 100% !important;
        padding: 1rem 5% 300px 5% !important;
    }

    /* FORZAR LÍNEA ÚNICA EN MÓVIL */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important; /* No permite que se apilen */
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        gap: 10px !important;
    }

    /* Ajuste de anchos para que el botón no se achique */
    div[data-testid="column"] {
        min-width: 0 !important;
    }

    /* Maxi-Botones Circulares */
    .stButton>button {
        border-radius: 50% !important;
        width: 80px !important;
        height: 80px !important;
        border: none !important;
        color: white !important;
        font-size: 2rem !important;
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }

    /* Colores */
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ar"] { background-color: #007AFF !important; }
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .right-label {
        text-align: right;
        font-size: 0.7rem;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .chat-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 15px;
        border-left: 8px solid #007AFF;
        margin-bottom: 10px;
    }
    
    .trad-text { font-size: 1.4rem !important; font-weight: 800; }
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

def procesar_v5(audio_bytes, es_a_extranjero=True, card_color="#007AFF"):
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
            <div style="color: #666; font-size: 0.75rem;">"{trans.text}"</div>
            <div class="trad-text" style="color: {card_color};">{trad}</div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(speech.content, autoplay=True)

# --- BLOQUES DE INTERFAZ ---

# BLOQUE 1: YO HABLO
# Forzamos proporciones fijas para que no se apilen
col_ar_txt, col_ar_btn = st.columns([0.7, 0.3])

with col_ar_btn:
    st.markdown("<p class='right-label' style='color: #007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')

with col_ar_txt:
    if audio_ar:
        procesar_v5(audio_ar['bytes'], True, "#007AFF")
    else:
        st.markdown("<p style='color:#333; font-size:0.9rem;'>Esperando audio...</p>", unsafe_allow_html=True)

st.markdown("<hr style='border: 0.5px solid #222; margin: 20px 0;'>", unsafe_allow_html=True)

# BLOQUE 2: INTERLOCUTOR
col_ex_txt, col_ex_btn = st.columns([0.7, 0.3])

with col_ex_btn:
    st.markdown(f"<p class='right-label' style='color: #FF3B30;'>🌐 EL ({info['label'][:3]})</p>", unsafe_allow_html=True)
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')

with col_ex_txt:
    if audio_ex:
        procesar_v5(audio_ex['bytes'], False, "#FF3B30")
    else:
        st.markdown("<p style='color:#333; font-size:0.9rem;'>Esperando audio...</p>", unsafe_allow_html=True)
