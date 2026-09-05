import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
import gen_schematic as g
import route as rt

PROJ = "/home/dev/kicad-ws/CANMD-60"
PCB_PATH = f"{PROJ}/CANMD-60.kicad_pcb"
LOCAL_PRETTY = f"{PROJ}/CANMD-60.pretty"

MM = pcbnew.FromMM

FP_LIB_MAP = {
    'AMASS_XT60PW-M': LOCAL_PRETTY,
    'PG-TO220-3_INF': LOCAL_PRETTY,
}

def std_fp_lib(footprint_field):
    # "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm" -> ("/usr/share/kicad/footprints/Package_SO.pretty", "SOIC-8_3.9x4.9mm_P1.27mm")
    libname, fpname = footprint_field.split(":", 1)
    return f"/usr/share/kicad/footprints/{libname}.pretty", fpname

# ---------------------------------------------------------------------------
# Physical placement (mm), rotation in degrees (pcbnew wants tenths-of-degree via EDA_ANGLE)
PLACEMENT = {
    # Power input
    'J1':  (18, 20, 90),
    'F1':  (46, 15, 0),
    'D1':  (72, 15, 0),
    'C1':  (88, 15, 0),
    'C2':  (98, 15, 0),
    'C3':  (108, 12, 90),
    'C4':  (108, 20, 90),
    'PWR1':(18, 40, 0),   # not a real footprint (power flag) - skip in PCB
    'PWR2':(18, 40, 0),
    'PWR3':(18, 40, 0),
    'GND1':(18, 40, 0),

    # Gate driver + FET cluster (passives spread well clear of the QFN's
    # 0.5mm pin pitch so single-layer fan-out traces don't graze neighbours)
    'U1':  (75, 45, 0),
    'C5':  (58, 28, 90),
    'C6':  (92, 28, 90),
    'C7':  (58, 62, 90),
    'C8':  (92, 62, 90),
    'C9':  (58, 45, 90),
    'C10': (92, 45, 90),
    'R1':  (75, 24, 90),
    'R4':  (85, 66, 90),
    'R5':  (95, 66, 90),
    'R2':  (75, 66, 90),
    'R3':  (65, 66, 90),
    'R6':  (65, 24, 90),

    'Q1':  (108, 40, 0),
    'Q2':  (108, 52, 0),
    'Q3':  (128, 40, 0),
    'Q4':  (128, 52, 0),
    'R7':  (132, 60, 0),

    'J2':  (162, 46, 270),
    'R8':  (146, 60, 90),
    'C11': (151, 60, 90),

    # 5V buck
    'U2':  (20, 80, 0),
    'C12': (10, 75, 90),
    'C13': (10, 85, 90),
    'C14': (28, 75, 90),
    'C15': (20, 92, 90),
    'L1':  (35, 80, 0),
    'C16': (45, 75, 90),
    'C17': (50, 75, 90),
    'R9':  (35, 92, 90),
    'R10': (35, 98, 90),

    # 3.3V LDO
    'U3':  (65, 80, 0),
    'C18': (58, 88, 90),
    'C19': (72, 88, 90),

    # CAN
    'U4':  (95, 80, 0),
    'R11': (95, 92, 90),
    'R12': (105, 72, 90),
    'J3':  (165, 75, 270),
    'J4':  (165, 92, 270),

    # MCU
    'U5':  (70, 112, 0),
    'C20': (52, 105, 90),
    'C21': (52, 109, 90),
    'C22': (52, 113, 90),
    'C23': (52, 117, 90),
    'C24': (60, 100, 90),
    'R13': (56, 100, 90),
    'R14': (60, 122, 90),
    'J5':  (115, 110, 0),

    # status LEDs
    'LED1':(128, 108, 0),
    'R15': (128, 100, 90),
    'LED2':(136, 108, 0),
    'R16': (136, 100, 90),
    'LED3':(144, 108, 0),
    'R17': (144, 100, 90),
}

SKIP_REFS = {'PWR1', 'PWR2', 'PWR3', 'GND1'}  # power-flag/GND symbols: schematic-only, no footprint

