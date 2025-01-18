import configparser
import os
import pytest
import uuid

from flask import Flask
from unittest.mock import MagicMock, patch, Mock
from remote_assist_display import create_app
from remote_assist_display.config_handler import get_saved_config, save_to_config
from remote_assist_display.websocket_manager import WebSocketManager
from remote_assist_display.navigate import load_dashboard


@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['TOKEN_RETRY_LIMIT'] = 3
    app.config['UNIQUE_ID'] = 'test-device-id'

    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def mock_get_saved_config():
    """Mock the get_saved_config function."""
    with patch('remote_assist_display.routes.get_saved_config') as mock:
        yield mock


@pytest.fixture
def mock_save_to_config():
    """Mock the save_to_config function."""
    with patch('remote_assist_display.routes.save_to_config') as mock:
        yield mock


@pytest.fixture
def mock_fetch_access_token():
    """Mock the fetch_access_token function."""
    with patch('remote_assist_display.routes.fetch_access_token') as mock:
        mock.return_value = "fake-token"
        yield mock


@pytest.fixture
def mock_load_dashboard():
    """Mock the load_dashboard function."""
    with patch('remote_assist_display.routes.load_dashboard') as mock:
        yield mock


@pytest.fixture
def mock_websocket_manager():
    """Mock the WebSocketManager."""
    with patch('remote_assist_display.routes.WebSocketManager') as mock_class:
        mock_instance = MagicMock()

        # Create an async mock for the initialize method
        async def mock_initialize(url):
            return None

        mock_instance.initialize.side_effect = mock_initialize

        mock_class.get_instance.return_value = mock_instance
        yield mock_class, mock_instance

@pytest.fixture
def mock_webview():
    """Mock the webview module."""
    with patch('remote_assist_display.auth.webview') as mock:
        # Create a mock window
        mock_window = Mock()
        mock.create_window.return_value = mock_window
        mock.windows = [mock_window]
        yield mock, mock_window

@pytest.fixture
def temp_config_file(tmp_path, monkeypatch):
    """Create a temporary config file and patch the CONFIG_FILE constant."""
    config_file = tmp_path / "test_config.ini"
    monkeypatch.setattr('remote_assist_display.config_handler.CONFIG_FILE', str(config_file))
    return config_file

@pytest.fixture
def sample_config(temp_config_file):
    """Create a sample config file with some initial data."""
    config = configparser.ConfigParser()
    config['TestSection'] = {
        'test_key': 'test_value',
        'another_key': 'another_value'
    }
    with open(temp_config_file, 'w') as f:
        config.write(f)
    return config

@pytest.fixture
def mock_uuid_node():
    """Mock uuid.getnode() to return a consistent value for testing."""
    with patch('uuid.getnode') as mock:
        # This will give us a known MAC address: "112233445566"
        mock.return_value = 0x112233445566
        yield mock