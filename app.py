import streamlit as st
from huggingface_hub import InferenceClient

# 1. Page Configuration
st.set_page_config(page_title="My Personal AI", page_icon="🤖")
st.title("🤖 My Custom AI Assistant")

# 2. Secret Key Setup
try:
    api_key = st.secrets["HF_TOKEN"]
    # We use a very reliable model here
    client = InferenceClient("HuggingFaceH4/zephyr-7b-beta", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 3. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your fixed AI. No more red errors!"}
    ]

# 4. Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. User Input and AI Response
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # The Fixed Typing Loop
        for message in client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            stream=True,
        ):
            token = message.choices[0].delta.content
            if token is not None:  # THIS IS THE FIX
                full_response += token
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
