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

# Custom CSS - Modern Dark Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp { background-color: #0e1117; font-family: 'Inter', sans-serif; color: #e0e0e0; }
    h1, h2, h3 { background: linear-gradient(90deg, #4da6ff, #9966ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700 !important; }
    [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid rgba(255, 255, 255, 0.1); }
    .stChatMessage { border-radius: 12px; padding: 1rem; margin-bottom: 0.5rem; border: 1px solid rgba(255, 255, 255, 0.05); }
    [data-testid="stChatMessage"]:nth-child(even) { background-color: rgba(77, 166, 255, 0.1); border-left: 3px solid #4da6ff; }
    [data-testid="stChatMessage"]:nth-child(odd) { background-color: rgba(153, 102, 255, 0.1); border-right: 3px solid #9966ff; }
    .stTextInput input, .stTextArea textarea { background-color: #1e2329 !important; border: 1px solid rgba(255, 255, 255, 0.2) !important; color: #fff !important; border-radius: 8px !important; }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: #4da6ff !important; box-shadow: 0 0 0 1px #4da6ff !important; }
    .stButton button { background-color: #21262d; border: 1px solid rgba(255, 255, 255, 0.2); color: #e0e0e0; transition: all 0.2s ease; }
    .stButton button:hover { border-color: #4da6ff; color: #4da6ff; }
    img { border-radius: 8px; }
    .stStatusWidget { background-color: #1e2329 !important; border-color: #2f363d !important; }
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

# LMS CLI Helpers with ROBUST State checking
def get_lms_models():
    try:
        # Use simple 'lms ls' text output parsing because JSON might be experimental or differ in versions
        result = subprocess.run("lms ls", shell=True, capture_output=True, text=True, encoding='utf-8')
        lines = result.stdout.split('\n')
        models = []
        for line in lines:
            parts = line.split()
            # Valid model lines usually look like: "model-name   PARAMS   ARCH ..."
            # We filter for lines that look like model entries (have size info GB/MB)
            if len(parts) >= 3 and ("GB" in line or "MB" in line) and "SIZE" not in line:
                models.append(parts[0])
        return models
    except:
        return []

def wait_for_model_state(client, should_be_loaded=True, timeout=15):
    """Waits until a model is loaded (or unloaded)"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            models = client.models.list()
            is_loaded = len(models.data) > 0
            if is_loaded == should_be_loaded:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def check_connection(base_url):
    try:
        client = OpenAI(base_url=base_url, api_key="lm-studio")
        models = client.models.list()
        # Ensure we have a valid model ID, or None if empty
        active_id = models.data[0].id if models.data else None
        return client, active_id
    except:
        return None, None

# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ System Control")
    base_url = st.text_input("LM Studio URL", "http://localhost:1234/v1")
    
    st.subheader("Model Manager")
    
    # State Management
    client_conn, active_model_id = check_connection(base_url)
    
    if client_conn:
        if active_model_id:
            st.success(f"🟢 Active: {active_model_id}")
            if st.button("🔴 Unload Model (Free RAM)", type="primary"):
                with st.spinner("Unloading model..."):
                    subprocess.run("lms unload --all", shell=True)
                    # Wait for it to actually disappear
                    if wait_for_model_state(client_conn, should_be_loaded=False):
                        st.success("Model unloaded!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Unload timed out. Try again.")
        else:
            st.warning("⚪ No model loaded")
            
            # Load Interface
            known_models = get_lms_models()
            if not known_models:
                # Fallback defaults if CLI fails
                known_models = ["qwen/qwen3-4b-thinking-2507", "llama-3.1-8b-lexi-uncensored-v2", "dolphin-2.9-llama3-8b"]
            
            selected_load = st.selectbox("Select Model to Load", known_models)
            
            if st.button("🟢 Load Model"):
                with st.spinner(f"Loading {selected_load}..."):
                    subprocess.run(f'lms load "{selected_load}"', shell=True)
                    # Wait for it to appear
                    if wait_for_model_state(client_conn, should_be_loaded=True):
                        st.success("Model loaded!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Load timed out or failed. Check LM Studio logs.")
    else:
        st.error("⚠️ Server Offline. Run 'lms server start' or check connection.")

    st.divider()
    system_prompt = st.text_area("System Prompt", "You are a helpful AI assistant.")
    # Use active_model_id if available, otherwise just a placeholder to prevent crashes
    model_id = active_model_id if active_model_id else "local-model"

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

# Input Area
with st.expander("📎 Add Attachment (Image/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Choose file", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

if prompt := st.chat_input("Type your message..."):
    
    encoded_img = None
    pdf_text = None
    warning_msg = None
    
    # 1. Validation Logic
    if uploaded_file:
        file_type = uploaded_file.type
        if "image" in file_type:
            if not is_vision_model(model_id):
                warning_msg = "⚠️ Model likely doesn't support vision. Sending text only."
            else:
                encoded_img = encode_image(uploaded_file)
        elif "pdf" in file_type:
            with st.spinner("Processing PDF..."):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text:
                    prompt = f"Reference PDF Content:\n{pdf_text}\n\n---\nUser Query: {prompt}"
                else:
                    warning_msg = "⚠️ PDF empty or failed."

    if warning_msg: st.toast(warning_msg, icon="⚠️")

    # 2. Add User Message
    new_message = {"role": "user", "content": prompt}
    if encoded_img: new_message["image"] = encoded_img
    st.session_state.messages.append(new_message)
    
    with st.chat_message("user"):
        display_prompt = prompt
        # Hide huge PDF text block from UI
        if pdf_text and len(pdf_text) > 200:
             display_prompt = prompt.split("User Query:")[1].strip() if "User Query:" in prompt else prompt
             st.info(f"📄 PDF Attached")
        st.markdown(display_prompt)
        if encoded_img: st.image(uploaded_file)

    # 3. Generate Response
    with st.chat_message("assistant"):
        # BLOCKING CHECK: Ensure model is actually loaded before trying to chat
        if not active_model_id:
            st.error("⛔ No Model Loaded. Please load a model from the sidebar first.")
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
