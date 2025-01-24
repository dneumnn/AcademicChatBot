import sys
import os
import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from ..app import changeTheme

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_streamlit():
    with patch('app.st') as mock_st:
        yield mock_st

def test_change_theme(mock_streamlit):
    st.session_state.themes = {
        "current_theme": "light",
        "light": {"theme.textColor": "#000000"},
        "dark": {"theme.textColor": "#FFFFFF"}
    }

    changeTheme()

    assert st.session_state["themes"]["current_theme"] == "dark"

if __name__ == "__main__":
    pytest.main()