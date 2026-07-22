/* AgentHub Macropad 3D Case */
/* Requires: 12x MX switches, 1x Pi Pico */

// --- Dimensions ---
KEY_W = 19.05;   // MX switch spacing
KEY_H = 19.05;
COLS = 4;
ROWS = 3;
PAD = 8;         // wall padding
WALL = 3;        // wall thickness
CASE_W = COLS * KEY_W + PAD * 2;
CASE_H = ROWS * KEY_H + PAD * 2;
CASE_Z = 12;     // case height
PLATE_Z = 1.5;   // switch plate thickness

// --- Plate ---
module plate() {
    difference() {
        square([CASE_W, CASE_H]);
        for (r = [0:ROWS-1], c = [0:COLS-1]) {
            x = PAD + c * KEY_W + KEY_W/2;
            y = PAD + r * KEY_H + KEY_H/2;
            translate([x, y])
                square([14, 14], center=true); // MX cutout
        }
    }
}

// --- Case bottom ---
module case_bottom() {
    difference() {
        linear_extrude(CASE_Z)
            square([CASE_W + WALL*2, CASE_H + WALL*2]);
        translate([WALL, WALL, PLATE_Z])
            linear_extrude(CASE_Z)
                square([CASE_W, CASE_H]);
    }
}

// --- Pico mount ---
module pico_mount() {
    translate([WALL + 5, WALL + CASE_H - 60, PLATE_Z]) {
        difference() {
            cube([55, 25, 4]);
            // mounting holes
            translate([3, 3, -1]) cylinder(r=1.5, h=6, $fn=12);
            translate([52, 3, -1]) cylinder(r=1.5, h=6, $fn=12);
            translate([3, 22, -1]) cylinder(r=1.5, h=6, $fn=12);
            translate([52, 22, -1]) cylinder(r=1.5, h=6, $fn=12);
        }
    }
}

// --- USB cutout ---
module usb_cutout() {
    translate([WALL + (CASE_W - 12)/2, -1, PLATE_Z + 2])
        cube([12, WALL + 2, 8]);
}

// --- Assembly ---
module assembly() {
    // Case bottom
    case_bottom();
    // USB cutout
    translate([CASE_W/2, -WALL, PLATE_Z])
        cube([14, WALL+1, 7], center=true);
    // Pico mount
    pico_mount();
}

assembly();
