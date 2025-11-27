import math
import sys
import os
import pytest
import numpy as np
# Ensure project root is on sys.path so tests can import application packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from hand.gestures import GestureManager

def make_hand(index_pos=(0.5,0.5), thumb_pos=(0.48,0.5)):
    # Build a mock hand dict with normalized landmarks (21,2)
    lm = np.zeros((21,2), dtype=float)
    # set index tip (8) and pip (6)
    lm[8] = index_pos
    lm[6] = (index_pos[0]-0.02, index_pos[1])
    # thumb tip
    lm[4] = thumb_pos
    # other fingers folded near pip
    lm[12] = (0.6,0.6); lm[10] = (0.6,0.6)
    lm[16] = (0.6,0.6); lm[14] = (0.6,0.6)
    lm[20] = (0.6,0.6); lm[18] = (0.6,0.6)
    return {"label":"Right", "normalized": lm, "landmarks": np.zeros((21,2))}

def test_detect_pinch():
    cfg = {"pinch_threshold":0.05, "pinch_confirm_frames":1}
    gm = GestureManager(cfg=cfg)
    h = make_hand(index_pos=(0.5,0.5), thumb_pos=(0.501,0.501))
    gm.update([h], tracker=type("T",(),{"trail":[], "trail_positions": []}))
    assert gm.consume_event("pinch") or gm.pinch_count>0

def test_detect_point():
    cfg = {"point_confirm_frames":1}
    gm = GestureManager(cfg=cfg)
    h = make_hand(index_pos=(0.7,0.3))
    # craft landmarks so index tip is far from pip and others folded
    # feed update multiple times to confirm
    for _ in range(2):
        gm.update([h], tracker=type("T",(),{"trail":[], "trail_positions": []}))
    assert gm.consume_event("point") or gm.point_count>0

def test_detect_tap():
    cfg = {"tap_speed_threshold":0.001, "tap_confirm_frames":1}
    gm = GestureManager(cfg=cfg)
    # simulate three frames with increased velocity
    seq = [
        {"label":"Right", "normalized": np.zeros((21,2)), "landmarks": np.zeros((21,2))},
        {"label":"Right", "normalized": np.zeros((21,2)), "landmarks": np.zeros((21,2))},
        {"label":"Right", "normalized": np.zeros((21,2)), "landmarks": np.zeros((21,2))}
    ]
    seq[0]["normalized"][8] = (0.5,0.5)
    seq[1]["normalized"][8] = (0.51,0.49)
    seq[2]["normalized"][8] = (0.56,0.44)
    for h in seq:
        gm.update([h], tracker=type("T",(),{"trail":[], "trail_positions": []}))
    assert gm.consume_event("tap") or gm.tap_count>0

def test_detect_circle():
    cfg = {"circle_min_points":12, "circle_min_sweep_degrees":200, "circle_confirm_frames":1}
    gm = GestureManager(cfg=cfg)
    # simulate circular trail in tracker
    center = (320,240)
    trail = []
    for a in range(0, 330, 30):
        rad = math.radians(a)
        x = center[0] + 60*math.cos(rad)
        y = center[1] + 60*math.sin(rad)
        trail.append((int(x),int(y)))
    tracker = type("T",(),{"trail": trail, "trail_positions": trail})
    gm.update([], tracker=tracker)
    circ = gm.consume_circle()
    assert circ is not None
