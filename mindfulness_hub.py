import streamlit as st
import time
import json
import os
from streamlit_extras import add_vertical_space
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.let_it_rain import rain
import webview

# Initialize theme settings in session_state
if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

if "primary_color" not in st.session_state:
    st.session_state["primary_color"] = "#4CAF50"

# Set Page Configuration
st.set_page_config(page_title="Mindfulness Hub", page_icon="🧘")

# Create Tabs
tab1, tab2 = st.tabs(["🕰️ Mindfulness Timer", "📚 Mindfulness Course"])

def save_preferences():
    preferences = {
        "theme": st.session_state["theme"],
        "primary_color": st.session_state["primary_color"]
    }
    try:
        with open("preferences.json", "w") as f:
            json.dump(preferences, f)
    except IOError as e:
        st.error(f"Error saving user data: {e}")


def load_preferences():
    if os.path.exists("preferences.json"):
        with open("preferences.json", "r") as f:
            preferences = json.load(f)
            st.session_state.update(preferences)


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

# 🎉 Function to trigger confetti animation
def show_confetti():
    rain(
        emoji="🎉✨🎊",
        font_size=40,
        falling_speed=3,
        animation_length="5s",
    )

apply_theme(st.session_state["theme"], st.session_state["primary_color"])

if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"

if "primary_color" not in st.session_state:
    st.session_state["primary_color"] = "#4CAF50"

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
    if st.button("Back to Journal 📝"):
        st.switch_page("home.py")

    if st.button("Go to Gratitude AI 🤖"):
        st.switch_page("pages/gratitude_ai.py")

with tab1:
    # Title
    st.title("🕰️ Mindfulness Timer")

    # User input for timer duration
    minutes = st.slider("Select duration (minutes)", 1, 30, 5)
    seconds = minutes * 60

    # Start button
    if st.button("Start Timer 🏁"):
        st.write(f"Starting a {minutes}-minute mindfulness session. Relax and breathe deeply. 🧘‍♂️")

        with st.empty():
            for remaining in range(seconds, 0, -1):
                mins, secs = divmod(remaining, 60)
                st.write(f"⏳ Time left: {mins:02}:{secs:02}")
                time.sleep(1)

            st.success("✅ Session Complete! Take a moment to reflect in the Gratitude Journal. 💙")
            show_confetti()  # 🎉 Trigger Confetti Effect

