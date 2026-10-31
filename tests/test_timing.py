from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from timing import CaptureTiming

class CaptureTimingTests(unittest.TestCase):
    def test_reports_separate_phases_without_clock_origin(self):
        values=iter([100,100.4,104,104.1,105,999])
        timing=CaptureTiming(lambda:next(values))
        for phase in ('backend','received','decoded','drawn','drawn'):
            timing.mark(phase)
        self.assertEqual(timing.summary(),'Preparar 0.40 s · Capturar 3.60 s · Cargar 0.10 s · Mostrar 0.90 s · Total 5.00 s')