def load_fp(footprint_field):
    if footprint_field in FP_LIB_MAP:
        libpath = FP_LIB_MAP[footprint_field]
        fpname = footprint_field
    else:
        libpath, fpname = std_fp_lib(footprint_field)
    fp = pcbnew.FootprintLoad(libpath, fpname)
    if fp is None:
        raise RuntimeError(f"footprint load failed: {libpath} :: {fpname}")
    return fp

# Extra pad-net ties not expressed as a schematic pin (thermal/exposed pads).
EXTRA_PAD_NETS = {
    'U1': {'25': 'GND'},   # DRV8701 VQFN exposed pad (PPAD) -> GND
}

BOARD_W, BOARD_H = 180.0, 130.0
BOARD_MARGIN = 4.0

def add_board_outline(board):
    seg_pts = [
        (BOARD_MARGIN, BOARD_MARGIN), (BOARD_W - BOARD_MARGIN, BOARD_MARGIN),
        (BOARD_W - BOARD_MARGIN, BOARD_H - BOARD_MARGIN), (BOARD_MARGIN, BOARD_H - BOARD_MARGIN),
        (BOARD_MARGIN, BOARD_MARGIN),
    ]
    for i in range(len(seg_pts) - 1):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(MM(seg_pts[i][0]), MM(seg_pts[i][1])))
        seg.SetEnd(pcbnew.VECTOR2I(MM(seg_pts[i+1][0]), MM(seg_pts[i+1][1])))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(MM(0.15))
        board.Add(seg)

