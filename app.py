import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de Página
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS Global
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }
    .main .block-container { max-width: 100% !important; padding: 1rem 5% 20px 5% !important; }
    
    /* Fila de Mics */
    .mic-row { display: flex; justify-content: space-around; padding-top: 15px; border-top: 1px solid #333; }
    .stButton > button { border-radius: 50% !important; width: 75px !important; height: 75px !important; border: none !important; }
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }
    .tag { font-size: 0.8rem; font-weight: bold; text-align: center; color: #888; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Estados de Sesión
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

# 4. Cabecera
st.markdown("<h3 style='text-align:center; color:white;'>Interprete Digital</h3>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 0.5])
with c1: 
    lang = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    gen = st.selectbox("", ["Voz Femenina", "Voz Masculina"], index=1, label_visibility="collapsed")
with c3:
    if st.button("🗑️"):
        st.session_state.history = []
        st.session_state.last_id = None
        st.rerun()

info = config_idiomas[lang]
v_id = "onyx" if "Masc" in gen else "nova"

# 5. Lógica de Procesamiento
def procesar(audio_data, es_yo):
    curr_id = hash(audio_data['bytes'])
    if st.session_state.last_id == curr_id: return

    with st.spinner(""):
        buf = io.BytesIO(audio_data['bytes']); buf.name = "audio.mp3"
        t_res = client.audio.transcriptions.create(model="whisper-1", file=buf)
        
        sys_p = f"Translate Spanish to {info['p']}." if es_yo else f"Translate {info['p']} to Spanish (Argentina 'voseo')."
        c_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_p + " Only the translated text."}, {"role": "user", "content": t_res.text}]
        )
        trad = c_res.choices[0].message.content
        s_res = client.audio.speech.create(model="tts-1", voice=v_id, input=trad)
        
        st.session_state.history.append({"me": es_yo, "orig": t_res.text, "trad": trad, "audio": s_res.content})
        st.session_state.last_id = curr_id
        st.rerun()

# --- RENDERIZADO VISUAL ---

# Construcción del HTML de las burbujas (Sin errores de escape)
chat_html = """
<div id="chat" style="display:flex; flex-direction:column; gap:12px; font-family:sans-serif; background:#0E1117; padding:10px;">
"""
for m in st.session_state.history:
    align = "flex-start" if m["me"] else "flex-end"
    bg = "#005C4B" if m["me"] else "#202C33"
    border = "5px solid #00A884" if m["me"] else "5px solid #FF3B30"
    chat_html += f"""
    <div style="align-self:{align}; background:{bg}; color:white; padding:12px; border-radius:15px; border-left:{border if m['me'] else 'none'}; border-right:{'none' if m['me'] else border}; max-width:85%;">
        <div style="font-size:0.75rem; opacity:0.5; font-style:italic;">"{m['orig']}"</div>
        <div style="font-size:1.1rem; font-weight:700; margin-top:4px;">{m['trad']}</div>
    </div>
    """
chat_html += "</div><script>window.scrollTo(0, document.body.scrollHeight);</script>"

# Inyectar el chat como un componente HTML real (Esto evita que se vea el código)
st.components.v1.html(f"<body style='background:#0E1117; margin:0;'>{chat_html}</body>", height=300, scrolling=True)

# Audio del último mensaje
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio"], autoplay=True)

# Mics
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)
cl, cr = st.columns(2)
with cl:
    st.markdown("<p class='tag' style='color:#007AFF;'>🇦🇷 YO</p>", unsafe_allow_html=True)
    a_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if a_yo: procesar(a_yo, True)
with cr:
    st.markdown(f"<p class='tag' style='color:#FF3B30;'>🌐 {info['l']}</p>", unsafe_allow_html=True)
    a_el = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if a_el: procesar(a_el, False)
st.markdown("</div>", unsafe_allow_html=True)
