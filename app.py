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
st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 0px;'>Made by KnIght</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-top: 0px;'><a href='https://www.youtube.com/@KnIght_Nextile' target='_blank'>Visit my YouTube Channel</a></p>", unsafe_allow_html=True)

# 3. Title & Usage Monitor
st.title("Nextile AI")

# Initialize usage tracker in session state
if "vision_uses" not in st.session_state:
    st.session_state.vision_uses = 0

# A small visual bar to show you how much the "Vision" brain is used
cols = st.columns([2, 8])
with cols[0]:
    st.write(f"🧠 **Vision Energy:** {10 - st.session_state.vision_uses}/10")
    st.progress((10 - st.session_state.vision_uses) * 10)

# 4. API Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    vision_client = InferenceClient("mistralai/Pixtral-12B-2409", token=api_key)
    text_client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key!")
    st.stop()

def encode_image(image_bytes):
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

# 5. Database Logic
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        chats[chat_id] = {"messages": messages, "title": "Chat " + datetime.now().strftime("%H:%M")}
        db["chats"] = chats

# 6. Sidebar
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight."}]
        st.session_state.vision_uses = 0 # Reset energy for new chat
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
                    elif part["type"] == "image_url": st.image(part["image_url"]["url"], width=250)
            else:
                st.markdown(content)

# 9. Plus Button (Popover Menu)
col1, col2 = st.columns([1, 15])
with col1:
    with st.popover("➕"):
        uploaded_file = st.file_uploader("Upload", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_file:
            st.success("Ready!")

with col2:
    prompt = st.chat_input("Message Nextile AI...")

# 10. Chat Logic
if prompt:
    user_content = []
    has_image = False
    if uploaded_file:
        img_bytes = uploaded_file.read()
        user_content.append({"type": "image_url", "image_url": {"url": encode_image(img_bytes)}})
        has_image = True
    
    user_content.append({"type": "text", "text": prompt})
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=250)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        system_prompt = {"role": "system", "content": "Your name is Nextile AI. Knight created you. Be kid-friendly."}
        msgs = [system_prompt] + st.session_state.messages
        
        # Logic to choose model based on energy
        try:
            if has_image and st.session_state.vision_uses < 10:
                client_to_use = vision_client
                st.session_state.vision_uses += 1
            else:
                client_to_use = text_client
            
            for message in client_to_use.chat_completion(messages=msgs, max_tokens=800, stream=True):
                token = message.choices[0].delta.content
                if token:
                    full_response += token
                    response_placeholder.markdown(full_response + "▌")
        except:
            st.error("API Limit hit. The AI is tired! Try again in a bit.")
            
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    save_chat(st.session_state.current_chat_id, st.session_state.messages)
    st.rerun() # Refresh to update the Energy Bar
