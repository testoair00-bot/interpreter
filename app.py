import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Botones a la derecha, colores y animaciones
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; overflow: hidden !important; }
    header, footer, [data-testid="stHeader"], [data-testid="stStatusWidget"] { 
        visibility: hidden !important; display: none !important; 
    }

    /* Contenedor Principal con espacio para el recorte inferior */
    .main .block-container {
        max-width: 100% !important;
        padding: 2rem 6% 160px 6% !important;
    }

    /* Forzar alineación horizontal: Texto izquierda (3), Botón derecha (1) */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 25px;
        padding: 10px 15px !important;
        margin: 10px 0 !important;
    }

    /* Estilo de los Botones Circulares */
    .stButton>button {
        border-radius: 50% !important;
        width: 75px !important;
        height: 75px !important;
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.4);
    }

    /* Color YO HABLO (Arriba - Azul) */
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ar"] {
        background-color: #007AFF !important;
    }

    /* Color ÉL HABLA (Abajo - Rojo) */
    div[data-testid="column"]:nth-of-type(2) button[key="mic_ex"] {
        background-color: #FF3B30 !important;
    }

    /* Tarjetas de Resultado */
    .chat-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 20px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 10px;
    }
    
    .trad-text {
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        margin-top: 5px;
    }

    /* Ajuste de Audio */
    stAudio { width: 100% !important; }
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

st.markdown("<h3 style='text-align: center; color: white;'>Interprete Digital</h3>", unsafe_allow_html=True)
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

# --- BLOQUES DE INTERFÁZ ---

# 1. BLOQUE SUPERIOR: YO HABLO (AR)
st.markdown("<p style='font-size:0.75rem; color: #007AFF; font-weight: bold;'>🇦🇷 YO HABLO</p>", unsafe_allow_html=True)
col_ar_txt, col_ar_btn = st.columns([3, 1])

with col_ar_btn:
    audio_ar = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')

with col_ar_txt:
    if audio_ar:
        procesar_v2(audio_ar['bytes'], True, "#007AFF")
    else:
        st.caption("Tocá el botón azul para hablar")

st.divider()

# 2. BLOQUE INFERIOR: ÉL HABLA (EXTRANJERO)
st.markdown(f"<p style='font-size:0.75rem; color: #FF3B30; font-weight: bold;'>🌐 ÉL HABLA ({info['label']})</p>", unsafe_allow_html=True)
col_ex_txt, col_ex_btn = st.columns([3, 1])

with col_ex_btn:
    audio_ex = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')

with col_ex_txt:
    if audio_ex:
        procesar_v2(audio_ex['bytes'], False, "#FF3B30")
    else:
        st.caption(f"Esperando {info['label']}... (Botón Rojo)")
