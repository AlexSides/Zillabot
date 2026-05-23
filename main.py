# =========================
# main.py
# =========================

import gc
import time
from machine import Pin

try:
    import _thread
except Exception:
    _thread = None

import core0_motor as motors
import core1_navigation as nav

try:
    import dfplayer
except Exception:
    dfplayer = None

from config import (
    MODE_1_SUMO,
    MODE_2_TUG,
    ENABLE_SENSOR_FILE_LOGGING,
    TRACK_COUNTDOWN_ROAR,
    SUMO_SELECTED_TRACK,
    TUG_SELECTED_TRACK,
)


MODE_PROGRAM = 0
DEFAULT_TOF_COUNT = 5
BUILD_TAG = "2026-05-02-main-rebuild-1"

DFPLAYER_VOLUME = 20

DEBOUNCE_S = 0.20
SW_DEBOUNCE_MS = 50
DELAY_ON_MS = 200
DELAY_OFF_MS = 800
SENSOR_SETTLE_MS = 500
SENSOR_RECHECK_MS = 250
SENSOR_LIVE_TIMEOUT_MS = 500


# ======================================================
# Sensor core bring-up
# ======================================================

sensor_core_available = False

try:
    import core0_sensors as sensors

    set_sensor_power = getattr(sensors, "set_sensor_power", lambda enabled: None)
    request_imu_calibration = getattr(sensors, "request_imu_calibration", lambda: None)
    start_file_logging = getattr(sensors, "start_file_logging", lambda *args, **kwargs: False)
    stop_file_logging = getattr(sensors, "stop_file_logging", lambda: None)

    imu_state = getattr(sensors, "imu_state")
    boundary_state = getattr(sensors, "boundary_state")
    tof_state = getattr(sensors, "tof_state")
    sensor_runtime_state = getattr(
        sensors,
        "sensor_runtime_state",
        {"enabled": False, "last_loop_ms": 0},
    )

    started = False
    start_sensor_core = getattr(sensors, "start_sensor_core", None)
    if callable(start_sensor_core):
        start_sensor_core()
        started = True
    else:
        sensor_thread = getattr(sensors, "sensor_thread", None)
        if callable(sensor_thread) and _thread is not None:
            if not bool(getattr(sensors, "_started", False)):
                setattr(sensors, "_started", True)
                _thread.start_new_thread(sensor_thread, ())
            started = True

    sensor_core_available = started
    if started:
        print("[MAIN] Sensor core started")
    else:
        print("[MAIN] Sensor core start helper unavailable")

except Exception as e:
    print("[MAIN] Sensor core failed to start:", e)

    def set_sensor_power(enabled):
        return None

    def request_imu_calibration():
        return None

    def start_file_logging(*args, **kwargs):
        return False

    def stop_file_logging():
        return None

    imu_state = {"heading": 0.0, "ok": False}
    boundary_state = {
        "left": 0,
        "right": 0,
        "left_sumo": False,
        "right_sumo": False,
        "left_tug": False,
        "right_tug": False,
        "left_blue": False,
        "right_blue": False,
        "left_black": False,
        "right_black": False,
    }
    tof_state = {
        "ok": False,
        "mm": [0] * DEFAULT_TOF_COUNT,
        "min": 0,
    }
    sensor_runtime_state = {"enabled": False, "last_loop_ms": 0}


# ======================================================
# Pins
# ======================================================

def init_control_pins():
    global btn_start, sw_sumo, sw_tug, led

    btn_start = Pin(0, Pin.IN, Pin.PULL_DOWN)
    sw_sumo = Pin(1, Pin.IN, Pin.PULL_UP)
    sw_tug = Pin(2, Pin.IN, Pin.PULL_UP)

    try:
        led = Pin("LED", Pin.OUT)
    except Exception:
        led = Pin(25, Pin.OUT)


init_control_pins()


# ======================================================
# State
# ======================================================

sensor_mode_enabled = False
sensor_ready = False
sensor_ready_at_ms = 0
sensor_wait_reason = ""

audio_enabled = False
audio_ready = False

_last_sw_raw = None
_last_sw_change_ms = time.ticks_ms()
last_start = 0
last_start_ms = 0


# ======================================================
# Helpers
# ======================================================

def _mode_name(mode):
    if mode == MODE_PROGRAM:
        return "PROGRAM"
    if mode == MODE_1_SUMO:
        return "SUMO"
    if mode == MODE_2_TUG:
        return "TUG"
    return str(mode)


