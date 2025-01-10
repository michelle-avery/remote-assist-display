from PyInstaller.utils.hooks import collect_system_data_files

datas = collect_system_data_files("/usr/lib/gtk-3.0", "gtk-3.0")
datas += collect_system_data_files("/usr/lib/gdk-pixbuf-2.0", "gdk-pixbuf-2.0")
datas += collect_system_data_files("/usr/share/icons/hicolor", "icons/hicolor")