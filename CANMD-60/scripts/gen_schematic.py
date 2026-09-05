import sys, os, uuid, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import symlib
import custom_symbols as cs

SYM = {
    'MCU': '/usr/share/kicad/symbols/MCU_ST_STM32F1.kicad_sym',
    'CAN': '/usr/share/kicad/symbols/Interface_CAN_LIN.kicad_sym',
    'REGSW': '/usr/share/kicad/symbols/Regulator_Switching.kicad_sym',
    'REGLIN': '/usr/share/kicad/symbols/Regulator_Linear.kicad_sym',
    'DEV': '/usr/share/kicad/symbols/Device.kicad_sym',
    'CONN': '/usr/share/kicad/symbols/Connector.kicad_sym',
    'PWR': '/usr/share/kicad/symbols/power.kicad_sym',
}

def U():
    return str(uuid.uuid4())

# ---------------------------------------------------------------------------
# Registry of lib symbols actually used -> (libpath, symname) or ('CUSTOM', name)
LIBID = {
    'MCU:STM32F103C8Tx': ('MCU', 'STM32F103C8Tx'),
    'CAN:MCP2561-H-SN': ('CAN', 'MCP2561-H-SN'),
    'REGSW:LMR33630ADDA': ('REGSW', 'LMR33630ADDA'),
    'REGLIN:AMS1117-3.3': ('REGLIN', 'AMS1117-3.3'),
    'DEV:C': ('DEV', 'C'),
    'DEV:D': ('DEV', 'D'),
    'DEV:LED': ('DEV', 'LED'),
    'DEV:L': ('DEV', 'L'),
    'DEV:Fuse': ('DEV', 'Fuse'),
    'DEV:D_TVS': ('DEV', 'D_TVS'),
    'DEV:R': ('DEV', 'R'),
    'CONN:Conn_01x04_Pin': ('CONN', 'Conn_01x04_Pin'),
    'CONN:Conn_01x02_Pin': ('CONN', 'Conn_01x02_Pin'),
    'PWR:GND': ('PWR', 'GND'),
    'PWR:PWR_FLAG': ('PWR', 'PWR_FLAG'),
    'CUSTOM:DRV8701E': ('CUSTOM', 'DRV8701E'),
    'CUSTOM:IRLB3813PBF': ('CUSTOM', 'IRLB3813PBF'),
    'CUSTOM:XT60PW-M': ('CUSTOM', 'XT60PW-M'),
}

_pin_cache = {}
def get_pins(libid):
    if libid in _pin_cache:
        return _pin_cache[libid]
    kind, name = LIBID[libid]
    if kind == 'CUSTOM':
        pins = cs.CUSTOM_PARTS[name][1]
    else:
        pins = symlib.get_pins(SYM[kind], name)
    d = {num: (etype, x, y, angle, pname) for etype, x, y, angle, pname, num in pins}
    _pin_cache[libid] = d
    return d

def get_footprint(libid):
    kind, name = LIBID[libid]
    if kind == 'CUSTOM':
        return cs.CUSTOM_PARTS[name][2]
    return symlib.get_footprint(SYM[kind], name)

# ---------------------------------------------------------------------------
# Part instances: ref -> dict(libid, x, y, value, footprint(optional override), nets={pin:net})
PARTS = {}

def snap(v):
    return round(round(v / 1.27) * 1.27, 2)

def add(ref, libid, x, y, value, nets, footprint=None, dnp=False):
    PARTS[ref] = dict(libid=libid, x=snap(x), y=snap(y), value=value, nets=nets,
                       footprint=footprint or get_footprint(libid), dnp=dnp)

mm = lambda v: round(v, 2)

