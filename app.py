import streamlit as st
import base64
import pypdf
import io
import time
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

# Helper function to check vision capability
def is_vision_model(model_name):
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
            if len(models.data) > 0:
                mp = models.data[0].id
                st.info(f"Loaded Model: {mp}")
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

# Input Area Layout
# We put the file uploader in an expander for cleaner look
with st.expander("📎 Add Attachment (Image/PDF)", expanded=False):
    uploaded_file = st.file_uploader("Choose file", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")

# Chat input
if prompt := st.chat_input("Type your message..."):
    
    # Process Attachments
    encoded_img = None
    pdf_text = None
    warning_msg = None
    
    # VALIDATION & PROCESSING LOGIC
    if uploaded_file:
        file_type = uploaded_file.type
        
        # IMAGE HANDLER
        if "image" in file_type:
            # Check capabilities
            if not is_vision_model(model_id):
                # SOFT FAIL: Warn user, but allow text to pass
                warning_msg = "⚠️ Image ignored: The current model library name doesn't imply vision capabilities. Sending text only."
            else:
                encoded_img = encode_image(uploaded_file)
        
        # PDF HANDLER
        elif "pdf" in file_type:
            with st.spinner("Processing PDF Document..."):
                pdf_text = extract_pdf_text(uploaded_file)
                if pdf_text:
                    prompt = f"Reference Document Content:\n{pdf_text}\n\n---\nUser Query: {prompt}"
                else:
                    warning_msg = "⚠️ PDF processing failed or empty."

    # Show warning if needed (Toast is better than error which persists)
    if warning_msg:
        st.toast(warning_msg, icon="⚠️")

    # User message object
    new_message = {"role": "user", "content": prompt}
    if encoded_img:
        new_message["image"] = encoded_img
    
    st.session_state.messages.append(new_message)
    
    # Render User Message immediately
    with st.chat_message("user"):
        display_prompt = prompt
        # Hide raw PDF text in UI to keep it clean
        if pdf_text and len(pdf_text) > 200:
             display_prompt = prompt.split("User Query:")[1].strip() if "User Query:" in prompt else prompt
             st.info(f"📄 PDF Attached: {uploaded_file.name}")
        
        st.markdown(display_prompt)
        if encoded_img:
            st.image(uploaded_file)
        if warning_msg:
             st.caption(f"_{warning_msg}_")

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        status_placeholder = st.empty()
        
        full_response = ""
        is_thinking = False
        
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
                                real_content = parts[0]
                                if real_content:
                                    full_response += real_content
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
                                response_buffer = "" # Discard </think>
                                is_thinking = False
                                status_placeholder.empty()
                            elif not any("</think>".startswith(response_buffer[-i:]) for i in range(1, 9)):
                                response_buffer = ""

            if response_buffer and not is_thinking:
                full_response += response_buffer
            
            status_placeholder.empty()
            message_placeholder.markdown(full_response)
            
            # Metrics
            end_time = time.time()
            duration = end_time - start_time
            tps = token_count / duration if duration > 0 else 0
            
            metrics_msg = f"<p style='color: #888; font-size: 0.8em; margin-top: 0.5em;'>Generated {token_count} tokens • {tps:.2f} tok/s • {duration:.2f}s</p>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.markdown(metrics_msg, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
