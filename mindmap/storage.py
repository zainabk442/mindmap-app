"""
Storage utilities for TUBA KHAN — AIR MINDMAP
Save/load JSON and export snapshot PNG.
"""
import os
import time
import json
from PIL import Image
import numpy as np
import cv2

class Storage:
    def __init__(self, out_dir="output"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def save_mindmap(self, mindmap, filename=None):
        if filename is None:
            filename = f"mindmap_{int(time.time())}.json"
        path = os.path.join(self.out_dir, filename)
        mindmap.save(path)
        return path

    def save_latest(self, mindmap, filename=None):
        """Save a consistent autosave filename for quick load."""
        if filename is None:
            filename = self.out_dir and os.path.join(self.out_dir, "mindmap_autosave.json") or "mindmap_autosave.json"
        path = os.path.join(self.out_dir, os.path.basename(filename))
        mindmap.save(path)
        return path

    def load_mindmap(self, path):
        from mindmap.core import MindMap
        m = MindMap()
        m.load(path)
        return m

    def export_snapshot(self, img, filename=None):
        if filename is None:
            filename = f"snapshot_{int(time.time())}.png"
        path = os.path.join(self.out_dir, filename)
        # img is numpy array BGR
        # convert to RGB and save via PIL
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(img_rgb)
        pil.save(path)
        return path