# ===== Power input section (left) =====
add('J1', 'CUSTOM:XT60PW-M', 20, 25, 'XT60PW-M', {'1': 'VBAT_RAW', '2': 'GND'})
add('F1', 'DEV:Fuse', 40, 20, '30A', {'1': 'VBAT_RAW', '2': 'VM'})
add('D1', 'DEV:D_TVS', 55, 30, 'SMBJ36CA', {'1': 'VM', '2': 'GND'})
add('C1', 'DEV:C', 65, 20, '100uF_35V', {'1': 'VM', '2': 'GND'})
add('C2', 'DEV:C', 72, 20, '100uF_35V', {'1': 'VM', '2': 'GND'})
add('C3', 'DEV:C', 79, 20, '2.2uF_50V', {'1': 'VM', '2': 'GND'})
add('C4', 'DEV:C', 86, 20, '2.2uF_50V', {'1': 'VM', '2': 'GND'})

# ===== Gate driver DRV8701E =====
add('U1', 'CUSTOM:DRV8701E', 110, 40, 'DRV8701E', {
    '1': 'VM', '2': 'VCP_N', '3': 'CPH_N', '4': 'CPL_N', '5': 'GND',
    '6': 'VREF_N', '7': 'AVDD_N', '8': 'DVDD_N', '9': 'nFAULT', '10': 'SNSOUT',
    '11': 'ISENSE', '12': 'IDRIVE_N',
    '13': 'nSLEEP', '14': 'DRV_EN', '15': 'DRV_PH', '16': 'GND',
    '17': 'GATE_H1', '18': 'PHASE_A', '19': 'GATE_L1', '20': 'GND',
    '21': 'SP_N', '22': 'GATE_L2', '23': 'PHASE_B', '24': 'GATE_H2',
})
add('C5', 'DEV:C', 100, 15, '0.1uF', {'1': 'VM', '2': 'GND'})
add('C6', 'DEV:C', 106, 15, '10uF_50V', {'1': 'VM', '2': 'GND'})
add('C7', 'DEV:C', 145, 15, '1uF_16V', {'1': 'VCP_N', '2': 'VM'})
add('C8', 'DEV:C', 152, 15, '0.1uF_VM', {'1': 'CPH_N', '2': 'CPL_N'})
add('C9', 'DEV:C', 100, 70, '1uF_6V3', {'1': 'AVDD_N', '2': 'GND'})
add('C10', 'DEV:C', 106, 70, '1uF_6V3', {'1': 'DVDD_N', '2': 'GND'})
add('R1', 'DEV:R', 92, 70, '200k', {'1': 'IDRIVE_N', '2': 'GND'})
add('R2', 'DEV:R', 92, 45, '10k', {'1': '+3V3', '2': 'nFAULT'})
add('R3', 'DEV:R', 92, 60, '10k', {'1': '+3V3', '2': 'SNSOUT'})
add('R4', 'DEV:R', 145, 70, '16k', {'1': 'AVDD_N', '2': 'VREF_N'})
add('R5', 'DEV:R', 145, 78, '10k', {'1': 'VREF_N', '2': 'GND'})
add('R6', 'DEV:R', 92, 38, '10k', {'1': '+3V3', '2': 'nSLEEP'})

# ===== H-bridge FETs =====
add('Q1', 'CUSTOM:IRLB3813PBF', 175, 20, 'IRLB3813PBF', {'1': 'GATE_H1', '2': 'VM', '3': 'PHASE_A'})
add('Q2', 'CUSTOM:IRLB3813PBF', 175, 40, 'IRLB3813PBF', {'1': 'GATE_L1', '2': 'PHASE_A', '3': 'SP_N'})
add('Q3', 'CUSTOM:IRLB3813PBF', 175, 60, 'IRLB3813PBF', {'1': 'GATE_H2', '2': 'VM', '3': 'PHASE_B'})
add('Q4', 'CUSTOM:IRLB3813PBF', 175, 80, 'IRLB3813PBF', {'1': 'GATE_L2', '2': 'PHASE_B', '3': 'SP_N'})
add('R7', 'DEV:R', 200, 95, '1mR_3W', {'1': 'SP_N', '2': 'GND'})

