import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import random
from datetime import datetime
import io
from PIL import Image
import base64

# 1. Page Configuration - Sets the Robot Icon in browser tabs
st.set_page_config(
    page_title="Nextile AI (Gemini 3)", 
    page_icon="🤖", 
    layout="wide"
)

# 2. Top Branding
st.markdown("<p style='text-align: center; font-size: 20px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px; margin-top: 0px;'><a href='https://www.youtube.com/@knxght.official' target='_blank'>Support the creator by Subscribing!</a></p>", unsafe_allow_html=True)

# 3. Main Title and Update Banner
st.title("Nextile AI")
st.info("✨ **new image genration try /draw**")

# 4. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # VISION BRAIN (Llama 3.2 11B Vision)
    chat_client = InferenceClient("meta-llama/Llama-3.2-11B-Vision-Instruct", token=api_key)
    image_client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 5. Helper for Image Analysis
def encode_image(image_bytes):
    return f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode('utf-8')}"

# 6. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        first_text = "New chat"
        for m in messages:
            if m["role"] == "user":
                if isinstance(m["content"], list):
                    for part in m["content"]:
                        if part["type"] == "text":
                            first_text = part["text"][:20] + "..."
                            break
                elif isinstance(m["content"], str):
                    first_text = m["content"][:20] + "..."
                break
        chats[chat_id] = {"messages": messages, "title": first_text, "date": datetime.now().strftime("%b %d")}
        db["chats"] = chats

def delete_all_chats():
    with shelve.open("nextile_storage") as db:
        db["chats"] = {}

# 7. Sidebar Navigation
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Gemini 3, created by Knight."}]
        st.rerun()

    st.divider()
    st.subheader("Recent")
    all_chats = get_all_chats()
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"💬 {chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

    st.divider()
    if st.button("🗑️ Clear history", use_container_width=True):
        delete_all_chats()
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "History cleared!"}]
        st.rerun()

# 8. Initialize Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Gemini 3, created by Knight."}]

# 9. Display Messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            if isinstance(message["content"], list):
                for part in message["content"]:
                    if part["type"] == "text": st.markdown(part["text"])
                    elif part["type"] == "image_url": st.image(part["image_url"]["url"], width=300)
            elif isinstance(message["content"], bytes):
                st.image(message["content"])
            else:
                st.markdown(message["content"])

# 10. INTERACTIVE BUTTON BAR
# We use a column layout to put the functional file uploader next to the input
col1, col2 = st.columns([0.15, 0.85])

with col1:
    # This is the actual interactive "Plus Button"
    uploaded_file = st.file_uploader("➕", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

with col2:
    prompt = st.chat_input("Ask Gemini 3...")

# 11. Chat & Vision Logic
if prompt:
    user_msg = {"role": "user", "content": []}
    
    if uploaded_file:
        img_bytes = uploaded_file.read()
        user_msg["content"].append({"type": "image_url", "image_url": {"url": encode_image(img_bytes)}})
    
    user_msg["content"].append({"type": "text", "text": prompt})
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if uploaded_file: st.image(uploaded_file, width=300)
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if prompt.lower().startswith("/draw"):
            image_prompt = prompt.replace("/draw", "").strip()
            st.write(f"🎨 Drawing '{image_prompt}'...")
            try:
                gen_image = image_client.text_to_image(image_prompt)
                buf = io.BytesIO()
                gen_image.save(buf, format='PNG')
                st.image(buf.getvalue())
                st.session_state.messages.append({"role": "assistant", "content": buf.getvalue()})
            except:
                st.error("Art generation failed.")
        else:
            response_placeholder = st.empty()
            full_response = ""
            
            # System Instruction for Safety, Kid-Friendliness, and Credit
            system_instruction = {
                "role": "system", 
                "content": "Your name is Gemini 3. You were created by Knight. Be helpful, kid-friendly, and never rude. Credit Knight creatively if asked who made you."
            }
            
            msgs_to_send = [system_instruction] + st.session_state.messages
            
            try:
                for message in chat_client.chat_completion(messages=msgs_to_send, max_tokens=500, stream=True):
                    token = message.choices[0].delta.content
                    if token:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except:
                st.error("Nextile AI (Gemini 3) is having trouble processing that.")
        
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
