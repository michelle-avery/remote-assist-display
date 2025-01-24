from contextlib import redirect_stdout
from io import StringIO

import webview

from remote_assist_display import create_app

if __name__ == '__main__':
    stream = StringIO()
    with redirect_stdout(stream):
        app = create_app()
        window = webview.create_window('Remote Assist Display', app, frameless=True, fullscreen=app.config['FULLSCREEN'])
        webview.start(debug=app.config['WEBVIEW_DEBUG'], private_mode=False)
