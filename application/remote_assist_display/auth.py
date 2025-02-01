import asyncio
import json
from typing import Any, Optional

import webview


class TokenStorage:
    _access_token = None

    @classmethod
    def set_token(cls, token):
        cls._access_token = token

    @classmethod
    def get_token(cls):
        return cls._access_token

    @classmethod
    def clear_token(cls):
        cls._access_token = None


async def ensure_window_loaded(app, window: webview.Window, url: str, timeout: int = 30) -> bool:
    """
    Ensures a pywebview window is fully loaded using the native loaded event.
    
    Args:
        app: Application instance with logging
        window: PyWebView window instance
        url: URL to load
        timeout: Maximum time to wait for load in seconds
        
    Returns:
        bool: True if window loaded successfully, False otherwise
        
    Raises:
        Exception: If there's an error loading the URL
    """
    load_event = asyncio.Event()
    
    def on_loaded():
        load_event.set()
        
    # Register load event handler
    window.events.loaded += on_loaded
    
    try:
        app.logger.debug(f"Loading URL: {url}")
        window.load_url(url)
        try:
            app.logger.debug(f"Waiting for page to load (timeout={timeout}s)")
            await asyncio.wait_for(load_event.wait(), timeout=timeout)
            # Add small delay for JS context initialization
            await asyncio.sleep(2)
            return True
        except asyncio.TimeoutError:
            app.logger.error("Timeout waiting for page to load")
            return False
    except Exception as e:
        app.logger.error(f"Error loading URL: {e}")
        raise
    finally:
        # Clean up event handler
        window.events.loaded -= on_loaded

async def evaluate_js_safely(app, window: webview.Window, js: str) -> Optional[Any]:
    """
    Safely evaluates JavaScript in a pywebview window with error handling.
    
    Args:
        app: Application instance with logging
        window: PyWebView window instance
        js: JavaScript code to evaluate
        
    Returns:
        Optional[Any]: Result of JavaScript evaluation or None if failed
    """
    try:
        app.logger.debug("Evaluating JS...")
        result = window.evaluate_js(js)
        if result is None:
            app.logger.debug("Got None response from evaluate_js")
        app.logger.debug(f"JS result: {result}")
        return result
    except Exception as e:
        app.logger.error(f"Python exception during evaluate_js: {type(e).__name__}: {str(e)}")
        app.logger.error(f"Exception details: {repr(e)}")
        return None

async def fetch_access_token(app, retries: int = 5, delay: int = 1, window: int = 0, 
                           url: Optional[str] = None, force: bool = False) -> str:
    """
    Fetches an access token from localStorage in a pywebview window.
    
    Args:
        app: Application instance with logging and TokenStorage
        retries: Number of attempts to fetch token
        delay: Delay between retries in seconds
        window: Window index to use
        url: URL to load before fetching token
        force: Whether to force refresh the token
        
    Returns:
        str: Access token
        
    Raises:
        Exception: If unable to fetch token after all retries
    """
    if force:
        TokenStorage.clear_token()
    else:
        token = TokenStorage.get_token()
        if token:
            return token

    main_window = webview.windows[window]
    
    if url:
        success = await ensure_window_loaded(app, main_window, url)
        app.logger.debug(f"Window loaded successfully: {success}")
        if not success:
            raise Exception("Failed to load window within timeout")

    js = """
        (function() {
            try {
                var token = localStorage.getItem("hassTokens");
                if (token) {
                    return token;
                }
                return "No token found";
            } catch (e) {
                return "Error: " + e.toString();
            }
        })();
        """

    for attempt in range(retries):
        app.logger.debug(f"Evaluating JS, attempt {attempt + 1} of {retries}")
        
        token = await evaluate_js_safely(app, main_window, js)
        
        if token and token != "No token found" and not token.startswith("Error:"):
            try:
                # The response seems to sometimes be json, and sometimes double-quoted json, so we'll try both
                try:
                    parsed_token = json.loads(token)
                except json.JSONDecodeError:
                    # Check if it's double-quoted
                    if isinstance(token, str) and token.startswith('"') and token.endswith('"'):
                        # remove the outer quotes and try again
                        token = token[1:-1]
                        token = token.replace('\\"', '"')
                        parsed_token = json.loads(token)
                    else:
                        raise
                if not isinstance(parsed_token, dict):
                    raise ValueError(f"Parsed token is not a dictionary: {type(parsed_token)}")
                
                if "access_token" not in parsed_token:
                    raise ValueError("No access_token found in parsed token")
                
                access_token = parsed_token["access_token"]
                if not isinstance(access_token, str):
                    raise ValueError(f"access_token is not a string: {type(access_token)}")
                TokenStorage.set_token(access_token)
                app.logger.debug("Successfully got and parsed access token")
                return access_token
            except Exception as e:
                app.logger.error(f"Error parsing token: {str(e)}")
                app.logger.debug(f"Token: {token}")
                app.logger.debug(f"Token type: {type(token)}")

        await asyncio.sleep(delay)
        app.logger.debug("Sleeping before next attempt...")

    raise Exception("Unable to fetch token from localStorage")