"""
MindMap core for TUBA KHAN — AIR MINDMAP
"""
import json
import math
import os
import time
from .node import Node

class MindMap:
    def __init__(self, cfg=None):
        self.cfg = cfg or {}
        self.nodes = {}  # id -> Node
        self.edges = []  # list of (a,b)
        self.selected_node_id = None
        self._next_id = 1
        self.last_created_node_id = None

    def _alloc_id(self):
        nid = f"n{self._next_id}"
        self._next_id += 1
        return nid

    def create_node(self, pos, title="New Idea"):
        nid = self._alloc_id()
        node = Node(nid, title, pos)
        node.start_spawn_animation()
        self.nodes[nid] = node
        self.last_created_node_id = nid
        return node

    def connect_nodes(self, a_id, b_id):
        if a_id not in self.nodes or b_id not in self.nodes:
            return False
        pair = (a_id, b_id)
        if pair in self.edges or (b_id,a_id) in self.edges:
            return False
        self.edges.append((a_id,b_id))
        return True

    def collapse_node(self, node_id):
        if node_id in self.nodes:
            self.nodes[node_id].collapsed = True

    def expand_node(self, node_id):
        # spawn three children around node if none exist
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        if node.children:
            # un-collapse children visibility
            for cid in node.children:
                if cid in self.nodes:
                    self.nodes[cid].visible = True
                    self.nodes[cid].collapsed = False
            return
        cx,cy = node.position
        radius = 100
        for i in range(3):
            angle = i * (2*math.pi/3)
            x = int(cx + math.cos(angle)*radius + (i*10))
            y = int(cy + math.sin(angle)*radius + (i*5))
            child_id = self._alloc_id()
            child = Node(child_id, f"Child {child_id}", (x,y))
            child.start_spawn_animation()
            self.nodes[child_id] = child
            node.children.append(child_id)
            self.edges.append((node_id, child_id))

    def toggle_collapse(self, node_id):
        if node_id in self.nodes:
            self.nodes[node_id].toggle_collapse()

    def pulse_node(self, node_id, duration=0.6):
        """Trigger pulse animation for a node."""
        if node_id in self.nodes:
            try:
                self.nodes[node_id].pulse(duration=duration)
            except Exception:
                # fallback: set pulse end timestamp
                self.nodes[node_id]._pulse_end = time.time() + duration

    def find_nearest_node_id(self, pos, radius=50):
        if pos is None:
            return None
        x,y = pos
        best = None
        best_d = radius*radius
        for nid, node in self.nodes.items():
            nx,ny = node.position
            d = (nx-x)*(nx-x)+(ny-y)*(ny-y)
            if d < best_d:
                best = nid
                best_d = d
        return best

    def nodes_inside_circle(self, center, radius):
        cx,cy = center
        out = []
        for nid, node in self.nodes.items():
            x,y = node.position
            if (x-cx)**2 + (y-cy)**2 <= radius*radius:
                out.append(nid)
        return out

    def get_selected_summary(self):
        if not self.selected_node_id:
            return None
        n = self.nodes.get(self.selected_node_id)
        if not n: return None
        return {"id": n.id, "title": n.title}

    def to_dict(self):
        return {
            "nodes": {nid: n.to_dict() for nid,n in self.nodes.items()},
            "edges": list(self.edges)
        }

    def save(self, path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self, path):
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.nodes = {}
        for nid, nd in data.get("nodes", {}).items():
            node = Node(nd["id"], nd.get("title",""), tuple(nd.get("position", (0,0))))
            node.children = nd.get("children", [])
            node.collapsed = nd.get("collapsed", False)
            self.nodes[nid] = node
        self.edges = [tuple(e) for e in data.get("edges", [])]
        return True
