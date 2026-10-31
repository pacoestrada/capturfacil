from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch, Mock
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import test_core  # Isolate GSettings and config before importing the app.
from capturfacil import Window
import cairo
from capture_io import load_surface
from gi.repository import Gdk

class GnomeCaptureTests(unittest.TestCase):
    def editor(self):
        geo = SimpleNamespace(x=1920,y=0,width=1920,height=1080)
        monitor = SimpleNamespace(get_geometry=lambda:geo)
        display = SimpleNamespace(get_monitor_at_window=lambda _:monitor,
                                  get_n_monitors=lambda:1,get_monitor=lambda _:monitor)
        w = SimpleNamespace(tempdir=None, get_display=lambda:display, get_window=lambda:None,
                            hide=Mock(), present=Mock(), error=Mock(), set_status=Mock())
        w.start_capture_process=lambda:Window.start_capture_process(w)
        w.cleanup_capture=lambda:Window.cleanup_capture(w)
        w.check_capture=lambda:Window.check_capture(w)
        w.load_image=Mock()
        return w

    def test_all_modes_use_gnome_and_never_read_root_drawable(self):
        for mode, extra in [('monitor',[]),('screen',[]),('area',['-a']),('window',['-w','-d','3'])]:
            w=self.editor()
            callbacks=[]
            with patch('capturfacil.GLib.timeout_add',side_effect=lambda ms,cb:callbacks.append(cb)), \
                 patch('capturfacil.subprocess.Popen') as process, \
                 patch('capturfacil.Gdk.pixbuf_get_from_window',side_effect=AssertionError('unsafe capture')):
                Window.capture(w,mode)
                callbacks[0]()
                self.assertEqual(process.call_args.args[0],['gnome-screenshot','-f',str(w.capture_path)]+extra)
            w.cleanup_capture()

    def test_waits_for_capture_completion_then_opens_complete_png(self):
        w=self.editor()
        callbacks=[]
        with patch('capturfacil.GLib.timeout_add',side_effect=lambda ms,cb:callbacks.append(cb)), \
             patch('capturfacil.subprocess.Popen') as process:
            Window.capture(w,'screen')
            callbacks[0]()
        process.return_value.poll.return_value=None
        w.capture_path.write_bytes(b'partial PNG')
        self.assertTrue(w.check_capture())
        w.load_image.assert_not_called()
        base=cairo.ImageSurface(cairo.FORMAT_ARGB32,3840,2160)
        cr=cairo.Context(base);cr.set_source_rgb(1,0,0);cr.paint()
        pixbuf=Gdk.pixbuf_get_from_surface(base,0,0,3840,2160)
        pixbuf.savev(str(w.capture_path),'bmp',[],[])
        received=[]
        w.load_image=lambda path,monitor:received.append(load_surface(path))
        process.return_value.poll.return_value=0
        process.return_value.communicate.return_value=(None,b'')
        process.return_value.returncode=0
        self.assertFalse(w.check_capture())
        self.assertEqual((received[0].get_width(),received[0].get_height()),(3840,2160))
        self.assertEqual(bytes(received[0].get_data()),bytes(base.get_data()))
        self.assertIsNone(w.tempdir)
        w.present.assert_called_once()
        w.error.assert_not_called()
