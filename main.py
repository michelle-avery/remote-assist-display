from contextlib import redirect_stdout
from io import StringIO

from server import create_app

import webview


if __name__ == '__main__':
    stream = StringIO()
    with redirect_stdout(stream):
        app = create_app()
        window = webview.create_window('Remote Assist Display', app)
        webview.start(debug=True, private_mode=False)