# ===== Motor output =====
add('J2', 'CUSTOM:XT60PW-M', 225, 30, 'XT60PW-M', {'1': 'PHASE_A', '2': 'PHASE_B'})
add('R8', 'DEV:R', 215, 55, '10R', {'1': 'PHASE_A', '2': 'SNUB_N'})
add('C11', 'DEV:C', 215, 62, '100nF', {'1': 'SNUB_N', '2': 'PHASE_B'})

# ===== 5V buck (LMR33630) =====
add('U2', 'REGSW:LMR33630ADDA', 45, 60, 'LMR33630ADDA', {
    '1': 'GND', '2': 'VM', '3': 'VM', '4': 'NC_PG', '5': 'FB_N', '6': 'VCC_N', '7': 'BOOT_N', '8': 'SW_N', '9': 'GND',
})
add('C12', 'DEV:C', 30, 55, '2.2uF_50V', {'1': 'VM', '2': 'GND'})
add('C13', 'DEV:C', 30, 70, '2.2uF_50V', {'1': 'VM', '2': 'GND'})
add('C14', 'DEV:C', 60, 50, '2.2nF_25V', {'1': 'BOOT_N', '2': 'SW_N'})
add('C15', 'DEV:C', 45, 75, '1uF_16V', {'1': 'VCC_N', '2': 'GND'})
add('L1', 'DEV:L', 60, 62, '15uH_3A', {'1': 'SW_N', '2': '+5V'})
add('C16', 'DEV:C', 70, 55, '22uF_16V', {'1': '+5V', '2': 'GND'})
add('C17', 'DEV:C', 76, 55, '22uF_16V', {'1': '+5V', '2': 'GND'})
add('R9', 'DEV:R', 55, 85, '40.2k', {'1': '+5V', '2': 'FB_N'})
add('R10', 'DEV:R', 55, 92, '10k', {'1': 'FB_N', '2': 'GND'})

# ===== 3.3V LDO =====
add('U3', 'REGLIN:AMS1117-3.3', 90, 100, 'AMS1117-3.3', {'1': 'GND', '2': '+3V3', '3': '+5V'})
add('C18', 'DEV:C', 80, 100, '10uF', {'1': '+5V', '2': 'GND'})
add('C19', 'DEV:C', 100, 100, '10uF', {'1': '+3V3', '2': 'GND'})

# ===== CAN transceiver =====
add('U4', 'CAN:MCP2561-H-SN', 120, 100, 'MCP2561-H-SN', {
    '1': 'CAN_TX', '2': 'GND', '3': '+5V', '4': 'CAN_RX', '5': 'NC_SPLIT', '6': 'CANL', '7': 'CANH', '8': 'STBY_N',
})
add('R11', 'DEV:R', 120, 118, '10k', {'1': 'STBY_N', '2': 'GND'})
add('R12', 'DEV:R', 140, 90, '120R', {'1': 'CANH', '2': 'CANL'})
add('J3', 'CONN:Conn_01x04_Pin', 150, 100, 'CAN_IN', {'1': 'GND', '2': 'CANL', '3': 'CANH', '4': 'BUSPWR'})
add('J4', 'CONN:Conn_01x04_Pin', 150, 115, 'CAN_OUT', {'1': 'GND', '2': 'CANL', '3': 'CANH', '4': 'BUSPWR'})

