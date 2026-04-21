import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración Base
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Scroll dinámico y fijación de controles
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }

    /* Contenedor principal */
    .main .block-container {
        max-width: 100% !important;
        padding: 1rem 5% 20px 5% !important;
        display: flex;
        flex-direction: column;
    }

    /* AREA DE CHAT: Ocupa el espacio disponible sin tapar los mics */
    .chat-scroll-area {
        height: 50vh; /* Usa el 50% de la altura de la pantalla */
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 10px;
        padding: 15px;
        background: rgba(255,255,255,0.03);
        border-radius: 20px;
        border: 1px solid #333;
        margin-bottom: 20px;
    }

    /* Burbujas tipo WhatsApp */
    .bubble { padding: 12px 16px; border-radius: 18px; max-width: 80%; animation: fadeIn 0.3s; }
    .bubble-me { background-color: #005C4B; color: #E9EDEF; align-self: flex-start; border-left: 5px solid #00A884; }
    .bubble-ex { background-color: #202C33; color: #E9EDEF; align-self: flex-end; border-right: 5px solid #FF3B30; text-align: right; }

    .trad-text { font-size: 1.1rem; font-weight: 700; display: block; }
    .orig-text { font-size: 0.8rem; opacity: 0.5; display: block; }

    /* Fila de Micrófonos: Siempre visibles abajo */
    .mic-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        padding-top: 10px;
        border-top: 1px solid #222;
    }
    
    .stButton > button {
        border-radius: 50% !important;
        width: 70px !important;
        height: 70px !important;
        border: none !important;
        font-size: 1.8rem !important;
    }
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }

    .label-tag { font-size: 0.7rem; font-weight: bold; text-align: center; margin-bottom: 5px; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# 3. Estado de la Sesión (Persistencia y control de bucle)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_processed_id' not in st.session_state:
    st.session_state.last_processed_id = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"prompt": "English", "label": "ING"},
    "Chino": {"prompt": "Chinese", "label": "CHI"},
    "Portugués": {"prompt": "Portuguese", "label": "POR"},
    "Italiano": {"prompt": "Italian", "label": "ITA"}
}

# 4. Cabecera y Configuración
st.markdown("<h3 style='text-align:center; color:white; margin-top:-20px;'>Interprete Pro</h3>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 1])
with c1: 
    idioma_sel = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    # Voz Masculina por defecto (index=1)
    genero_sel = st.selectbox("", ["Voz Femenina", "Voz Masculina"], index=1, label_visibility="collapsed")
with c3:
    if st.button("🗑️ Limpiar"):
        st.session_state.history = []
        st.session_state.last_processed_id = None
        st.rerun()

info = config_idiomas[idioma_sel]
voz_id = "onyx" if "Masc" in genero_sel else "nova"

# 5. Función de procesamiento (Lógica anti-bucle)
def procesar_audio(audio_data, es_yo):
    # Generar un ID único basado en el tamaño de los bytes para evitar repetir el mismo audio
    audio_id = hash(audio_data['bytes'])
    if st.session_state.last_processed_id == audio_id:
        return

    with st.spinner("..."):
        audio_file = io.BytesIO(audio_data['bytes']); audio_file.name = "audio.mp3"
        trans = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        
        sys_msg = f"Translate to {info['prompt']}" if es_yo else "Traducí al español de Argentina (voseo)."
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": f"{sys_msg}. Solo texto."}, {"role": "user", "content": trans.text}]
        )
        trad = res.choices[0].message.content
        speech = client.audio.speech.create(model="tts-1", voice=voz_id, input=trad)
        
        # Guardar en historial y marcar como procesado
        st.session_state.history.append({
            "es_yo": es_yo,
            "orig": trans.text,
            "trad": trad,
            "audio": speech.content
        })
        st.session_state.last_processed_id = audio_id
        st.rerun()

# --- INTERFAZ ---

# Area de Chat con Scroll
chat_container = st.empty()
with chat_container.container():
    chat_html = '<div class="chat-scroll-area">'
    for msg in st.session_state.history:
        side = "bubble-me" if msg["es_yo"] else "bubble-ex"
        chat_html += f'''
        <div class="bubble {side}">
            <span class="orig-text">"{msg["orig"]}"</span>
            <span class="trad-text">{msg["trad"]}</span>
        </div>
        '''
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

# Reproductor de audio automático del último mensaje
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio"], autoplay=True)

# Controles inferiores (Fijos)
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)

col_yo, col_el = st.columns(2)

with col_yo:
    st.markdown("<p class='label-tag' style='color:#007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    audio_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if audio_yo: procesar_audio(audio_yo, True)

with col_el:
    st.markdown(f"<p class='label-tag' style='color:#FF3B30;'>🌐 EL ({info['label']})</p>", unsafe_allow_html=True)
    audio_el = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if audio_el: procesar_audio(audio_el, False)

st.markdown("</div>", unsafe_allow_html=True)
