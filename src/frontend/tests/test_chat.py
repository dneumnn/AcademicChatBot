import sys
import os
import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from ..app import get_chat_response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE_URL = "http://localhost:8000"

@pytest.fixture
def mock_streamlit():
    with patch('app.st') as mock_st:
        yield mock_st

@pytest.fixture
def mock_requests_post():
    with patch('app.requests.post') as mock_post:
        yield mock_post

def test_get_chat_response(mock_streamlit, mock_requests_post):
    st.session_state.settings = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "playlist_id": None,
        "video_id": None,
        "history": False,
        "database": "all",
        "stream": True,
        "plaintext": False,
        "mode": "fast",
        "use_logical_routing": False,
        "use_semantic_routing": False
    }
    st.session_state.selectedModel = "test-model"
    st.session_state.username = "testuser"

    mock_response = MagicMock()
    mock_response.iter_lines.return_value = iter([b"line1", b"line2"])
    mock_requests_post.return_value = mock_response

    prompt = "What is the capital of France?"
    response = get_chat_response(prompt)

    assert list(response) == [b"line1", b"line2"]

    expected_payload = {
        "prompt": prompt,
        "message_history": None,
        "model_id": "test-model",
        "database": 'all',
        "model_parameters": {
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 50
        },
        "playlist_id": None,
        "video_id": None,
        "knowledge_base": "fallback",
        "stream": True,
        "plaintext": False,
        "mode": "fast",
        "use_logical_routing": False,
        "use_semantic_routing": False
    }

    print(mock_requests_post.call_args)
    print(st.session_state.settings)
    mock_requests_post.assert_called_once_with(f"{BASE_URL}/chat", json=expected_payload)

if __name__ == "__main__":
    pytest.main()