def decode_switch():
    s = sw_sumo.value()
    t = sw_tug.value()

    if s == 0 and t == 1:
        return MODE_1_SUMO
    if s == 1 and t == 0:
        return MODE_2_TUG
    if s == 1 and t == 1:
        return MODE_PROGRAM
    return "INVALID"


def read_switch_debounced():
    global _last_sw_raw, _last_sw_change_ms

    raw = decode_switch()
    now = time.ticks_ms()

    if _last_sw_raw is None:
        _last_sw_raw = raw
        _last_sw_change_ms = now
        return raw

    if raw != _last_sw_raw:
        _last_sw_raw = raw
        _last_sw_change_ms = now
        return None

    if time.ticks_diff(now, _last_sw_change_ms) >= SW_DEBOUNCE_MS:
        return raw

    return None


def setup_audio():
    global audio_enabled, audio_ready

    if dfplayer is None:
        audio_enabled = False
        audio_ready = False
        print("[AUDIO] DFPlayer import unavailable")
        return False

    audio_enabled = True
    audio_ready = False
    print("[AUDIO] DFPlayer available")
    return True


def warm_audio():
    global audio_ready

    if not audio_enabled or dfplayer is None:
        return False

    if audio_ready:
        return True

    try:
        dfplayer.init(volume=DFPLAYER_VOLUME)
        audio_ready = True
        print("[AUDIO] DFPlayer warmed at volume", DFPLAYER_VOLUME)
        return True
    except Exception as e:
        print("[AUDIO] warm failed:", repr(e))
        audio_ready = False
        return False


def apply_audio_volume():
    if not audio_enabled or dfplayer is None:
        return False

    try:
        if hasattr(dfplayer, "set_volume"):
            dfplayer.set_volume(DFPLAYER_VOLUME)
        return True
    except Exception as e:
        print("[AUDIO] volume set failed:", repr(e))
        return False


def start_countdown_audio():
    if not audio_enabled or dfplayer is None:
        return False

    try:
        if not warm_audio():
            return False
        apply_audio_volume()
        dfplayer.play(int(TRACK_COUNTDOWN_ROAR))
        print("[AUDIO] playing: COUNTDOWN at volume", DFPLAYER_VOLUME)
        return True
    except Exception as e:
        print("[AUDIO] countdown start failed:", repr(e))
        return False


def _match_track_for_mode(mode):
    if mode == MODE_1_SUMO:
        return SUMO_SELECTED_TRACK, "SUMO"

    if mode == MODE_2_TUG:
        return TUG_SELECTED_TRACK, "TUG"

    return 0, ""


def start_match_audio(mode):
    if not audio_enabled or dfplayer is None:
        return False

    raw_track, label = _match_track_for_mode(mode)
    try:
        track = int(raw_track)
    except Exception:
        track = 0

    if track <= 0:
        print("[AUDIO]", label or "MATCH", "track disabled/invalid:", raw_track)
        return False

    try:
        if not warm_audio():
            return False
        apply_audio_volume()
        dfplayer.play(track)
        print(
            "[AUDIO] playing:",
            label or "MATCH",
            "track",
            track,
            "at volume",
            DFPLAYER_VOLUME,
        )
        return True
    except Exception as e:
        print("[AUDIO] match start failed:", repr(e))
        return False


def stop_audio(label=""):
    if not audio_enabled or dfplayer is None:
        return False

    try:
        dfplayer.stop()
        if label:
            print("[AUDIO] stopped:", label)
        return True
    except Exception as e:
        print("[AUDIO] stop failed:", repr(e))
        return False


def sensor_status(current_mode, now_ms=None):
    if current_mode == MODE_PROGRAM:
        return True, ""

    if not sensor_core_available:
        return False, "sensor core unavailable"

    if now_ms is None:
        now_ms = time.ticks_ms()

    last_loop_ms = int(sensor_runtime_state.get("last_loop_ms", 0) or 0)
    if last_loop_ms > 0 and time.ticks_diff(now_ms, last_loop_ms) > SENSOR_LIVE_TIMEOUT_MS:
        return False, "sensor thread stale"

    left_raw = int(boundary_state.get("left", 0))
    right_raw = int(boundary_state.get("right", 0))
    if left_raw <= 0 and right_raw <= 0:
        return False, "IR sensors not live"

    if not bool(imu_state.get("ok", False)):
        return False, "IMU not ready"

    if current_mode == MODE_1_SUMO and not bool(tof_state.get("ok", False)):
        return False, "ToF not ready"

    return True, ""


