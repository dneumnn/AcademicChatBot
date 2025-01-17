import random
from typing import Dict, List, Optional
import time
import streamlit as st
from streamlit_navigation_bar import st_navbar
import sqlite3
import hashlib
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
DB_PATH = "database/chatbot.db"
BASE_URL = "http://localhost:8000"

# Database Initialization
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    # Chat history
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT,
        response TEXT,
        message_timestamp TEXT,
        response_timestamp TEXT
    )
    """)
    # Support requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS support_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        message TEXT
    )
    """)

    # Add admin user
    admin_password = hash_password("admin")
    cursor.execute("INSERT OR IGNORE INTO users (username, password) VALUES ('admin', ?)", (admin_password,))
    conn.commit()
    conn.close()


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",(username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        stored_password = result[0]
        return stored_password == hash_password(password)
    return False
    
#TO-DO: use optional params if needed
def get_chat_response(prompt, message_history=None, model_id=None, database=None, model_parameters=None, playlist_id=None, video_id=None, knowledge_base=None):

    model_parameters = {
        "temperature": st.session_state.settings["temperature"],
        "top_p": st.session_state.settings["top_p"],
        "top_k": st.session_state.settings["top_k"]
    }   

    if st.session_state.settings["playlist_id"]:
        playlist_id = st.session_state.settings["playlist_id"]

    if st.session_state.settings["video_id"]:
        video_id = st.session_state.settings["video_id"]

    if st.session_state.settings["history"]:
        message_history = get_chat_history(st.session_state.username, True)
        logging.info(f"Message History: {message_history}")
        logging.info(f"Prompt: {prompt}")

    if st.session_state.settings["database"] != "All":
        database = st.session_state.settings["database"]
        database = database.lower()

    payload = {
        "prompt": prompt,
        "message_history": message_history,
        "model_id": st.session_state.selectedModel,
        "database": database,
        "model_parameters": model_parameters,
        "playlist_id": playlist_id,
        "video_id": video_id,
        "knowledge_base": knowledge_base
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload, stream=True)
    return response.iter_lines()

def get_analyze_response(prompt, chunk_max_length=550, chunk_overlap_length=50, embedding_model="nomic-embed-text"):
    payload = {
        "video_input": prompt,
        "chunk_max_length": st.session_state.settings["chunk_max_length"],
        "chunk_overlap_length": st.session_state.settings["chunk_overlap_length"],
    }
    response = requests.post(f"{BASE_URL}/analyze",json=payload)
    return response.iter_lines()

# TO-DO: real timestamps when bot answers
def save_chat(username, message, response):
    import datetime
    message_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    response_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (username, message, response, message_timestamp, response_timestamp) VALUES (?, ?, ?, ?, ?)", (username, message, response, message_timestamp, response_timestamp))
    conn.commit()
    conn.close()


