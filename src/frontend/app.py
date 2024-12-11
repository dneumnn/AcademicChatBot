import random
import time
import streamlit as st
import sqlite3
import hashlib
import requests

DB_PATH = "database/chatbot.db"
MOCKED_MODELS = ["Llama3.2", "gpt-4", "other-llm"]
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
    # TO-DO: Differentiate between multiple chats of one user
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
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, password) VALUES ('admin', ?)
    """, (admin_password,))
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password))) # hash necessary?
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

def chat(user_input):
    try:
        payload = {"input": user_input}
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            return response.json().get("response", "no response field")
        else:
            st.error(f"Error analyzing input: {response.status_code}")
            return "Error analyzing input."
    except requests.ConnectionError:
        st.error("Connection error")
        return "Connection error"

def save_chat(username, message, response):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat_history (username, message, response) VALUES (?, ?, ?)", (username, message, response))
    conn.commit()
    conn.close()

# TO-DO: real timestamps when bot asnwers 
def save_chat(username, message, response):
    import datetime
    message_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    response_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO chat_history (username, message, response, message_timestamp, response_timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (username, message, response, message_timestamp, response_timestamp))
    conn.commit()
    conn.close()

def get_chat_history(username):
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
        response = requests.get(f"{BASE_URL}/models")
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

def mocked_response():
    response = random.choice(
        [
            "Hi there, this is our academic chatbot. How can I help you today?",
            "Hi, human! Do you want to analyze a youtube video?",
        ]
    )
    for word in response.split():
        yield word

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

                    "dark":  {"theme.base": "light",
                              "theme.backgroundColor": "white",
                              "theme.primaryColor": "#5591f5",
                              "theme.secondaryBackgroundColor": "#82E1D7",
                              "theme.textColor": "#0a1464",
                              "button_face": "🌜"},
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

#TO-DO: change behavior of on_change logging in -> prioritize register? 
# Login/Register Page
if st.session_state.page == "Login":
    st.title("Login")

    def login_user():
        if authenticate_user(st.session_state.login_username, st.session_state.login_password):
            st.session_state.username = st.session_state.login_username
            st.session_state.page = "Chat" 
            st.session_state.rerun = True  
        else:
            st.error("Invalid username or password.")

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

# Navigation Panel
st.sidebar.title("Navigation")

model = st.sidebar.selectbox("Select LLM Model", MOCKED_MODELS)

if st.session_state.username == "admin":
    if st.sidebar.button("Admin Panel", key="admin_panel"):
        st.session_state.page = "Admin Panel"
        st.rerun()

if st.sidebar.button("Chat", key="chat_button"):
    st.session_state.page = "Chat"
    st.rerun()

if st.sidebar.button("Support", key="support_button"):
    st.session_state.page = "Support"
    st.rerun()

if st.sidebar.button("Chat History", key="chat_history_button"):
    st.session_state.page = "Chat History"
    st.rerun()

if st.sidebar.button("Logout", key="logout"):
    st.session_state.page = "Login"
    st.session_state.username = None
    st.rerun()

btn_face = st.session_state.themes[st.session_state.themes["current_theme"]]["button_face"]
if st.button(btn_face):
    ChangeTheme()

# CHAT
if st.session_state.page == "Chat":
    st.title(f"Welcome, {st.session_state.username}")

    # manage session chats
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("...................."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("Chatbot"):
            response_placeholder = st.empty()  #placeholder
            response_content = ""
            for word in mocked_response():
                response_content += word + " "
                response_placeholder.markdown(response_content)
                time.sleep(0.05)
            st.session_state.messages.append({"role": "Chatbot", "content": response_content})

        save_chat(st.session_state.username, prompt, response_content)

        # TO-DO: Uncomment this block to use the backend
        # response = chat(prompt)
        # with st.chat_message("Chatbot"):
        #     response_placeholder = st.empty()
        #     response_content = ""
        #    for word in response.split():
        #         response_content += word + " "
        #         response_placeholder.markdown(response_content)
        #         time.sleep(0.05)
        #     st.session_state.messages.append({"role": "Chatbot", "content": response})

        # save_chat(st.session_state.username, prompt, response)
        

elif st.session_state.page == "Support":
    st.title("Support")
    support_message = st.text_area("Your support request")
    if st.button("Submit"):
        if support_message:
            st.success(send_support_request(st.session_state.username, support_message))

elif st.session_state.page == "Chat History":
    st.title(f"Chat History - {st.session_state.username}")
    history = get_chat_history(st.session_state.username)
    if history:
        for message, response, msg_time, resp_time in history:
            st.write(f"**You ({msg_time}):** {message}")
            st.write(f"**Bot ({resp_time}):** {response}")
    else:
        st.info("No chat history found.")

elif st.session_state.page == "Admin Panel":
    if st.session_state.username == "admin":
        st.title("Admin Panel")
        requests = get_all_support_requests()
        if requests:
            st.table(requests)
        else:
            st.info("No support requests found.")
    else:
        st.error("Access denied.")
