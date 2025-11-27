"""
HandTracker for TUBA KHAN — AIR MINDMAP
Provides MediaPipe Hands capture, smoothing, and history buffers.
"""
import collections
import time
import threading
import cv2
import numpy as np
import mediapipe as mp

from utils.smoothing import EMAFilter

class HandTracker:
    def __init__(self, cam_index=0, width=1280, height=720, config=None):
        self.cam_index = cam_index
        self.width = width
        self.height = height
        self.config = config or {}
        self.history_length = int(self.config.get("history_length", 64))
        # history of index fingertip positions (both hands), store pixel coords
        self.trail_positions = collections.deque(maxlen=self.config.get("trail_length", 40))
        self._mp_hands = mp.solutions.hands
        self._hands = None
        self.cap = None
        # smoothing filters per landmark (21 landmarks per hand), store EMA for x,y
        self.smoothing_alpha = 0.6
        self.filters = {}  # key: hand_idx:landmark_idx -> EMAFilter
        self.lock = threading.Lock()
        self._last_frame_time = time.time()

    def start(self):
        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        # initialize MediaPipe Hands
        self._hands = self._mp_hands.Hands(static_image_mode=False,
                                           max_num_hands=2,
                                           min_detection_confidence=0.5,
                                           min_tracking_confidence=0.5)
        return self.cap

    def _smooth_point(self, hand_idx, lm_idx, x, y):
        key = f"{hand_idx}-{lm_idx}"
        if key not in self.filters:
            self.filters[key] = EMAFilter(alpha=self.smoothing_alpha, initial=(x,y))
        sx, sy = self.filters[key].update((x,y))
        return sx, sy

    def get_landmarks(self, frame):
        """
        Process a frame and return list of hands:
        [{'label':'Left'|'Right','landmarks': np.array((21,2)), 'normalized': np.array((21,2))}]
        Landmarks are pixel coordinates (x,y).
        """
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._hands.process(img_rgb)
        hands_out = []
        with self.lock:
            if not results.multi_hand_landmarks:
                # decay trail slightly
                return hands_out
            for h_idx, (hand_landmarks, handedness) in enumerate(zip(results.multi_hand_landmarks, results.multi_handedness)):
                label = handedness.classification[0].label
                pts = []
                normalized = []
                for i, lm in enumerate(hand_landmarks.landmark):
                    nx, ny = lm.x, lm.y
                    px = int(nx * self.width)
                    py = int(ny * self.height)
                    sx, sy = self._smooth_point(h_idx, i, px, py)
                    pts.append((sx, sy))
                    normalized.append((nx, ny))
                pts_a = np.array(pts, dtype=np.float32)
                normalized_a = np.array(normalized, dtype=np.float32)
                hands_out.append({"label": label, "landmarks": pts_a, "normalized": normalized_a})
                # update trail with index fingertip (landmark 8)
                if pts_a.shape[0] >= 9:
                    ix, iy = pts_a[8]
                    self.trail_positions.append((int(ix), int(iy)))
        return hands_out

    @property
    def trail(self):
        return list(self.trail_positions)