def get_chat_history(username, forChatParameter: Optional[bool] = False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT message, response, message_timestamp, response_timestamp
    FROM chat_history
    WHERE username = ?
    ORDER BY message_timestamp ASC
    """, (username,))
    history = cursor.fetchall()
    conn.close()
    if forChatParameter:
        history = [{"message": request[0], "response": request[1]} for request in history]
    return history

def send_support_request(username, message):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO support_requests (username, message) VALUES (?, ?)", (username, message))
    conn.commit()
    conn.close()
    return "Support request submitted successfully!"


def get_all_support_requests():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT username, message FROM support_requests")
    requests = cursor.fetchall()
    conn.close()
    return requests


def get_available_models():
    try:
        response = requests.get(f"{BASE_URL}/model")
        if response.status_code == 200:
            return response.json().get("models", [])
        else:
            st.error(f"Error fetching models: {response.status_code}")
            return []
    except requests.ConnectionError:
        st.error("Unable to connect to the backend.")
        return []


def ChangeTheme():
    # Toggle the current theme
    if st.session_state.themes["current_theme"] == "light":
        st.session_state.themes["current_theme"] = "dark"
    else:
        st.session_state.themes["current_theme"] = "light"

    # Get the theme dictionary for the new theme
    tdict = st.session_state.themes[st.session_state.themes["current_theme"]]

    # Apply the theme settings
    for vkey, vval in tdict.items():
        if vkey.startswith("theme"):
            st._config.set_option(vkey, vval)

    st.rerun()

# Initialize Database
init_db()

if "themes" not in st.session_state:
    st.session_state.themes = {
        "current_theme": "dark",
        "refreshed": True,

        "light": {"theme.base": "dark",
                  "theme.backgroundColor": "black",
                  "theme.primaryColor": "#c98bdb",
                  "theme.secondaryBackgroundColor": "#5591f5",
                  "theme.textColor": "white",
                  "theme.textColor": "white",
                  "button_face": "🌞"},

        "dark": {"theme.base": "light",
                 "theme.backgroundColor": "white",
                 "theme.primaryColor": "#5591f5",
                 "theme.secondaryBackgroundColor": "#82E1D7",
                 "theme.textColor": "#0a1464",
                 "button_face": "🌜"},
    }


if "settings" not in st.session_state:
    st.session_state.settings = {
        "history": False,
        "database": "All",
        "routing": True,
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 40,
        "playlist_id":None, 
        "video_id":None,
        "chunk_max_length": 550,
        "chunk_overlap_length": 50,
        "embedding_model": "nomic-embed-text"
    }

# Session management
if "username" not in st.session_state:
    st.session_state.username = None

if "page" not in st.session_state:
    st.session_state.page = "Login"

# Dark Mode
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Rerun trigger
if "rerun" not in st.session_state:
    st.session_state.rerun = False

if st.session_state.rerun:
    st.session_state.rerun = False
    st.rerun()

# TO-DO: change behavior of on_change logging in -> prioritize register?
# Login/Register Page
if st.session_state.page == "Login":
    st.title("Login")

    def login_user():
        if authenticate_user(st.session_state.login_username, st.session_state.login_password):
            st.session_state.username = st.session_state.login_username
            st.session_state.page = "Chat"
            st.session_state.models = get_available_models()
            st.session_state.rerun = True
        else:
            st.error("Invalid username or password.")

    # TO-DO: change behavior of on_change logging in -> prioritize register?
    st.text_input("Username", key="login_username")
    st.text_input("Password", type="password", key="login_password", on_change=login_user)

    login_button, register_button = st.columns(2)
    if login_button.button("Login"):
        login_user()


    def register_user_and_login():
        if register_user(st.session_state.login_username, st.session_state.login_password):
            st.success("Registration successful! You can now log in.")
            st.session_state.username = st.session_state.login_username
            st.session_state.page = "Chat"
            st.session_state.rerun = True
        else:
            st.error("Username already exists.")


    if register_button.button("Register"):
        register_user_and_login()

    st.stop()

# TODO: chat page keeps twitching when other page is selected, highlight stays on chat instead of the newly selected page
# Page navigation
pages = ["Chat", "Settings", "Support", "Chat History", "Admin Panel"]
page = st_navbar(pages)

# Navigation Panel
st.sidebar.title("Navigation")

# Begrüßung und Benutzeranzeige
if st.session_state.username:
    st.sidebar.markdown(f"👤 **User:** {st.session_state.username}")
else:
    st.sidebar.markdown("👤 **User:** Gast")

# LLM-Auswahl
st.session_state.selectedModel = st.sidebar.selectbox("🧠 **Select LLM Model**", st.session_state.models)

if st.sidebar.button("Logout", key="logout"):
    st.session_state.page = "Login"
    st.session_state.username = None
    st.rerun()

# Info-Bereich
st.sidebar.subheader("ℹ️ About the Bot")
st.sidebar.info("""
Hier die Erklärung über den Bot einfügen.
""")

# Farbschema-Wechsel
# TO-DO: default theme with streamlit.toml?
btn_face = st.session_state.themes[st.session_state.themes["current_theme"]]["button_face"]
if st.sidebar.button(btn_face, help="Thema wechseln"):
    ChangeTheme()


if page == "Settings":
    st.title("Streamlit Chat Settings")

    col1, spacer, col2 = st.columns([2,1,2])

    with col1:
        st.markdown("### Chat Settings")
        history = st.checkbox("Use the context of the chat history ", st.session_state.settings["history"])
        database = st.selectbox(
            "Select Database Type",
            ["All", "Vector", "Graph"],
            index=["All", "Vector", "Graph"].index(str(st.session_state.settings["database"]).strip())) 
        routing = st.checkbox("Use Logical Routing", st.session_state.settings["routing"])
        temperature = st.slider("Controls randomness (lower = precise, higher = creative)", 0.0, 1.0, st.session_state.settings["temperature"])
        top_p = st.slider("Chooses tokens based on cumulative probability (higher = diverse)", 0.0, 1.0, st.session_state.settings["top_p"])
        top_k = st.slider("Limits the number of tokens considered (higher = creative)", 1, 100, st.session_state.settings["top_k"])
        playlist_id = st.text_input("Enter a Playlist to use as context", st.session_state.settings["playlist_id"])
        video_id = st.text_input("Enter a Video to use as context", st.session_state.settings["video_id"])

    with spacer:
        st.write("")

    with col2:
        st.markdown("### Analyze Settings")
        chunk_max_length = st.slider("Select a value for the chunk size", 250, 1000, st.session_state.settings["chunk_max_length"])
        chunk_overlap_length = st.slider("Select a value for the chunk overlap length", 0, 100, st.session_state.settings["chunk_overlap_length"])
        embedding_model = st.selectbox(
            "Select Embedding Model",
            ["nomic-embed-text"],
            index=["nomic-embed-text"].index(str(st.session_state.settings["embedding_model"]).strip()))

    st.session_state.settings["history"] = history
    st.session_state.settings["database"] = database
    st.session_state.settings["routing"] = routing
    st.session_state.settings["chunk_max_length"] = chunk_max_length
    st.session_state.settings["chunk_overlap_length"] = chunk_overlap_length
    st.session_state.settings["embedding_model"] = embedding_model
    st.session_state.settings["tempreature"] = temperature
    st.session_state.settings["top_p"] = top_p
    st.session_state.settings["top_k"] = top_k
    st.session_state.settings["playlist_id"] = playlist_id
    st.session_state.settings["video_id"] = video_id

    # Display current settings
    st.markdown("### Current Settings")
    st.write(f"Chatsettings:{st.session_state.settings['history']}{st.session_state.settings['database']}{st.session_state.settings['routing']}{st.session_state.settings['temperature']}{st.session_state.settings['top_p']}{st.session_state.settings['top_k']}{st.session_state.settings['playlist_id']}{st.session_state.settings['video_id']}")
    st.write(f"Chatsettings:{st.session_state.settings['chunk_max_length']}{st.session_state.settings['chunk_overlap_length']}{st.session_state.settings['embedding_model']}")

# CHAT
elif page == "Chat":
    st.title(f"Welcome, {st.session_state.username}")

    # manage session chats
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # TO-DO: make bot stream response instead of writing all at once
    # User Input
    if prompt := st.chat_input("..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()  # placeholder
            response_content = ""
            if "youtube.com" in prompt or "youtu.be" in prompt:
                lines = get_analyze_response(prompt)

            else:
                lines = get_chat_response(prompt)

            for line in lines:
                if line:
                    word = line.decode('utf-8')
                    response_content += word + " "
                    response_placeholder.markdown(response_content)
                    time.sleep(0.05)
            st.session_state.messages.append({"role": "assistant", "content": response_content})
            # TO-DO: timestamp correctly    
            save_chat(st.session_state.username, prompt, response_content)

elif page == "Support":
    st.title("Support")
    support_message = st.text_area("Your support request")
    if st.button("Submit"):
        if support_message:
            st.success(send_support_request(st.session_state.username, support_message))

elif page == "Chat History":
    st.title(f"Chat History - {st.session_state.username}")
    history = get_chat_history(st.session_state.username)
    if history:
        for message, response, msg_time, resp_time in history:
            st.write(f"**You ({msg_time}):** {message}")
            st.write(f"**Bot ({resp_time}):** {response}")
    else:
        st.info("No chat history found.")

elif page == "Admin Panel":
    if st.session_state.username == "admin":
        st.title("Admin Panel")
        requests = get_all_support_requests()
        if requests:
            st.table(requests)
        else:
            st.info("No support requests found.")
    else:
        st.error("Access denied.")