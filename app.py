import streamlit as st
import base64
import pypdf
import io
import time
import subprocess
import json
from openai import OpenAI

# Page config - EtherChat Premium
st.set_page_config(page_title="EtherChat | Local AI", page_icon="🔮", layout="wide")

# Helper to load local images as base64 for CSS background
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Background and icon paths
bg_path = r"C:/Users/hemra/.gemini/antigravity/brain/71ed8a64-d452-4453-9152-78561772a936/fantasy_bg_premium_1767197253696.png"
icon_path = r"C:/Users/hemra/.gemini/antigravity/brain/71ed8a64-d452-4453-9152-78561772a936/ai_decorative_icon_1767197271843.png"

try:
    bg_base64 = get_base64_of_bin_file(bg_path)
    icon_base64 = get_base64_of_bin_file(icon_path)
except:
    bg_base64 = ""
    icon_base64 = ""

# Custom CSS - Responsive Stripe-style Glassmorphism + Fantasy Theme
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    :root {{
        --glass-bg: rgba(13, 17, 23, 0.7);
        --glass-border: rgba(255, 255, 255, 0.1);
        --accent-purple: #9966ff;
        --accent-blue: #4da6ff;
        --text-main: #e6edf3;
    }}

    .stApp {{
        background-image: linear-gradient(rgba(13, 17, 23, 0.8), rgba(13, 17, 23, 0.8)), url("data:image/png;base64,{bg_base64}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        font-family: 'Outfit', sans-serif;
        color: var(--text-main);
    }}

    /* Global Responsive Adjustments */
    @media (max-width: 768px) {{
        .premium-header {{ font-size: 1.8rem !important; }}
        .stChatMessage {{ padding: 1rem !important; border-radius: 15px !important; }}
        [data-testid="stSidebar"] {{ width: 100% !important; }}
    }}

    /* Hide default Streamlit style */
    [data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stSidebar"] {{
        background: rgba(20, 24, 33, 0.8) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
    }}

    /* Premium Heading */
    .premium-header {{
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        text-align: center;
        letter-spacing: -1px;
    }}

    /* Message Styling */
    .stChatMessage {{
        background: var(--glass-bg) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease;
    }}
    .stChatMessage:hover {{
        transform: translateY(-2px);
        border-color: rgba(255, 255, 255, 0.2) !important;
    }}

    /* Input & Buttons (Stripe Like) */
    .stTextInput input, .stTextArea textarea, .stChatInput input {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 12px 16px !important;
    }}

    /* Custom Button Style */
    .stButton button {{
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        color: white;
        font-weight: 600;
        padding: 0.6rem 1rem;
        width: 100%;
        display: block;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .stButton button:hover {{
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple));
        border-color: transparent;
        transform: scale(1.02);
    }}

    /* Sidebar Status Cards */
    .status-card {{
        padding: 1rem;
        border-radius: 15px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--glass-border);
        margin-bottom: 1rem;
    }}

    /* Sidebar AI Icon */
    .ai-orb {{
        width: 80px;
        max-width: 40%;
        display: block;
        margin: 0 auto 1rem;
        filter: drop-shadow(0 0 20px rgba(153, 102, 255, 0.4));
        animation: float 6s ease-in-out infinite;
    }}

    @keyframes float {{
        0% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
        100% {{ transform: translateY(0px); }}
    }}

    /* Scrollbar */
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-thumb {{
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# === SIDEBAR LOGO & TITLE ===
with st.sidebar:
    st.markdown(f'<img src="data:image/png;base64,{icon_base64}" class="ai-orb">', unsafe_allow_html=True)
    st.markdown('<div style="text-align: center; font-size: 1.5rem; font-weight: 700; margin-bottom: 1rem;">EtherChat</div>', unsafe_allow_html=True)

# === HELPER FUNCTIONS ===

def is_vision_model(model_name):
    vision_keywords = ['vision', 'llava', 'bakllava', 'moondream', 'yi-vl', 'qwen-vl', 'minicpm-v', 'cogvlm', 'clip']
    return any(keyword in model_name.lower() for keyword in vision_keywords)

def encode_image(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    return None

def extract_pdf_text(uploaded_file):
    try:
        reader = pypdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Failed to read PDF: {str(e)}")
        return None

@st.cache_data(ttl=300) # Cache for 5 mins to prevent flicker
def get_lms_models():
    try:
        result = subprocess.run("lms ls", shell=True, capture_output=True, text=True, encoding='utf-8')
        lines = result.stdout.split('\n')
        models = []
        for line in lines:
            line = line.strip()
            if not line: continue
            if "LLM" in line and "ARCH" in line: continue 
            if "You have" in line: continue
            parts = line.split()
            if len(parts) >= 2 and ("GB" in line or "MB" in line):
                if "embedding" in line.lower(): continue
                models.append(parts[0])
        return models
    except:
        return []

def check_connection(base_url):
    try:
        client = OpenAI(base_url=base_url, api_key="lm-studio")
        models = client.models.list()
        active_id = models.data[0].id if models.data else None
        return client, active_id
    except:
        return None, None

# === MAIN APP LOGIC ===

if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_unloading" not in st.session_state:
    st.session_state.is_unloading = False
if "unload_start_time" not in st.session_state:
    st.session_state.unload_start_time = 0

with st.sidebar:
    st.header("⚙️ Configuration")
    base_url = st.text_input("LM Studio URL", "http://localhost:1234/v1")
    
    st.divider()
    
    client_conn, active_model_id = check_connection(base_url)

    if st.session_state.is_unloading:
        time_waiting = time.time() - st.session_state.unload_start_time
        if time_waiting > 10:
            st.session_state.is_unloading = False
            st.error("⚠️ Unload timed out.")
            st.rerun()
            
        if active_model_id:
            st.warning(f"⏳ Purging Core...\n({int(10 - time_waiting)}s)")
            time.sleep(1) 
            st.rerun()    
        else:
            st.session_state.is_unloading = False
            st.success("✅ System Purged")
            time.sleep(1)
            st.rerun()

    if client_conn and active_model_id and not st.session_state.is_unloading:
        st.markdown(f"""
        <div class="status-card" style="border-left: 4px solid var(--accent-blue);">
            <div style="font-size: 0.7rem; color: #888; letter-spacing: 1px;">NEURAL LINK ACTIVE</div>
            <div style="font-weight: 700; color: var(--accent-blue); font-size: 0.9rem; margin-top: 4px;">{active_model_id}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-card" style="border-left: 4px solid #ff4d4d; background: rgba(255, 77, 77, 0.05);">
            <div style="font-size: 0.7rem; color: #888; letter-spacing: 1px;">CORE DISCONNECTED</div>
            <div style="font-weight: 700; color: #ff4d4d; font-size: 0.9rem; margin-top: 4px;">No Active Link</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.subheader("Core Selection")
    
    # Refresh list control
    if st.button("🔄 Sync Model List", help="Click if you downloaded new models in LM Studio"):
        st.cache_data.clear()
        st.rerun()

    known_models = get_lms_models()
    if not known_models:
        known_models = ["qwen/qwen3-4b-thinking-2507", "llama-3.1-8b-lexi-uncensored-v2", "dolphin-2.9-llama3-8b"]
    
    default_ix = 0
    if active_model_id:
        for i, m in enumerate(known_models):
            if active_model_id in m or m in active_model_id:
                default_ix = i
                break
                
    selected_load = st.selectbox("Choose Fragment:", known_models, index=default_ix)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔮 Load Core", use_container_width=True):
            with st.spinner("Linking..."):
                st.session_state.is_unloading = False
                subprocess.run("lms unload --all", shell=True)
                time.sleep(1)
                subprocess.run(f'lms load "{selected_load}"', shell=True)
                start_wait = time.time()
                while time.time() - start_wait < 45:
                    _, check_id = check_connection(base_url)
                    if check_id: break
                    time.sleep(1)
                st.rerun()

    with col2:
        if st.button("💀 Purge Core", use_container_width=True):
             st.session_state.is_unloading = True
             st.session_state.unload_start_time = time.time()
             subprocess.run("lms unload --all", shell=True)
             st.rerun()

    if st.session_state.is_unloading:
        if st.button("Reset Sensor Loop"):
            st.session_state.is_unloading = False
            st.rerun()

    st.divider()
    system_prompt = st.text_area("System Directives", "You are a mystical AI advisor in a high-tech fantasy realm.")
    model_id = active_model_id if active_model_id else "local-model"

# Main Chat Display
st.markdown('<div class="premium-header">EtherChat Global Terminal</div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"]:
            st.image(base64.b64decode(message["image"]))

with st.expander("📎 Augment Query (Image/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Upload Fragment", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if prompt := st.chat_input("Relay message to the core..."):
    encoded_img = None
    pdf_text = None
    
    if uploaded_file:
        file_type = uploaded_file.type
        if "image" in file_type:
            if not is_vision_model(model_id):
                st.toast("⚠️ Core lacks Vision. Sending text only.", icon="⚠️")
            else:
                encoded_img = encode_image(uploaded_file)
        elif "pdf" in file_type:
            with st.spinner("Extracting Knowledge..."):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text:
                    prompt = f"Reference Fragment:\n{pdf_text}\n\n---\nRelay: {prompt}"

    new_message = {"role": "user", "content": prompt}
    if encoded_img: new_message["image"] = encoded_img
    st.session_state.messages.append(new_message)
    
    with st.chat_message("user"):
        display_prompt = prompt
        if pdf_text and len(pdf_text) > 200:
             display_prompt = prompt.split("Relay:")[1].strip() if "Relay:" in prompt else prompt
             st.info(f"📜 Knowledge Scroll Attached")
        st.markdown(display_prompt)
        if encoded_img: st.image(uploaded_file)

    with st.chat_message("assistant"):
        if not active_model_id:
            st.error("⛔ System Offline. Load a Core in the configuration hub.")
            st.stop()
            
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        full_response = ""
        is_thinking = False
        start_time = time.time()
        token_count = 0 
        
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            content = [{"type": "text", "text": m["content"]}]
            if "image" in m and m["image"]:
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{m['image']}"}})
            api_messages.append({"role": m["role"], "content": content})

        try:
            client = OpenAI(base_url=base_url, api_key="lm-studio")
            stream = client.chat.completions.create(
                model=model_id,
                messages=api_messages,
                stream=True,
                temperature=0.8,
            )
            
            response_buffer = "" 
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    token_count += 1 
                    for char in content_chunk:
                        response_buffer += char
                        if not is_thinking:
                            if "<think>" in response_buffer:
                                parts = response_buffer.split("<think>")
                                if parts[0]: 
                                    full_response += parts[0]
                                    message_placeholder.markdown(full_response + "▌")
                                response_buffer = "" 
                                is_thinking = True
                                status_placeholder.status("Astral Reasoning...", expanded=False)
                            elif not any("<think>".startswith(response_buffer[-i:]) for i in range(1, 8)):
                                full_response += response_buffer
                                message_placeholder.markdown(full_response + "▌")
                                response_buffer = ""
                        else:
                            if "</think>" in response_buffer:
                                response_buffer = ""
                                is_thinking = False
                                status_placeholder.empty()
                            elif not any("</think>".startswith(response_buffer[-i:]) for i in range(1, 9)):
                                response_buffer = ""

            if response_buffer and not is_thinking: full_response += response_buffer
            
            status_placeholder.empty()
            message_placeholder.markdown(full_response)
            
            duration = time.time() - start_time
            tps = token_count / duration if duration > 0 else 0
            metrics_msg = f"<p style='color: #888; font-size: 0.8em; margin-top: 0.5em;'>Resonated {token_count} echoes • {tps:.2f} e/s • {duration:.2f}s</p>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.markdown(metrics_msg, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Distortion detected: {str(e)}")
