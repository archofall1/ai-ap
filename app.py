import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import base64

# 1. Setup
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# Branding
st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 0px;'>Made by KnIght</p>", unsafe_allow_html=True)

# API (Using Pixtral as a reliable Vision model)
try:
    api_key = st.secrets["HF_TOKEN"]
    client = InferenceClient("mistralai/Pixtral-12B-2409", token=api_key)
except Exception:
    st.error("Missing HF_TOKEN in Secrets!")
    st.stop()

def encode_image(image_bytes):
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

# 2. Session & History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight. How can I help?"}]

# Display History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for part in msg["content"]:
                if part["type"] == "text": st.markdown(part["text"])
                elif part["type"] == "image_url": st.image(part["image_url"]["url"], width=250)
        else:
            st.markdown(msg["content"])

# 3. Input UI (Plus Button + Chat Bar)
col1, col2 = st.columns([1, 15])
with col1:
    with st.popover("➕"):
        uploaded_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"], label_visibility="collapsed")
        if uploaded_file:
            st.success("Image attached!")

with col2:
    prompt = st.chat_input("Message Nextile AI...")

# 4. Response Logic
if prompt:
    user_msg = []
    if uploaded_file:
        img_data = encode_image(uploaded_file.read())
        user_msg.append({"type": "image_url", "image_url": {"url": img_data}})
    
    user_msg.append({"type": "text", "text": prompt})
    st.session_state.messages.append({"role": "user", "content": user_msg})
    
    # Show user message immediately
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=250)
        st.markdown(prompt)

    # Generate Assistant Response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        sys_msg = {"role": "system", "content": "You are Nextile AI, created by Knight. Be kid-friendly and polite."}
        
        try:
            # The stream=True needs a loop to display properly
            for message in client.chat_completion(messages=[sys_msg] + st.session_state.messages, max_tokens=1000, stream=True):
                token = message.choices[0].delta.content
                if token:
                    full_res += token
                    placeholder.markdown(full_res + "▌")
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
            # CRITICAL: This line ensures the app refreshes to save the chat history!
            st.rerun() 
            
        except Exception as e:
            st.error(f"Nextile AI had a hiccup: {e}")
