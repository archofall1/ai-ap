import streamlit as st
from huggingface_hub import InferenceClient
import shelve

# 1. Page Configuration
st.set_page_config(page_title="Nextile AI", page_icon="🤖")
st.title("🤖 Nextile AI")

# 2. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    client = InferenceClient("meta-llama/Llama-3.2-3B-Instruct", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 3. Persistent Memory Functions
def load_chat_history():
    with shelve.open("nextile_storage") as db:
        return db.get("messages", [])

def save_chat_history(messages):
    with shelve.open("nextile_storage") as db:
        db["messages"] = messages

# 4. Initialize or Load Chat History
if "messages" not in st.session_state:
    saved_history = load_chat_history()
    if saved_history:
        st.session_state.messages = saved_history
    else:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm Nextile AI. I'll remember our chat even if you refresh!"}
        ]

# 5. Sidebar with a "Delete" button (To start a fresh chat)
with st.sidebar:
    if st.button("Clear Chat History"):
        st.session_state.messages = [{"role": "assistant", "content": "Chat cleared! How can I help?"}]
        save_chat_history(st.session_state.messages)
        st.rerun()

# 6. Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. User Input and AI Response
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            messages_for_api = [{"role": "system", "content": "You are Nextile AI, a helpful assistant."}]
            for m in st.session_state.messages:
                messages_for_api.append(m)

            for message in client.chat_completion(
                messages=messages_for_api,
                max_tokens=1000,
                stream=True,
            ):
                if hasattr(message.choices[0].delta, 'content'):
                    token = message.choices[0].delta.content
                    if token: 
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
        except Exception:
            st.error("Nextile AI had a tiny hiccup. Please try typing again!")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    # SAVE to long-term memory after every response
    save_chat_history(st.session_state.messages)
