from unittest.mock import patch

import pytest

from remote_assist_display.state import DisplayState


@pytest.fixture
def mock_state_webview(mock_webview):
    """Mock webview for state.py"""
    with patch("remote_assist_display.state.webview", mock_webview[0]):
        yield mock_webview


@pytest.mark.asyncio
async def test_local_storage_set_on_url_load(app, mock_state_webview):
    """Test that localStorage is set when loading a URL."""
    mock_webview, mock_window = mock_state_webview
    app.config["DEVICE_NAME_KEY"] = "device_name" 
    state = DisplayState.get_instance()
    
    await state.load_url("http://test.url")
    
    mock_window.evaluate_js.assert_called_with(
        f'\n            localStorage.setItem("{app.config["DEVICE_NAME_KEY"]}", "{app.config["UNIQUE_ID"]}")\n        '
    )

@pytest.mark.asyncio
async def test_local_storage_not_set_on_url_load(app, mock_state_webview):
    """Test that localStorage is not set when loading a URL."""
    mock_webview, mock_window = mock_state_webview
    app.config["DEVICE_NAME_KEY"] = "device_name"
    state = DisplayState.get_instance()
    
    await state.load_url("http://test.url", local_storage=False)
    
    mock_window.evaluate_js.assert_not_called()

@pytest.mark.asyncio
async def test_local_storage_set_on_card_load(app, mock_state_webview):
    """Test that localStorage is set when loading a card."""
    mock_webview, mock_window = mock_state_webview
    app.config["DEVICE_NAME_KEY"] = "device_name"
    app.config["url"] = "http://test.local:8123"
    state = DisplayState.get_instance()
    
    await state.load_card({"path": "/test-card"})
    
    mock_window.evaluate_js.assert_called_with(
        f'\n            localStorage.setItem("{app.config["DEVICE_NAME_KEY"]}", "{app.config["UNIQUE_ID"]}")\n        '
    )
