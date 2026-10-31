from pathlib import Path
import sys
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import test_core
from backends import capture_commands
import test_capture
from capturfacil import Window

class BackendTests(unittest.TestCase):
    def test_fast_only_for_full_screen_x11_with_compatible_fallback(self):
        with patch('backends.shutil.which',return_value='/usr/bin/scrot'):
            for mode in ('monitor','screen'):
                commands=capture_commands(mode,'/tmp/capture.bmp',x11=True)
                self.assertEqual(commands,[['/usr/bin/scrot','-z','-o','/tmp/capture.bmp'],['gnome-screenshot','-f','/tmp/capture.bmp']])
            for mode in ('area','window'):
                self.assertEqual(len(capture_commands(mode,'/tmp/capture.png',x11=True)),1)
            self.assertEqual(len(capture_commands('screen','/tmp/capture.bmp',x11=False)),1)
            self.assertEqual(len(capture_commands('screen','/tmp/capture.bmp',x11=True,compatible=True)),1)
        with patch('backends.shutil.which',return_value=None):
            self.assertEqual(len(capture_commands('screen','/tmp/capture.bmp',x11=True)),1)

    def make_capture(self):
        w=test_capture.GnomeCaptureTests().editor()
        callbacks=[]
        with patch('capturfacil.GLib.timeout_add',side_effect=lambda ms,cb:callbacks.append(cb)),patch('capturfacil.subprocess.Popen'):
            Window.capture(w,'screen')
            callbacks[0]()
        return w

    def test_failed_fast_process_discards_file_and_retries_gnome_once(self):
        w=self.make_capture()
        w.capture_path.write_bytes(b'partial')
        w.pending_commands=[['gnome-screenshot','-f',str(w.capture_path)]]
        w.process.poll.return_value=1
        w.process.returncode=1
        w.process.communicate.return_value=(None,b'capture failed')
        with patch('capturfacil.subprocess.Popen') as process:
            self.assertTrue(w.check_capture())
            self.assertEqual(process.call_args.args[0][0],'gnome-screenshot')
        self.assertFalse(w.capture_path.exists())
        self.assertEqual(w.pending_commands,[])
        w.load_image.assert_not_called()
        w.cleanup_capture()

    def test_undecodable_fast_image_retries_without_showing_error(self):
        w=self.make_capture()
        w.capture_path.write_bytes(b'not a bitmap')
        w.pending_commands=[['gnome-screenshot','-f',str(w.capture_path)]]
        w.process.poll.return_value=0
        w.process.returncode=0
        w.process.communicate.return_value=(None,b'')
        w.load_image.side_effect=ValueError('invalid image')
        with patch('capturfacil.subprocess.Popen'):
            self.assertTrue(w.check_capture())
        self.assertEqual(w.pending_commands,[])
        w.error.assert_not_called()
        self.assertIsNotNone(w.tempdir)
        w.cleanup_capture()

    def test_missing_fast_binary_uses_fallback_without_aborting(self):
        w=self.make_capture()
        w.pending_commands=[['scrot','-z',str(w.capture_path)],['gnome-screenshot','-f',str(w.capture_path)]]
        with patch('capturfacil.subprocess.Popen',side_effect=[FileNotFoundError('scrot'),Mock()]):
            self.assertTrue(w.start_capture_process())
        self.assertEqual(w.capture_backend,'gnome-screenshot')
        w.error.assert_not_called()
        w.cleanup_capture()
