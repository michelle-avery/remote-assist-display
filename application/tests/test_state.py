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
    state = DisplayState.get_instance()
    
    await state.load_url("http://test.url")
    
    mock_window.evaluate_js.assert_called_once()
    assert "localStorage.setItem" in mock_window.evaluate_js.call_args[0][0]

@pytest.mark.asyncio
async def test_local_storage_not_set_on_url_load(app, mock_state_webview):
    """Test that localStorage is not set when loading a URL."""
    mock_webview, mock_window = mock_state_webview
    state = DisplayState.get_instance()
    
    await state.load_url("http://test.url", local_storage=False)
    
    mock_window.evaluate_js.assert_not_called()

@pytest.mark.asyncio
async def test_local_storage_set_on_card_load(app, mock_state_webview):
    """Test that localStorage is set when loading a card."""
    mock_webview, mock_window = mock_state_webview
    state = DisplayState.get_instance()
    
    await state.load_card({"path": "/test-card"})
    
    mock_window.evaluate_js.assert_called()
    assert "localStorage.setItem" in mock_window.evaluate_js.call_args[0][0]

@pytest.mark.asyncio
async def test_relative_url_calls_load_hass_path(app, mock_state_webview):
    """Test that a relative URL calls load_hass_path."""
    mock_webview, mock_window = mock_state_webview
    mock_window.get_current_url.return_value = "http://test.local:8123/original-card"
    state = DisplayState.get_instance()
    
    await state.load_card({"path": "/test-card"})

    mock_window.get_current_url.assert_called_once()
    mock_window.load_url.assert_not_called()

@pytest.mark.asyncio
async def test_relative_url_different_current_url(app, mock_state_webview):
    """Test that a relative URL calls load_url if the window currently doesn't have the home assistant URL loaded."""
    mock_webview, mock_window = mock_state_webview
    mock_window.get_current_url.return_value = "http://different-url.com"

    state = DisplayState.get_instance()
    
    await state.load_card({"path": "/test-card"})
    
    mock_window.get_current_url.assert_called_once()
    mock_window.load_url.assert_called_once()