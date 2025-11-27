"""
Node definition for TUBA KHAN — AIR MINDMAP
"""
import time
import math

class Node:
    def __init__(self, id_, title, position):
        self.id = id_
        self.title = title
        self.position = (int(position[0]), int(position[1]))
        self.children = []
        self.collapsed = False
        self.visible = True
        self._spawn_frame = 0
        self._spawn_start = time.time()
        self._pulse_end = 0

    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        self._pulse_end = time.time() + 0.6

    def pulse(self, duration=0.6):
        """Trigger a pulse animation for this node."""
        self._pulse_end = time.time() + duration

    def add_child(self, node):
        self.children.append(node.id)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "position": self.position,
            "children": list(self.children),
            "collapsed": bool(self.collapsed)
        }

    def start_spawn_animation(self):
        self._spawn_start = time.time()
        self._spawn_frame = 0

    def get_spawn_scale(self):
        # simple spawn scaling based on elapsed time
        elapsed = time.time() - self._spawn_start
        t = min(1.0, elapsed / 0.6)
        return 0.5 + 0.5 * t