# ===== MCU =====
add('U5', 'MCU:STM32F103C8Tx', 90, 150, 'STM32F103C8T6', {
    '1': '+3V3', '2': 'NC_PC13', '3': 'NC_PC14', '4': 'NC_PC15', '5': 'NC_PD0', '6': 'NC_PD1',
    '7': 'NRST_N', '8': 'GND', '9': '+3V3',
    '10': 'ISENSE', '11': 'NC_PA1', '12': 'NC_PA2', '13': 'NC_PA3', '14': 'NC_PA4', '15': 'NC_PA5',
    '16': 'DRV_EN', '17': 'DRV_PH',
    '18': 'nSLEEP', '19': 'nFAULT', '20': 'SNSOUT', '21': 'NC_PB10', '22': 'NC_PB11',
    '23': 'GND', '24': '+3V3',
    '25': 'NC_PB12', '26': 'NC_PB13', '27': 'NC_PB14', '28': 'NC_PB15',
    '29': 'NC_PA8', '30': 'NC_PA9', '31': 'NC_PA10', '32': 'CAN_RX', '33': 'CAN_TX',
    '34': 'SWDIO', '35': 'GND', '36': '+3V3', '37': 'SWCLK', '38': 'NC_PA15',
    '39': 'NC_PB3', '40': 'NC_PB4', '41': 'NC_PB5', '42': 'NC_PB6', '43': 'NC_PB7',
    '44': 'BOOT0_N', '45': 'LED_CANACT', '46': 'NC_PB9',
    '47': 'GND', '48': '+3V3',
})
add('C20', 'DEV:C', 70, 130, '100nF', {'1': '+3V3', '2': 'GND'})
add('C21', 'DEV:C', 76, 130, '100nF', {'1': '+3V3', '2': 'GND'})
add('C22', 'DEV:C', 82, 130, '100nF', {'1': '+3V3', '2': 'GND'})
add('C23', 'DEV:C', 88, 130, '4.7uF', {'1': '+3V3', '2': 'GND'})
add('C24', 'DEV:C', 60, 145, '100nF', {'1': 'NRST_N', '2': 'GND'})
add('R13', 'DEV:R', 60, 138, '10k', {'1': '+3V3', '2': 'NRST_N'})
add('R14', 'DEV:R', 60, 165, '10k', {'1': 'BOOT0_N', '2': 'GND'})
add('J5', 'CONN:Conn_01x04_Pin', 130, 150, 'SWD', {'1': '+3V3', '2': 'SWDIO', '3': 'SWCLK', '4': 'GND'})

# ===== Status LEDs =====
add('LED1', 'DEV:LED', 140, 130, 'PWR', {'1': 'GND', '2': 'LED_PWR_A'})
add('R15', 'DEV:R', 140, 122, '1k', {'1': '+3V3', '2': 'LED_PWR_A'})
# FAULT LED: +3V3 --R16-- LED_FAULT_A --LED2(A->K)-- nFAULT (lights when nFAULT pulled low)
add('LED2', 'DEV:LED', 150, 130, 'FAULT', {'1': 'nFAULT', '2': 'LED_FAULT_A'})
add('R16', 'DEV:R', 150, 122, '1k', {'1': '+3V3', '2': 'LED_FAULT_A'})
add('LED3', 'DEV:LED', 160, 130, 'CAN_ACT', {'1': 'GND', '2': 'LED_CANACT_A'})
add('R17', 'DEV:R', 160, 122, '330R', {'1': 'LED_CANACT', '2': 'LED_CANACT_A'})

# ===== PWR_FLAGs =====
add('PWR1', 'PWR:PWR_FLAG', 20, 15, 'PWR_FLAG', {'1': 'GND'})
add('PWR2', 'PWR:PWR_FLAG', 30, 15, 'PWR_FLAG', {'1': 'VM'})
add('PWR3', 'PWR:PWR_FLAG', 70, 45, 'PWR_FLAG', {'1': '+5V'})

# a couple of explicit GND symbol instances (grounding a few far-flung spots visually
# is optional cosmetically; not required for connectivity since labels handle it, so
# we only add one near the input to anchor the PWR_FLAG visually)
add('GND1', 'PWR:GND', 20, 12, 'GND', {'1': 'GND'})

print(f"Total parts: {len(PARTS)}")

# ---------------------------------------------------------------------------
# Emission

def pin_global(part, pinnum):
    pins = get_pins(part['libid'])
    etype, lx, ly, angle, pname = pins[pinnum]
    gx = part['x'] + lx
    gy = part['y'] - ly
    return mm(gx), mm(gy), etype, pname

