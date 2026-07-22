#!/usr/bin/env python3
"""Generate KiCad 8 project for AgentHub Macropad (3x4 + RP2040).

Usage: python generate_kicad.py
Output: ./agenthub-macropad/  (KiCad 8 project folder)
"""
import json, os, textwrap

PROJ = "agenthub-macropad"
OUT = os.path.join(os.path.dirname(__file__), PROJ)
os.makedirs(OUT, exist_ok=True)

# ── Component positions (mm) ──────────────────────────────────
# Grid: 4 cols × 3 rows, 19.05mm spacing, origin at (50, 50)
GRID_X0, GRID_Y0 = 50, 50
SPACING = 19.05

# Pi Pico position
PICO_X, PICO_Y = 100, 10

def sw_pos(r, c):  # switch center
    return (GRID_X0 + c * SPACING, GRID_Y0 + r * SPACING)

def d_pos(r, c):  # diode (offset from switch)
    return (GRID_X0 + c * SPACING + 5, GRID_Y0 + r * SPACING - 3)

HEADER = f"""(kicad_sch (version 20240126) (generator "manual")
  (paper "A4")
  (title_block
    (title "AgentHub Macropad 3x4 + RP2040")
    (date "{__import__("datetime").datetime.now().strftime("%Y-%m-%d")}")
    (rev "1.0")
    (company "AgentHub OS")
  )
"""

FOOTER = """
  (sheet_instances
    (path "/" (page "1"))
  )
  (symbol_instances
    (path "/B1C1C8B6-6CCE-4ECA-8C3C-4AAEAB1D8A23" (reference "U1") (unit 1))
  )
)
"""

# ── Build schematic body ──────────────────────────────────────
parts = [HEADER]

# Raspberry Pi Pico symbol (from official library)
parts.append(f"""  (symbol (lib_id "MCU_Module:RPi_Pico") (at {PICO_X} {PICO_Y} 0) (unit 1)
    (in_bom yes) (on_board yes)
    (reference "U1") (value "Raspberry Pi Pico")
    (footprint "RPi_Pico_SMD_TH:RPi_Pico_SMD_TH")
    (fields_autoplaced yes)
    (path "/B1C1C8B6-6CCE-4ECA-8C3C-4AAEAB1D8A23")
  )""")

# Row labels and connections
ROW_PINS = ["GP2", "GP3", "GP4"]
for r, pin in enumerate(ROW_PINS):
    _, y = sw_pos(r, 0)
    parts.append(f"""  (label "R{r}" (at {GRID_X0 - 15} {y} 0) (fields_autoplaced yes))
    (wire (pts (xy {GRID_X0 - 15} {y}) (xy {GRID_X0 - 8} {y})))""")

# Column labels
COL_PINS = ["GP5", "GP6", "GP7", "GP8"]
for c, pin in enumerate(COL_PINS):
    x, _ = sw_pos(0, c)
    parts.append(f"""  (label "C{c}" (at {x} {GRID_Y0 - 15} 90) (fields_autoplaced yes))
    (wire (pts (xy {x} {GRID_Y0 - 15}) (xy {x} {GRID_Y0 - 8})))""")

# 12 switches + 12 diodes
for r in range(3):
    for c in range(4):
        idx = r * 4 + c + 1
        sx, sy = sw_pos(r, c)
        dx, dy = d_pos(r, c)

        # Switch
        parts.append(f"""  (symbol (lib_id "Switch:SW_Push") (at {sx} {sy} 0) (unit 1)
    (in_bom yes) (on_board yes)
    (reference "SW{idx}") (value "MX Switch")
    (footprint "Switch_Keyboard:SW_Cherry_MX_PCB")
  )""")

        # Diode
        parts.append(f"""  (symbol (lib_id "Device:D") (at {dx} {dy} 90) (unit 1)
    (in_bom yes) (on_board yes)
    (reference "D{idx}") (value "1N4148")
    (footprint "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal")
  )""")

        # Row wire (switch top pin → row bus)
        parts.append(f"""    (wire (pts (xy {sx} {sy - 4}) (xy {sx} {GRID_Y0 - 8})))""")

        # Diode connections
        parts.append(f"""    (wire (pts (xy {sx} {sy + 4}) (xy {dx} {dy - 3})))
    (wire (pts (xy {dx} {dy + 3}) (xy {sx + 10} {sy + 4})))""")

        # Column wire
        parts.append(f"""    (wire (pts (xy {sx + 10} {sy + 4}) (xy {GRID_X0 + 3 * SPACING + 10} {sy + 4})))""")

parts.append(FOOTER)
schematic = "\n".join(parts)

# ── PCB placeholder ────────────────────────────────────────────
BOARD_W = 4 * SPACING + 16
BOARD_H = 3 * SPACING + 16

pcb = f"""(kicad_pcb (version 20240126) (generator "manual")
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (35 "Edge.Cuts" user)
  )
  (setup
    (pad_to_mask_clearance 0.05)
    (tracks_clearance 0.2)
  )
  (gr_line (start 0 0) (end {BOARD_W} 0) (layer Edge.Cuts) (width 0.15))
  (gr_line (start {BOARD_W} 0) (end {BOARD_W} {BOARD_H}) (layer Edge.Cuts) (width 0.15))
  (gr_line (start {BOARD_W} {BOARD_H}) (end 0 {BOARD_H}) (layer Edge.Cuts) (width 0.15))
  (gr_line (start 0 {BOARD_H}) (end 0 0) (layer Edge.Cuts) (width 0.15))
)
"""

# ── Project file ───────────────────────────────────────────────
PROJECT = {
    "board": {
        "design_settings": {
            "defaults": {
                "track_width": 0.254,
                "via_dia": 0.6,
                "via_drill": 0.3,
            },
            "rules": {"min_clearance": 0.2},
        }
    },
    "meta": {"version": 1},
    "project": {
        "name": PROJ,
        "files": [f"{PROJ}.kicad_sch"],
    },
    "schematic": {
        "drawing": {},
        "annotate_start_num": 0,
    },
}

# ── Write files ────────────────────────────────────────────────
def write(name, content):
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {name}")

if __name__ == "__main__":
    print(f"Generating KiCad project: {PROJ}/")
    write(f"{PROJ}.kicad_pro", json.dumps(PROJECT, indent=2))
    write(f"{PROJ}.kicad_sch", schematic)
    write(f"{PROJ}.kicad_pcb", pcb)
    print(f"\nOpen {OUT}/ in KiCad 8 then:")
    print("  1. Update symbols from library (Rescue symbols)")
    print("  2. Annotate schematic (Tools → Annotate)")
    print("  3. Run Pcbnew, place footprints, route traces")
    print("  4. Generate Gerber files (File → Fabrication Outputs)")
