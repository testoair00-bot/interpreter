import streamlit as st
from openai import OpenAI
from streamlit_mic_recorder import mic_recorder
import io

# 1. Configuración de Página
st.set_page_config(page_title="Interprete Pro", layout="centered")

# 2. CSS: WhatsApp Dark Style
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    header, footer, [data-testid="stHeader"] { visibility: hidden !important; height: 0; }
    .main .block-container { max-width: 100% !important; padding: 1rem 5% 10px 5% !important; }
    
    .mic-row { display: flex; justify-content: space-around; padding-top: 15px; border-top: 1px solid #333; margin-top: 10px; }
    .stButton > button { border-radius: 50% !important; width: 70px !important; height: 70px !important; border: none !important; }
    button[key="mic_ar"] { background-color: #007AFF !important; }
    button[key="mic_ex"] { background-color: #FF3B30 !important; }
    .tag { font-size: 0.75rem; font-weight: bold; text-align: center; color: #888; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Estados de Sesión (Para evitar repeticiones)
if 'history' not in st.session_state:
    st.session_state.history = []
if 'last_ar_id' not in st.session_state: # ID último audio tuyo
    st.session_state.last_ar_id = None
if 'last_ex_id' not in st.session_state: # ID último audio de él
    st.session_state.last_ex_id = None

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

config_idiomas = {
    "Inglés": {"p": "English", "l": "ING"},
    "Chino": {"p": "Chinese", "l": "CHI"},
    "Portugués": {"p": "Portuguese", "l": "POR"},
    "Italiano": {"p": "Italian", "l": "ITA"}
}

# 4. Header y Controles
st.markdown("<h4 style='text-align:center; color:white; margin:0;'>Interprete Digital</h4>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1.5, 1, 0.5])
with c1: 
    lang = st.selectbox("", list(config_idiomas.keys()), label_visibility="collapsed")
with c2: 
    gen = st.selectbox("", ["Voz Fem.", "Voz Masc."], index=1, label_visibility="collapsed")
with c3:
    if st.button("🗑️"):
        st.session_state.history = []
        st.session_state.last_ar_id = None
        st.session_state.last_ex_id = None
        st.rerun()

info = config_idiomas[lang]
v_id = "onyx" if "Masc" in gen else "nova"

# 5. Función de Procesamiento con Filtro de ID
def procesar_traduccion(audio_data, es_yo):
    # Crear ID único para este audio específico
    m_id = hash(audio_data['bytes'])
    
    # Verificar si este audio ya fue procesado según el botón que se tocó
    if es_yo and st.session_state.last_ar_id == m_id: return
    if not es_yo and st.session_state.last_ex_id == m_id: return

    with st.spinner(""):
        buf = io.BytesIO(audio_data['bytes'])
        buf.name = "audio.mp3"
        
        # Transcripción
        t_res = client.audio.transcriptions.create(model="whisper-1", file=buf)
        
        # Prompts Directos
        if es_yo:
            sys_p = f"Translate Spanish to {info['p']}. Output ONLY the translation."
        else:
            sys_p = f"Translate {info['p']} to Spanish (Argentina 'voseo'). Output ONLY the translation."
        
        c_res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": sys_p}, {"role": "user", "content": t_res.text}]
        )
        trad = c_res.choices[0].message.content
        s_res = client.audio.speech.create(model="tts-1", voice=v_id, input=trad)
        
        # Guardar en historial
        st.session_state.history.append({
            "me": es_yo,
            "orig": t_res.text,
            "trad": trad,
            "audio": s_res.content
        })
        
        # Actualizar el ID correspondiente para bloquear re-procesamiento
        if es_yo: st.session_state.last_ar_id = m_id
        else: st.session_state.last_ex_id = m_id
        
        st.rerun()

# --- INTERFAZ ---

# Chat Histórico (Visor HTML)
chat_content = ""
for m in st.session_state.history:
    align = "flex-start" if m["me"] else "flex-end"
    bg = "#005C4B" if m["me"] else "#202C33"
    border = "4px solid #00A884" if m["me"] else "4px solid #FF3B30"
    chat_content += f"""
    <div style="align-self:{align}; background:{bg}; color:white; padding:10px 14px; border-radius:15px; margin-bottom:8px; max-width:80%; border-left:{border if m['me'] else 'none'}; border-right:{'none' if m['me'] else border};">
        <div style="font-size:0.7rem; opacity:0.5; font-style:italic;">"{m['orig']}"</div>
        <div style="font-size:1rem; font-weight:600;">{m['trad']}</div>
    </div>
    """

st.components.v1.html(f"""
<div id="box" style="display:flex; flex-direction:column; background:#0E1117; font-family:sans-serif;">
    {chat_content}
</div>
<script>window.scrollTo(0, document.body.scrollHeight);</script>
""", height=350, scrolling=True)

# Reproducir solo el último audio
if st.session_state.history:
    st.audio(st.session_state.history[-1]["audio"], autoplay=True)

# Controles inferiores
st.markdown("<div class='mic-row'>", unsafe_allow_html=True)
cl, cr = st.columns(2)

with cl:
    st.markdown("<p class='tag' style='color:#007AFF;'>🇦🇷 YO (ES)</p>", unsafe_allow_html=True)
    a_yo = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ar')
    if a_yo: procesar_traduccion(a_yo, True)

with cr:
    st.markdown(f"<p class='tag' style='color:#FF3B30;'>🌐 EL ({info['l']})</p>", unsafe_allow_html=True)
    a_el = mic_recorder(start_prompt="🎙️", stop_prompt="⌛", key='mic_ex')
    if a_el: procesar_traduccion(a_el, False)
st.markdown("</div>", unsafe_allow_html=True)
