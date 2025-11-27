"""
Gesture detectors for TUBA KHAN — AIR MINDMAP
Provides functions to detect pinch, point, circle, two-hand stretch, and tap.
"""
import math
import time
import numpy as np
from collections import deque
import cv2

class GestureManager:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.history_length = self.cfg.get("history_length", 64)
        self._hand_histories = {}  # hand_id -> deque of normalized index positions
        self.current_state = "idle"
        self.event_queue = []
        self.circle_buffer = deque(maxlen=self.cfg.get("circle_min_points", 20)*2)
        self.shape_buffer = deque(maxlen=8)
        self.last_point_pos = None
        self.last_pinch_pos = None
        self.last_created_time = 0
        # confirmation counters
        self.pinch_count = 0
        self.point_count = 0
        self.tap_count = 0
        self.stretch_count = 0
        self._stretch_last = None
        self.left_last = None
        self.right_last = None

    def update(self, hands, tracker):
        """
        Update histories and detect gestures.
        hands: list from HandTracker.get_landmarks()
        tracker: HandTracker instance (for trail)
        """
        # update per-hand histories
        # use labels as keys
        for h in hands:
            label = h["label"]
            norm = h["normalized"]
            if label not in self._hand_histories:
                self._hand_histories[label] = deque(maxlen=self.history_length)
            # use index fingertip (8)
            if norm.shape[0] >= 9:
                nx, ny = float(norm[8][0]), float(norm[8][1])
                self._hand_histories[label].append((nx, ny))
                # store last point pos in pixel coords for actions
                self.last_point_pos = tuple(map(int, h["landmarks"][8]))
        # detect pinch for any hand
        pinch_threshold = self.cfg.get("pinch_threshold", 0.05)
        pinch_confirm = self.cfg.get("pinch_confirm_frames", 6)
        pinch_detected = False
        for h in hands:
            norm = h["normalized"]
            if norm.shape[0] >= 9:
                # thumb tip 4 and index tip 8
                t = norm[4]
                idx = norm[8]
                dist = math.hypot(t[0]-idx[0], t[1]-idx[1])
                if dist < pinch_threshold:
                    self.pinch_count += 1
                else:
                    self.pinch_count = max(0, self.pinch_count-1)
                if self.pinch_count >= pinch_confirm:
                    pinch_detected = True
                    self.last_pinch_pos = tuple(map(int, h["landmarks"][8]))
        if pinch_detected:
            self.enqueue_event("pinch")
            self.current_state = "pinch"
            return

        # detect point (index extended, others folded)
        point_confirm = self.cfg.get("point_confirm_frames", 4)
        point_detected = False
        for h in hands:
            lm = h.get("landmarks")
            norm = h.get("normalized")
            if norm is None:
                continue
            # prefer normalized distances (0..1). Use pixel landmarks if normalized seems missing.
            try:
                # normalized distance thresholds (for normalized coords 0..1)
                def ndist(a,b): return math.hypot(norm[a][0]-norm[b][0], norm[a][1]-norm[b][1])
                idx_ext_n = ndist(8,6)
                others_pairs = [(12,10),(16,14),(20,18)]
                # be permissive for normalized inputs from tests and cameras
                folded_n = all(ndist(a,b) < 0.06 for a,b in others_pairs)
                if idx_ext_n > 0.015 and folded_n:
                    self.point_count += 1
                else:
                    self.point_count = max(0, self.point_count-1)
                if self.point_count >= point_confirm:
                    point_detected = True
                    # set last_point_pos from pixel coords if available, else approximate
                    if lm is not None and lm.shape[0] >= 9:
                        self.last_point_pos = tuple(map(int, lm[8]))
                    else:
                        # approximate using normalized to pixel later by caller
                        self.last_point_pos = (int(norm[8][0]*self.cfg.get('canvas_width',1280)), int(norm[8][1]*self.cfg.get('canvas_height',720)))
            except Exception:
                # fallback to pixel-based check
                if lm is None or lm.shape[0] < 9:
                    continue
                def pdist(i,j): return np.linalg.norm(lm[i]-lm[j])
                idx_ext = pdist(8,6)
                others = [(12,10),(16,14),(20,18)]
                folded = all(pdist(a,b) < 20 for a,b in others)
                if idx_ext > 30 and folded:
                    self.point_count += 1
                else:
                    self.point_count = max(0, self.point_count-1)
                if self.point_count >= point_confirm:
                    point_detected = True
                    self.last_point_pos = tuple(map(int, lm[8]))
        if point_detected:
            self.enqueue_event("point")
            self.current_state = "point"
            return

        # detect tap (fast forward poke by index) - approximate with velocity change
        tap_confirm = self.cfg.get("tap_confirm_frames", 3)
        for label, hist in self._hand_histories.items():
            if len(hist) >= 3:
                # approximate speed by difference in normalized positions
                (x0,y0) = hist[-3]
                (x1,y1) = hist[-2]
                (x2,y2) = hist[-1]
                v1 = math.hypot(x1-x0, y1-y0)
                v2 = math.hypot(x2-x1, y2-y1)
                if v2 > self.cfg.get("tap_speed_threshold", 0.035) and v2 > v1*2:
                    self.tap_count += 1
                else:
                    self.tap_count = max(0, self.tap_count-1)
                if self.tap_count >= tap_confirm:
                    self.enqueue_event("tap")
                    self.current_state = "tap"
                    return

        # detect circle gesture using tracker trail (pixel positions)
        circ = self._detect_circle(list(tracker.trail))
        if circ:
            path_points, center, radius = circ
            self.circle_buffer.append((path_points, center, radius))
            if len(self.circle_buffer) >= self.cfg.get("circle_confirm_frames",6):
                # confirm and emit circle
                self.event_queue.append(("circle", (path_points, center, radius)))
                self.current_state = "circle"
                self.circle_buffer.clear()
                return

        # detect polygon / rectangle gesture using tracker trail
        shape = self._detect_shape(list(tracker.trail))
        if shape is not None:
            self.shape_buffer.append(shape)
            if len(self.shape_buffer) >= 2:
                # confirm and emit rectangle/shape
                self.event_queue.append(("shape_rect", shape))
                self.current_state = "shape_rect"
                self.shape_buffer.clear()
                return

        # detect two-hand stretch
        if len(hands) >= 2:
            # find left and right
            left = next((h for h in hands if h["label"]=="Left"), None)
            right = next((h for h in hands if h["label"]=="Right"), None)
            if left is not None and right is not None:
                lc = np.mean(left["normalized"], axis=0)
                rc = np.mean(right["normalized"], axis=0)
                d = math.hypot(lc[0]-rc[0], lc[1]-rc[1])
                if self._stretch_last is None:
                    self._stretch_last = d
                    self.stretch_count = 0
                else:
                    if d - self._stretch_last > self.cfg.get("stretch_distance_threshold", 0.12):
                        self.stretch_count += 1
                    else:
                        self.stretch_count = max(0, self.stretch_count-1)
                    self._stretch_last = d
                if self.stretch_count >= self.cfg.get("stretch_confirm_frames",8):
                    self.enqueue_event("stretch")
                    self.current_state = "stretch"
                    return
        # default
        self.current_state = "idle"

    def enqueue_event(self, name, payload=None):
        self.event_queue.append((name, payload))

    def consume_event(self, name):
        for i,(n,p) in enumerate(self.event_queue):
            if n == name:
                self.event_queue.pop(i)
                return True
        return False

    def consume_circle(self):
        for i,(n,p) in enumerate(self.event_queue):
            if n == "circle":
                self.event_queue.pop(i)
                return p
        return None

    def consume_shape(self):
        for i,(n,p) in enumerate(self.event_queue):
            if n == "shape_rect":
                self.event_queue.pop(i)
                return p
        return None

    def get_current_shape(self):
        """Return most recent in-progress polygon/shape for visualization."""
        if len(self.shape_buffer) > 0:
            return self.shape_buffer[-1]
        return None

    def _detect_shape(self, trail_points):
        """
        Detect a polygon-like shape from trail (pixel coordinates). Returns list of corner points if rectangle-like.
        """
        if len(trail_points) < 8:
            return None
        pts = np.array(trail_points, dtype=np.int32)
        # compute convex hull
        try:
            hull = cv2.convexHull(pts)
            if hull is None or len(hull) < 4:
                return None
            hull = hull.reshape(-1,2)
            # approximate polygon
            peri = cv2.arcLength(hull.astype(np.float32), True)
            approx = cv2.approxPolyDP(hull.astype(np.float32), epsilon=0.02*peri, closed=True)
            if approx is None:
                return None
            approx = approx.reshape(-1,2)
            # if approx has 4 vertices -> possible rectangle
            if len(approx) == 4:
                # check area
                area = abs(cv2.contourArea(approx))
                if area < 2000:
                    return None
                # check angles close to 90 deg
                def angle(a,b,c):
                    ab = a-b
                    cb = c-b
                    cosang = np.dot(ab,cb) / (np.linalg.norm(ab)*np.linalg.norm(cb)+1e-6)
                    return math.degrees(math.acos(max(-1.0,min(1.0,cosang))))
                angs = []
                for i in range(4):
                    a = approx[(i-1)%4]
                    b = approx[i]
                    c = approx[(i+1)%4]
                    angs.append(angle(a,b,c))
                if all(60 <= ag <= 120 for ag in angs):
                    return [tuple(pt) for pt in approx]
        except Exception:
            return None
        return None

    def get_current_circle(self):
        """Return the latest in-progress circle (path_points, center, radius) if available for visualization."""
        if len(self.circle_buffer) > 0:
            return self.circle_buffer[-1]
        return None

    def _detect_circle(self, trail_points):
        """
        Analyze last M pixel points to detect approximate circular drawing.
        Returns (path_points, center, radius) or None
        """
        # be slightly forgiving: allow detection with a few fewer points than configured
        min_pts = self.cfg.get("circle_min_points", 20)
        threshold = max(8, min_pts - 2)
        if len(trail_points) < threshold:
            return None
        take = min(len(trail_points), self.cfg.get("circle_min_points",20))
        pts = np.array(trail_points[-take:], dtype=np.float32)
        # center via mean
        cx, cy = pts.mean(axis=0)
        # compute radii
        rs = np.linalg.norm(pts - np.array([cx,cy]), axis=1)
        r_mean = float(rs.mean())
        r_std = float(rs.std())
        circularity = 1.0 - (r_std / (r_mean+1e-6))
        # compute angular sweep
        angles = np.arctan2(pts[:,1]-cy, pts[:,0]-cx)
        ang_diffs = np.abs(np.unwrap(angles))
        sweep = (angles.max() - angles.min()) * 180.0 / math.pi
        if sweep < self.cfg.get("circle_min_sweep_degrees", 250):
            return None
        if circularity < 0.55:
            return None
        return (pts.tolist(), (int(cx),int(cy)), int(r_mean))
