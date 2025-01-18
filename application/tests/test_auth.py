import json
import pytest
from remote_assist_display.auth import TokenStorage, fetch_access_token

class TestTokenStorage:
    def test_set_and_get_token(self):
        """Test setting and getting a token."""
        TokenStorage.clear_token()  # Start fresh
        test_token = "test-token-123"

        TokenStorage.set_token(test_token)
        assert TokenStorage.get_token() == test_token

    def test_clear_token(self):
        """Test clearing a token."""
        test_token = "test-token-123"
        TokenStorage.set_token(test_token)

        TokenStorage.clear_token()
        assert TokenStorage.get_token() is None


class TestFetchAccessToken:
    @pytest.mark.asyncio
    async def test_fetch_token_from_storage(self, app):
        """Test fetching token when it's already in storage."""
        stored_token = "stored-token-123"
        TokenStorage.set_token(stored_token)
        token = await fetch_access_token(app)
        assert token == stored_token

    @pytest.mark.asyncio
    async def test_fetch_token_from_window_success(self, mock_webview, app):
        """Test successfully fetching token from window localStorage."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # Mock the localStorage response
        test_token = "new-token-456"
        mock_window.evaluate_js.return_value = json.dumps({"access_token": test_token})

        token = await fetch_access_token(app)

        assert token == test_token
        mock_window.evaluate_js.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_token_multiple_attempts(self, mock_webview, app):
        """Test token fetch with multiple attempts before success."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # First attempts return None, last attempt succeeds
        test_token = "delayed-token-789"
        mock_window.evaluate_js.side_effect = [
            None,
            None,
            json.dumps({"access_token": test_token})
        ]

        token = await fetch_access_token(app, retries=3, delay=0.1)

        assert token == test_token
        assert mock_window.evaluate_js.call_count == 3

    @pytest.mark.asyncio
    async def test_fetch_token_failure_existing_window(self, mock_webview, app):
        """Test token fetch failure after max retries."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # All attempts return None
        mock_window.evaluate_js.return_value = None

        with pytest.raises(Exception, match="Unable to fetch token from localStorage"):
            await fetch_access_token(app, retries=2, delay=0.1)

        assert mock_window.evaluate_js.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_token_failure_new_window(self, mock_webview, app):
        """Test token fetch failure after max retries with new window."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # All attempts return None
        mock_window.evaluate_js.return_value = None

        with pytest.raises(Exception, match="Unable to fetch token from localStorage"):
            await fetch_access_token(app, retries=2, delay=0.1, url="http://test.local:8123")

        assert mock_window.evaluate_js.call_count == 2


    @pytest.mark.asyncio
    async def test_fetch_token_existing_window(self, mock_webview, app):
        """Test fetching token using an existing window."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        test_token = "existing-window-token"
        mock_window.evaluate_js.return_value = json.dumps({"access_token": test_token})

        token = await fetch_access_token(app, window=0, url=None)

        assert token == test_token

    @pytest.mark.asyncio
    async def test_fetch_token_invalid_json(self, mock_webview, app):
        """Test handling invalid JSON in localStorage."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # Return invalid JSON
        mock_window.evaluate_js.return_value = "invalid json"

        with pytest.raises(Exception):
            await fetch_access_token(app, retries=1)

    @pytest.mark.asyncio
    async def test_fetch_token_missing_access_token(self, mock_webview, app):
        """Test handling JSON without access_token field."""
        mock_wv, mock_window = mock_webview
        TokenStorage.clear_token()

        # Return JSON without access_token
        mock_window.evaluate_js.return_value = json.dumps({"other_field": "value"})

        with pytest.raises(Exception):
            await fetch_access_token(app, retries=1)