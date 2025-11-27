"""
Smoothing utilities for TUBA KHAN — AIR MINDMAP
Provides EMAFilter and helpers.
"""
import math

class EMAFilter:
    def __init__(self, alpha=0.6, initial=(0.0,0.0)):
        self.alpha = alpha
        self.value = tuple(initial)

    def update(self, point):
        x,y = point
        vx,vy = self.value
        nx = self.alpha * x + (1.0 - self.alpha) * vx
        ny = self.alpha * y + (1.0 - self.alpha) * vy
        self.value = (nx, ny)
        return self.value
