from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from focus import present_requested,Gdk
from capturfacil import Application

class FocusTests(unittest.TestCase):
    def test_each_explicit_activation_uses_fresh_server_timestamp(self):
        events=[]
        class Native:
            mask=Gdk.EventMask.EXPOSURE_MASK
            def get_events(self): return self.mask
            def set_events(self,mask): self.mask=mask;events.append('mask')
            def set_user_time(self,value): events.append(('user',value))
        native=Native()
        window=Mock()
        window.realize.side_effect=lambda:events.append('realize')
        window.get_window.return_value=native
        window.deiconify.side_effect=lambda:events.append('deiconify')
        window.present_with_time.side_effect=lambda stamp:events.append(('present',stamp))
        stamps=iter([100,200])
        def server_time(w):
            self.assertTrue(w.mask & Gdk.EventMask.PROPERTY_CHANGE_MASK)
            self.assertTrue(w.mask & Gdk.EventMask.EXPOSURE_MASK)
            return next(stamps)
        with patch('focus.GdkX11',SimpleNamespace(X11Window=Native,x11_get_server_time=server_time)):
            present_requested(window)
            present_requested(window)
        self.assertEqual(events,['realize','mask',('user',100),'deiconify',('present',100),
                                 'realize','mask',('user',200),'deiconify',('present',200)])
        window.present.assert_not_called()

    def test_non_x11_uses_normal_activation(self):
        window=Mock()
        with patch('focus.GdkX11',None):
            present_requested(window)
        window.deiconify.assert_called_once()
        window.present.assert_called_once()
        window.present_with_time.assert_not_called()

    def test_background_and_capture_never_request_focus(self):
        with patch('capturfacil.present_requested') as present:
            Application.do_activate(SimpleNamespace(window=SimpleNamespace(tempdir=None),background=True))
            Application.do_activate(SimpleNamespace(window=SimpleNamespace(tempdir=object()),background=False))
        present.assert_not_called()
