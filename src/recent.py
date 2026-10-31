"""Register completed exports with the desktop's recent-file manager."""
from pathlib import Path
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


def register_saved_image(path, manager=None):
    path = Path(path)
    if not path.is_file():
        return False
    settings = Gtk.Settings.get_default()
    if settings is not None and not settings.get_property('gtk-recent-files-enabled'):
        return False
    data = Gtk.RecentData()
    data.display_name = path.name
    data.mime_type = 'image/png'
    data.app_name = 'CapturFácil'
    # CapturFácil is a capture tool, not an existing-image viewer.
    data.app_exec = '/usr/bin/gio open %u'
    data.is_private = False
    try:
        manager = manager if manager is not None else Gtk.RecentManager.get_default()
        return bool(manager.add_full(path.resolve().as_uri(), data))
    except (GLib.Error, RuntimeError):
        # The exported image must remain saved even if recent-history is unavailable.
        return False
