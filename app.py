import streamlit as st
import base64
import pypdf
import io
from openai import OpenAI

# Page config
st.set_page_config(page_title="Local AI Chatbot", page_icon="🤖", layout="wide")

# Custom CSS for Sci-Fi / Cyberpunk theme
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Rajdhani:wght@300;500;700&display=swap');

    /* General Reset & Theme */
    .stApp {
        background-color: #050510;
        background-image: 
            radial-gradient(circle at 10% 20%, rgba(0, 242, 255, 0.05) 0%, transparent 20%),
            radial-gradient(circle at 90% 80%, rgba(112, 0, 255, 0.05) 0%, transparent 20%);
        font-family: 'Rajdhani', sans-serif;
        color: #e0e0e0;
    }
    
    /* Headers */
    h1, h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        background: linear-gradient(90deg, #00f2ff, #7000ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(0, 242, 255, 0.3);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0a0a16;
        border-right: 1px solid rgba(0, 242, 255, 0.1);
        box-shadow: 5px 0 15px rgba(0,0,0,0.5);
    }
    
    /* Chat Messages */
    .stChatMessage {
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(5px);
        transition: all 0.3s ease;
    }
    
    /* User Message */
    [data-testid="stChatMessage"]:nth-child(even) {
        background: linear-gradient(135deg, rgba(0, 242, 255, 0.05) 0%, rgba(0, 242, 255, 0.01) 100%);
        border-left: 3px solid #00f2ff;
        box-shadow: -5px 5px 15px rgba(0, 242, 255, 0.05);
    }
    
    /* AI Message */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background: linear-gradient(135deg, rgba(112, 0, 255, 0.05) 0%, rgba(112, 0, 255, 0.01) 100%);
        border-right: 3px solid #7000ff;
        box-shadow: 5px 5px 15px rgba(112, 0, 255, 0.05);
    }

    /* Input Area */
    .stTextInput input, .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(0, 242, 255, 0.2) !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-family: 'Rajdhani', sans-serif;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #00f2ff !important;
        box-shadow: 0 0 10px rgba(0, 242, 255, 0.2) !important;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(45deg, #0a0a16, #1a1a2e);
        border: 1px solid #00f2ff;
        color: #00f2ff;
        font-family: 'Orbitron', sans-serif;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: #00f2ff;
        color: #000;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.5);
    }
    
    /* Images */
    img {
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Code Blocks */
    code {
        font-family: 'Consolas', monospace;
        color: #ff79c6;
    }
    
    /* Expander / Status */
    .stStatusWidget {
        background-color: rgba(0, 255, 0, 0.05) !important;
        border: 1px solid #00ff00 !important;
        color: #00ff00 !important;
    }
    
    /* Toast/Error Popups */
    .stToast {
        background-color: #1a0505 !important;
        border: 1px solid #ff3333 !important;
        color: #ffcccc !important;
    }

</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center;">🚀 NEURAL__LINK // SYSTEM_ACTIVE</h1>', unsafe_allow_html=True)

# Helper function to check vision capability
def is_vision_model(model_name):
    """
    Heuristic check to see if a model supports vision based on its name.
    Common vision models: llava, bakllava, yap-vl, moondream, yi-vl, qwen-vl, minicpm-v
    """
    vision_keywords = ['vision', 'llava', 'bakllava', 'moondream', 'yi-vl', 'qwen-vl', 'minicpm-v', 'cogvlm', 'clip']
    return any(keyword in model_name.lower() for keyword in vision_keywords)

# Helper to encode image
def encode_image(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    return None

# Helper to extract PDF text
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

# Sidebar settings
with st.sidebar:
    st.header("Settings")
    base_url = st.text_input("LM Studio URL", "http://localhost:1234/v1")
    model_id = st.text_input("Model ID", "local-model")
    system_prompt = st.text_area("System Prompt", "You are a helpful AI assistant.")
    
    if st.button("Test Connection"):
        try:
            client = OpenAI(base_url=base_url, api_key="lm-studio")
            models = client.models.list()
            st.success(f"Connected! Found {len(models.data)} models.")
            # Try to auto-detect model ID if generic 'local-model' is used
            if len(models.data) > 0:
                mp = models.data[0].id
                st.info(f"Loaded Model: {mp}")
                if is_vision_model(mp):
                    st.success("✨ Vision Capabilities Detected")
                else:
                    st.warning("⚠️ No Vision Capabilities Detected in Name")
        except Exception as e:
            st.error(f"Connection failed: {str(e)}")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image" in message and message["image"]:
            st.image(base64.b64decode(message["image"]))

# Input area
with st.popover("📎 Attach File"):
    uploaded_file = st.file_uploader("Upload Image or PDF", type=["png", "jpg", "jpeg", "pdf"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    
    # Process Attachments
    encoded_img = None
    pdf_text = None
    
    # VALIDATION LOGIC
    if uploaded_file:
        file_type = uploaded_file.type
        
        # IMAGE HANDLER
        if "image" in file_type:
            # Check capabilities
            if not is_vision_model(model_id):
                st.error("⛔ ACCESS DENIED: The current model does not support Vision/Image inputs. Please unload this model and load a Vision-capable model (e.g., LLaVA, BakLLaVA).")
                st.stop()
            else:
                encoded_img = encode_image(uploaded_file)
        
        # PDF HANDLER
        elif "pdf" in file_type:
            with st.spinner("Processing PDF Document..."):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text:
                    # Append PDF content to prompt context transparently
                    prompt = f"Reference Document Content:\n{pdf_text}\n\n---\nUser Query: {prompt}"
                else:
                    st.stop()

    # User message object
    new_message = {"role": "user", "content": prompt}
    
    if encoded_img:
        new_message["image"] = encoded_img
    
    st.session_state.messages.append(new_message)
    with st.chat_message("user"):
        # If PDF was added, show a cleaner UI message than the huge raw text
        display_prompt = prompt
        if pdf_text and len(pdf_text) > 200:
             # Show truncated version in UI to keep it clean, but send full to API
             display_prompt = prompt.split("User Query:")[1].strip() if "User Query:" in prompt else prompt
             st.info(f"📄 PDF Attached: {uploaded_file.name}")
        
        st.markdown(display_prompt)
        if encoded_img:
            st.image(uploaded_file)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        full_response = ""
        thought_buffer = ""
        is_thinking = False
        
        # Performance tracking
        import time
        start_time = time.time()
        token_count = 0 
        
        # Construct messages for API
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in st.session_state.messages:
            content = [{"type": "text", "text": m["content"]}]
            if "image" in m and m["image"]:
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{m['image']}"
                    }
                })
            api_messages.append({"role": m["role"], "content": content})

        try:
            client = OpenAI(base_url=base_url, api_key="lm-studio")
            stream = client.chat.completions.create(
                model=model_id,
                messages=api_messages,
                stream=True,
                temperature=0.7,
            )
            
            # State for parsing
            response_buffer = "" 
            is_thinking = False
            thought_status = None
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    token_count += 1 
                    
                    for char in content_chunk:
                        response_buffer += char
                        
                        if not is_thinking:
                            if "<think>" in response_buffer:
                                parts = response_buffer.split("<think>")
                                real_content = parts[0]
                                if real_content:
                                    full_response += real_content
                                    message_placeholder.markdown(full_response + "▌")
                                response_buffer = "" 
                                is_thinking = True
                                thought_status = status_placeholder.status("Thinking...", expanded=False)
                            elif not any("<think>".startswith(response_buffer[-i:]) for i in range(1, 8)):
                                full_response += response_buffer
                                message_placeholder.markdown(full_response + "▌")
                                response_buffer = ""
                        else:
                            if "</think>" in response_buffer:
                                response_buffer = "" # Discard </think>
                                is_thinking = False
                                status_placeholder.empty()
                                thought_status = None
                            elif not any("</think>".startswith(response_buffer[-i:]) for i in range(1, 9)):
                                response_buffer = ""

            if response_buffer:
                if not is_thinking:
                    full_response += response_buffer
            
            status_placeholder.empty()
            message_placeholder.markdown(full_response)
            
            end_time = time.time()
            duration = end_time - start_time
            tps = token_count / duration if duration > 0 else 0
            
            metrics_msg = f"<p style='color: #666; font-size: 0.8em; margin-top: 0.5em;'>Generated {token_count} tokens • {tps:.2f} tok/s • {duration:.2f}s</p>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.markdown(metrics_msg, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
