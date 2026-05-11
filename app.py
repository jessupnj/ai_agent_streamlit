import os
import json
import requests
import streamlit as st

# --- Streamlit UI must be configured first ---
st.set_page_config(
    page_title="Nashville Airbnb Agent",
    page_icon="🎸",
    layout="centered",
)

# Read token from environment variable (injected from Databricks secret at runtime)
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
DATABRICKS_HOST = "https://dbc-0726d26f-3749.cloud.databricks.com"
ENDPOINT_NAME = "agents_isa632_7474656346303369-jessupnj-nashville_model"
ENDPOINT_URL = f"{DATABRICKS_HOST}/serving-endpoints/{ENDPOINT_NAME}/invocations"

if not DATABRICKS_TOKEN:
    st.error("DATABRICKS_TOKEN is not set. Please configure the secret resource in your app deployment.")
    st.stop()


def get_agent_response(user_message: str, conversation_history: list) -> str:
    """Send a message to the Nashville agent endpoint and return the response."""
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type": "application/json",
    }

    # Build the input with conversation history
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    payload = {"input": messages}
    response = requests.post(url=ENDPOINT_URL, headers=headers, data=json.dumps(payload))

    if response.status_code != 200:
        return f"Error: Request failed with status {response.status_code}. {response.text}"

    # Extract text from the agent response
    try:
        result = response.json()
        output = result["output"]
        for item in output:
            if item.get("type") == "message":
                for content_block in item.get("content", []):
                    if content_block.get("type") == "output_text":
                        return content_block["text"]
        return json.dumps(result, indent=2)
    except (KeyError, IndexError, TypeError):
        return json.dumps(result, indent=2)


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
        
        **Sample Questions:**
        - I'm thinking about adding a hot tub to my listing. Is this a good idea?
        - Why do guests like the airbnbs they stay at in Nashville?
        """
    )
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
