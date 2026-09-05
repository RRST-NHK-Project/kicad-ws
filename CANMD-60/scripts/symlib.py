"""Helpers to extract balanced-paren symbol blocks from .kicad_sym library files,
resolving (extends "Base") chains, for embedding into a hand-generated .kicad_sch."""
import re

def extract_block(text, start_idx):
    """Given index of an opening '(' , return the substring up to its matching ')'."""
    depth = 0
    i = start_idx
    n = len(text)
    in_str = False
    while i < n:
        c = text[i]
        if c == '"' and text[i-1] != '\\':
            in_str = not in_str
        elif not in_str:
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i+1]
        i += 1
    raise ValueError("unbalanced")

def find_symbol_block(text, name):
    pat = '(symbol "%s"' % name
    idx = text.find(pat)
    if idx < 0:
        raise KeyError(name)
    return extract_block(text, idx)

def get_extends(block):
    m = re.search(r'\(extends "([^"]+)"\)', block)
    return m.group(1) if m else None

_cache = {}

def load_lib(path):
    if path not in _cache:
        _cache[path] = open(path, encoding='utf-8').read()
    return _cache[path]

def _get_subunit_blocks(block):
    """Return the list of nested (symbol "NAME_x_y" ...) blocks directly under a
    top-level symbol block (its graphical/pin sub-units)."""
    subs = []
    search_from = 1  # skip the block's own opening "(symbol " at index 0
    while True:
        idx = block.find('(symbol "', search_from)
        if idx < 0:
            break
        sub = extract_block(block, idx)
        subs.append(sub)
        search_from = idx + len(sub)
    return subs

def get_flattened_block(libpath, name):
    """Resolve a (possibly extends-based) symbol into one self-contained block:
    the named symbol's own properties + the base symbol's pin/graphic sub-units,
    with no (extends ...) reference left (schematic-embedded lib_symbols must not
    depend on cross-symbol inheritance resolution)."""
    text = load_lib(libpath)
    block = find_symbol_block(text, name)
    ext = get_extends(block)
    if not ext:
        return block
    base_block = find_symbol_block(text, ext)
    # base may itself extend something (rare); resolve recursively
    base_ext = get_extends(base_block)
    if base_ext:
        base_block = get_flattened_block(libpath, ext)
    subunits = _get_subunit_blocks(base_block)
    # subunit blocks are named "<base>_<unit>_<style>"; KiCad associates a symbol's
    # graphical sub-units with it purely by name prefix, so after flattening under
    # the derived name they must be renamed to "<derived>_<unit>_<style>" or the
    # instance ends up with no resolvable pins at all (label/no-connect "dangling").
    renamed = []
    for su in subunits:
        su2 = re.sub(r'^\(symbol "' + re.escape(ext) + r'_',
                      '(symbol "' + name + '_', su, count=1)
        renamed.append(su2)
    subunits = renamed
    # strip the (extends "...") line from the derived block
    derived_no_extends = re.sub(r'\s*\(extends "[^"]+"\)', '', block, count=1)
    # insert the base's sub-unit blocks just before the derived block's final closing paren
    insert_at = derived_no_extends.rstrip().rfind(')')
    flattened = (derived_no_extends[:insert_at].rstrip() + "\n    "
                 + "\n    ".join(subunits) + "\n  )")
    return flattened

def get_symbol_with_deps(libpath, name):
    """Return list of raw blocks: [base_block(s)..., named_block] needed to embed `name`."""
    text = load_lib(libpath)
    block = find_symbol_block(text, name)
    ext = get_extends(block)
    blocks = []
    if ext:
        blocks.extend(get_symbol_with_deps(libpath, ext))
    blocks.append(block)
    return blocks

def get_pins(libpath, name, resolve_extends=True):
    """Return list of (elec_type, x, y, angle, pinname, pinnum) for the *_1_1 (or _0_1) unit."""
    text = load_lib(libpath)
    block = find_symbol_block(text, name)
    ext = get_extends(block)
    if ext and resolve_extends:
        block = find_symbol_block(text, ext)
    pins = []
    for m in re.finditer(
        r'\(pin (\w+) line\s*\(at ([-0-9.]+) ([-0-9.]+) (\d+)\)[\s\S]{0,300}?'
        r'\(name "([^"]*)"[\s\S]{0,150}?\(number "([^"]+)"',
        block):
        pins.append((m.group(1), float(m.group(2)), float(m.group(3)), int(m.group(4)), m.group(5), m.group(6)))
    return pins

def get_footprint(libpath, name):
    text = load_lib(libpath)
    block = find_symbol_block(text, name)
    m = re.search(r'Footprint" "([^"]*)"', block)
    return m.group(1) if m else None
