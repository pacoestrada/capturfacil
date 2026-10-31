from pathlib import Path
import sys
import tempfile
from unittest.mock import Mock,patch
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import test_core
from recent import register_saved_image
from gi.repository import Gtk

class RecentTests(unittest.TestCase):
    def test_registration_has_correct_uri_type_viewer_and_public_visibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'Captura con acento á.png'
            path.write_bytes(b'test')
            manager=Mock();manager.add_full.return_value=True
            with patch('recent.Gtk.Settings.get_default',return_value=None):
                self.assertTrue(register_saved_image(path,manager))
            uri,data=manager.add_full.call_args.args
            self.assertEqual(uri,path.as_uri())
            self.assertEqual(data.mime_type,'image/png')
            self.assertEqual(data.app_name,'CapturFácil')
            self.assertEqual(data.app_exec,'/usr/bin/gio open %u')
            self.assertFalse(data.is_private)

    def test_history_disabled_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.png';path.touch()
            settings=Mock();settings.get_property.return_value=False
            manager=Mock()
            with patch('recent.Gtk.Settings.get_default',return_value=settings):
                self.assertFalse(register_saved_image(path,manager))
            manager.add_full.assert_not_called()

    def test_missing_file_not_registered_and_history_failure_keeps_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.png';manager=Mock()
            self.assertFalse(register_saved_image(path,manager))
            manager.add_full.assert_not_called()
            path.write_bytes(b'completed export')
            manager.add_full.side_effect=RuntimeError('unavailable history')
            with patch('recent.Gtk.Settings.get_default',return_value=None):
                self.assertFalse(register_saved_image(path,manager))
            self.assertEqual(path.read_bytes(),b'completed export')
