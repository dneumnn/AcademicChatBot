import sys
import os
import requests
import sqlite3
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..app import register_user, authenticate_user, save_chat, get_chat_history, hash_password, send_support_request, get_all_support_requests, get_available_models

DB_PATH = "test_chatbot.db"

@pytest.fixture(scope="function")
def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    """)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            message TEXT
        )
    """)
    conn.commit()
    yield
    conn.close()
    os.remove(DB_PATH)

def test_register_user(setup_database):
    assert register_user("testuser", "testpass", db_path=DB_PATH)
    # test duplicate registration
    assert not register_user("testuser", "testpass", db_path=DB_PATH)

def test_authenticate_user(setup_database):
    register_user("testuser", "testpass", db_path=DB_PATH)
    assert authenticate_user("testuser", "testpass", db_path=DB_PATH)
    assert not authenticate_user("testuser", "wrongpass", db_path=DB_PATH)
    assert not authenticate_user("unknownuser", "testpass", db_path=DB_PATH)

def test_save_chat_and_get_history(setup_database):
    register_user("testuser", "testpass", db_path=DB_PATH)
    save_chat("testuser", "Hello!", "Hi there!", db_path=DB_PATH)
    history = get_chat_history("testuser", db_path=DB_PATH)
    assert len(history) == 1
    assert history[0][0] == "Hello!"
    assert history[0][1] == "Hi there!"

def test_hash_password(setup_database):
    hashed = hash_password("testpass")
    assert hashed == hash_password("testpass")
    assert hashed != hash_password("differentpass")

def test_send_support_request(setup_database):
    register_user("testuser", "testpass", db_path=DB_PATH)
    response = send_support_request("testuser", "I need help!", db_path=DB_PATH)
    assert response == "Support request submitted successfully!"
    requests = get_all_support_requests(db_path=DB_PATH)
    assert len(requests) == 1
    assert requests[0][0] == "testuser"
    assert requests[0][1] == "I need help!"

def test_get_all_support_requests(setup_database):
    register_user("testuser", "testpass", db_path=DB_PATH)
    send_support_request("testuser", "First I need help!", db_path=DB_PATH)
    send_support_request("testuser", "I need more help!", db_path=DB_PATH)
    requests = get_all_support_requests(db_path=DB_PATH)
    assert len(requests) == 2
    assert requests[0][0] == "testuser"
    assert requests[1][1] == "I need more help!"

if __name__ == "__main__":
    pytest.main()
