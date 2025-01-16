from contextlib import redirect_stdout
from io import StringIO

from remote_assist_display import create_app

import webview


if __name__ == '__main__':
    stream = StringIO()
    with redirect_stdout(stream):
        app = create_app()
        # window is created fullscreen, unless running in debug mode
        window = webview.create_window('Remote Assist Display', app, frameless=True, fullscreen=not app.debug)
        webview.start(debug=app.debug, private_mode=False)
