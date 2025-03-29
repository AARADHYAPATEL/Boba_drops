import streamlit as st
import requests
import json
import os
from textblob import TextBlob
import webview

OLLAMA_URL = "http://localhost:11434/api/generate"
CHAT_HISTORY_FILE = "chat_history.json"

def save_preferences():
    """Save theme preferences to a file."""
    preferences = {
        "theme": st.session_state["theme"],
        "primary_color": st.session_state["primary_color"]
    }
    try:
        with open("preferences.json", "w") as f:
            json.dump(preferences, f)
    except IOError as e:
        st.error(f"Error saving user data: {e}")

def analyze_sentiment(response):
    """Analyze sentiment of the AI response."""
    sentiment = TextBlob(response).sentiment.polarity
    return "positive" if sentiment > 0 else "neutral" if sentiment == 0 else "negative"

def save_chat_history():
    """Save chat history to a JSON file."""
    with open(CHAT_HISTORY_FILE, "w") as file:
        json.dump(st.session_state["chat_history"], file, indent=4)

# Function to load chat history
def load_chat_history():
    if os.path.exists(CHAT_HISTORY_FILE):
        with open(CHAT_HISTORY_FILE, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return []  # If file is corrupted, return an empty list
    return []  # If file doesn't exist, return empty history

def ollama_request(prompt):
    """Send a mindfulness-focused prompt to the model and stream the response properly."""
    mindfulness_prompt = f"""
        You are 'The Mind Partner' – a thoughtful AI designed to guide users 
        through mindfulness, self-awareness, and mental well-being.

        When responding, focus on:
        - Encouraging mindfulness and self-reflection
        - Providing practical meditation and relaxation techniques
        - Offering perspective shifts to reduce stress and anxiety
        - Promoting gratitude, positivity, and emotional balance

        Be warm, empathetic, and inspiring.
        If the user is anxious, gently guide them towards calmness.
        If they are curious, provide insightful mindfulness teachings.

        Here’s the user's question:
        {prompt}
    """

    payload = {"model": "mistral", "prompt": mindfulness_prompt, "stream": True}

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()

        full_response = ""
        response_container = st.empty()  # Create an updating UI component

        # Stream response properly
        for line in response.iter_lines():
            if line:
                try:
                    json_chunk = json.loads(line)  # Parse JSON chunk
                    if "response" in json_chunk:
                        full_response += json_chunk["response"]  # Append to final response
                        st.session_state["current_response"] = full_response  # Store for persistence
                        response_container.markdown(full_response)  # Update UI dynamically
                except json.JSONDecodeError:
                    continue  # Skip invalid JSON chunks

        # Save full response in chat history
        st.session_state["chat_history"].append({"user": prompt, "bot": full_response})
        save_chat_history()

        return full_response  # Return final response

    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {e}"

def apply_theme(theme, primary_color):
    """Dynamically apply the theme with custom styles."""
    if theme == "Dark":
        background_color = "#121212"
        text_color = "#FFFFFF"
        sidebar_color = "#333333"
        widget_background = "#2E2E2E"
    else:  # Light theme
        background_color = "#E8F5E9"  # Light green background
        text_color = "#2E7D32"  # Dark green text
        sidebar_color = "#C8E6C9"  # Light sidebar green
        widget_background = "#FFFFFF"  # White widget background

    st.markdown(f"""
    <style>
        /* Main app styling */
        .stApp {{
            background-color: {background_color};
            color: {text_color};
        }}

        /* Sidebar styling */
        .css-1d391kg {{
            background-color: {sidebar_color} !important;
        }}
        
        body, div, p, h1, h2, h3, h4, h5, h6, span {{
            color: {text_color} !important;
        }}

        /* Title styling */
        .main-title {{
            text-align: center;
            font-size: 36px;
            color: {text_color};
            font-weight: bold;
        }}
        .sub-title {{
            text-align: center;
            font-size: 18px;
            color: {text_color};
        }}

        /* General Text Inputs and Labels */
        .stTextInput > div > input {{
            border-radius: 8px !important;
            border: 2px solid {primary_color} !important;
            padding: 10px !important;
            font-size: 16px !important;
            background-color: {widget_background} !important;
            color: {text_color} !important;
        }}
        .stTextInput label, .stTextArea label, .stSelectBox > label {{
            color: {text_color} !important;
        }}

        /* Radio button labels */
        .stRadio > label {{
            color: {text_color} !important;
        }}

        label {{
            color: {text_color} !important;
        }}

        /* Text above radio buttons (e.g., "Choose an option") */
        .stRadio > div > label > div {{
            color: {text_color} !important;
        }}

        /* Button styling */
        .stButton > button {{
            background-color: {primary_color} !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-size: 16px !important;
        }}
        .stButton > button:hover {{
            background-color: {primary_color}cc !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = load_chat_history()

if "current_response" not in st.session_state:
    st.session_state["current_response"] = ""

if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

if "primary_color" not in st.session_state:
    st.session_state["primary_color"] = "#4CAF50"

apply_theme(st.session_state["theme"], st.session_state["primary_color"])

# Sidebar for theme settings
with st.sidebar:
    st.header("Customize Theme")
    theme = st.radio("Choose Theme:", ["Light", "Dark"], index=0 if st.session_state["theme"] == "Light" else 1)
    primary_color = st.color_picker("Pick Primary Color:", value=st.session_state["primary_color"])

    if st.button("Apply Theme"):
        st.session_state["theme"] = theme
        st.session_state["primary_color"] = primary_color
        with open("preferences.json", "w") as f:
            json.dump({"theme": theme, "primary_color": primary_color}, f)
        st.rerun()

    # Redirect back to Journal
    if st.button("Back to Journal"):
        st.switch_page("home.py")

    if st.button("Go to Mindfulness Timer 🕰️"):
        st.switch_page("pages/mindfulness_hub.py")

# Display AI Section
st.title("🤖 Gratitude AI - Powered by Ollama")


# Display Chat History
st.subheader("Chat History")
for chat in st.session_state["chat_history"]:
    with st.chat_message("user"):
        st.write(chat["user"])
    if chat["bot"]:
        with st.chat_message("assistant"):
            st.markdown(chat["bot"])

# User Input
user_prompt = st.text_input("Ask Gratitude AI anything...", placeholder="How can I feel more grateful today?", key="ai_input")

if user_prompt:
    with st.chat_message("user"):
        st.write(user_prompt)

    # Get AI response
    with st.spinner("Thinking... 🤔"):
        ai_response = ollama_request(user_prompt)

    # No need to append to chat history again (already done in `ollama_request()`)

# Clear chat history button
if st.button("Clear Chat History"):
    st.session_state["chat_history"] = []
    if os.path.exists(CHAT_HISTORY_FILE):
        os.remove(CHAT_HISTORY_FILE)
    st.rerun()

webview.create_window("Streamlit App", "http://localhost:8501")
webview.start()
