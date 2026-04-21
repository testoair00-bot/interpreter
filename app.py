import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# Configuración Base
st.set_page_config(page_title="Traductor Pro", layout="centered")

# CSS para Interfaz de App Nativa (Minimalista)
st.markdown("""
    <style>
    /* Fondo oscuro y limpieza */
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
    
    /* Contenedor tipo Tarjeta */
    .main .block-container {
        max-width: 450px !important;
        padding-top: 2rem !important;
    }

    /* Estilo de las burbujas */
    .stCaption { color: #8E8E93 !important; font-size: 0.9rem !important; text-align: center; }
    
    .chat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 25px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }

    .trad-text {
        color: #007AFF;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        margin: 10px 0;
    }

    /* Botones Gigantes */
    div[data-testid="stHorizontalBlock"] {
        background: rgba(0, 122, 255, 0.1);
        border-radius: 50px;
        padding: 10px;
        margin: 15px 0;
    }
    
    .stButton>button {
        width: 100% !important;
        height: 60px !important;
        border-radius: 30px !important;
        background-color: #007AFF !important;
        font-weight: bold !important;
        border: none !important;
    }

    /* Selector de idioma */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1C1C1E !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Inicialización
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "INGLÉS"},
    "Chino": {"prompt": "Chinese", "label": "CHINO"},
    "Portugués": {"prompt": "Portuguese", "label": "PORTUGUÉS"},
    "Italiano": {"prompt": "Italian", "label": "ITALIANO"}
}

# --- INTERFAZ CENTRALIZADA ---
st.markdown("<h2 style='text-align: center; color: white;'>Interprete Digital</h2>", unsafe_allow_html=True)

idioma_sel = st.selectbox("", list(config_idiomas.keys()))
info = config_idiomas[idioma_sel]

def procesar_v2(audio_bytes, es_a_extranjero=True):
    if not audio_bytes: return
    audio_file = io.BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    
    trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    
    sys_msg = f"Translate to {info['prompt']}" if es_a_extranjero else "Traducí al español de Argentina (voseo)."
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": f"{sys_msg}. Solo texto."}, {"role": "user", "content": trans.text}]
    )
    trad = res.choices[0].message.content
    speech = client.audio.speech.create(model="tts-1", voice="nova", input=trad)
    
    # Mostrar Resultado en Tarjeta
    st.markdown(f"""
    <div class="chat-card">
        <div style="color: grey; font-size: 0.8rem; text-align: center;">DICE: "{trans.text}"</div>
        <div class="trad-text">{trad}</div>
    </div>
    """, unsafe_allow_html=True)
    st.audio(speech.content, autoplay=True)

# Botones de Acción
st.markdown("<p class='lang-label'>🇦🇷 YO HABLO</p>", unsafe_allow_html=True)
audio_ar = mic_recorder(start_prompt="HABLAR (ESPAÑOL)", stop_prompt="PROCESANDO...", key='ar')
if audio_ar: procesar_v2(audio_ar['bytes'], True)

st.markdown(f"<p class='lang-label'>🌐 ÉL HABLA ({info['label']})</p>", unsafe_allow_html=True)
audio_ex = mic_recorder(start_prompt=f"HABLAR ({info['label']})", stop_prompt="PROCESANDO...", key='ex')
if audio_ex: procesar_v2(audio_ex['bytes'], False)
