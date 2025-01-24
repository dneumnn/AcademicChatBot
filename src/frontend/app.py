from typing import Dict, List, Optional
import time
import streamlit as st
from streamlit_navigation_bar import st_navbar
import sqlite3
import hashlib
import requests
import logging
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
DB_PATH = "src/frontend/database/chatbot.db"
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
        return False # User already exists
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


def get_chat_response(prompt, message_history=None, model_id=None, database=None, model_parameters=None, playlist_id=None, video_id=None, knowledge_base=None, stream=True, plaintext=False,mode=None, use_logical_routing=False, use_semantic_routing=False):
    knowledge_base= "fallback"
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
        "knowledge_base": knowledge_base,
        "stream": st.session_state.settings["stream"],
        "plaintext": st.session_state.settings["plaintext"],
        "mode": st.session_state.settings["mode"],
        "use_logical_routing": st.session_state.settings["use_logical_routing"],
        "use_semantic_routing": st.session_state.settings["use_semantic_routing"]
    }
    response = requests.post(f"{BASE_URL}/chat", json=payload)
    return response.iter_lines()


def get_analyze_response(prompt, ytvideo, chunk_max_length=550, chunk_overlap_length=50, embedding_model="nomic-embed-text"):
    payload = {
        "video_input": ytvideo,
        "chunk_max_length": st.session_state.settings["chunk_max_length"],
        "chunk_overlap_length": st.session_state.settings["chunk_overlap_length"],
        "max_limit_similarity": st.session_state.settings["max_limit_similarity"],
        "embedding_model": st.session_state.settings["embedding_model"],
        "seconds_between_frames": st.session_state.settings["seconds_between_frames"],
        "local_model": st.session_state.settings["local_model"],
        "enabled_detailed_chunking": st.session_state.settings["enabled_detailed_chunking"]        
    }
    response = requests.post(f"{BASE_URL}/analyze",json=payload)
    source_placeholder = st.empty()
    response_content = ""

    # Error Handling
    if response.status_code != 200:
        if response.status_code == 400:
            response_content = "The input parameters or the configuration could not be validated."     
        elif response.status_code == 404:
            response_content = "The requested video URL does not exist."      
        elif response.status_code == 415:
            response_content = "The video URL exists, but its type is not supported."  
        elif response.status_code == 424:
            response_content = "Either an env variable is not set, the API key does not work or the local models are not available."
        else:
            response_content= "Something went wrong, most probably a backend programming error."
        source_placeholder.markdown(response_content)  
        st.session_state.messages.append({"role": "assistant", "content": response_content, "sources": []})
        save_chat(st.session_state.username, prompt, response_content)
        return
    return response.iter_lines()


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
    excluded_model_name = "nomic-embed-text"
    try:
        response = requests.get(f"{BASE_URL}/model")
        if response.status_code == 200:
            models = response.json()
            if isinstance(models, list) and all(isinstance(model, str) for model in models):
                if excluded_model_name:
                    models = [model for model in models if model != excluded_model_name]
                return models
            else:
                st.error("Unexpected response format.")
                return []
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
                  "theme.backgroundColor": "#0E1117",
                  "theme.primaryColor": "#FF4B4B",
                  "theme.secondaryBackgroundColor": "#262730",
                  "theme.textColor": "white",
                  "button_face": "🌞"},

        "dark": {"theme.base": "light",
                 "theme.backgroundColor": "white",
                 "theme.primaryColor": "#FF4B4B",
                 "theme.secondaryBackgroundColor": "#F0F2F6",
                 "theme.textColor": "#31333F",
                 "button_face": "🌜"},
    }