def sync_sensor_mode(current_mode):
    global sensor_mode_enabled, sensor_ready, sensor_ready_at_ms, sensor_wait_reason

    sensors_on = current_mode in (MODE_1_SUMO, MODE_2_TUG)
    if sensors_on == sensor_mode_enabled:
        return

    sensor_mode_enabled = sensors_on
    set_sensor_power(sensors_on)
    sensor_ready = False
    sensor_wait_reason = ""

    if sensors_on:
        sensor_ready_at_ms = time.ticks_add(time.ticks_ms(), SENSOR_SETTLE_MS)
    else:
        sensor_ready_at_ms = 0


def start_countdown_5s(mode):
    start_countdown_audio()

    for i in range(5, 0, -1):
        print("[MAIN] Starting in", i, "...")
        led.value(1)
        time.sleep(DELAY_ON_MS / 1000)
        led.value(0)
        time.sleep(DELAY_OFF_MS / 1000)

    stop_audio("COUNTDOWN_DONE")
    start_match_audio(mode)


def led_tick(current_mode):
    now = time.ticks_ms()
    phase = (now // 200) % 2

    if current_mode == MODE_PROGRAM:
        led.value(phase)
        return

    if not sensor_ready:
        led.value((now // 600) % 2)
        return

    if current_mode == MODE_1_SUMO:
        led.value(1 if phase else 0)
        return

    if current_mode == MODE_2_TUG:
        led.value(1 if ((now // 100) % 4) < 2 else 0)
        return

    led.value(0)


# ======================================================
# Setup
# ======================================================

print("=== ZillaBot Mode Codes ===")
print("[MAIN] BUILD:", BUILD_TAG)
print("MODE 0 PROGRAM")
print("MODE 1 SUMO")
print("MODE 2 TUG")
print("GP0 START -> required 5s visible countdown then run")

motors.stop()
setup_audio()
warm_audio()
init_control_pins()

mode = decode_switch()
if mode == "INVALID":
    mode = MODE_PROGRAM

sync_sensor_mode(mode)
print("[MAIN] Initial mode:", _mode_name(mode))


# ======================================================
# Main loop
# ======================================================

while True:
    now = time.ticks_ms()

    if sensor_mode_enabled:
        ready_now, wait_reason = sensor_status(mode, now)

        if sensor_ready and not ready_now:
            sensor_ready = False
            sensor_ready_at_ms = time.ticks_add(now, SENSOR_RECHECK_MS)
            if wait_reason and wait_reason != sensor_wait_reason:
                sensor_wait_reason = wait_reason
                print("[MAIN] Sensors lost / start blocked:", wait_reason)

        elif (not sensor_ready) and time.ticks_diff(now, sensor_ready_at_ms) >= 0:
            if ready_now:
                sensor_ready = True
                sensor_wait_reason = ""
                print("[MAIN] Sensors ready / start allowed")
            else:
                sensor_ready_at_ms = time.ticks_add(now, SENSOR_RECHECK_MS)
                if wait_reason and wait_reason != sensor_wait_reason:
                    sensor_wait_reason = wait_reason
                    print("[MAIN] Waiting on sensors:", wait_reason)
    else:
        sensor_ready = False
        sensor_wait_reason = ""

    sel = read_switch_debounced()
    if sel == "INVALID":
        pass
    elif sel in (MODE_PROGRAM, MODE_1_SUMO, MODE_2_TUG) and sel != mode:
        mode = sel
        sync_sensor_mode(mode)
        print("[MAIN] Mode changed to:", _mode_name(mode))
        if mode in (MODE_1_SUMO, MODE_2_TUG):
            warm_audio()

    s = btn_start.value()
    if s == 1 and last_start == 0:
        now_ms = time.ticks_ms()

        if time.ticks_diff(now_ms, last_start_ms) > int(DEBOUNCE_S * 1000):
            if mode == MODE_PROGRAM:
                print("[MAIN] START ignored (PROGRAM)")
            elif not sensor_ready:
                if sensor_wait_reason:
                    print("[MAIN] START ignored (" + sensor_wait_reason + ")")
                else:
                    print("[MAIN] START ignored (sensors not ready)")
            else:
                print("[MAIN] START pressed in mode:", _mode_name(mode))

                try:
                    request_imu_calibration()
                except Exception as e:
                    print("[MAIN] IMU calibration request failed:", repr(e))

                start_countdown_5s(mode)

                nav.set_mode(mode)
                gc.collect()

                if ENABLE_SENSOR_FILE_LOGGING:
                    start_file_logging("sensor_log.csv", period_ms=100)

                try:
                    nav.run_selected_mode()
                finally:
                    if ENABLE_SENSOR_FILE_LOGGING:
                        stop_file_logging()

                motors.stop()

            last_start_ms = now_ms

    last_start = s
    led_tick(mode)
    time.sleep(0.01)

