import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de Página
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: Estilo Chat Robusto
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }
    
    /* Contenedor principal */
    .main .block-container { 
        max-width: 100% !important; 
        padding: 1rem 5% 30px 5% !important; 
    }

    /* AREA DE CHAT REPARADA */
    .chat-container {
        height: 45vh;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 15px;
        padding: 15px;
        background: #161C23;
        border-radius: 20px;
        margin-bottom: 20px;
        border: 1px solid #333;
    }

    /* Burbujas Blindadas */
    .bubble { 
        padding: 12px 16px; 
        border-radius: 18px; 
        max-width: 85%; 
        line-height: 1.4; 
        display: block;
        clear: both;
    }
    
    .bubble-me { 
        background-color: #005C4B; 
        color: #E9EDEF; 
        align-self: flex-start; 
        border-left: 5px solid #00A884;
        text-align: left;
    }
    
    .bubble-ex { 
        background-color: #202C33; 
        color: #E9EDEF; 
        align-self: flex-end; 
        border-right: 5px solid #FF3B30; 
        text-align: right;
    }

    .t-text { font-size: 1.1rem; font-weight: 700; margin-top: 4px; display: block; }
    .o-text { font-size: 0.8rem; opacity: 0.5; font-style: italic; display: block; }

    /* Fila de Mics */
    .mic-row { display: flex; justify-content: space-around; padding-top: 10px; }
    .stButton > button { border-radius: 50% !important; width: 75px !important; height: 75px !important; border: none !important; }
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }
    .tag { font-size: 0.7rem; font-weight: bold; text-align: center; margin-bottom: 5px; color: #888; }
    </style>
    """, unsafe_allow_html=True)

# 3. Inicialización de Sesión
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_id' not in st.session_state:
    st.session_state.last_id = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"p": "English", "l": "ING"},
    "Chino": {"p": "Chinese", "l": "CHI"},
    "Portugués": {"p": "Portuguese", "l": "POR"},
    "Italiano": {"p": "Italian", "l": "ITA"}
}

# 4. Cabecera y Controles
st.markdown("<h3 style='text-align:center; color:white; margin-bottom:15px;'>Interprete Digital</h3>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 1, 0.5])
with col1: 
    lang = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with col2: 
    # Voz Masculina por defecto
    gen = st.selectbox("", ["Voz Femenina", "Voz Masculina"], index=1, label_visibility="collapsed")
with col3:
    if st.button("🗑️"):
        st.session_state.history = []
        st.session_state.last_id = None
        st.rerun()

info = config_idiomas[lang]
v_id = "onyx" if "Masc" in gen else "nova"

# 5. Lógica de Traducción
def handle_audio(audio_data, is_me):
    # Generar ID único para evitar bucles
    curr_id = hash(audio_data['bytes'])
    if st.session_state.last_id == curr_id:
        return

    with st.spinner("..."):
        # Convertir audio
        buf = io.BytesIO(audio_data['bytes'])
        buf.name = "audio.mp3"
        
        # Transcripción
        t_res = client.audio.transcriptions.create(model="whisper-1", file=buf)
        
        # Traducción Cruzada
        if is_me:
            sys_p = f"Translate Spanish to {info['p']}. Output only the translation."
        else:
            sys_p = f"Translate {info['p']} to Spanish (Argentina 'voseo'). Output only the translation."
        
        c_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_p}, {"role": "user", "content": t_res.text}]
        )
        trad = c_res.choices[0].message.content
        
        # Voz
        s_res = client.audio.speech.create(model="tts-1", voice=v_id, input=trad)
        
        # Guardar y Refrescar
        st.session_state.history.append({
            "is_me": is_me,
            "orig": t_res.text,
            "trad": trad,
            "audio": s_res.content
        })
        st.session_state.last_id = curr_id
        st.rerun()

# --- INTERFAZ DE USUARIO ---

# Renderizado del Chat (Limpio y robusto)
history_html = '<div class="chat-container">'
for m in st.session_state.history:
    side = "bubble-me" if m["is_me"] else "bubble-ex"
    history_html += f'''
    <div class="bubble {side}">
        <span class="o-text">"{m["orig"]}"</span>
        <span class="t-text">{m["trad"]}</span>
    </div>
    '''
history_html += '</div>'
st.markdown(history_html, unsafe_allow_html=True)

# Reproducción de audio (Último mensaje)
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio"], autoplay=True)

# Controles de Micrófono
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)
cl, cr = st.columns(2)

with cl:
    st.markdown("<p class='tag' style='color:#007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    a_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if a_yo: handle_audio(a_yo, True)

with cr:
    st.markdown(f"<p class='tag' style='color:#FF3B30;'>🌐 EL ({info['l']})</p>", unsafe_allow_html=True)
    a_el = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if a_el: handle_audio(a_el, False)

st.markdown("</div>", unsafe_allow_html=True)
