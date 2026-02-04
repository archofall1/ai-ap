import streamlit as st
from huggingface_hub import InferenceClient
import shelve
import uuid
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖", layout="wide")

# 2. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 3. Database Functions
def get_all_chats():
    with shelve.open("nextile_storage") as db:
        return db.get("chats", {})

def save_chat(chat_id, messages):
    with shelve.open("nextile_storage") as db:
        chats = db.get("chats", {})
        # This keeps the sidebar titles short and clean
        first_question = messages[1]["content"][:20] if len(messages) > 1 else "New chat"
        chats[chat_id] = {
            "messages": messages,
            "title": first_question,
            "date": datetime.now().strftime("%b %d")
        }
        db["chats"] = chats

def delete_all_chats():
    with shelve.open("nextile_storage") as db:
        db["chats"] = {}

# 4. Sidebar Navigation
with st.sidebar:
    st.title("Nextile AI")
    if st.button("➕ New chat", use_container_width=True):
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI. Ready for use."}]
        st.rerun()

    st.divider()
    st.subheader("Recent")
    all_chats = get_all_chats()
    
    for c_id, chat_data in reversed(list(all_chats.items())):
        if st.button(f"{chat_data['title']}", key=c_id, use_container_width=True):
            st.session_state.current_chat_id = c_id
            st.session_state.messages = chat_data["messages"]
            st.rerun()

    st.divider()
    if st.button("Clear history"):
        delete_all_chats()
        st.session_state.current_chat_id = str(uuid.uuid4())
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI. Ready for use."}]
        st.rerun()

# 5. Initialize Current Session
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Nextile AI. Ready for use."}]

# THIS IS THE PART YOU WANTED CHANGED:
st.title("New chat")

# 6. Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Chat Logic
if prompt := st.chat_input("Message Nextile AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            for message in client.chat_completion(messages=st.session_state.messages, max_tokens=1000, stream=True):
                if hasattr(message.choices[0].delta, 'content'):
                    token = message.choices[0].delta.content
                    if token: 
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
        except Exception:
            st.error("Nextile AI had a tiny hiccup.")
        
        response_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_chat(st.session_state.current_chat_id, st.session_state.messages)