# 📚 Mindfulness Course Tab
with tab2:
    st.title("📚 Mindfulness Course")

    # List of course topics with expanded content
    course_content = [
        {
            "title": "What is Mindfulness? 🧘‍♂️",
            "content": """ 
            ### 🌿 Understanding Mindfulness  
            **Mindfulness** is the practice of being **fully present and engaged** in the moment. It involves **observing your thoughts, emotions, and sensations without judgment**.  

            **🌟 Key Benefits:**  
            - 🧠 **Enhances cognitive function** – Increases focus and memory.  
            - 💆 **Reduces stress & anxiety** – Activates relaxation responses.  
            - ❤️ **Improves emotional regulation** – Encourages self-awareness and self-compassion.  
            - 🛌 **Better sleep quality** – Helps with insomnia and overthinking.  

            **📝 Practical Exercise:**  
            **"5 Senses Grounding"** – Engage with the present moment using your senses:  
            - 👀 **See** – Name 5 things you can see.  
            - 👂 **Hear** – Name 4 things you can hear.  
            - 🤲 **Touch** – Name 3 things you can feel.  
            - 👃 **Smell** – Name 2 things you can smell.  
            - 👅 **Taste** – Name 1 thing you can taste.  
            

            🧘‍♂️ _Use this technique anytime you feel overwhelmed or distracted._
            
            ✅ _Use this video for more information on Mindfulness._
            """,
            "video": "https://www.youtube.com/watch?v=7-1Y6IbAxdM"
        },
        {
            "title": "Breathing Techniques 🌬️",
            "content": """ 
            ### 🌬️ The Power of Breath  
            Your **breath is a powerful tool** for calming the nervous system.  
            When you focus on **slow, deep breathing**, you shift your body into a **relaxed state**.

            **🟢 Box Breathing (4-4-4-4)**
            - Inhale deeply through your nose for **4 seconds**  
            - Hold your breath for **4 seconds**  
            - Exhale slowly through your mouth for **4 seconds**  
            - Hold for **4 seconds**, then repeat 5–10 times  

            **🔵 Diaphragmatic Breathing (Belly Breathing)**
            - Sit or lie down, placing one hand on your chest and the other on your stomach.  
            - Inhale deeply through your nose—your belly should rise while your chest stays still.  
            - Exhale fully through your mouth, feeling your belly fall.  
            - Repeat **for 5 minutes** to induce relaxation.  

            🧘‍♂️ _Try deep breathing before bed or in moments of stress._
            
            ✅ _Use this video for more information on Diaphragmatic breathing and its benefits._
            """,
            "video": "https://www.youtube.com/watch?v=g2wo2Impnfg"
        },
        {
            "title": "Guided Meditation 🎧",
            "content": """ 
            ### 🎧 What is Guided Meditation?  
            **Guided meditation** is a structured meditation practice where you listen to verbal instructions guiding your focus.

            **🕉️ Simple 5-Minute Meditation**
            - **Find a quiet space** and sit comfortably.  
            - **Close your eyes** and focus on your breath.  
            - **Scan your body** from head to toe, noticing any tension.  
            - If your mind wanders, **gently bring it back to your breath**.  
            - Continue for **at least 5 minutes**.  

            **🎶 Recommended Apps for Guided Meditations**
            - 🎧 Headspace  
            - 🧘 Calm  
            - 🌿 Insight Timer  

            🧘‍♂️ _Try this meditation first thing in the morning for a calm start._
            
            ✅ _Use this video for guided meditation from a expert._
            """,
            "video": "https://www.youtube.com/watch?v=sG7DBA-mgFY"
        },
        {
            "title": "Mindful Thinking 🤔",
            "content": """ 
            ### 🤔 Training Your Mind to Think Mindfully  
            Mindfulness is **not about stopping thoughts** but about observing them **without attachment or judgment**.

            **💡 How to Practice Mindful Thinking**
            - 🌱 **Observe your thoughts** as if they were passing clouds.  
            - ❤️ **Practice gratitude** – Write 3 things you’re grateful for daily.  
            - 🏃‍♂️ **Stay present in daily activities** – Eat, walk, and talk with full awareness.  
            - 🔄 **Shift negative thoughts** – Replace self-criticism with self-compassion.  

            **📝 Mindful Reflection Exercise**  
            - Sit quietly and ask yourself:  
            - 🧘‍♂️ "What emotions am I feeling right now?"  
            - 💡 "What are my thoughts without judgment?"  
            - 🎯 "What can I let go of to feel lighter?"  
            - Write down your responses in a journal.  

            🧘‍♂️ _The more you observe your thoughts, the better control you have over them._
            
            ✅ _Watch this video to get help combating negative thoughts._
            """,
            "video": "https://www.youtube.com/watch?v=JkB7hJan0Q0"
        },
        {
            "title": "Applying Mindfulness 💡",
            "content": """ 
            ### 💡 Bringing Mindfulness into Daily Life  
            Mindfulness is not just about meditation—it can be applied to **everything** you do.

            **🏡 Mindfulness in Everyday Activities**
            - 🍽️ **Mindful Eating** – Eat slowly, noticing flavors, textures, and sensations.  
            - 🚶 **Mindful Walking** – Focus on each step and your surroundings.  
            - 🎧 **Mindful Listening** – Give full attention when someone is speaking.  

            **📌 10-Minute Daily Mindfulness Challenge**
            - Spend **10 minutes fully immersed** in a task without distractions.  
            - Whether it’s **eating, cleaning, or reading**, engage **100% in the experience**.  
            - At the end, reflect: "How did that feel?"  

            🧘‍♂️ _Mindfulness is not about doing something extra—it’s about being fully present in what you’re already doing._
            
            ✅ _Watch this video to understand how can we apply mindfulness in our daily lives._
            """,
            "video": "https://www.youtube.com/watch?v=iGjY41vZAU8"
        }
    ]

    # Ensure session state variable exists
    if "course_progress" not in st.session_state:
        st.session_state["course_progress"] = 0

    # Get the current section (Index)
    current_step = int(st.session_state["course_progress"] * len(course_content))

    if current_step < len(course_content):
        # Display current section
        st.subheader(f"📌 Section {current_step + 1}: {course_content[current_step]['title']}")
        st.write(course_content[current_step]['content'])  # ✅ Renders Markdown Correctly

        # ✅ Safely Check for 'video' Key Before Embedding Video
        if "video" in course_content[current_step]:
            st.video(course_content[current_step]['video'])
        else:
            st.warning("🚨 No video available for this section.")

        # ✅ Prevent progress from going negative
        if st.session_state["course_progress"] < 0:
            st.session_state["course_progress"] = 0

        # Progress Bar (5 steps)
        st.progress(st.session_state["course_progress"])

        col1, col2, col3 = st.columns(3)
        # "Go Back" Button (Enabled only if not on the first section)
        with col1:
            if st.button("⬅️ Go Back One Step", disabled=current_step == 0):
                if st.session_state["course_progress"] > 0:
                    st.session_state["course_progress"] = max(
                        0, st.session_state["course_progress"] - 1 / (len(course_content) - 1)
                    )
                st.rerun()

        with col2:
            if st.button("Complete this section ✅"):
                if st.session_state["course_progress"] < 1.0:
                    st.session_state["course_progress"] += 1/ (len(course_content))  # Moves in 5 steps
                st.rerun()

        with col3:
            if st.button("🔄 Reset Course"):
                st.session_state["course_progress"] = 0
                st.rerun()

    else:
        st.success("🎉 Congratulations! You have completed the Mindfulness Course! 🎊")
        show_confetti()  # 🎉 Trigger Confetti Effect
        st.progress(1.0)  # Full progress

        # Reset Course Button after completion
        if st.button("🔄 Reset Course"):
            st.session_state["course_progress"] = 0
            st.rerun()

webview.create_window("Streamlit App", "http://localhost:8501")
webview.start()
