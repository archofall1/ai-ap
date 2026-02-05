import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import random
from datetime import datetime
import io
from PIL import Image

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # Text Brain
    chat_client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
    # Image Brain (FLUX is one of the best for this!)
    image_client = InferenceClient("black-forest-labs/FLUX.1-schnell", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 3. Random Greeting List
GREETINGS = [
    "Hi! I'm Nextile AI. Want me to draw something? Try typing '/draw a cool robot'.",
    "Nextile AI online. I can chat or generate images with /draw!",
    "Ready for use. Type /draw followed by a prompt to see some magic."
]

# 4. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        first_question = messages[1]["content"][:20] if len(messages) > 1 else "New chat"
        chats[chat_id] = {
            "messages": messages,
            "title": first_question,
            "date": datetime.now().strftime("%b %d")
        }
        db["chats"] = chats

# 5. Sidebar Navigation
with st.sidebar:
    st.title("Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]
        st.rerun()

    st.divider()
    st.subheader("Recent")
    all_chats = get_all_chats()
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"{chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

# 6. Initialize Current Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": random.choice(GREETINGS)}]

st.title("New chat")

# 7. Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if isinstance(message["content"], bytes): # If it's a generated image
            st.image(message["content"])
        else:
            st.markdown(message["content"])

# 8. Chat & Image Logic
if prompt := st.chat_input("Message Nextile AI (use /draw for images)..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if prompt.lower().startswith("/draw"):
            # --- IMAGE GENERATION MODE ---
            image_prompt = prompt.replace("/draw", "").strip()
            st.write(f"🎨 Generating: '{image_prompt}'...")
            try:
                # Generate image
                image = image_client.text_to_image(image_prompt)
                
                # Convert PIL image to bytes for Streamlit
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                st.image(img_bytes)
                st.session_state.messages.append({"role": "assistant", "content": img_bytes})
            except Exception as e:
                st.error("Image generation failed. The model might be busy!")
        else:
            # --- NORMAL CHAT MODE ---
            response_placeholder = st.empty()
            full_response = ""
            try:
                for message in chat_client.chat_completion(messages=st.session_state.messages, max_tokens=1000, stream=True):
                    if hasattr(message.choices[0].delta, 'content'):
                        token = message.choices[0].delta.content
                        if token: 
                            full_response += token
                            response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception:
                st.error("Nextile AI had a tiny hiccup.")
        
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
