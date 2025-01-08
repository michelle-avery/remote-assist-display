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

async def fetch_access_token(retries=5, delay=1):
    token = TokenStorage.get_token()
    if token:
        return token

    for _ in range(retries):
        token = webview.windows[0].evaluate_js("""
                    localStorage.getItem("hassTokens")
                """)
        if token:
            access_token = json.loads(token)["access_token"]
            TokenStorage.set_token(access_token)
            return access_token
        await asyncio.sleep(delay)
    raise Exception("Unable to fetch token from localStorage")