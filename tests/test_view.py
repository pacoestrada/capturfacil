import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import cairo
from view import fit_scale, monitor_crop
from capturfacil import Window
from types import SimpleNamespace


class ViewTests(unittest.TestCase):
    def test_fit_large_desktop_in_maximized_editor(self):
        scale = fit_scale(7680, 2160, 1650, 850)
        self.assertLessEqual(scale * 7680, 1650 - 36)
        self.assertLessEqual(scale * 2160, 850 - 36)
        self.assertGreater(fit_scale(3840, 2160, 1650, 850), scale)

    def test_small_capture_can_enlarge(self):
        self.assertGreater(fit_scale(400, 300, 1650, 850), 1)

    def test_zoomed_pointer_maps_to_original_image(self):
        base = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2000, 1000)
        for scale in [.2, .5, 1, 2, 4]:
            w = SimpleNamespace(scale=scale, offset=(18, 18), base=base)
            point = Window.point(w, SimpleNamespace(x=300*scale+18, y=200*scale+18))
            self.assertAlmostEqual(point[0], 300)
            self.assertAlmostEqual(point[1], 200)

    def test_monitor_crop_respects_desktop_scaling_and_position(self):
        base = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2400, 1000)
        cr = cairo.Context(base)
        cr.set_source_rgb(1, 0, 0)
        cr.paint()
        cr.set_source_rgb(0, 1, 0)
        cr.rectangle(800, 100, 1600, 900)
        cr.fill()
        crop = monitor_crop(base, (400, 50, 800, 450), (0, 0, 1200, 500))
        self.assertEqual((crop.get_width(), crop.get_height()), (1600, 900))
        crop.flush()
        self.assertEqual(bytes(crop.get_data()[:4]), bytes([0, 255, 0, 255]))

    def test_monitor_left_of_origin(self):
        base = cairo.ImageSurface(cairo.FORMAT_ARGB32, 2400, 1000)
        crop = monitor_crop(base, (-400, 0, 400, 500), (-400, 0, 1200, 500))
        self.assertEqual((crop.get_width(), crop.get_height()), (800, 1000))

if __name__ == '__main__':
    unittest.main()
