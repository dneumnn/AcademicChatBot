import sys
import os
import requests
import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..app import get_available_models

@pytest.fixture
def mock_requests_get():
    with patch('app.requests.get') as mock_get:
        yield mock_get

def test_get_available_models_success(mock_requests_get):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = ["model1", "model2", "nomic-embed-text"]

    expected_models = ["model1", "model2"]
    models = get_available_models()
    assert models == expected_models

def test_get_available_models_unexpected_format(mock_requests_get):
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"unexpected": "format"}

    models = get_available_models()
    assert models == []

def test_get_available_models_error_status(mock_requests_get):
    mock_requests_get.return_value.status_code = 500

    models = get_available_models()
    assert models == []

def test_get_available_models_connection_error(mock_requests_get):
    mock_requests_get.side_effect = requests.ConnectionError

    models = get_available_models()
    assert models == []

if __name__ == "__main__":
    pytest.main()