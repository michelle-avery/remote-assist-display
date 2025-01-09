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

async def fetch_access_token(retries=5, delay=1, window=0, url=None):
    token = TokenStorage.get_token()
    if token:
        return token

    if url:
        token_window = webview.create_window(title="token", url=url, hidden=True)
    else:
        token_window = webview.windows[window]
    for _ in range(retries):
        js = """
                localStorage.getItem("hassTokens")
            """
        token = token_window.evaluate_js(js)
        if token:
            access_token = json.loads(token)["access_token"]
            TokenStorage.set_token(access_token)
            if url:
                token_window.destroy()
            return access_token
        await asyncio.sleep(delay)
    raise Exception("Unable to fetch token from localStorage")