if "settings" not in st.session_state:
    st.session_state.settings = {
        "history": False,
        "database": "all",
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 40,
        "playlist_id":None, 
        "video_id":None,
        "stream": True,
        "plaintext": False,
        "mode": "fast",
        "use_logical_routing": False,
        "use_semantic_routing": False,
        "max_limit_similarity": 0.85,
        "chunk_max_length": 550,
        "chunk_overlap_length": 50,
        "embedding_model": "nomic-embed-text",
      #  "knowledge_base": "all",
        "seconds_between_frames": 30,
        "local_model": False,
        "enabled_detailed_chunking": False
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

# Login/Register Page
if st.session_state.page == "Login":
    if 'models' not in st.session_state:
        st.session_state.models = get_available_models()
    st.title("Login")

    def login_user():
        if authenticate_user(st.session_state.login_username, st.session_state.login_password):
            st.session_state.username = st.session_state.login_username
            st.session_state.page = "Chat"
            st.rerun()
            
        else:
            st.error("Invalid username or password.")

    def register():
        if register_user(st.session_state.login_username, st.session_state.login_password):
                st.success("Registration successful! You can now log in.")
        else:
                st.error("Username already exists.")

    def fix_on_change():
        time.sleep(1)
        login_user()

    st.text_input("Username", key="login_username")
    st.text_input("Password", type="password", key="login_password", on_change=fix_on_change)

    login_button, register_button = st.columns(2)
    if login_button.button("Login"):
        login_user()
    if register_button.button("Register"):
        register()

    st.stop()

# Page navigation
pages = ["Chat", "Settings", "Support", "Chat History", "Admin Panel"]
styles = {
    "nav": {
        "background-color": st.session_state.themes[st.session_state.themes["current_theme"]]["theme.secondaryBackgroundColor"],
    },
    "div": {
        "max-width": "32rem",
    },
    "span": {
        "border-radius": "0.5rem",
        "color": st.session_state.themes[st.session_state.themes["current_theme"]]["theme.textColor"],
        "margin": "0 0.125rem",
        "padding": "0.4375rem 0.625rem",
    },
    "active": {
        "background-color": st.session_state.themes[st.session_state.themes["current_theme"]]["theme.backgroundColor"],
    },
    "hover": {
        "background-color": st.session_state.themes[st.session_state.themes["current_theme"]]["theme.backgroundColor"],
    },
}

options = {
    "show_menu": False,
}
st.session_state.page  = st_navbar(pages, styles=styles, options=options)

# Navigation Panel
st.sidebar.title("Navigation")

# User Info
if st.session_state.username:
    st.sidebar.markdown(f"👤 **User:** {st.session_state.username}")
else:
    st.sidebar.markdown("👤 **User:** Gast")

# Change Theme Button
btn_face = st.session_state.themes[st.session_state.themes["current_theme"]]["button_face"]
if st.sidebar.button(btn_face, help="Thema wechseln"):
    ChangeTheme()

st.session_state.selectedModel = st.sidebar.selectbox("🧠 **Select LLM Model**", st.session_state.models)

# Info
st.sidebar.subheader("ℹ️ About the Bot")
st.sidebar.info("""
This chatbot is an academic tool that processes YouTube videos for interactive user engagement.
""")

# Logout Button
if st.sidebar.button("Logout", key="logout"):
    st.session_state.page = "Login"
    st.session_state.username = None
    st.session_state.messages = []
    st.rerun()

if  st.session_state.page == "Settings":
    st.title("Streamlit Chat Settings")

    col1, spacer, col2 = st.columns([2,1,2])

    with col1:
        st.markdown("### Chat Settings")
        st.markdown("#### Settings for the creation model")
        history = st.checkbox("Use the context of the chat history ", st.session_state.settings["history"])
        database = st.selectbox(
            "Select Database Type",
            ["all", "vector", "graph"],
            index=["all", "vector", "graph"].index(str(st.session_state.settings["database"]).strip())) 
        temperature = st.slider("Controls randomness (lower = precise, higher = creative)", 0.0, 1.0, st.session_state.settings["temperature"])
        top_p = st.slider("Chooses tokens based on cumulative probability (higher = diverse)", 0.0, 1.0, st.session_state.settings["top_p"])
        top_k = st.slider("Limits the number of tokens considered (higher = creative)", 1, 100, st.session_state.settings["top_k"])
      #  knowledge_base = st.selectbox(
       #     "Select a Knowledge Base",
        #    ["all", "IDK"],
         #   index=["all", "IDK"].index(str(st.session_state.settings["knowledge_base"]).strip()))
        playlist_id = st.text_input("Enter a Playlist to use as context", st.session_state.settings["playlist_id"])
        video_id = st.text_input("Enter a Video to use as context", st.session_state.settings["video_id"])
        mode = st.selectbox(
            "Select mode of text Generation",
            ["fast", "smart"],
            index=["fast", "smart"].index(str(st.session_state.settings["mode"]).strip())) 
        use_logical_routing = st.checkbox("Use Logical Routing", st.session_state.settings["use_logical_routing"])
        use_semantic_routing = st.checkbox("Use Semantic Routing", st.session_state.settings["use_semantic_routing"])
        st.markdown("#### Settings for the output of the answer")
        stream = st.checkbox("Get answer as a stream", st.session_state.settings["stream"])
        plaintext = st.checkbox("Only get text without sources", st.session_state.settings["plaintext"])
        
    with spacer:
        st.write("")

    with col2:
        st.markdown("### Analyze Settings")
        chunk_max_length = st.slider("Select a value for the chunk size", 100, 10000, st.session_state.settings["chunk_max_length"])
        chunk_overlap_length = st.slider("Select a value for the chunk overlap length", 0, 500, st.session_state.settings["chunk_overlap_length"])
        embedding_model = st.selectbox(
            "Select Embedding Model",
            ["nomic-embed-text"],
            index=["nomic-embed-text"].index(str(st.session_state.settings["embedding_model"]).strip()))
        
        max_limit_similarity = st.slider("Select a value for the maximum limit of similarity (higher = higher chance to remove duplicates)", 0.0, 1.0, st.session_state.settings["max_limit_similarity"])
        seconds_between_frames = st.slider("Select a value for the seconds between frames", 1, 600, st.session_state.settings["seconds_between_frames"])
        local_model = st.checkbox("Use local model", st.session_state.settings["local_model"])
        enabled_detailed_chunking = st.checkbox("Enable detailed chunking", st.session_state.settings["enabled_detailed_chunking"])

    st.session_state.settings["history"] = history
    st.session_state.settings["database"] = database
    st.session_state.settings["chunk_max_length"] = chunk_max_length
    st.session_state.settings["chunk_overlap_length"] = chunk_overlap_length
    st.session_state.settings["embedding_model"] = embedding_model
    st.session_state.settings["temperature"] = temperature
    st.session_state.settings["top_p"] = top_p
    st.session_state.settings["top_k"] = top_k
    st.session_state.settings["playlist_id"] = playlist_id
    st.session_state.settings["video_id"] = video_id
    st.session_state.settings["stream"] = stream
    st.session_state.settings["plaintext"] = plaintext
    st.session_state.settings["mode"] = mode
    st.session_state.settings["use_logical_routing"] = use_logical_routing
    st.session_state.settings["use_semantic_routing"] = use_semantic_routing
    st.session_state.settings["max_limit_similarity"] = max_limit_similarity
 #   st.session_state.settings["knowledge_base"] = knowledge_base
    st.session_state.settings["seconds_between_frames"] = seconds_between_frames
    st.session_state.settings["local_model"] = local_model
    st.session_state.settings["enabled_detailed_chunking"] = enabled_detailed_chunking

# CHAT
elif  st.session_state.page == "Chat":
    
    st.title(f"Welcome, {st.session_state.username}")

    # manage session chats
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # container for dynamic content
    response_container = st.container(height = 650)
    input_container = st.container()  # Container for user input

    with response_container:
        # placeholder for dynamic content
        user_placeholder = st.empty()
        response_placeholder = st.empty()
        source_placeholder = st.empty()
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if message["sources"] != [] and int(len(message["sources"])) != 0:
                    logging.info(f"Message: {int(len(message['sources']))}")
                    sources = "Sources: " + ", ".join(message["sources"])
                    st.markdown(sources)

    # User input
    with input_container:
        if prompt := st.chat_input("..."):
            st.session_state.messages.append({"role": "user", "content": prompt, "sources": []})
            
            with response_container:
                # answer
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    response_content = ""
                    if "youtube.com" in prompt or "youtu.be" in prompt:
                        youtube_regex = r"(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)"
                        match = re.search(youtube_regex, prompt)
                        if match:
                            logging.info(f"Match: {match.group(0)}")
                            with st.spinner("Analyzing video..."):
                                lines = get_analyze_response(prompt, match.group(0))
                        else:
                            st.write("Youtube Link is not in the correct format. Please use https:// or backend is not available.")
                            st.session_state.messages.append(
                                {"role": "assistant", "content": "Youtube Link is not in the correct format. Please use https:// or backend is not available.", "sources": []}
                            )
                            save_chat(st.session_state.username, prompt, "Youtube Link is not in the correct format. Please use https:// or backend is not available.")
                            lines = None
                    else:
                        with st.spinner("Generating response..."):
                            lines = get_chat_response(prompt)

                    if st.session_state.settings["plaintext"] == False:
                        if lines:
                            combined_content = ""
                            all_sources = set()
                            buffer = ""

                            for line in lines:
                                if line:
                                    try:
                                        buffer += line.decode("utf-8")

                                        while buffer:
                                            try:
                                                data, index = json.JSONDecoder().raw_decode(buffer)
                                                combined_content += data.get("content", "")
                                                combined_content += data.get("message", "")

                                                if data.get("sources", []):
                                                    all_sources.update(data.get("sources", []))

                                                buffer = buffer[index:].lstrip()
                                            except json.JSONDecodeError:
                                                break
                                    except Exception as e:
                                        print(f"Fehler beim Verarbeiten der Zeile: {e}")

                            st.write(combined_content)
                            if int(len(all_sources)) != 0:
                                st.write("Sources: " + ", ".join(all_sources))
                                content = combined_content + "Sources: " + ", ".join(all_sources)
                            else:
                                content = combined_content

                            st.session_state.messages.append(
                                {"role": "assistant", "content": combined_content, "sources": all_sources}
                            )
                            save_chat(st.session_state.username, prompt, content)

                    else:
                        if lines:
                            for line in lines:
                                if line:
                                    word = line.decode("utf-8")
                                    response_content += word + " "
                                    st.markdown(response_content)
                                    time.sleep(0.05)

                            st.session_state.messages.append(
                                {"role": "assistant", "content": response_content, "sources": []}
                            )
                            save_chat(st.session_state.username, prompt, response_content)

elif  st.session_state.page == "Support":
    st.title("Support")
    support_message = st.text_area("Your support request")
    if st.button("Submit"):
        if support_message:
            st.success(send_support_request(st.session_state.username, support_message))

elif  st.session_state.page == "Chat History":
    st.title(f"Chat History - {st.session_state.username}")
    history = get_chat_history(st.session_state.username)
    if history:
        for message, response, msg_time, resp_time in history:
            st.write(f"**You ({msg_time}):** {message}")
            st.write(f"**Bot ({resp_time}):** {response}")
    else:
        st.info("No chat history found.")

elif  st.session_state.page == "Admin Panel":
    if st.session_state.username == "admin":
        st.title("Admin Panel")
        requests = get_all_support_requests()
        if requests:
            st.table(requests)
        else:
            st.info("No support requests found.")
    else:
        st.error("Access denied.")