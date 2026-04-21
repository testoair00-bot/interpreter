import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS Avanzado: Maxi-Botones, Animaciones de Pulso y Textos Grandes
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

    /* Animación de Pulso Suave */
    @keyframes pulse {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 15px rgba(255, 255, 255, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
    }

    /* Maxi-Botones Circulares a la derecha */
    .stButton>button {
        border-radius: 50% !important;
        width: 90px !important; /* Más grandes */
        height: 90px !important;
        border: none !important;
        color: white !important;
        font-size: 2rem !important;
        animation: pulse 2s infinite; /* Animación constante */
        box-shadow: 0 8px 25px rgba(0,0,0,0.5);
    }

    /* Colores Específicos */
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ar"] { background-color: #007AFF !important; }
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ex"] { background-color: #FF3B30 !important; }

    /* Tarjetas de Chat más grandes */
    .chat-card {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 25px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 10px;
    }
    
    .trad-text {
        font-size: 1.6rem !important; /* Texto de traducción más grande */
        font-weight: 800;
        text-align: center;
        line-height: 1.2;
    }

    .orig-text {
        color: #8E8E93;
        font-size: 0.9rem;
        text-align: center;
        font-style: italic;
    }

    /* Etiquetas de Idioma */
    .lang-label {
        font-size: 1rem !important;
        letter-spacing: 1px;
        margin-bottom: 5px !important;
    }

    /* Selector de voz y lengua */
    .stSelectbox label { display: none; }
    div[data-baseweb="select"] {
        background-color: #1C1C1E !important;
        border-radius: 15px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialización
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "INGLÉS"},
    "Chino": {"prompt": "Chinese", "label": "CHINO"},
    "Portugués": {"prompt": "Portuguese", "label": "PORTUGUÉS"},
    "Italiano": {"prompt": "Italian", "label": "ITALIANO"},
    "Francés": {"prompt": "French", "label": "FRANCÉS"}
}

voces = {
    "Femenina (Nova)": "nova",
    "Masculina (Onyx)": "onyx",
    "Femenina Suave (Shimmer)": "shimmer",
    "Masculina Enérgica (Fable)": "fable"
}

st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 0;'>Interprete Digital</h2>", unsafe_allow_html=True)

col_head1, col_head2 = st.columns(2)
with col_head1:
    idioma_sel = st.selectbox("Idioma", list(config_idiomas.keys()))
with col_head2:
    voz_sel = st.selectbox("Voz", list(voces.keys()))

info = config_idiomas[idioma_sel]
voz_id = voces[voz_sel]

def procesar_v3(audio_bytes, es_a_extranjero=True, card_color="#007AFF"):
    if not audio_bytes: return
    with st.spinner("Traduciendo..."):
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.mp3"
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        sys_msg = f"Translate to {info['prompt']}" if es_a_extranjero else "Traducí al español de Argentina (voseo)."
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"{sys_msg}. Solo texto."}, {"role": "user", "content": trans.text}]
        )
        trad = res.choices[0].message.content
        speech = client.audio.speech.create(model="tts-1", voice=voz_id, input=trad)
        
        st.markdown(f"""
        <div class="chat-card" style="border-bottom: 6px solid {card_color};">
            <div class="orig-text">"{trans.text}"</div>
            <div class="trad-text" style="color: {card_color};">{trad}</div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(speech.content, autoplay=True)

# --- BLOQUES DE INTERFAZ ---

# 1. YO HABLO
st.markdown("<p class='lang-label' style='color: #007AFF;'>🇦🇷 YO HABLO (ESPAÑOL)</p>", unsafe_allow_html=True)
col_ar_txt, col_ar_btn = st.columns([2.5, 1])

with col_ar_btn:
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')

with col_ar_txt:
    if audio_ar:
        procesar_v3(audio_ar['bytes'], True, "#007AFF")
    else:
        st.markdown("<p style='color:#444; font-size: 1.2rem;'>Toca el botón azul...</p>", unsafe_allow_html=True)

st.divider()

# 2. ÉL HABLA
st.markdown(f"<p class='lang-label' style='color: #FF3B30;'>🌐 INTERLOCUTOR ({info['label']})</p>", unsafe_allow_html=True)
col_ex_txt, col_ex_btn = st.columns([2.5, 1])

with col_ex_btn:
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')

with col_ex_txt:
    if audio_ex:
        procesar_v3(audio_ex['bytes'], False, "#FF3B30")
    else:
        st.markdown(f"<p style='color:#444; font-size: 1.2rem;'>Toca el botón rojo...</p>", unsafe_allow_html=True)
