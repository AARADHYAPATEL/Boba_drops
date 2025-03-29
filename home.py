import os
import time
from datetime import datetime
import json
import streamlit as st
from hashlib import sha512
import re
import uuid
import zipfile
import io
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from textblob import TextBlob
import pickle
import base64
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText

# Scopes required for sending email
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

success_placeholder = st.empty()

# Path to store user_info
USER_DATA_FILE = "user_data.json"

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["current_user"] = None

# Load existing user
if os.path.exists(USER_DATA_FILE):
    try:
        with open(USER_DATA_FILE, "r") as f:
            users = json.load(f)
        if not isinstance(users, dict):
            raise ValueError("Invalid user data structure, Expected a dictionary")
    except Exception as e:
        users = {}
        st.error(f"Failed to load user data: {e}")
else:
    users = {}


def hash_password(password):
    return sha512(password.encode()).hexdigest()


def is_valid_username(username):
    """Validate the username based on specific rules"""
    if not username or len(username.strip()) < 3 or len(username.strip()) > 20:
        return False, "Username must be between 3 and 20 characters long."
    if not re.match("^[A-Za-z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""


def is_valid_password(password):
    """Validate the password based on specific rules"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not any(char.isupper() for char in password):
        return False, "Password must include at least one uppercase letter."
    if not any(char.islower() for char in password):
        return False, "Password must include at least one lowercase letter."
    if not any(char.isdigit() for char in password):
        return False, "Password must include at least one digit."
    if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
        return False, "Password must include at least one special character."
    return True, ""


def generate_user_id():
    """Generation of a unique UUID"""
    return str(uuid.uuid4())


def create_zip_file(user_folder):
    zip_buffer = io.BytesIO()  # In-memory zip file
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, _, files in os.walk(user_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, user_folder)
                zip_file.write(file_path, arcname)
    zip_buffer.seek(0)  # Reset buffer pointer
    return zip_buffer

def analyze_sentiment(entry):
    blob = TextBlob(entry)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive", polarity
    elif polarity < 0:
        return "Negative", polarity
    else:
        return "Neutral", polarity


def authenticate_gmail():
    """Authenticate the user and return the Gmail service object."""
    creds = None

    # Check if token.pickle exists for saved credentials
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, prompt the user to log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=8083)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    # Build the Gmail service
    service = build('gmail', 'v1', credentials=creds)
    return service

def generate_pdf(title, timestamp, content):
    """
        Generate a PDF using a text object for word wrapping.
        Returns an in-memory PDF buffer.
        """
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    margin = 50  # Margin from the edges

    # Draw title and timestamp at the top
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin, height - margin, f"Title: {title}")
    c.setFont("Helvetica", 12)
    c.drawString(margin, height - margin - 20, f"Date: {timestamp}")

    # Initialize text object for content with a starting position below the header
    text_object = c.beginText()
    text_object.setTextOrigin(margin, height - margin - 50)
    text_object.setFont("Helvetica", 12)

    # Use textwrap to wrap content lines to fit within the page width
    # Adjust the width parameter (here, 100 characters) as needed for your layout
    wrapped_lines = []
    for paragraph in content.split('\n'):
        # Wrap each paragraph and add a blank line after each
        wrapped_lines.extend(textwrap.wrap(paragraph, width=100))
        wrapped_lines.append('')

    # Add wrapped lines to the text object and manage page breaks
    for line in wrapped_lines:
        text_object.textLine(line)
        # If the y-position is too low, finish the current page and start a new one
        if text_object.getY() < margin:
            c.drawText(text_object)
            c.showPage()
            text_object = c.beginText()
            text_object.setTextOrigin(margin, height - margin)
            text_object.setFont("Helvetica", 12)

    # Finalize drawing and save the PDF
    c.drawText(text_object)
    c.save()
    pdf_buffer.seek(0)
    return pdf_buffer

def create_message(sender, to, subject, message_text):
    """Create an email message."""
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(service, sender, to, subject, message_text):
    """Send an email through Gmail API."""
    message = create_message(sender, to, subject, message_text)
    try:
        sent_message = service.users().messages().send(userId='me', body=message).execute()
        print(f"Message sent! Message ID: {sent_message['id']}")
    except Exception as error:
        print(f"An error occurred: {error}")

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


st.title("🌿 The Mind Partner")

query_params = st.query_params
default_tab = query_params.get("auth_tab", ["Login"])[0]


if default_tab not in ["Login", "Sign Up"]:
    default_tab = "Login"

# Initialize session state for navigation
if "page" not in st.session_state:
    st.session_state["page"] = "journal"  # Default page
# Initialize session state for theme and primary color
if "theme" not in st.session_state:
    st.session_state["theme"] = "Light"  # Default theme
if "primary_color" not in st.session_state:
    st.session_state["primary_color"] = "#4CAF50"  # Default primary color

load_preferences()

with st.sidebar:
    st.header("Customize Theme")
    theme = st.radio("Choose Theme:", ["Light", "Dark"], index=0 if st.session_state["theme"] == "Light" else 1)
    primary_color = st.color_picker("Pick Primary Color:", value=st.session_state["primary_color"])
    if st.button("Apply Theme"):
        st.session_state["theme"] = theme
        st.session_state["primary_color"] = primary_color
        save_preferences()
        success_placeholder.success("Theme updated successfully!")
        time.sleep(3)
        success_placeholder.empty()

    # Redirect to Gratitude AI
    if st.button("Go to Gratitude AI 🤖"):
        st.switch_page("pages/gratitude_ai.py")  # Redirect to Gratitude AI Page

    # Redirect to Mindfulness Timer ✅ Add this!
    if st.button("Go to Mindfulness Timer 🕰️"):
        st.switch_page("pages/mindfulness_hub.py")

# Apply the chosen theme
apply_theme(st.session_state["theme"], st.session_state["primary_color"])

try:
    tab = st.radio("Choose an option:", ["Login", "Sign Up"], index=["Login", "Sign Up"].index(default_tab),
                   key="auth_tab")
except ValueError as e:
    st.error(f"Error: {e}")
    tab = "Login"

if tab == "Sign Up":
    st.subheader("Create a Mind Partner account")
    st.text("Your own Mind Partner Account")

    # Input fields for username and password
    username = st.text_input("Enter a username: ", placeholder="coolguy123", key="registering_username")
    password = st.text_input("Enter a password: ", type="password", key="registering_password")
    confirm_password = st.text_input("Confirm your password: ", type="password", key="confirmation_registering_password")

    if st.button("Create Account", key="account_creation"):
        username_valid, username_message = is_valid_username(username)
        password_valid, password_message = is_valid_password(password)
        if not username.strip():
            st.warning("Username cannot be blank!")
        elif not username_valid:
            st.warning(username_message)
        elif not password_valid:
            st.warning(password_message)
        elif password != confirm_password:
            st.warning("Passwords do not match! Please try again")
        elif username in users:
            st.warning("Username already taken, please choose another username")
        else:
            user_id = str(uuid.uuid4())
            users[user_id] = {"username": username, "password": hash_password(password)}
            with open(USER_DATA_FILE, "w") as f:
                json.dump(users, f)
            success_placeholder.success("Account created successfully! You can now log in.")
            time.sleep(3)
            success_placeholder.empty()

elif tab == "Login":
    st.subheader("Login to your Mind Partner")

    username = st.text_input("Enter your Username: ", key="username_input")
    password = st.text_input("Enter you Password: ", type="password", key="password_input")

    if st.button("Login", key="loging_user_in"):
        if username.strip() and password.strip():
            valid_users = {uid: data for uid, data in users.items() if isinstance(data, dict) and "username" in data}
            user_id = [uid for uid, data in valid_users.items() if data["username"] == username]

            if user_id and users[user_id[0]]["password"] == hash_password(password):
                user_id = user_id[0]  # Assign user_id
                st.session_state["logged_in"] = True
                st.session_state["current_user"] = username
                st.session_state["user_id"] = user_id  # Store user_id in session state

                success_placeholder.success(f"✅ Welcome back, {username}!")
                time.sleep(3)
                success_placeholder.empty()
                st.rerun()

            else:
                st.warning("Invalid username or password. Please try again.")
        else:
            st.warning("Please enter both username and password.")


# Input area for the Journal Entry
if st.session_state["logged_in"]:
    st.subheader("📖 The Gratitude Journal")

    valid_users = {uid: data for uid, data in users.items() if isinstance(data, dict) and "username" in data}
    if len(valid_users) != len(users):
        st.warning("Some invalid user entries were ignored")

    user_id = [uid for uid, data in users.items() if data["username"] == st.session_state["current_user"]]
    if user_id:
        user_id = user_id[0]
    else:
        st.error("Logged-in user not found. Please log in again.")
        st.session_state["logged_in"] = False  # Reset login state
        st.stop()

    st.subheader(f"Hello, {st.session_state['current_user']}")
    user_folder = os.path.join("journal_entries", user_id)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    journal_entry = st.text_area("Write your journal entry here:", height=500, placeholder="I am grateful of...", key="journal_entry_area")

    custom_name = st.text_input("Enter a name for your entry (Optional):", placeholder="e.g. MyBeautifulEntry", key="custom_name")

    if st.button("logout", key="loging_out_user"):
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.query_params.update(auth_tab="Login")
        success_placeholder.success("You have successfully logged out. Please manually refresh page if needed")
        time.sleep(3)
        success_placeholder.empty()
        st.rerun()

    # Save button for the journal entry
    if st.button("Save and Analyze Entry", key="saving_and_analyzing_entry"):
        if journal_entry.strip():
            with st.spinner("Saving your entry..."):
                entry_id = str(uuid.uuid4())
                timestamp = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

                sentiment, polarity = analyze_sentiment(journal_entry)

                # Save metadata
                metadata = {
                    "id": entry_id,
                    "title": custom_name.strip() if custom_name.strip() else f"Entry {timestamp}",
                    "timestamp": timestamp,
                    "content": journal_entry.strip(),
                    "sentiment": sentiment,
                }

                metadata_file = os.path.join(user_folder, "metadata.json")
                if os.path.exists(metadata_file):
                    with open(metadata_file, "r") as f:
                        entries = json.load(f)
                else:
                    entries = []

                entries.append(metadata)
                with open(metadata_file, "w") as f:
                    json.dump(entries, f, indent=4)

            success_placeholder.success(f"Your entry '{metadata['title']}' has been saved.")
            time.sleep(3)
            success_placeholder.empty()
            st.info(f"Sentiment Analysis Result: {sentiment}")
        else:
            st.warning("Please write something before saving!")
else:
    st.warning("Please log in before using")

# Display previous entries
if st.session_state.get("logged_in", False):
    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("Unexpected error: User ID not found. Please log in again.")
        st.session_state["logged_in"] = False
        st.session_state["current_user"] = None
        st.stop()
    user_folder = os.path.join("journal_entries", user_id)
    metadata_file = os.path.join(user_folder, "metadata.json")
    trash_file = os.path.join(user_folder, "trash.json")
    with st.spinner("Loading your entries..."):
        st.subheader("Your Journal Entries")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                entries = json.load(f)

            if entries:
                # Download metadata as JSON
                st.download_button(
                    label="Download metadata",
                    data=json.dumps(entries, indent=4),
                    file_name="metadata.json",
                    mime="application/json",
                    key="metadata_download"
                )

                # Sort entries
                sort_option = st.selectbox(
                    "Sort entries by:",
                    ["Timestamp (Newest First)", "Timestamp (Oldest First)", "Title (A-Z)", "Title (Z-A)"]
                )
                sort_map = {
                    "Timestamp (Newest First)": lambda x: x["timestamp"],
                    "Timestamp (Oldest First)": lambda x: x["timestamp"],
                    "Title (A-Z)": lambda x: x["title"].lower(),
                    "Title (Z-A)": lambda x: x["title"].lower(),
                }
                reverse_sort = "Newest" in sort_option or "Z-A" in sort_option
                entries = sorted(entries, key=sort_map[sort_option], reverse=reverse_sort)

                # Display entries
                select_all = st.checkbox("Select all entries", key="select_all")
                selected_entries = set()

                for entry in entries:
                    col1, col2 = st.columns([0.05, 0.95]) # Creation of layout for checkboxes
                    with col1:
                        selected = st.checkbox("", key=f"selection_{entry['id']}", value=select_all)
                        if selected:
                            selected_entries.add(entry["id"])
                    with col2:
                        with st.expander(f"{entry['title']} ({entry['timestamp']})"):
                            st.write(entry["content"])
                            sentiment = entry.get("sentiment", "Unknown") # This is used to handle missing keys
                            st.info(f"Sentiment: {sentiment}")

                            recipient_email = st.text_input(f"Recipient Email for '{entry['title']}'", placeholder="Enter recipient email", key=f"email_input_{entry['id']}")

                            if st.button(f"Send '{entry['title']}' via Email", key=f"send_entry{entry['id']}"):
                                if not recipient_email.strip():
                                    st.warning(f"Please provide a recipient email for '{entry['title']}'!")
                                elif not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
                                    st.warning(f"Please provide a valid email address for '{entry['title']}'!")
                                else:
                                    try:
                                        # Email body content
                                        message_body = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"

                                        # Sending the email
                                        service = authenticate_gmail()  # Assuming this function handles Gmail API authentication
                                        send_email(service, "youremail@gmail.com", recipient_email,
                                                   "My Gratitude Journal Entry", message_body)

                                        # Confirmation
                                        success_placeholder.success(f"Email for '{entry['title']}' sent successfully!")
                                        time.sleep(3)
                                        success_placeholder.empty()
                                    except Exception as e:
                                        st.error(f"Failed to send email for '{entry['title']}': {e}")

                            # Download as .txt
                            txt_content = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"
                            st.download_button(
                                label="Download as .txt",
                                data=txt_content,
                                file_name=f"{entry['title']}.txt",
                                mime="text/plain",
                                key=f"txt_{entry['id']}"
                            )

                            # Download as .pdf
                            pdf_buffer = generate_pdf(entry['title'], entry['timestamp'], entry['content'])
                            st.download_button(
                                label="Download as .pdf",
                                data=pdf_buffer,
                                file_name=f"{entry['title']}.pdf",
                                mime="application/pdf",
                                key=f"pdf_{entry['id']}"
                            )
                if selected_entries:
                    if st.button("Move selected entries to trash", key="move_to_trash"):
                        if os.path.exists(trash_file):
                            with open(metadata_file, "w") as f:
                                json.dump(entries, f, indent=4)
                        else:
                            trashed_entries = []

                        trashed_entries.extend([e for e in entries if e["id"] in selected_entries])
                        entries = [e for e in entries if e["id"] not in selected_entries]

                        with open(metadata_file, "w") as f:
                            json.dump(entries, f, indent=4)
                        with open(trash_file, "w") as f:
                            json.dump(trashed_entries, f, indent=4)

                        success_placeholder.success(f"Deleted {len(selected_entries)} entries successfully")
                        time.sleep(3)
                        success_placeholder.empty()
                if os.path.exists(trash_file):
                    with open(trash_file, "r") as f:
                        trashed_entries = json.load(f)

                    if trashed_entries:
                        st.subheader("🗑️ Trash Bin")
                        st.info("Deleted entries are stored here. You can restore or permanently delete them.")

                        restore_all = st.checkbox("Select all Trashed Entries", key="restore_all")
                        selected_trash = set()

                        for entry in trashed_entries:
                            col1, col2 = st.columns([0.05, 0.95])

                            with col1:
                                selected = st.checkbox("", key=f"trash_selection_{entry['id']}", value=restore_all)
                                if selected:
                                    selected_trash.add(entry["id"])

                            with col2:
                                with st.expander(f"{entry['title']} ({entry['timestamp']})"):
                                    st.write(entry["content"])
                                    sentiment = entry.get("sentiment", "Unknown")  # This is used to handle missing keys
                                    st.info(f"Sentiment: {sentiment}")

                                    recipient_email = st.text_input(f"Recipient Email for '{entry['title']}'",
                                                                    placeholder="Enter recipient email", key=f"email_input_{entry['id']}")

                                    if st.button(f"Send '{entry['title']}' via Email", key="send_email"):
                                        if not recipient_email.strip():
                                            st.warning(f"Please provide a recipient email for '{entry['title']}'!")
                                        elif not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
                                            st.warning(f"Please provide a valid email address for '{entry['title']}'!")
                                        else:
                                            try:
                                                # Email body content
                                                message_body = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"

                                                # Sending the email
                                                service = authenticate_gmail()  # Assuming this function handles Gmail API authentication
                                                send_email(service, "youremail@gmail.com", recipient_email,
                                                           "My Gratitude Journal Entry", message_body)

                                                # Confirmation
                                                success_placeholder.success(
                                                    f"Email for '{entry['title']}' sent successfully!")
                                                time.sleep(3)
                                                success_placeholder.empty()
                                            except Exception as e:
                                                st.error(f"Failed to send email for '{entry['title']}': {e}")

                                    # Download as .txt
                                    txt_content = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"
                                    st.download_button(
                                        label="Download as .txt",
                                        data=txt_content,
                                        file_name=f"{entry['title']}.txt",
                                        mime="text/plain",
                                        key=f"txt_{entry['id']}"
                                    )

                                    # Download as .pdf
                                    pdf_buffer = generate_pdf(entry['title'], entry['timestamp'], entry['content'])
                                    st.download_button(
                                        label="Download as .pdf",
                                        data=pdf_buffer,
                                        file_name=f"{entry['title']}.pdf",
                                        mime="application/pdf",
                                        key=f"pdf_{entry['id']}"
                                    )
                        if selected_trash:
                            if st.button("Restore Selected Entries", key="restore_entries"):
                                entries.extend([e for e in trashed_entries if e["id"] in selected_trash])
                                trashed_entries = [e for e in trashed_entries if e["id"] not in selected_trash]

                                with open(metadata_file, "w") as f:
                                    json.dump(entries, f, indent=4)
                                with open(trash_file, "w") as f:
                                    json.dump(trashed_entries, f, indent=4)

                                success_placeholder.success(f"Restored {len(selected_trash)} entries!")
                                time.sleep(3)
                                success_placeholder.empty()

                        if selected_trash:
                            if st.button("Permanently Delete Selected Entries", key="delete_permanently"):
                                trashed_entries = [e for e in trashed_entries if e["id"] not in selected_trash]

                                with open(trash_file, "w") as f:
                                    json.dump(trashed_entries, f, indent=4)

                                success_placeholder.success(f"Permanently deleted {len(selected_trash)} entries!")
                                time.sleep(3)
                                success_placeholder.empty()

            else:
                st.info("No journal entries found.")
        else:
            st.info("No journal entries found.")

    # Bulk download everything as ZIP
    if st.button("Download all entries as ZIP", key="download_as_zip"):
        if entries:  # Ensure there are entries to download
            try:
                with st.spinner("Preparing your entries..."):
                    zip_buffer = io.BytesIO()  # In-memory zip file
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        # Add metadata to ZIP
                        zf.writestr("metadata.json", json.dumps(entries, indent=4))

                        for entry in entries:
                            # Add .txt file
                            txt_content = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"
                            zf.writestr(f"{entry['title']}.txt", txt_content)

                            # Add .pdf file
                            pdf_buffer = io.BytesIO()
                            pdf = canvas.Canvas(pdf_buffer)
                            pdf.drawString(100, 800, f"Title: {entry['title']}")
                            pdf.drawString(100, 780, f"Date: {entry['timestamp']}")
                            text = entry['content'].replace("\n", "\n\n")
                            pdf.drawString(100, 760, text)
                            pdf.save()
                            pdf_buffer.seek(0)
                            zf.writestr(f"{entry['title']}.pdf", pdf_buffer.getvalue())

                    zip_buffer.seek(0)
                    st.download_button(
                        label="Download everything as ZIP",
                        data=zip_buffer,
                        file_name="journal_entries.zip",
                        mime="application/zip",
                        key="all_download"
                    )
            except Exception as e:
                st.error(f"Failed to create ZIP file: {e}")
        else:
            st.warning("No entries found to download.")

    if st.button("Send via Email", key="send_entries_via_emails"):
        if not recipient_email.strip():
            st.warning("Please provide a recipient email address!")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", recipient_email):
            st.warning("Please provide a valid email address!")
        else:
            try:
                for entry in entries:
                    recipient_email = st.text_input("Recipient Email Address",
                                                    placeholder="Enter the recipient's email address",
                                                    key=f"email_input_{entry['id']}")
                    service = authenticate_gmail()
                    message_body = f"Title: {entry['title']}\nDate: {entry['timestamp']}\n\n{entry['content']}"
                    send_email(service, "youremail@gmail.com", recipient_email, "My Gratitude Journal Entry", message_body)
                    success_placeholder.success("Email sent successfully")
                    time.sleep(3)
                    success_placeholder.empty()
            except Exception as e:
                st.error(f"Failed to send email: {e}")
