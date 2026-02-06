import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
from datetime import datetime
import io
import base64

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Top Branding
st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-top: 0px;'><a href='https://www.youtube.com/@knxght.official' target='_blank'>Visit my YouTube Channel</a></p>", unsafe_allow_html=True)

# 3. Main Title
st.title("Nextile AI")
st.info("✨ **new image genration try /draw**")

# 4. Secret Key & Vision Model Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # We use the 11B Vision model so the AI can actually see your uploads
    client = InferenceClient("meta-llama/Llama-3.2-11B-Vision-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

def encode_image(image_bytes):
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

# 5. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        first_text = "New chat"
        for m in messages:
            if m["role"] == "user":
                content = m["content"]
                text = content if isinstance(content, str) else content[-1]["text"]
                first_text = text[:20] + "..."
                break
        chats[chat_id] = {"messages": messages, "title": first_text}
        db["chats"] = chats

# 6. Sidebar
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight."}]
        st.rerun()
    st.divider()
    all_chats = get_all_chats()
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"💬 {chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

# 7. Initialize Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight."}]

# 8. Display History
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            content = message["content"]
            if isinstance(content, list):
                for part in content:
                    if part["type"] == "text": st.markdown(part["text"])
                    elif part["type"] == "image_url": st.image(part["image_url"]["url"], width=300)
            else:
                st.markdown(content)

# 9. THE INTERACTIVE PLUS BUTTON (CLEAN POPOVER)
col1, col2 = st.columns([1, 15])
with col1:
    with st.popover("➕"):
        st.write("Upload an Image")
        # The label is hidden to keep it looking like a clean menu
        uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_file:
            st.success("Image Ready!")

with col2:
    prompt = st.chat_input("Message Nextile AI...")

# 10. Logic to Combine Image + Text
if prompt:
    user_content = []
    
    # Check if an image was uploaded in the popover
    if uploaded_file:
        img_bytes = uploaded_file.read()
        encoded = encode_image(img_bytes)
        user_content.append({"type": "image_url", "image_url": {"url": encoded}})
    
    user_content.append({"type": "text", "text": prompt})
    
    # Add to history and display
    st.session_state.messages.append({"role": "user", "content": user_content})
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        system_prompt = {"role": "system", "content": "Your name is Nextile AI. Knight created you. Be kid-friendly."}
        msgs = [system_prompt] + st.session_state.messages
        
        try:
            # The stream=True makes it type out word by word
            for message in client.chat_completion(messages=msgs, max_tokens=1000, stream=True):
                token = message.choices[0].delta.content
                if token:
                    full_response += token
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except:
            st.error("Nextile AI had a problem. Check your internet or API limit.")
    
    save_chat(st.session_state.current_chat_id, st.session_state.messages)