def main():
    board = pcbnew.CreateEmptyBoard()
    board.SetFileName(PCB_PATH)

    # 2-layer, 1.6mm board, 2oz (70um) copper for the high-current layers.
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)
    # NOTE: 2oz (70um) outer copper is specified as a JLCPCB order option at
    # fabrication time (see hand-off notes), not encoded in the layer stack here.

    add_board_outline(board)

    # ---- nets ----
    netinfo = board.GetNetInfo()
    nets = {}
    def get_net(name):
        if name not in nets:
            n = pcbnew.NETINFO_ITEM(board, name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    footprints = {}
    for ref, p in g.PARTS.items():
        if ref in SKIP_REFS:
            continue
        x, y, rot = PLACEMENT[ref]
        fp = load_fp(p['footprint'])
        fp.SetReference(ref)
        fp.SetValue(p['value'])
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        footprints[ref] = fp
        if ref in ('Q1', 'Q2', 'Q3', 'Q4'):
            # move the silkscreen reference clear of the TO-220 pads (cosmetic only)
            fp.Reference().SetPosition(pcbnew.VECTOR2I(MM(x), MM(y - 4.5)))

        pad_nets = dict(p['nets'])
        pad_nets.update(EXTRA_PAD_NETS.get(ref, {}))
        for pad in fp.Pads():
            padnum = pad.GetNumber()
            if padnum in pad_nets:
                pad.SetNet(get_net(pad_nets[padnum]))

    # ---- copper zones: GND plane on both layers, VM pour over the power section ----
    def add_zone(net_name, layer, rect, priority=0):
        x0, y0, x1, y1 = rect
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNetCode(get_net(net_name).GetNetCode())
        zone.SetAssignedPriority(priority)
        zone.SetLocalClearance(MM(0.3))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        outline = zone.Outline()
        outline.NewOutline()
        for (x, y) in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
            outline.Append(MM(x), MM(y))
        board.Add(zone)
        return zone

    whole = (BOARD_MARGIN, BOARD_MARGIN, BOARD_W - BOARD_MARGIN, BOARD_H - BOARD_MARGIN)
    power_area = (8, 5, 140, 96)
    zones = []
    zones.append(add_zone('GND', pcbnew.F_Cu, whole, priority=0))
    zones.append(add_zone('GND', pcbnew.B_Cu, whole, priority=0))
    zones.append(add_zone('VM', pcbnew.F_Cu, power_area, priority=1))

    # ---- escape stubs for tightly-pitched parts ----
    # A track landing straight on a pin that sits close to its neighbours
    # (0.5mm QFN/LQFP pitch, or a 2.54mm TO-220 leg row carrying a 2.5-3mm
    # power trace) immediately grazes the pin(s) next to it. So every such
    # pin first gets a short thin 0.2mm stub straight out, clear of the
    # package, and the *rest* of that net's run (at whatever width it needs)
    # starts from the stub tip instead of the raw pad.
    def four_side_outward(padnum, per_side):
        n = int(padnum)
        side = (n - 1) // per_side
        return [(-1, 0), (0, 1), (1, 0), (0, -1)][side % 4]

    def add_stubs(ref, outward_fn, stub_len_mm, pins=None):
        fp = footprints[ref]
        pin_net = g.PARTS[ref]['nets']
        stub_end = {}
        for pad in fp.Pads():
            padnum = pad.GetNumber()
            if padnum not in pin_net:
                continue
            if pins is not None and padnum not in pins:
                continue
            pos = pad.GetPosition()
            dx, dy = outward_fn(padnum)
            L = MM(stub_len_mm)
            tip = (pos.x + dx * L, pos.y + dy * L)
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pos.x, pos.y))
            t.SetEnd(pcbnew.VECTOR2I(int(tip[0]), int(tip[1])))
            t.SetLayer(pcbnew.F_Cu)
            t.SetWidth(MM(0.2))
            t.SetNet(get_net(pin_net[padnum]))
            board.Add(t)
            stub_end[pin_net[padnum]] = tip
        return stub_end

    stub_ends = {}  # net name -> list of stub-tip points that replace a raw pad
    for netname, tip in add_stubs('U1', lambda p: four_side_outward(p, 6), 1.6).items():
        stub_ends.setdefault(netname, []).append(tip)
    for netname, tip in add_stubs('U5', lambda p: four_side_outward(p, 12), 1.6).items():
        stub_ends.setdefault(netname, []).append(tip)
    # TO-220 legs (Q1-Q4) sit in a single row 2.54mm apart; stub straight up
    # (away from the row) before the wide PHASE/SP_N trace is allowed to widen.
    for ref in ('Q1', 'Q2', 'Q3', 'Q4'):
        for netname, tip in add_stubs(ref, lambda p: (0, -1), 2.0).items():
            stub_ends.setdefault(netname, []).append(tip)

    stubbed_refs = {'U1', 'U5', 'Q1', 'Q2', 'Q3', 'Q4'}

    # ---- routing ----
    # net -> list of (x_nm, y_nm) pad positions, gathered from the *placed* footprints
    net_pads = {}
    for ref, fp in footprints.items():
        if ref in stubbed_refs:
            continue  # represented by stub tips instead, added below
        for pad in fp.Pads():
            net = pad.GetNet()
            if net.GetNetCode() == 0:
                continue
            pos = pad.GetPosition()
            net_pads.setdefault(net.GetNetname(), []).append((pos.x, pos.y))
    for netname, tips in stub_ends.items():
        net_pads.setdefault(netname, []).extend(tips)

    router = rt.Router(board)
    router.collect_pads(footprints.values())
    for t in board.Tracks():
        if t.GetLayer() == pcbnew.F_Cu and t.GetNet().GetNetCode() != 0:
            router.f_segs.append((
                (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y),
                pcbnew.ToMM(t.GetWidth()), t.GetNet().GetNetname(),
            ))
    WIDE_NETS = {'PHASE_A': 3.0, 'PHASE_B': 3.0, 'SP_N': 2.5, 'GND': 0.8, 'VM': 0.8}
    # GND/VM are also poured as copper zones above; routing them explicitly
    # too is a deliberate belt-and-suspenders backup, since zone fill can
    # occasionally miss a pad tucked right next to a fine-pitch escape stub.
    for netname, pads in net_pads.items():
        if len(pads) < 2:
            continue
        width = WIDE_NETS.get(netname, 0.25)
        # Vias are now pad-aware (route.Router._via_ok checks clearance to every
        # pad/hole before placing one), so B.Cu is available as a real escape
        # route instead of being blanket-disabled near dense fine-pitch parts.
        router.route_net(pads, get_net(netname), width_mm=width, allow_vias=True)

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())

    board.Save(PCB_PATH)
    print("wrote", PCB_PATH, "with", len(footprints), "footprints and", len(nets), "nets")

if __name__ == "__main__":
    main()
