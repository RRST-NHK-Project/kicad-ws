"""Simple greedy router: MST per net, straight segments on F.Cu, fall back to
B.Cu + vias when a new segment would cross an already-routed one on F.Cu."""
import math
import pcbnew

MM = pcbnew.FromMM

def _clamp01(t):
    return 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)

def _closest_pt_on_seg(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    L2 = dx*dx + dy*dy
    if L2 == 0:
        return a
    t = _clamp01(((px - ax)*dx + (py - ay)*dy) / L2)
    return (ax + t*dx, ay + t*dy)

def seg_seg_distance(p1, p2, p3, p4):
    """Minimum distance between segments p1-p2 and p3-p4 (proper intersection -> 0)."""
    def ccw(a, b, c):
        return (c[1]-a[1])*(b[0]-a[0]) - (b[1]-a[1])*(c[0]-a[0])
    d1, d2 = ccw(p3, p4, p1), ccw(p3, p4, p2)
    d3, d4 = ccw(p1, p2, p3), ccw(p1, p2, p4)
    if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
       ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
        return 0.0
    candidates = [
        dist(p1, _closest_pt_on_seg(p1, p3, p4)),
        dist(p2, _closest_pt_on_seg(p2, p3, p4)),
        dist(p3, _closest_pt_on_seg(p3, p1, p2)),
        dist(p4, _closest_pt_on_seg(p4, p1, p2)),
    ]
    return min(candidates)

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def mst_edges(points):
    """points: list of (x,y). Returns list of (i,j) index pairs forming an MST."""
    n = len(points)
    if n <= 1:
        return []
    in_tree = [False]*n
    in_tree[0] = True
    edges = []
    best = [(dist(points[0], points[i]), 0) for i in range(n)]
    for _ in range(n-1):
        cand = min((best[i][0], i) for i in range(n) if not in_tree[i])
        _, j = cand
        edges.append((best[j][1], j))
        in_tree[j] = True
        for i in range(n):
            if not in_tree[i]:
                d = dist(points[j], points[i])
                if d < best[i][0]:
                    best[i] = (d, j)
    return edges

MM_F = 1000000.0  # pcbnew internal units per mm (nanometres)
CLEARANCE_MM = 0.22  # safety margin added on top of the two trace half-widths

class Router:
    def __init__(self, board):
        self.board = board
        # each entry: (p1, p2, width_mm, netname)
        self.f_segs = []
        self.b_segs = []
        self.unrouted = []  # (p1, p2, netname) hops left as ratsnest
        # every pad on the board: (x, y, radius_nm, netname, layer_set) - used
        # so a track routed *near* (not just through) a foreign pad is caught.
        self.pads = []

    def collect_pads(self, footprints):
        for fp in footprints:
            for pad in fp.Pads():
                pos = pad.GetPosition()
                sz = pad.GetSize()
                radius = max(sz.x, sz.y) / 2.0
                net = pad.GetNet()
                on_front = pad.IsOnLayer(pcbnew.F_Cu)
                on_back = pad.IsOnLayer(pcbnew.B_Cu)
                self.pads.append((pos.x, pos.y, radius, net.GetNetname(), on_front, on_back))

    def seed_existing(self, layer_segs, width_mm, netname):
        """Register pre-existing tracks (e.g. escape stubs) so later routing
        keeps clear of them too."""
        for p1, p2 in layer_segs:
            self.f_segs.append((p1, p2, width_mm, netname))

    def _blocked(self, segs, p1, p2, width_mm, netname, front):
        min_gap_nm = (width_mm/2 + CLEARANCE_MM) * MM_F
        for q1, q2, qwidth, qnet in segs:
            if qnet == netname:
                continue  # same net: touching/overlap is fine
            need = min_gap_nm + (qwidth/2) * MM_F
            if seg_seg_distance(p1, p2, q1, q2) < need:
                return True
        for px, py, pradius, pnet, on_front, on_back in self.pads:
            if pnet == netname:
                continue
            if front and not on_front:
                continue
            if not front and not on_back:
                continue
            need = min_gap_nm + pradius
            if dist(_closest_pt_on_seg((px, py), p1, p2), (px, py)) < need:
                return True
        return False

    def _add_track(self, p1, p2, layer, width_mm, net):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(int(p1[0]), int(p1[1])))
        t.SetEnd(pcbnew.VECTOR2I(int(p2[0]), int(p2[1])))
        t.SetLayer(layer)
        t.SetWidth(MM(width_mm))
        t.SetNet(net)
        self.board.Add(t)

    def _via_ok(self, p, netname, dia_mm=0.7):
        need_base = (dia_mm/2 + CLEARANCE_MM) * MM_F
        for px, py, pradius, pnet, on_front, on_back in self.pads:
            if pnet == netname:
                continue
            if dist(p, (px, py)) < need_base + pradius:
                return False
        for q1, q2, qwidth, qnet in self.f_segs + self.b_segs:
            if qnet == netname:
                continue
            if dist(_closest_pt_on_seg(p, q1, q2), p) < need_base + (qwidth/2)*MM_F:
                return False
        return True

    def _add_via(self, p, net, drill_mm=0.35, dia_mm=0.7):
        v = pcbnew.PCB_VIA(self.board)
        v.SetPosition(pcbnew.VECTOR2I(int(p[0]), int(p[1])))
        v.SetDrill(MM(drill_mm))
        v.SetWidth(MM(dia_mm))
        v.SetNet(net)
        self.board.Add(v)

    def route_pair(self, p1, p2, net, width_mm=0.3, allow_vias=True):
        p1 = (float(p1[0]), float(p1[1]))
        p2 = (float(p2[0]), float(p2[1]))
        netname = net.GetNetname()
        can_via = allow_vias and self._via_ok(p1, netname) and self._via_ok(p2, netname)
        if not self._blocked(self.f_segs, p1, p2, width_mm, netname, True):
            self._add_track(p1, p2, pcbnew.F_Cu, width_mm, net)
            self.f_segs.append((p1, p2, width_mm, netname))
        elif can_via and not self._blocked(self.b_segs, p1, p2, width_mm, netname, False):
            self._add_via(p1, net)
            self._add_via(p2, net)
            self._add_track(p1, p2, pcbnew.B_Cu, width_mm, net)
            self.b_segs.append((p1, p2, width_mm, netname))
        else:
            # Nowhere clean to put it (F.Cu blocked, B.Cu blocked or no via
            # room): leave this specific hop unrouted rather than force a
            # track that DRC would flag as an actual short/bridge. It shows
            # up as an honest ratsnest line for a manual routing pass instead
            # of a silent short.
            self.unrouted.append((p1, p2, netname))

    def route_net(self, pad_positions, net, width_mm=0.3, allow_vias=True):
        """pad_positions: list of (x_nm, y_nm). Connects them via an MST."""
        if len(pad_positions) < 2:
            return
        for i, j in mst_edges(pad_positions):
            self.route_pair(pad_positions[i], pad_positions[j], net, width_mm, allow_vias)
