"""Hand-authored custom symbols (modern KiCad 10 S-expression), plus their pin tables
in the same (elec_type, x, y, angle, name, number) tuple format symlib.get_pins() returns,
so the schematic generator can treat custom and library symbols identically."""

def _prop(name, value, x, y, hide=True, size=1.27):
    hide_s = " hide" if hide else ""
    return f'''(property "{name}" "{value}"
      (at {x} {y} 0)
      (effects (font (size {size} {size})){hide_s})
    )'''

def _pin(etype, x, y, angle, name, number, length=2.54):
    return f'''(pin {etype} line (at {x} {y} {angle}) (length {length})
      (name "{name}" (effects (font (size 1.016 1.016))))
      (number "{number}" (effects (font (size 1.016 1.016))))
    )'''

# ---------------------------------------------------------------------------
# DRV8701E - TI single H-bridge gate driver, VQFN-24 (RGE), PH/EN interface.
# Layout: 12 pins left (x=-2.54, angle 0 = pointing right into body),
#         12 pins right (x=27.94, angle 180 = pointing left into body).
# Body rectangle: x 0..25.4, y -15.24..+15.24
DRV8701E_LEFT = [
    ("power_in", "VM", "1"),
    ("power_out", "VCP", "2"),
    ("passive", "CPH", "3"),
    ("passive", "CPL", "4"),
    ("power_in", "GND", "5"),
    ("input", "VREF", "6"),
    ("power_out", "AVDD", "7"),
    ("power_out", "DVDD", "8"),
    ("open_collector", "nFAULT", "9"),
    ("open_collector", "SNSOUT", "10"),
    ("output", "SO", "11"),
    ("input", "IDRIVE", "12"),
]
DRV8701E_RIGHT = [
    ("input", "nSLEEP", "13"),
    ("input", "EN", "14"),
    ("input", "PH", "15"),
    ("power_in", "GND", "16"),
    ("output", "GH1", "17"),
    ("passive", "SH1", "18"),
    ("output", "GL1", "19"),
    ("input", "SN", "20"),
    ("input", "SP", "21"),
    ("output", "GL2", "22"),
    ("passive", "SH2", "23"),
    ("output", "GH2", "24"),
]

def _drv8701_pins():
    pins = []
    y0 = 13.97
    for i, (etype, name, num) in enumerate(DRV8701E_LEFT):
        y = y0 - i * 2.54
        pins.append((etype, -2.54, y, 0, name, num))
    for i, (etype, name, num) in enumerate(DRV8701E_RIGHT):
        y = y0 - i * 2.54
        pins.append((etype, 27.94, y, 180, name, num))
    return pins

DRV8701E_PINS = _drv8701_pins()
DRV8701E_FOOTPRINT = "Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.5x2.5mm"

def _drv8701_block():
    pin_lines = []
    for etype, x, y, angle, name, num in DRV8701E_PINS:
        pin_lines.append(_pin(etype, x, y, angle, name, num))
    pins_txt = "\n    ".join(pin_lines)
    return f'''(symbol "DRV8701E"
    (pin_names (offset 1.016))
    (in_bom yes) (on_board yes)
    {_prop("Reference", "U", 0, 17.5, hide=False)}
    {_prop("Value", "DRV8701E", 0, 15, hide=False)}
    {_prop("Footprint", DRV8701E_FOOTPRINT, 0, -17.5)}
    {_prop("Datasheet", "https://www.ti.com/lit/ds/symlink/drv8701.pdf", 0, 0)}
    {_prop("Description", "Single H-Bridge Gate Driver for 4x external N-FET, PH/EN, VQFN-24", 0, 0)}
    (symbol "DRV8701E_0_1"
      (rectangle (start 0 -15.24) (end 25.4 15.24)
        (stroke (width 0.254) (type default)) (fill (type background))
      )
      {pins_txt}
    )
  )'''

DRV8701E_BLOCK = _drv8701_block()

