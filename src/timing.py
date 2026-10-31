"""Monotonic, per-capture timings; no screenshot or user data is recorded."""
import time

class CaptureTiming:
    def __init__(self, clock=None):
        self.clock = clock or time.monotonic
        self.points = {'start': self.clock()}

    def mark(self, name):
        self.points.setdefault(name, self.clock())

    def summary(self):
        p = self.points
        phases = [('start','backend','Preparar'), ('backend','received','Capturar'),
                  ('received','decoded','Cargar'), ('decoded','drawn','Mostrar')]
        parts = [f'{label} {p[end]-p[start]:.2f} s' for start,end,label in phases
                 if start in p and end in p]
        if 'drawn' in p:
            parts.append(f"Total {p['drawn']-p['start']:.2f} s")
        return ' · '.join(parts)
