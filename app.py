import streamlit as st
from huggingface_hub import InferenceClient

# 1. Page Configuration
st.set_page_config(page_title="My Personal AI", page_icon="🤖")
st.title("🤖 My Custom AI Assistant")
st.markdown("---")

# 2. Secret Key Setup (This pulls from Streamlit's settings)
try:
    api_key = st.secrets["HF_TOKEN"]
    client = InferenceClient("mistralai/Mistral-7B-Instruct-v0.2", token=api_key)
except Exception:
    st.error("Missing API Key! Please add HF_TOKEN to your Streamlit Secrets.")
    st.stop()

# 3. Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am your AI. How can I help you today?"}
    ]

# 4. Display Messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. User Input and AI Response
if prompt := st.chat_input("Type your message here..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # This makes the AI "type" in real-time
        for message in client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            stream=True,
        ):
            token = message.choices[0].delta.content
            if token:
                full_response += token
                response_placeholder.markdown(full_response + "▌")
        
        response_placeholder.markdown(full_response)
    
    # Save assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
