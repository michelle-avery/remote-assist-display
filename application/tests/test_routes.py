# test_routes.py
import pytest
from http import HTTPStatus
from configparser import ConfigParser


def test_config_no_saved_url(client, mock_get_saved_config):
    """Test config route when no URL is saved."""
    mock_get_saved_config.return_value = ConfigParser()

    response = client.get('/')

    assert response.status_code == 302
    assert '/hass-login' in response.headers['Location']


def test_config_with_saved_url(client, mock_get_saved_config):
    """Test config route when URL is saved."""
    config = ConfigParser()
    config.add_section('HomeAssistant')
    config.set('HomeAssistant', 'url', 'http://test.local:8123')
    mock_get_saved_config.return_value = config

    response = client.get('/')

    assert response.status_code == 302
    assert '/waiting' in response.headers['Location']


def test_hass_login(client):
    """Test hass_login route."""
    response = client.get('/hass-login')

    assert response.status_code == 200
    assert b'login.html' in response.data


@pytest.mark.asyncio
async def test_connect(app, mock_fetch_access_token, mock_save_to_config, mock_load_dashboard):
    """Test successful connection to Home Assistant."""
    test_url = 'http://test.local:8123'

    with app.test_request_context('/connect', method='POST', data={'haUrl': test_url}):
        response = await app.view_functions['connect']()

    assert response[1] == HTTPStatus.OK
    mock_fetch_access_token.assert_called_once_with(app=app, url=test_url, retries=app.config['TOKEN_RETRY_LIMIT'])
    mock_save_to_config.assert_called_once_with('HomeAssistant', 'url', test_url)
    assert mock_load_dashboard.call_count == 2


def test_waiting(client):
    """Test waiting route."""
    response = client.get('/waiting')

    assert response.status_code == 200
    assert b'Configuration Pending' in response.data


@pytest.mark.asyncio
async def test_hass_config(app, mock_websocket_manager):
    """Test successful Home Assistant configuration."""
    mock_manager, mock_instance = mock_websocket_manager
    mock_instance.initialize.return_value = None

    with app.test_request_context('/hass-config', method='POST'):
        app.config['url'] = 'http://test.local:8123'
        response = await app.view_functions['hassconfig']()

    assert response[1] == HTTPStatus.OK
    mock_instance.initialize.assert_called_once_with('http://test.local:8123')

@pytest.mark.asyncio
async def test_hass_config_failure(app, mock_websocket_manager):
    """Test failed Home Assistant configuration."""
    mock_manager, mock_instance = mock_websocket_manager

    # Create an async mock that raises an exception
    async def mock_initialize_error(url):
        raise Exception("WebSocket connection failed")

    mock_instance.initialize.side_effect = mock_initialize_error

    with app.test_request_context('/hass-config', method='POST'):
        app.config['url'] = 'http://test.local:8123'
        with pytest.raises(Exception, match="WebSocket connection failed"):
            await app.view_functions['hassconfig']()