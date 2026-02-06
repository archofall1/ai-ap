import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import random
from datetime import datetime
import io
import re
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Top Branding
st.markdown("<p style='text-align: center; font-size: 20px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px; margin-top: 0px;'><a href='https://www.youtube.com/@knxght.official'>Support the creator!</a></p>", unsafe_allow_html=True)

# 3. Main Title
st.title("Nextile AI")
st.info("✨ **NEW IMAGE GENERATION UPDATE! TRY /draw TO GENERATE NEW IMAGES!**")

# 4. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    chat_client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
    image_client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# --- STRENGTHENED SAFETY FILTER ---
BANNED_WORDS = [
    "porn", "sex", "nude", "naked", "nsfw", "hentai", "xxx", "gore", 
    "blood", "violent", "kill", "suicide", "drug", "weed", "cigar",
    "bra", "underwear", "bikini", "lingerie", "stripped"
]

def is_safe(prompt):
    # Clean the prompt: remove symbols that people use to hide words (e.g., p0rn, s.ex)
    clean_prompt = re.sub(r'[^a-zA-Z\s]', '', prompt).lower()
    
    # Check for exact matches and partial matches
    for word in BANNED_WORDS:
        if word in clean_prompt:
            return False
    return True

# 5. Greetings
GREETINGS = [
    "Hi! I'm Nextile AI. I'm a safe, family-friendly assistant!",
    "Hello! Ready to chat or draw? Remember to keep prompts friendly!",
    "Nextile AI online! Type /draw to create art, but keep it clean!"
]

# 6. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        first_text = "New chat"
        for m in messages:
            if m["role"] == "user" and isinstance(m["content"], str):
                first_text = m["content"][:20] + "..."
                break
        chats[chat_id] = {"messages": messages, "title": first_text, "date": datetime.now().strftime("%b %d")}
        db["chats"] = chats

def delete_all_chats():
    with shelve.open("nextile_storage") as db:
        db["chats"] = {}

# 7. Sidebar
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]
        st.rerun()

    st.divider()
    all_chats = get_all_chats()
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"💬 {chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

# 8. Initialize Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]

# 9. Display Messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            if isinstance(message["content"], bytes):
                st.image(message["content"])
            else:
                st.markdown(message["content"])

# 10. Chat & Image Logic
if prompt := st.chat_input("Message Nextile AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if prompt.lower().startswith("/draw"):
            image_prompt = prompt.replace("/draw", "").strip()
            
            # THE FILTER CHECK
            if not is_safe(image_prompt):
                warning_text = "⚠️ Nextile AI is unable to generate that image because it is inappropriate and does not meet our family-friendly safety guidelines."
                st.warning(warning_text)
                st.session_state.messages.append({"role": "assistant", "content": warning_text})
            else:
                st.write(f"🎨 Drawing '{image_prompt}'...")
                try:
                    image = image_client.text_to_image(image_prompt)
                    img_byte_arr = io.BytesIO()
                    image.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    st.image(img_bytes)
                    st.session_state.messages.append({"role": "assistant", "content": img_bytes})
                except Exception:
                    st.error("Error generating image.")
        else:
            # Regular Chat Logic
            response_placeholder = st.empty()
            full_response = ""
            system_instruction = {
                "role": "system", 
                "content": "You are Nextile AI, a kid-friendly assistant built by Knight. Refuse all inappropriate requests politely."
            }
            messages_to_send = [system_instruction] + st.session_state.messages
            
            try:
                for message in chat_client.chat_completion(messages=messages_to_send, max_tokens=1000, stream=True):
                    token = message.choices[0].delta.content
                    if token: 
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception:
                st.error("Nextile AI had a tiny hiccup.")
        
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
