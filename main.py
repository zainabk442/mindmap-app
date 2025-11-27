#!/usr/bin/env python3
"""
TUBA KHAN — AIR MINDMAP
Main application entry point.
"""
import argparse
import os
import time
import threading
import math
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import yaml

from hand.hand_tracker import HandTracker
from hand.gestures import GestureManager
from mindmap.core import MindMap
from ui.canvas import Canvas
from ui.overlay import Overlay
from mindmap.storage import Storage

CONFIG_PATH = "config.yaml"
APP_TITLE = "TUBA KHAN AIR MINDMAP"

def ensure_output_dir(cfg):
    out = cfg.get("output_dir", "output")
    os.makedirs(out, exist_ok=True)
    return out

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--demo-mode", action="store_true", help="Run scripted demo gestures")
    return p.parse_args()

def main():
    args = parse_args()
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)

    out_dir = ensure_output_dir(cfg)

    cap_device = cfg.get("camera_index", 0)
    width = cfg.get("canvas_width", 1280)
    height = cfg.get("canvas_height", 720)

    tracker = HandTracker(cam_index=cap_device, width=width, height=height, config=cfg)
    gestures = GestureManager(cfg=cfg)
    mindmap = MindMap(cfg=cfg)
    canvas = Canvas(width=width, height=height, cfg=cfg)
    overlay = Overlay(width=width, height=height, cfg=cfg, title=APP_TITLE)
    storage = Storage(out_dir=out_dir)

    executor = ThreadPoolExecutor(max_workers=2)
    cap = tracker.start()

    demo_mode = args.demo_mode
    demo_start_time = time.time()

    last_save_ts = 0
    last_action_ts = 0

    autosave_interval = cfg.get('autosave_interval', 30)
    autosave_fn = cfg.get('autosave_filename', 'mindmap_autosave.json')
    last_autosave = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            hands = tracker.get_landmarks(frame)

            # update gesture manager with latest tracked data
            gestures.update(hands, tracker)

            # Check gestures and map to actions
            g_state = gestures.current_state

            # Finger point -> create node
            if gestures.consume_event("point"):
                pos = gestures.last_point_pos
                if pos is not None:
                    node = mindmap.create_node(pos)
                    try:
                        node.start_spawn_animation()
                    except Exception:
                        pass
                    last_action_ts = time.time()

            # Tap -> select node
            if gestures.consume_event("tap"):
                pos = gestures.last_point_pos
                if pos is not None:
                    nid = mindmap.find_nearest_node_id(pos, radius=cfg.get("node_radius",36)*2)
                    mindmap.selected_node_id = nid

            # Pinch -> toggle collapse
            if gestures.consume_event("pinch"):
                pos = gestures.last_pinch_pos
                if pos is not None:
                    nid = mindmap.find_nearest_node_id(pos, radius=cfg.get("node_radius",36)*2)
                    if nid is not None:
                        mindmap.toggle_collapse(nid)
                        mindmap.pulse_node(nid)
                        last_action_ts = time.time()

            # Circle -> connect
            circ = gestures.consume_circle()
            if circ:
                path_points, center, radius = circ
                # find nodes inside circle
                inside = mindmap.nodes_inside_circle(center, radius)
                if inside:
                    # connect most recently pointed node to nearest marked node(s)
                    if mindmap.last_created_node_id:
                        a = mindmap.last_created_node_id
                        for nid in inside:
                            if nid != a:
                                mindmap.connect_nodes(a, nid)
                                mindmap.pulse_node(nid)
                else:
                    # if no nodes inside, create a node at the circle center
                    cx, cy = int(center[0]), int(center[1])
                    nid = mindmap.create_node((cx, cy), title="Idea")
                    mindmap.pulse_node(nid)
                last_action_ts = time.time()

            # Shape / Rectangle gesture -> create nodes at corners and connect them
            shape = gestures.consume_shape()
            if shape:
                corners = shape
                created_ids = []
                for (x,y) in corners:
                    nid = mindmap.create_node((int(x), int(y)), title="Corner")
                    created_ids.append(nid)
                # connect in polygon cycle
                for i in range(len(created_ids)):
                    a = created_ids[i]
                    b = created_ids[(i+1)%len(created_ids)]
                    mindmap.connect_nodes(a,b)
                # create a center root and connect to corners
                cx = int(sum(p[0] for p in corners)/len(corners))
                cy = int(sum(p[1] for p in corners)/len(corners))
                root = mindmap.create_node((cx, cy), title="Cluster")
                for nid in created_ids:
                    mindmap.connect_nodes(root, nid)
                mindmap.pulse_node(root)
                last_action_ts = time.time()

            # Stretch -> expand subtree
            if gestures.consume_event("stretch"):
                nid = mindmap.selected_node_id or None
                if nid is None and mindmap.nodes:
                    # pick root candidate
                    nid = list(mindmap.nodes.keys())[0]
                if nid is not None:
                    mindmap.expand_node(nid)
                    last_action_ts = time.time()

            # Update animations & draw
            canvas_img = np.zeros((height, width, 3), dtype=np.uint8)
            canvas.draw_mindmap(canvas_img, mindmap, selected_id=mindmap.selected_node_id)
            # draw current circle gesture overlay if present
            current_circle = gestures.get_current_circle() if hasattr(gestures, 'get_current_circle') else None
            if current_circle:
                path_points, center, radius = current_circle
                # draw translucent filled circle and path on a separate overlay layer
                overlay_layer = canvas_img.copy()
                cx,cy = center
                cv2.circle(overlay_layer, (cx,cy), int(radius), (60,200,120), -1)
                cv2.addWeighted(overlay_layer, 0.08, canvas_img, 0.92, 0, canvas_img)
                # draw path
                try:
                    pts = np.array(path_points, dtype=np.int32)
                    if pts.shape[0] > 1:
                        cv2.polylines(canvas_img, [pts], isClosed=True, color=(0,255,200), thickness=2)
                except Exception:
                    pass
            # draw current shape/rectangle preview if present
            curr_shape = gestures.get_current_shape() if hasattr(gestures, 'get_current_shape') else None
            if curr_shape:
                try:
                    canvas.draw_shape_preview(canvas_img, curr_shape)
                except Exception:
                    pass
            overlay.draw_panel(canvas_img, gesture_text=gestures.current_state, selected=mindmap.get_selected_summary(), tracker=tracker, frame=frame)
            # draw trails and fingertip indicator
            canvas.draw_trails(canvas_img, tracker.trail_positions)
            canvas.draw_fingertip_indicator(canvas_img, gestures.last_point_pos)

            # draw webcam small inset
            overlay.draw_webcam_inset(canvas_img, frame)

            # If pinch occurred, check if it was over a UI button and handle Save/Load via pinch
            if gestures.consume_event("pinch"):
                p = gestures.last_pinch_pos
                if p is not None:
                    btn = overlay.button_at_pos(p)
                    if btn == 'save':
                        # async save
                        executor.submit(storage.save_mindmap, mindmap, f"mindmap_manual_{int(time.time())}.json")
                    elif btn == 'load':
                        # load autosave if present
                        autosave_path = os.path.join(out_dir, autosave_fn)
                        if os.path.exists(autosave_path):
                            mindmap.load(autosave_path)
                    else:
                        # pinch outside UI -> toggle nearest node collapse
                        nid = mindmap.find_nearest_node_id(p, radius=cfg.get("node_radius",36)*2)
                        if nid is not None:
                            mindmap.toggle_collapse(nid)
                            mindmap.pulse_node(nid)
                            last_action_ts = time.time()

            # Autosave periodically
            if time.time() - last_autosave > autosave_interval:
                executor.submit(storage.save_latest, mindmap, autosave_fn)
                last_autosave = time.time()

            cv2.imshow(APP_TITLE, canvas_img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            # demo mode automated sequence (kept for --demo-mode only)
            if demo_mode:
                # intentionally use gestures.enqueue_event to simulate real gesture flow
                t = time.time() - demo_start_time
                if int(t) % 6 == 0:
                    # simulate a point event at center-left
                    px = int(width*0.3)
                    py = int(height*0.4)
                    # directly create node but mark as from demo
                    mindmap.create_node((px,py))

    finally:
        cap.release()
        cv2.destroyAllWindows()
        executor.shutdown(wait=False)
        # save on exit
        ts = int(time.time())
        storage.save_mindmap(mindmap, f"mindmap_exit_{ts}.json")
        print("Exited, mindmap saved.")

if __name__ == "__main__":
    main()