def build_lib_symbols():
    seen = set()
    blocks = []
    for ref, p in PARTS.items():
        kind, name = LIBID[p['libid']]
        if kind == 'CUSTOM':
            block = cs.CUSTOM_PARTS[name][0]
            if name not in seen:
                seen.add(name)
                blocks.append(block)
        else:
            libpath = SYM[kind]
            if name not in seen:
                seen.add(name)
                blocks.append(symlib.get_flattened_block(libpath, name))
    return "\n".join(blocks)

def indent(text, n=4):
    pad = " " * n
    return "\n".join(pad + line if line.strip() else line for line in text.splitlines())

def emit_instance(ref, p):
    kind, name = LIBID[p['libid']]
    lib_id = name if kind == 'CUSTOM' else f"{name}"
    # KiCad lib_id in schematic normally looks like "Library:Symbol"; since every
    # symbol here is embedded directly (no external lib table dependency needed
    # for kicad-cli ERC/plotting), we key it by the bare symbol name we embedded.
    uid = U()
    lines = []
    lines.append(f'  (symbol (lib_id "{lib_id}") (at {mm(p["x"])} {mm(p["y"])} 0) (unit 1)')
    lines.append(f'    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if p["dnp"] else "no"}) (fields_autoplaced yes)')
    lines.append(f'    (uuid "{uid}")')
    lines.append(f'    (property "Reference" "{ref}" (at {mm(p["x"]+2)} {mm(p["y"]-2)} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'    (property "Value" "{p["value"]}" (at {mm(p["x"]+2)} {mm(p["y"]+2)} 0) (effects (font (size 1.27 1.27))))')
    lines.append(f'    (property "Footprint" "{p["footprint"]}" (at {mm(p["x"])} {mm(p["y"])} 0) (effects (font (size 1.27 1.27)) hide))')
    pins = get_pins(p['libid'])
    for pinnum in pins:
        lines.append(f'    (pin "{pinnum}" (uuid "{U()}"))')
    lines.append('  )')
    return "\n".join(lines)

def emit_label(net, gx, gy):
    uid = U()
    return (f'  (global_label "{net}" (shape bidirectional) (at {gx} {gy} 0) (fields_autoplaced yes)\n'
            f'    (effects (font (size 1.27 1.27)) (justify left))\n'
            f'    (uuid "{uid}")\n'
            f'    (property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at {gx} {gy} 0) (effects (font (size 1.27 1.27)) hide))\n'
            f'  )')

def emit_no_connect(gx, gy):
    return f'  (no_connect (at {gx} {gy}) (uuid "{U()}"))'

def build_body():
    instances = []
    labels = []
    ncs = []
    for ref, p in PARTS.items():
        instances.append(emit_instance(ref, p))
        pins = get_pins(p['libid'])
        for pinnum in pins:
            if pinnum in p['nets']:
                net = p['nets'][pinnum]
                gx, gy, etype, pname = pin_global(p, pinnum)
                if net.startswith('NC_') or net.startswith('NC-'):
                    ncs.append(emit_no_connect(gx, gy))
                else:
                    labels.append(emit_label(net, gx, gy))
            else:
                gx, gy, etype, pname = pin_global(p, pinnum)
                ncs.append(emit_no_connect(gx, gy))
    return "\n".join(instances), "\n".join(labels), "\n".join(ncs)

# ---------------------------------------------------------------------------
# Explicit footprint assignment for generic Device:*/Connector:* symbols
# (these library symbols ship with no default Footprint field).
FOOTPRINT_OVERRIDE = {
    'F1':  'Fuse:FuseHolder_Blade_ATO_Littelfuse_FLR_178.6165',
    'D1':  'Diode_SMD:D_SMB',
    'C1':  'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',
    'C2':  'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',
    'C3':  'Capacitor_SMD:C_1210_3225Metric',
    'C4':  'Capacitor_SMD:C_1210_3225Metric',
    'C5':  'Capacitor_SMD:C_0603_1608Metric',
    'C6':  'Capacitor_SMD:C_1210_3225Metric',
    'C7':  'Capacitor_SMD:C_0805_2012Metric',
    'C8':  'Capacitor_SMD:C_0805_2012Metric',
    'C9':  'Capacitor_SMD:C_0603_1608Metric',
    'C10': 'Capacitor_SMD:C_0603_1608Metric',
    'C11': 'Capacitor_SMD:C_0805_2012Metric',
    'C12': 'Capacitor_SMD:C_1210_3225Metric',
    'C13': 'Capacitor_SMD:C_1210_3225Metric',
    'C14': 'Capacitor_SMD:C_0603_1608Metric',
    'C15': 'Capacitor_SMD:C_0603_1608Metric',
    'C16': 'Capacitor_SMD:C_1210_3225Metric',
    'C17': 'Capacitor_SMD:C_1210_3225Metric',
    'C18': 'Capacitor_SMD:C_0805_2012Metric',
    'C19': 'Capacitor_SMD:C_0805_2012Metric',
    'C20': 'Capacitor_SMD:C_0603_1608Metric',
    'C21': 'Capacitor_SMD:C_0603_1608Metric',
    'C22': 'Capacitor_SMD:C_0603_1608Metric',
    'C23': 'Capacitor_SMD:C_0805_2012Metric',
    'C24': 'Capacitor_SMD:C_0603_1608Metric',
    'R1':  'Resistor_SMD:R_0603_1608Metric',
    'R2':  'Resistor_SMD:R_0603_1608Metric',
    'R3':  'Resistor_SMD:R_0603_1608Metric',
    'R4':  'Resistor_SMD:R_0603_1608Metric',
    'R5':  'Resistor_SMD:R_0603_1608Metric',
    'R6':  'Resistor_SMD:R_0603_1608Metric',
    'R7':  'Resistor_SMD:R_2512_6332Metric',
    'R8':  'Resistor_SMD:R_1206_3216Metric',
    'R9':  'Resistor_SMD:R_0603_1608Metric',
    'R10': 'Resistor_SMD:R_0603_1608Metric',
    'R11': 'Resistor_SMD:R_0603_1608Metric',
    'R12': 'Resistor_SMD:R_0603_1608Metric',
    'R13': 'Resistor_SMD:R_0603_1608Metric',
    'R14': 'Resistor_SMD:R_0603_1608Metric',
    'R15': 'Resistor_SMD:R_0603_1608Metric',
    'R16': 'Resistor_SMD:R_0603_1608Metric',
    'R17': 'Resistor_SMD:R_0603_1608Metric',
    'L1':  'Inductor_SMD:L_6.3x6.3_H3',
    'LED1':'LED_SMD:LED_0603_1608Metric',
    'LED2':'LED_SMD:LED_0603_1608Metric',
    'LED3':'LED_SMD:LED_0603_1608Metric',
    'J3':  'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',
    'J4':  'Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical',
    'J5':  'Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical',
}
for _ref, _fp in FOOTPRINT_OVERRIDE.items():
    PARTS[_ref]['footprint'] = _fp

def main():
    lib_symbols = build_lib_symbols()
    instances, labels, ncs = build_body()
    sch = f'''(kicad_sch (version 20260101) (generator "eeschema") (generator_version "10.0")

  (uuid "{U()}")

  (paper "A3")

  (lib_symbols
{indent(lib_symbols, 4)}
  )

{instances}

{labels}

{ncs}

  (sheet_instances
    (path "/" (page "1"))
  )
)
'''
    outpath = "/home/dev/kicad-ws/CANMD-60/CANMD-60.kicad_sch"
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(sch)
    print("wrote", outpath, len(sch), "bytes,", len(PARTS), "parts")

if __name__ == "__main__":
    main()

