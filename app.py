import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
from datetime import datetime
import io
import base64

# 1. Page Configuration - Robot Icon for browser tab
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Top Branding (Small and Centered)
st.markdown("<p style='text-align: center; font-size: 14px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; margin-top: 0px;'><a href='https://www.youtube.com/@KnIght_Nextile' target='_blank'>Support the creator!</a></p>", unsafe_allow_html=True)

# 3. Main Title and Update Banner
st.title("Nextile AI")
st.info("✨ **NEW IMAGE GENERATION UPDATE! TYR /draw FOLLOWED BY YOUR PROMPT TO GENERATE NEW IMAGES!**")

# 4. Secret Key & Model Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # We MUST use the Vision model for the 'upload' to actually work
    client = InferenceClient("meta-llama/Llama-3.2-11B-Vision-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# Helper to encode image for the AI
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
                # Extract text for sidebar title
                content = m["content"]
                text = content if isinstance(content, str) else content[-1]["text"]
                first_text = text[:20] + "..."
                break
        chats[chat_id] = {"messages": messages, "title": first_text, "date": datetime.now().strftime("%b %d")}
        db["chats"] = chats

# 6. Sidebar Navigation
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

# 8. Display Messages
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

# 9. THE INTERACTIVE PLUS BUTTON (POPOVER)
# This hides the 'Drag and Drop' box inside the button
col1, col2 = st.columns([1, 15])
with col1:
    with st.popover("➕"):
        st.write("Upload an Image")
        uploaded_file = st.file_uploader("Choose image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

with col2:
    prompt = st.chat_input("Message Nextile AI...")

# 10. Chat & Vision Logic
if prompt:
    user_content = []
    if uploaded_file:
        img_bytes = uploaded_file.read()
        user_content.append({"type": "image_url", "image_url": {"url": encode_image(img_bytes)}})
    
    user_content.append({"type": "text", "text": prompt})
    st.session_state.messages.append({"role": "user", "content": user_content})
    
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        system_instruction = {
            "role": "system", 
            "content": "Your name is Nextile AI. You were created by Knight. Be kid-friendly, never rude, and never mention inappropriate topics. Always credit Knight."
        }
        
        msgs = [system_instruction] + st.session_state.messages
        
        try:
            for message in client.chat_completion(messages=msgs, max_tokens=1000, stream=True):
                token = message.choices[0].delta.content
                if token: 
                    full_response += token
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except:
            st.error("Nextile AI is having trouble seeing that image. Please refresh you rpage to try again")
    
    save_chat(st.session_state.current_chat_id, st.session_state.messages)
