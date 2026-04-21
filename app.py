import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS Avanzado: Animaciones, Colores y Layout a la derecha
st.markdown("""
    <style>
    /* Fondo y Reset */
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; display: none !important; 
    }

    /* Contenedor Principal */
    .main .block-container {
        max-width: 100% !important;
        padding: 2rem 8% 150px 8% !important;
    }

    /* Tarjetas de Chat */
    .chat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .trad-text {
        color: #007AFF;
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        margin-top: 5px;
    }

    /* Alineación de Botones a la Derecha */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 25px;
        padding: 10px 15px !important;
        margin: 10px 0 !important;
    }

    /* Estilos de Botones Circulares */
    .stButton>button {
        border-radius: 50% !important;
        width: 70px !important;
        height: 70px !important;
        border: none !important;
        color: white !important;
        font-size: 1.5rem !important;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }

    /* Colores por ID (vía el texto del botón o selectores específicos) */
    /* YO HABLO (Azul) */
    div.stButton > button:first-child[kind="primary"], 
    div.stButton > button:contains("🎙️") { background-color: #007AFF !important; }
    
    /* Animación de Pulso (Escuchando) */
    @keyframes pulse-blue {
        0% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(0, 122, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(0, 122, 255, 0); }
    }
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7); }
        70% { box-shadow: 0 0 0 15px rgba(255, 59, 48, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
    }

    /* Aplicación de colores y animaciones según la key */
    div[data-testid="stColumn"]:has(button[key="ar"]) button { background-color: #007AFF !important; }
    div[data-testid="stColumn"]:has(button[key="ex"]) button { background-color: #FF3B30 !important; }

    /* Forzar que el audio sea visible */
    stAudio { margin-top: 10px !important; width: 100% !important; }

    /* Selector de Idioma */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1C1C1E !important;
        border-radius: 12px !important;
    }
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

st.markdown("<h3 style='text-align: center; color: white; margin-bottom: 0;'>Interprete Digital</h3>", unsafe_allow_html=True)
idioma_sel = st.selectbox("", list(config_idiomas.keys()))
info = config_idiomas[idioma_sel]

def procesar_v2(audio_bytes, es_a_extranjero=True, card_color="#007AFF"):
    if not audio_bytes: return
    with st.spinner("..."):
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
        
        st.markdown(f"""
        <div class="chat-card" style="border-left: 5px solid {card_color};">
            <div style="color: #8E8E93; font-size: 0.75rem; text-align: center;">"{trans.text}"</div>
            <div class="trad-text" style="color: {card_color};">{trad}</div>
        </div>
        """, unsafe_allow_html=True)
        st.audio(speech.content, autoplay=True)

# --- BLOQUES DE INTERACCIÓN (Botones a la derecha) ---

# BLOQUE YO (ARGENTINA)
st.markdown("<p style='font-size:0.7rem; color: #8E8E93; margin-bottom: -10px;'>🇦🇷 YO HABLO</p>", unsafe_allow_html=True)
col_ar_txt, col_ar_btn = st.columns([3, 1])
with col_ar_btn:
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='ar')
with col_ar_txt:
    if audio_ar:
        procesar_v2(audio_ar['bytes'], True, "#007AFF")
    else:
        st.caption("Presioná el círculo azul")

st.write("") # Espaciador

# BLOQUE ÉL (EXTRANJERO)
st.markdown(f"<p style='font-size:0.7rem; color: #8E8E93; margin-bottom: -10px;'>🌐 ÉL HABLA ({info['label']})</p>", unsafe_allow_html=True)
col_ex_txt, col_ex_btn = st.columns([3, 1])
with col_ex_btn:
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='ex')
with col_ex_txt:
    if audio_ex:
        procesar_v2(audio_ex['bytes'], False, "#FF3B30")
    else:
        st.caption(f"Presioná el círculo rojo")
