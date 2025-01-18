import webview
import json
import asyncio

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


async def fetch_access_token(app, retries=5, delay=1, window=0, url=None):
    token = TokenStorage.get_token()
    if token:
        return token

    main_window = webview.windows[window]

    if url:
        try:
            main_window.load_url(url)
        except Exception as e:
            app.logger.error(f"Error loading URL: {e}")
        await asyncio.sleep(2)

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
        try:
            token = main_window.evaluate_js(js)
        except Exception as e:
            app.logger.error(f"Python exception during evaluate_js: {type(e).__name__}: {str(e)}")
            app.logger.error(f"Exception details: {repr(e)}")
        else:
            if token and token != "No token found" and not token.startswith("Error:"):
                try:
                    access_token = json.loads(token)["access_token"]
                    TokenStorage.set_token(access_token)
                    app.logger.debug("Successfully got and parsed access token")
                    return access_token
                except Exception as e:
                    app.logger.error(f"Error parsing token: {e}")

        await asyncio.sleep(delay)
        app.logger.debug("Sleeping before next attempt...")

    raise Exception("Unable to fetch token from localStorage")