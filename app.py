import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# Configuración Base
st.set_page_config(page_title="Traductor Pro", layout="centered")

# CSS para Interfaz de App Nativa (Minimalista)
st.markdown("""
    <style>
    /* 1. CONFIGURACIÓN DE FONDO Y RECORTE */
    .stApp { 
        background-color: #0E1117; 
        overflow: hidden !important;
    }
    
    /* Ocultar elementos nativos (Plan A) */
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; 
        display: none !important; 
    }
    button[title="View fullscreen"] { display: none !important; }

    /* 2. CONTENEDOR TIPO TARJETA Y TRUCO ANTI-ZÓCALO */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 10% !important;  /* Le da aire a los costados */
        padding-right: 10% !important;
        padding-top: 2rem !important;
        padding-bottom: 120px !important; /* Espacio para que el corte no tape botones */
    }

    /* 3. ESTILO DE COMPONENTES (Glassmorphism) */
    .stCaption { 
        color: #8E8E93 !important; 
        font-size: 0.85rem !important; 
        text-align: center; 
        margin-top: 5px;
    }
    
    .chat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 22px;
        padding: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }

    .trad-text {
        color: #007AFF;
        font-size: 1.4rem;
        font-weight: 700;
        text-align: center;
        margin: 8px 0;
        line-height: 1.2;
    }

    /* 4. BOTONES GIGANTES ADAPTADOS */
    div[data-testid="stHorizontalBlock"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 20px;
        padding: 15px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .stButton>button {
        width: 100% !important;
        height: 65px !important;
        border-radius: 18px !important;
        background-color: #007AFF !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        border: none !important;
        transition: transform 0.1s;
    }
    
    .stButton>button:active {
        transform: scale(0.98);
        background-color: #0056b3 !important;
    }

    /* 5. SELECTOR DE IDIOMA MINIMALISTA */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1C1C1E !important;
        border: 1px solid #333 !important;
        border-radius: 12px !important;
        color: white !important;
    }
    
    /* Eliminar espaciado extra de dividers */
    hr { margin: 1rem 0 !important; border-bottom: 1px solid rgba(255,255,255,0.1) !important; }
    
    /* Forzar que el zócalo de componentes (mic_recorder) sea invisible */
    .stCustomComponentV1 { margin-bottom: -20px !important; }
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
