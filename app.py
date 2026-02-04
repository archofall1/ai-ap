import streamlit as st
from huggingface_hub import InferenceClient
from PIL import Image
import io
import base64

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖")
st.title("🤖 Nextile AI")

# 2. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    client = InferenceClient("meta-llama/Llama-3.2-11B-Vision-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key in Streamlit Secrets!")
    st.stop()

# 3. Image Upload with "Shrink Ray"
uploaded_file = st.file_uploader("Upload an image (Max 10MB)", type=["jpg", "jpeg", "png"])

# 4. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI. Ready to analyze your images!"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. Chat Input and Vision Analysis
if prompt := st.chat_input("Ask Nextile about the image..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            if uploaded_file:
                # OPEN AND RESIZE IMAGE (The Fix for 413 Error)
                img = Image.open(uploaded_file)
                # If image is huge, shrink it so it's under 1MB
                img.thumbnail((800, 800)) 
                
                # Convert resized image to base64
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{base64_image}"
                
                messages = [{"role": "user", "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]}]
            else:
                messages = [{"role": "user", "content": prompt}]

            for message in client.chat_completion(messages=messages, max_tokens=500, stream=True):
                if hasattr(message.choices[0].delta, 'content'):
                    token = message.choices[0].delta.content
                    if token:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
        except Exception as e:
            if "413" in str(e):
                st.error("Image is still too big! Try a smaller photo.")
            else:
                st.error(f"Error: {e}")
        
        response_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})
