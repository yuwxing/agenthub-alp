#pragma once
#include "config_common.h"

#define VENDOR_ID       0xFEED
#define PRODUCT_ID      0x0A0A
#define DEVICE_VER      0x0001
#define MANUFACTURER    AgentHub
#define PRODUCT         AgentHub Macropad

#define MATRIX_ROWS 3
#define MATRIX_COLS 4

#define MATRIX_ROW_PINS { GP2, GP3, GP4 }
#define MATRIX_COL_PINS { GP5, GP6, GP7, GP8 }
#define DIODE_DIRECTION COL2ROW

#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET
#define RP2040_BOOTLOADER_DOUBLE_TAP_RESET_TIMEOUT 500U

#define TAPPING_TERM 200

#define RAW_USAGE_PAGE 0xFF60
#define RAW_USAGE_ID 0x61
