import streamlit as st
import base64
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

</style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center;">🚀 NEURAL__LINK // SYSTEM_ACTIVE</h1>', unsafe_allow_html=True)

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
# Helper to encode image
def encode_image(uploaded_file):
    if uploaded_file is not None:
        return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    return None

# File uploader
with st.popover("📎 Attach Image"):
    uploaded_image = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    # User message
    new_message = {"role": "user", "content": prompt}
    encoded_img = None
    
    if uploaded_image:
        encoded_img = encode_image(uploaded_image)
        new_message["image"] = encoded_img
    
    st.session_state.messages.append(new_message)
    with st.chat_message("user"):
        st.markdown(prompt)
        if encoded_img:
            st.image(uploaded_image)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        # Create a container for the status/thought process
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
            # Clean up history for API - maybe remove old thoughts if we stored them? 
            # For now, just sending what we have.
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
                    
                    # Accumulate for parsing safety (handle split tags like < + think + >)
                    # Simple state machine approach
                    
                    # We process char by char to be 100% robust against split tags
                    for char in content_chunk:
                        response_buffer += char
                        
                        # Check state transitions
                        if not is_thinking:
                            # Look for start tag
                            if "<think>" in response_buffer:
                                # Found start tag. 
                                # Everything before it is real content.
                                parts = response_buffer.split("<think>")
                                real_content = parts[0]
                                if real_content:
                                    full_response += real_content
                                    message_placeholder.markdown(full_response + "▌")
                                
                                # Reset buffer to look for end tag, but discard the <think> tag itself
                                response_buffer = "" 
                                is_thinking = True
                                # Show distinct status indicator
                                thought_status = status_placeholder.status("Thinking...", expanded=False)
                            elif not any("<think>".startswith(response_buffer[-i:]) for i in range(1, 8)):
                                # If we are NOT strictly in the middle of a potential tag match, 
                                # we can safely flush the buffer to the UI to keep it snappy.
                                full_response += response_buffer
                                message_placeholder.markdown(full_response + "▌")
                                response_buffer = ""
                        else:
                            # We ARE thinking
                            # Look for end tag
                            if "</think>" in response_buffer:
                                # Found end tag.
                                # Discard thought content entirely
                                
                                # Reset
                                response_buffer = "" # Discard </think>
                                is_thinking = False
                                # Remove status indicator when done
                                status_placeholder.empty()
                                thought_status = None
                            elif not any("</think>".startswith(response_buffer[-i:]) for i in range(1, 9)):
                                # Not in middle of end tag
                                # Just consume the thought content without displaying it
                                response_buffer = ""

            # Check for any remaining buffer content
            if response_buffer:
                if is_thinking:
                    # Trailing thought content - ignore
                    pass
                else:
                    full_response += response_buffer
            
            # Finalize UI - ensure status is gone
            status_placeholder.empty()
                
            message_placeholder.markdown(full_response)
            
            end_time = time.time()
            duration = end_time - start_time
            tps = token_count / duration if duration > 0 else 0
            
            # Formatted like LM Studio: 'Generated 56 tokens • 2.62 tok/s • 0.38s'
            metrics_msg = f"<p style='color: #666; font-size: 0.8em; margin-top: 0.5em;'>Generated {token_count} tokens • {tps:.2f} tok/s • {duration:.2f}s</p>"
            message_placeholder.markdown(full_response, unsafe_allow_html=True)
            st.markdown(metrics_msg, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"Error calling API: {str(e)}")