# ---------------------------------------------------------------------------
# IRLB3813PBF - Infineon TO-220AB HEXFET, re-authored in modern syntax
# (electrically identical to the part already used in MD/MDv5, footprint reused).
IRLB3813_PINS = [
    ("passive", 0.0, 0.0, 0, "G", "1"),
    ("passive", 15.24, -2.54, 180, "D", "2"),
    ("passive", 15.24, 0.0, 180, "S", "3"),
]
IRLB3813_FOOTPRINT = "PG-TO220-3_INF"

def _irlb3813_block():
    pin_lines = []
    for etype, x, y, angle, name, num in IRLB3813_PINS:
        pin_lines.append(_pin(etype, x, y, angle, name, num, length=5.08 if num != "1" else 5.08))
    pins_txt = "\n      ".join(pin_lines)
    return f'''(symbol "IRLB3813PBF"
    (pin_names (offset 1.016))
    (in_bom yes) (on_board yes)
    {_prop("Reference", "Q", 0, 8, hide=False)}
    {_prop("Value", "IRLB3813PBF", 0, 5.5, hide=False)}
    {_prop("Footprint", IRLB3813_FOOTPRINT, 0, -6)}
    {_prop("Datasheet", "IRLB3813PBF", 0, 0)}
    {_prop("Description", "N-Channel 30V 260A TO-220 HEXFET, Rds(on)=1.95mOhm", 0, 0)}
    (symbol "IRLB3813PBF_0_1"
      (polyline (pts (xy 2.54 2.54) (xy 2.54 -5.08)) (stroke (width 0.127) (type default)) (fill (type none)))
      (polyline (pts (xy 2.54 -5.08) (xy 12.7 -5.08)) (stroke (width 0.127) (type default)) (fill (type none)))
      (polyline (pts (xy 12.7 -5.08) (xy 12.7 2.54)) (stroke (width 0.127) (type default)) (fill (type none)))
      (polyline (pts (xy 12.7 2.54) (xy 2.54 2.54)) (stroke (width 0.127) (type default)) (fill (type none)))
      {pin_lines[0]}
      {pin_lines[1]}
      {pin_lines[2]}
    )
  )'''

IRLB3813_BLOCK = _irlb3813_block()

# ---------------------------------------------------------------------------
# XT60PW-M - Amass 2-pin power connector, re-authored in modern syntax
# (footprint reused from the existing MD/MDv5 local library).
XT60PWM_PINS = [
    ("passive", -5.08, 2.54, 0, "+", "1"),
    ("passive", -5.08, 0.0, 0, "-", "2"),
]
XT60PWM_FOOTPRINT = "AMASS_XT60PW-M"

def _xt60pwm_block():
    pin_lines = [_pin(etype, x, y, angle, name, num, length=5.08) for etype, x, y, angle, name, num in XT60PWM_PINS]
    pins_txt = "\n      ".join(pin_lines)
    return f'''(symbol "XT60PW-M"
    (pin_names (offset 1.016))
    (in_bom yes) (on_board yes)
    {_prop("Reference", "J", -2.5, 5, hide=False)}
    {_prop("Value", "XT60PW-M", -2.5, -3.5, hide=False)}
    {_prop("Footprint", XT60PWM_FOOTPRINT, 0, 0)}
    {_prop("Datasheet", "~", 0, 0)}
    {_prop("Description", "AMASS XT60PW-M, 2-pin 60A power connector", 0, 0)}
    (symbol "XT60PW-M_0_1"
      (rectangle (start 0 -2.54) (end 10.16 5.08)
        (stroke (width 0.254) (type default)) (fill (type background))
      )
      {pins_txt}
    )
  )'''

XT60PWM_BLOCK = _xt60pwm_block()

CUSTOM_PARTS = {
    "DRV8701E": (DRV8701E_BLOCK, DRV8701E_PINS, DRV8701E_FOOTPRINT),
    "IRLB3813PBF": (IRLB3813_BLOCK, IRLB3813_PINS, IRLB3813_FOOTPRINT),
    "XT60PW-M": (XT60PWM_BLOCK, XT60PWM_PINS, XT60PWM_FOOTPRINT),
}

if __name__ == "__main__":
    for k, (block, pins, fp) in CUSTOM_PARTS.items():
        print("===", k, "===")
        print(block[:200])
        print("npins", len(pins))
