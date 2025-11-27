"""
Canvas drawing utilities for TUBA KHAN — AIR MINDMAP
Draws nodes, edges, trails, fingertip indicator, and animations.
"""
import cv2
import numpy as np
import math
import time

NODE_COLOR = (40, 40, 220)
NODE_TEXT_COLOR = (255,255,255)
EDGE_COLOR = (80, 200, 255)
GLOW_COLOR = (120,220,255)
SHADOW_COLOR = (20,20,20)
FINGERTIP_COLOR = (0,255,200)

class Canvas:
    def __init__(self, width=1280, height=720, cfg=None):
        self.width = width
        self.height = height
        self.cfg = cfg or {}
        self.node_radius = int(self.cfg.get("node_radius", 36))
        self.trail_max = int(self.cfg.get("trail_length", 40))

    def draw_mindmap(self, img, mindmap, selected_id=None):
        # draw edges first as curved glow lines
        for (a,b) in mindmap.edges:
            if a in mindmap.nodes and b in mindmap.nodes:
                p1 = mindmap.nodes[a].position
                p2 = mindmap.nodes[b].position
                self.draw_glow_curve(img, tuple(p1), tuple(p2), EDGE_COLOR, width=2, glow_strength=3)
        # draw nodes
        for nid, node in mindmap.nodes.items():
            x,y = node.position
            r = self.node_radius
            # shadow
            cv2.circle(img, (int(x+4), int(y+6)), r+6, SHADOW_COLOR, -1)
            # node circle
            color = NODE_COLOR
            cv2.circle(img, (int(x), int(y)), r, color, -1)
            # pulse/animation scale
            scale = node.get_spawn_scale()
            if scale != 1.0:
                # temporary overlay to show growth (draw a ring)
                cv2.circle(img, (int(x),int(y)), int(r*scale), (255,255,255), 2)
            # text
            title = node.title
            (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.putText(img, title, (int(x - tw/2), int(y+th/2)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, NODE_TEXT_COLOR, 1, cv2.LINE_AA)
            # collapse icon
            if node.collapsed:
                cv2.putText(img, "+", (int(x + r - 10), int(y - r + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2, cv2.LINE_AA)
            else:
                cv2.putText(img, "-", (int(x + r - 10), int(y - r + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2, cv2.LINE_AA)
            # pulse animation
            now = time.time()
            if hasattr(node, '_pulse_end') and node._pulse_end > now:
                rem = node._pulse_end - now
                # draw expanding ring
                max_dur = 0.8
                t = max(0.0, min(1.0, rem / max_dur))
                ring_r = int(r + (1.0-t) * 30)
                alpha = 0.4 * (1.0 - t)
                overlay = img.copy()
                cv2.circle(overlay, (int(x),int(y)), ring_r, (255,255,255), 2)
                cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
            # selection highlight
            if selected_id is not None and nid == selected_id:
                # draw glow ring
                overlay = img.copy()
                for i in range(3):
                    col = (50, 220 - i*40, 200)
                    cv2.circle(overlay, (int(x),int(y)), r + 8 + i*6, col, 2)
                cv2.addWeighted(overlay, 0.25, img, 0.75, 0, img)

    def draw_glow_line(self, img, p1, p2, color, width=2, glow_strength=3):
        overlay = img.copy()
        # draw multiple strokes increasing width and decreasing alpha
        for i in range(glow_strength, 0, -1):
            w = width + i*2
            alpha = 0.08 + (0.12 * (i / glow_strength))
            cv2.line(overlay, (int(p1[0]),int(p1[1])), (int(p2[0]),int(p2[1])), color, w, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)

    def draw_glow_curve(self, img, p1, p2, color, width=2, glow_strength=3):
        # draw a quadratic bezier-like curve using midpoint offset
        (x1,y1) = p1
        (x2,y2) = p2
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        # perpendicular offset based on distance
        dx = x2 - x1
        dy = y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            ctrl = (mx, my)
        else:
            # offset magnitude smaller for longer edges
            off = min(120, max(30, dist * 0.18))
            # perpendicular direction
            nx = -dy / (dist + 1e-6)
            ny = dx / (dist + 1e-6)
            ctrl = (int(mx + nx * off), int(my + ny * off))
        # sample points along quadratic curve
        pts = []
        for t in np.linspace(0.0,1.0,30):
            xa = (1-t)*(1-t)*x1 + 2*(1-t)*t*ctrl[0] + t*t*x2
            ya = (1-t)*(1-t)*y1 + 2*(1-t)*t*ctrl[1] + t*t*y2
            pts.append((int(xa), int(ya)))
        overlay = img.copy()
        for i in range(glow_strength, 0, -1):
            w = int(width + i*2)
            alpha = 0.06 + 0.12*(i/glow_strength)
            for j in range(1, len(pts)):
                cv2.line(overlay, pts[j-1], pts[j], color, w, cv2.LINE_AA)
            cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)

    def draw_trails(self, img, trail_positions):
        pts = list(trail_positions)[-self.trail_max:]
        for i, (x,y) in enumerate(pts):
            alpha = (i+1)/len(pts) if len(pts)>0 else 1.0
            r = int(4 * alpha) + 1
            c = (int(FINGERTIP_COLOR[0]*alpha), int(FINGERTIP_COLOR[1]*alpha), int(FINGERTIP_COLOR[2]*alpha))
            cv2.circle(img, (int(x),int(y)), r, c, -1)

    def draw_fingertip_indicator(self, img, pos):
        if pos is None:
            return
        x,y = pos
        cv2.circle(img, (int(x),int(y)), 8, FINGERTIP_COLOR, -1)
        cv2.circle(img, (int(x),int(y)), 14, (FINGERTIP_COLOR[0],FINGERTIP_COLOR[1],FINGERTIP_COLOR[2]), 2)

    def draw_shape_preview(self, img, corners, color=(0,255,150)):
        """Draw a translucent polygon preview given corner points (list of (x,y))."""
        try:
            pts = np.array(corners, dtype=np.int32)
            if pts.shape[0] < 3:
                return
            overlay = img.copy()
            cv2.fillPoly(overlay, [pts], color)
            cv2.addWeighted(overlay, 0.12, img, 0.88, 0, img)
            # outline
            cv2.polylines(img, [pts], isClosed=True, color=color, thickness=2)
        except Exception:
            pass
