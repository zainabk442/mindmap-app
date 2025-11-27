"""
Overlay UI for TUBA KHAN — AIR MINDMAP
Draws right-hand translucent panel, webcam inset, labels, and instructions.
"""
import cv2
import numpy as np
import datetime

TITLE = "TUBA KHAN AIR MINDMAP"

class Overlay:
    def __init__(self, width=1280, height=720, cfg=None, title=TITLE):
        self.width = width
        self.height = height
        self.cfg = cfg or {}
        self.panel_w = 360
        self.title = title
        # button rects stored as {name: (x,y,w,h)} in panel coordinates
        self.button_rects = {}

    def draw_panel(self, img, gesture_text="idle", selected=None, tracker=None, frame=None):
        # draw translucent right panel
        overlay = img.copy()
        x0 = self.width - self.panel_w
        cv2.rectangle(overlay, (x0,0), (self.width, self.height), (30,30,30), -1)
        alpha = 0.45
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
        # Title
        cv2.putText(img, self.title, (x0+16, 36), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,240,255), 2, cv2.LINE_AA)
        # Gesture state
        cv2.putText(img, f"Gesture: {gesture_text}", (x0+16, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220,220,220), 1, cv2.LINE_AA)
        # Selected node info
        cv2.putText(img, "Selected:", (x0+16, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1, cv2.LINE_AA)
        if selected:
            cv2.putText(img, f"{selected.get('title','')}", (x0+16, 132), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1, cv2.LINE_AA)
            cv2.putText(img, f"ID: {selected.get('id','')}", (x0+16, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180,180,180), 1, cv2.LINE_AA)
        # Instructions
        y = 190
        lines = [
            "Instructions & Shortcuts:",
            "- Point: Create node",
            "- Circle: Connect nodes",
            "- Pinch: Toggle collapse",
            "- Tap: Select node",
            "",
            "Keyboard:",
            "q: Quit",
            "s: Save mindmap",
            "e: Export snapshot",
        ]
        for i,ln in enumerate(lines):
            cv2.putText(img, ln, (x0+16, y + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.43, (200,200,200), 1, cv2.LINE_AA)

        # Draw persistent Save / Load buttons (respond to pinch)
        btn_w = self.panel_w - 40
        btn_h = 36
        bx = x0 + 20
        by = self.height - 120
        # Save button
        cv2.rectangle(img, (bx, by), (bx+btn_w, by+btn_h), (30,120,30), -1)
        cv2.putText(img, "Save Mindmap", (bx+12, by+24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (220,255,220), 1, cv2.LINE_AA)
        # Load button
        by2 = by + btn_h + 12
        cv2.rectangle(img, (bx, by2), (bx+btn_w, by2+btn_h), (70,70,140), -1)
        cv2.putText(img, "Load Mindmap", (bx+12, by2+24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (230,230,255), 1, cv2.LINE_AA)
        # store rects
        self.button_rects = {
            'save': (bx, by, btn_w, btn_h),
            'load': (bx, by2, btn_w, btn_h)
        }

    def draw_webcam_inset(self, img, frame):
        # Draw a small framed webcam in the top-right corner (inside panel)
        # slightly larger thumbnail for better visibility
        h,w = 200, 280
        # Thumbnail
        thumb = cv2.resize(frame, (w,h))
        x = self.width - self.panel_w + 20
        y = 220
        # rounded rectangle frame approximate
        cv2.rectangle(img, (x-8,y-8), (x+w+8,y+h+8), (0,255,200), 2)
        # paste with alpha-safe copy to avoid size mismatch
        try:
            img[y:y+h, x:x+w] = thumb
        except Exception:
            # if frame smaller than expected, resize safely
            small = cv2.resize(frame, (min(w, frame.shape[1]), min(h, frame.shape[0])))
            img[y:y+small.shape[0], x:x+small.shape[1]] = small
        # label above thumbnail
        cv2.putText(img, "TUBA KHAN", (x+6, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,200), 2, cv2.LINE_AA)

    def button_at_pos(self, pos):
        """Return button name under pixel position `pos` or None."""
        if not pos or not self.button_rects:
            return None
        px,py = pos
        for name,(bx,by,bw,bh) in self.button_rects.items():
            if bx <= px <= bx+bw and by <= py <= by+bh:
                return name
        return None
