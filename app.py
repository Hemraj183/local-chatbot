import streamlit as st
import base64
import pypdf
import io
import time
import subprocess
import json
from openai import OpenAI

# Page config
st.set_page_config(page_title="Local AI Chatbot", page_icon="🤖", layout="wide")

# Custom CSS - Modern Dark Theme (Softer than Sci-Fi)
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

    /* General Theme */
    .stApp {
        background-color: #0e1117; /* Standard dark background, less "void black" */
        font-family: 'Inter', sans-serif;
        color: #e0e0e0;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        background: linear-gradient(90deg, #4da6ff, #9966ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* User Message */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: rgba(77, 166, 255, 0.1);
        border-left: 3px solid #4da6ff;
    }
    
    /* AI Message */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: rgba(153, 102, 255, 0.1);
        border-right: 3px solid #9966ff;
    }

    /* Input Fields - High Visibility */
    .stTextInput input, .stTextArea textarea {
        background-color: #1e2329 !important; /* Lighter dark */
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        color: #fff !important;
        border-radius: 8px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #4da6ff !important;
        box-shadow: 0 0 0 1px #4da6ff !important;
    }
    
    /* Buttons */
    .stButton button {
        background-color: #21262d;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #e0e0e0;
        transition: all 0.2s ease;
    }
    
    .stButton button:hover {
        border-color: #4da6ff;
        color: #4da6ff;
    }
    
    /* Images */
    img {
        border-radius: 8px;
    }
    
    /* Status Container */
    .stStatusWidget {
        background-color: #1e2329 !important;
        border-color: #2f363d !important;
    }

</style>
""", unsafe_allow_html=True)

st.title("🤖 Local AI Chatbot")

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

# LMS CLI Helpers
def get_lms_models():
    try:
        # Run 'lms ls' 
        result = subprocess.run("lms ls", shell=True, capture_output=True, text=True, encoding='utf-8')
        lines = result.stdout.split('\n')
        models = []
        for line in lines:
            # Heuristic: Find lines with content but not headers
            args = line.split()
            if len(args) >= 3 and "GB" in line:
                 # Usually format: NAME PARAMS ARCH SIZE
                 models.append(args[0])
        return models
    except:
        return []

def lms_unload_all():
    subprocess.run("lms unload --all", shell=True)
    
def lms_load_model(model_key):
    subprocess.run(f'lms load "{model_key}"', shell=True)

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ System Control")
    
    # Connection Settings
    base_url = st.text_input("LM Studio URL", "http://localhost:1234/v1")
    
    # Model Manager
    st.subheader("Model Manager")
    
    # Check Connection & Get Current Model
    current_model = None
    try:
        client = OpenAI(base_url=base_url, api_key="lm-studio")
        models = client.models.list()
        if len(models.data) > 0:
            current_model = models.data[0].id
            st.success(f"🟢 Active: {current_model}")
            
            # Unload Button
            if st.button("🔴 Unload Model (Free RAM)", type="primary"):
                with st.spinner("Unloading model..."):
                    lms_unload_all()
                    time.sleep(2)
                    st.rerun()
        else:
            st.warning("⚪ No model loaded")
            
            # Load Interface
            # Fetch from CLI or defaults
            known_models = get_lms_models()
            if not known_models:
                known_models = ["qwen/qwen3-4b-thinking-2507", "llama-3.1-8b-lexi-uncensored-v2", "dolphin-2.9-llama3-8b"]
            
            selected_load = st.selectbox("Select Model to Load", known_models)
            
            if st.button("🟢 Load Model"):
                with st.spinner(f"Loading {selected_load}..."):
                    lms_load_model(selected_load)
                    time.sleep(5) # Give it time to load
                    st.rerun()
                    
    except Exception as e:
        st.error("Server Offline")

    st.divider()
    system_prompt = st.text_area("System Prompt", "You are a helpful AI assistant.")
    model_id = current_model if current_model else "local-model"

# === MAIN CHAT APP ===

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"]:
            st.image(base64.b64decode(message["image"]))

# Input Area Layout
with st.expander("📎 Add Attachment (Image/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Choose file", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

# Chat input
if prompt := st.chat_input("Type your message..."):
    
    encoded_img = None
    pdf_text = None
    warning_msg = None
    
    # VALIDATION
    if uploaded_file:
        file_type = uploaded_file.type
        
        if "image" in file_type:
            if not is_vision_model(model_id):
                warning_msg = "⚠️ Image ignored: Model doesn't support vision. Sending text only."
            else:
                encoded_img = encode_image(uploaded_file)
        
        elif "pdf" in file_type:
            with st.spinner("Processing PDF Document..."):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text:
                    prompt = f"Reference Document Content:\n{pdf_text}\n\n---\nUser Query: {prompt}"
                else:
                    warning_msg = "⚠️ PDF processing failed or empty."

    if warning_msg: st.toast(warning_msg, icon="⚠️")

    # User message
    new_message = {"role": "user", "content": prompt}
    if encoded_img: new_message["image"] = encoded_img
    
    st.session_state.messages.append(new_message)
    
    with st.chat_message("user"):
        display_prompt = prompt
        if pdf_text and len(pdf_text) > 200:
             display_prompt = prompt.split("User Query:")[1].strip() if "User Query:" in prompt else prompt
             st.info(f"📄 PDF Attached: {uploaded_file.name}")
        
        st.markdown(display_prompt)
        if encoded_img: st.image(uploaded_file)
        if warning_msg: st.caption(f"_{warning_msg}_")

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        full_response = ""
        is_thinking = False
        start_time = time.time()
        token_count = 0 
        
        # If no model is loaded, warn user
        if not current_model:
            st.error("❌ No AI Model Loaded! Please load a model from the sidebar to chat.")
            st.stop()
        
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
                temperature=0.7,
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
                                status_placeholder.status("Thinking...", expanded=False)
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
            metrics_msg = f"<p style='color: #888; font-size: 0.8em; margin-top: 0.5em;'>Generated {token_count} tokens • {tps:.2f} tok/s • {duration:.2f}s</p>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.markdown(metrics_msg, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
