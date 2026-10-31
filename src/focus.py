"""Present a window in response to an explicit activation, including warm starts."""
import gi
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib
try:
    gi.require_version('GdkX11', '3.0')
    from gi.repository import GdkX11
except (ImportError, ValueError):
    GdkX11 = None


def present_requested(window):
    # D-Bus Activate from the Print shortcut contains no GTK key event. present()
    # may reuse the old Save click timestamp, which GNOME regards as stale.
    window.realize()
    native = window.get_window()
    timestamp = 0
    if GdkX11 is not None and isinstance(native, GdkX11.X11Window):
        try:
            # get_server_time waits for a PropertyNotify event on this window.
            native.set_events(native.get_events() | Gdk.EventMask.PROPERTY_CHANGE_MASK)
            timestamp = GdkX11.x11_get_server_time(native)
            if timestamp:
                native.set_user_time(timestamp)
        except (GLib.Error, RuntimeError):
            timestamp = 0
    window.set_accept_focus(True)
    window.set_focus_on_map(True)
    window.deiconify()
    if timestamp:
        window.present_with_time(timestamp)
    else:
        window.present()
