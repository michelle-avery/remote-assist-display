import logging
from contextlib import redirect_stdout
from io import StringIO

from server import server

import webview

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    stream = StringIO()
    with redirect_stdout(stream):
        window = webview.create_window('Remote Assist Display', server)
        webview.start(debug=True, private_mode=False)
