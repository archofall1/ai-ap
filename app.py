import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
import random
from datetime import datetime

# 1. Page Configuration - Robot Icon for browser tab
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Top Branding (Small and Centered)
st.markdown("<p style='text-align: center; font-size: 20px; margin-bottom: 0px;'>Made by Knight</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 20px; margin-top: 0px;'><a href='https://www.youtube.com/@knxght.official' target='_blank'>Support the Creator</a></p>", unsafe_allow_html=True)

# 3. Main Title and Update Banner
st.title("Nextile AI")
st.info("✨ **new image genration try /draw**")

# 4. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # Using the fast Llama 3.2 3B model for text
    client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

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
                first_text = m["content"][:20] + "..."
                break
        chats[chat_id] = {"messages": messages, "title": first_text, "date": datetime.now().strftime("%b %d")}
        db["chats"] = chats

def delete_all_chats():
    with shelve.open("nextile_storage") as db:
        db["chats"] = {}

# 6. Sidebar Navigation
with st.sidebar:
    st.title("🤖 Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight."}]
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

# 7. Initialize Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI, created by Knight."}]

# 8. Display Messages
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 9. THE INTERACTIVE PLUS BUTTON (POPOVER STYLE)
footer_col1, footer_col2 = st.columns([1, 15])

with footer_col1:
    # Popover acts as the "Menu" for the plus button
    with st.popover("➕"):
        st.write("Upload to Nextile AI")
        uploaded_file = st.file_uploader("Choose a file", label_visibility="collapsed")
        if uploaded_file:
            st.success(f"Attached: {uploaded_file.name}")

with footer_col2:
    prompt = st.chat_input("Message Nextile AI...")

# 10. Chat Logic
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Identity corrected to Nextile AI only
        system_instruction = {
            "role": "system", 
            "content": "Your name is Nextile AI. You were created by Knight. Be kid-friendly, never rude, and never mention inappropriate/sexual topics. Credit Knight in fun ways if asked who made you."
        }
        
        msgs_to_send = [system_instruction] + st.session_state.messages
        
        try:
            for message in client.chat_completion(messages=msgs_to_send, max_tokens=1000, stream=True):
                if hasattr(message.choices[0].delta, 'content'):
                    token = message.choices[0].delta.content
                    if token: 
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        except:
            st.error("Nextile AI had a hiccup. Please refresh the page to try again")
    
    save_chat(st.session_state.current_chat_id, st.session_state.messages)
