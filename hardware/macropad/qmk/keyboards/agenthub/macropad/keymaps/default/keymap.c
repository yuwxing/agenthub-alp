#include QMK_KEYBOARD_H

enum ag_keycodes {
    AG_GOAL = SAFE_RANGE,
    AG_CONTEXT,
    AG_DATA,
    AG_PLAN,
    AG_CREATE,
    AG_EXECUTE,
    AG_ANALYZE,
    AG_SEARCH,
    AG_INPUT,
    AG_GENERATE,
    AG_RUN,
    AG_CLEAR,
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    [0] = LAYOUT_ortho_3x4(
        AG_GOAL,    AG_CONTEXT, AG_DATA,   AG_PLAN,
        AG_CREATE,  AG_EXECUTE, AG_ANALYZE, AG_SEARCH,
        AG_INPUT,   AG_GENERATE, AG_RUN,    AG_CLEAR
    )
};

#if defined(RAW_ENABLE)
#    include "raw_hid.h"
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    if (record->event.pressed) {
        uint8_t data[32] = {0};
        data[0] = keycode - SAFE_RANGE;
        raw_hid_send(data, sizeof(data));
    }
    return false;
}
#else
bool process_record_user(uint16_t keycode, keyrecord_t *record) {
    return true;
}
#endif
