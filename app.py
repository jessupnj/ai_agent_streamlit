import os
import json
import streamlit as st
from databricks.sdk import WorkspaceClient

# --- Streamlit UI must be configured first ---
st.set_page_config(
    page_title="Nashville Airbnb Agent",
    page_icon="🎸",
    layout="centered",
)

# Read credentials from environment variables (injected from Databricks secret)
token = os.getenv("DATABRICKS_TOKEN")
host = os.getenv("DATABRICKS_HOST")

# Initialize the client using the injected environment variables
try:
    w = WorkspaceClient(host=host, token=token)
    st.success(f"Connected as: {w.current_user.me().user_name}")
except Exception as e:
    st.error(f"Authentication failed: {e}")
    st.stop()

ENDPOINT_NAME = "agents_isa632_7474656346303369-jessupnj-nashville_model"


def get_agent_response(user_message: str, conversation_history: list) -> str:
    """Send a message to the Nashville agent endpoint and return the response."""
    # Build the input with conversation history
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {"input": messages}

    response = w.serving_endpoints.query(
        name=ENDPOINT_NAME,
        inputs=[payload],
    )

    # Extract text from the agent response
    try:
        result = response.as_dict()
        output = result["output"]
        for item in output:
            if item.get("type") == "message":
                for content_block in item.get("content", []):
                    if content_block.get("type") == "output_text":
                        return content_block["text"]
        return json.dumps(result, indent=2)
    except (KeyError, IndexError, TypeError):
        return json.dumps(response.as_dict(), indent=2)


# --- Chat UI ---
st.title("🎸 Nashville Airbnb Agent")
st.caption("Ask questions about improving your Nashville Airbnb listing")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask the Nashville Airbnb agent..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Get agent response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response_text = get_agent_response(prompt, st.session_state.messages[:-1])
        st.markdown(response_text)

    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# Sidebar
with st.sidebar:
    st.header("About")
    st.markdown(
        """
        This app connects to the **Nashville Airbnb Agent** 
        serving endpoint on Databricks.
        
        **Capabilities:**
        - Airbnb listing improvement suggestions
        - Nashville market insights
        - Review optimization tips
        """
    )
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
