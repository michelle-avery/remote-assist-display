# test_routes.py
from configparser import ConfigParser
from http import HTTPStatus

import pytest


def test_config_no_saved_url(client, mock_get_saved_config):
    """Test config route when no URL is saved."""
    mock_get_saved_config.return_value = ConfigParser()

    response = client.get("/")

    assert response.status_code == 302
    assert "/hass-login" in response.headers["Location"]


def test_config_with_saved_url(client, mock_get_saved_config):
    """Test config route when URL is saved."""
    config = ConfigParser()
    config.add_section("HomeAssistant")
    config.set("HomeAssistant", "url", "http://test.local:8123")
    mock_get_saved_config.return_value = config

    response = client.get("/")

    assert response.status_code == 302
    assert "/waiting" in response.headers["Location"]


def test_hass_login(client):
    """Test hass_login route."""
    response = client.get("/hass-login")

    assert response.status_code == 200
    assert b"login.html" in response.data


@pytest.mark.asyncio
async def test_connect(
    app, mock_fetch_access_token, mock_save_to_config, mock_load_dashboard
):
    """Test successful connection to Home Assistant."""
    test_url = "http://test.local:8123"

    with app.test_request_context("/connect", method="POST", data={"haUrl": test_url}):
        response = await app.view_functions["connect"]()

    assert response[1] == HTTPStatus.OK
    mock_fetch_access_token.assert_called_once_with(
        app=app, url=test_url, retries=app.config["TOKEN_RETRY_LIMIT"], delay=10
    )
    mock_save_to_config.assert_called_once_with("HomeAssistant", "url", test_url)
    assert mock_load_dashboard.call_count == 2


def test_waiting(client):
    """Test waiting route."""
    response = client.get("/waiting")

    assert response.status_code == 200
    assert b"Configuration Pending" in response.data


def test_hass_config(app, mock_websocket_manager):
    """Test successful Home Assistant configuration."""
    mock_manager, mock_instance = mock_websocket_manager

    with app.test_request_context("/hass-config", method="POST"):
        app.config["url"] = "http://test.local:8123"
        response = app.view_functions["hassconfig"]()

    assert response[1] == HTTPStatus.OK
    mock_manager.get_instance.assert_called_once_with(app)
    mock_instance.initialize.assert_called_once_with("http://test.local:8123")


def test_hass_config_failure(app, mock_websocket_manager):
    """Test failed Home Assistant configuration."""
    mock_manager, mock_instance = mock_websocket_manager

    # Mock initialize to raise an exception
    mock_instance.initialize.side_effect = Exception("WebSocket connection failed")

    with app.test_request_context("/hass-config", method="POST"):
        app.config["url"] = "http://test.local:8123"
        response = app.view_functions["hassconfig"]()

    assert response[1] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert "WebSocket connection failed" in response[0]["error"]
    mock_manager.get_instance.assert_called_once_with(app)


def test_hass_config_missing_url(app, mock_websocket_manager):
    """Test Home Assistant configuration with missing URL."""
    mock_manager, mock_instance = mock_websocket_manager

    with app.test_request_context("/hass-config", method="POST"):
        # Don't set app.config["url"]
        response = app.view_functions["hassconfig"]()

    assert response[1] == HTTPStatus.BAD_REQUEST
    assert "Missing Home Assistant URL" in response[0]["error"]
    mock_manager.get_instance.assert_not_called()
