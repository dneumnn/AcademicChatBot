import sys
import os
import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from ..app import get_analyze_response

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

def test_get_analyze_response_success(mock_streamlit, mock_requests_post):
    st.session_state.settings = {
        "chunk_max_length": 550,
        "chunk_overlap_length": 50,
        "max_limit_similarity": 0.8,
        "embedding_model": "nomic-embed-text",
        "seconds_between_frames": 1,
        "local_model": True,
        "enabled_detailed_chunking": False
    }
    st.session_state.username = "testuser"
    st.session_state.messages = []

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.iter_lines.return_value = iter([b"line1", b"line2"])
    mock_requests_post.return_value = mock_response

    prompt = "Analyze this video"
    ytvideo = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    response = get_analyze_response(prompt, ytvideo)

    assert list(response) == [b"line1", b"line2"]

    expected_payload = {
        "video_input": ytvideo,
        "chunk_max_length": 550,
        "chunk_overlap_length": 50,
        "max_limit_similarity": 0.8,
        "embedding_model": "nomic-embed-text",
        "seconds_between_frames": 1,
        "local_model": True,
        "enabled_detailed_chunking": False
    }
    mock_requests_post.assert_called_once_with(f"{BASE_URL}/analyze", json=expected_payload)

def test_get_analyze_response_error(mock_streamlit, mock_requests_post):
    st.session_state.settings = {
        "chunk_max_length": 550,
        "chunk_overlap_length": 50,
        "max_limit_similarity": 0.8,
        "embedding_model": "nomic-embed-text",
        "seconds_between_frames": 1,
        "local_model": True,
        "enabled_detailed_chunking": False
    }
    st.session_state.username = "testuser"
    st.session_state.messages = []

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_post.return_value = mock_response

    prompt = "Analyze this video"
    ytvideo = "https://www.youtube.com/watjknpOch?v=dQw4w9WgXcQ"
    response = get_analyze_response(prompt, ytvideo)

    assert response is None

    expected_message = "The requested video URL does not exist."
    assert st.session_state.messages[-1]["content"] == expected_message

if __name__ == "__main__":
    pytest.main()