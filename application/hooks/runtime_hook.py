import os
import sys

def _append_sys_path():
    gdk_pixbuf_path = os.path.join(sys._MEIPASS, "gdk-pixbuf-2.0")
    gtk_path = os.path.join(sys._MEIPASS, "gtk-3.0")
    os.environ["GDK_PIXBUF_MODULE_FILE"] = os.path.join(gdk_pixbuf_path, "loaders.cache")
    os.environ["GTK_PATH"] = gtk_path
    if not os.environ.get("XDG_DATA_DIRS"):
        os.environ["XDG_DATA_DIRS"] = os.path.join(sys._MEIPASS, "icons")

_append_sys_path()