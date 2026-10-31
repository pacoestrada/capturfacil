from pathlib import Path
import tempfile
import unittest
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from capture_io import temporary_suffix,load_surface
from gi.repository import Gdk, GdkPixbuf, GLib
from unittest.mock import patch
import cairo
from view import monitor_crop

class CaptureIOTests(unittest.TestCase):
    def test_full_screen_bmp_and_transparent_window_png(self):
        self.assertEqual(temporary_suffix('screen'),'.bmp')
        self.assertEqual(temporary_suffix('monitor'),'.bmp')
        self.assertEqual(temporary_suffix('window'),'.png')
        self.assertEqual(temporary_suffix('area'),'.png')
        with patch('capture_io.GdkPixbuf.Pixbuf.get_formats',return_value=[]):
            self.assertEqual(temporary_suffix('screen'),'.png')

    def test_bmp_matches_png_pixel_for_pixel_including_last_row_and_column(self):
        # Odd width exercises BMP row padding and bottom-up row order.
        width,height=101,63
        data=bytes((i*37+i//7)%256 for i in range(width*height*3))
        original=GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(data),GdkPixbuf.Colorspace.RGB,False,8,width,height,width*3)
        with tempfile.TemporaryDirectory() as tmp:
            for fmt in ('png','bmp'):
                original.savev(str(Path(tmp)/('test.'+fmt)),fmt,[],[])
            png=load_surface(Path(tmp)/'test.png');bmp=load_surface(Path(tmp)/'test.bmp')
            self.assertEqual((bmp.get_width(),bmp.get_height()),(width,height))
            self.assertEqual(bytes(bmp.get_data()),bytes(png.get_data()))
            # Identical monitor crop at 200% with negative desktop origin.
            a=monitor_crop(png,(-25,0,25,30),(-25,0,50,30))
            b=monitor_crop(bmp,(-25,0,25,30),(-25,0,50,30))
            self.assertEqual(bytes(a.get_data()),bytes(b.get_data()))

    def test_png_still_preserves_window_transparency(self):
        surface=cairo.ImageSurface(cairo.FORMAT_ARGB32,40,30)
        cr=cairo.Context(surface);cr.set_source_rgba(1,0,0,.5);cr.rectangle(5,5,20,20);cr.fill()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'window.png';surface.write_to_png(str(path))
            loaded=load_surface(path)
            self.assertEqual(bytes(loaded.get_data()),bytes(surface.get_data()))
