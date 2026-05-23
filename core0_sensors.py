# ======================================================
# core0_sensors.py
# ======================================================

import time
import _thread
import struct
from machine import ADC, I2C, Pin

import vl53l0x

from config import (
    IR_LEFT_ADC_PIN,
    IR_RIGHT_ADC_PIN,
    BOUNDARY_BLUE_THRESHOLD,
    ENABLE_SENSOR_FILE_LOGGING,
    TOF_POLL_MS,

    TUG_BLUE_L_THRESHOLD,
    TUG_BLUE_R_THRESHOLD,
    TUG_BLACK_THRESHOLD,
    TUG_LINE_COOLDOWN_MS,

    IMU_SDA,
    IMU_SCL,
    IMU_HEADING_FILTER,

    TOF_SDA,
    TOF_SCL,
    TOF_NAMES,
    TOF_XSHUT,
    TOF_ADDRESSES,
    TOF_ENABLED,
)

# ======================================================
# Shared state
# ======================================================

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

    "tug_blue_count": 0,
    "tug_last_blue_ms": 0,
}

imu_state = {
    "heading": 0.0,
    "gx_dps": 0.0,
    "gy_dps": 0.0,
    "gz_dps": 0.0,
    "turn_rate_dps": 0.0,
    "bias_x_dps": 0.0,
    "bias_y_dps": 0.0,
    "bias_z_dps": 0.0,
    "ok": False,
    "calibrate_requested": False,
    "calibrating": False,
}

tof_state = {
    "ok": False,
    "mm": [0] * len(TOF_NAMES),
    "min": 0,
}

sensor_runtime_state = {
    "enabled": False,
    "last_loop_ms": 0,
}

_started = False
_sensors_enabled = False

# ======================================================
# File logging state
# ======================================================

_log_enabled = False
_log_fp = None
_log_period_ms = 100
_log_last_ms = 0
_log_flush_every = 10
_log_rows_since_flush = 0

# ======================================================
# Retry / calibration timing
# ======================================================

IMU_RETRY_MS = 2000
TOF_RETRY_MS = 2000

IMU_CAL_SAMPLES = 120
IMU_CAL_DELAY_MS = 5

IMU_GYRO_DEADBAND_DPS = 0.5

# Pick which gyro axis represents bot turning.
# Try "z" first if the board is flat.
# If heading stays stuck, switch to "x" or "y".
HEADING_AXIS = "z"

# ======================================================
# Helpers
# ======================================================

def _angle_wrap_360(x):
    x %= 360
    if x < 0:
        x += 360
    return x


def request_imu_calibration():
    imu_state["calibrate_requested"] = True


def reset_imu_heading(new_heading=0):
    imu_state["heading"] = _angle_wrap_360(float(new_heading))


def _tof_shutdown_pins():
    try:
        for p in TOF_XSHUT:
            Pin(p, Pin.OUT).value(0)
    except Exception:
        pass


def set_sensor_power(enabled):
    global _sensors_enabled
    _sensors_enabled = bool(enabled)
    sensor_runtime_state["enabled"] = bool(enabled)

    if not _sensors_enabled:
        _tof_shutdown_pins()
        _clear_tof_mm(tof_state["mm"])
        tof_state["ok"] = False
        tof_state["min"] = 0

        imu_state["ok"] = False
        imu_state["heading"] = 0.0
        imu_state["gx_dps"] = 0.0
        imu_state["gy_dps"] = 0.0
        imu_state["gz_dps"] = 0.0
        imu_state["turn_rate_dps"] = 0.0
        imu_state["calibrate_requested"] = False
        imu_state["calibrating"] = False


def start_file_logging(filename="sensor_log.csv", period_ms=100):
    global _log_enabled, _log_fp, _log_period_ms, _log_last_ms, _log_rows_since_flush

    if not ENABLE_SENSOR_FILE_LOGGING:
        _log_enabled = False
        return False

    stop_file_logging()

    _log_period_ms = max(20, int(period_ms))
    _log_last_ms = 0
    _log_rows_since_flush = 0

    _log_fp = open(filename, "w")
    header = ["t_ms", "dt_ms", "hz", "ir_left", "ir_right"]
    for name in TOF_NAMES:
        header.append("tof_" + str(name).lower())
    _log_fp.write(",".join(header) + "\n")
    _log_fp.flush()

    _log_enabled = True
    print("[LOG] file logging started:", filename, "@", _log_period_ms, "ms")
    return True


def stop_file_logging():
    global _log_enabled, _log_fp, _log_rows_since_flush

    _log_enabled = False
    _log_rows_since_flush = 0

    if _log_fp is not None:
        try:
            _log_fp.flush()
        except:
            pass
        try:
            _log_fp.close()
        except:
            pass
        _log_fp = None

    print("[LOG] file logging stopped")

# ======================================================
# IMU Driver
# ======================================================

class LSM6DS3_GyroOnly:
    ADDR = 0x6A
    WHO_AM_I = 0x0F
    CTRL2_G = 0x11

    OUTX_L_G = 0x22
    OUTY_L_G = 0x24
    OUTZ_L_G = 0x26

    SENS = 0.00875

    def __init__(self, i2c):
        self.i2c = i2c
        self._write(self.CTRL2_G, 0x40)
        time.sleep(0.05)
        who = self._read(self.WHO_AM_I)
        print("[IMU] WHO_AM_I =", hex(who))

    def _read(self, reg):
        return self.i2c.readfrom_mem(self.ADDR, reg, 1)[0]

    def _write(self, reg, val):
        self.i2c.writeto_mem(self.ADDR, reg, bytes([val]))

    def read_gyro_xyz_dps_raw(self):
        data = self.i2c.readfrom_mem(self.ADDR, self.OUTX_L_G, 6)
        raw_x, raw_y, raw_z = struct.unpack("<hhh", data)
        return (
            raw_x * self.SENS,
            raw_y * self.SENS,
            raw_z * self.SENS,
        )

# ======================================================
# ToF setup
# ======================================================

def _tof_setup(i2c):
    if not (
        len(TOF_NAMES)
        == len(TOF_XSHUT)
        == len(TOF_ADDRESSES)
        == len(TOF_ENABLED)
    ):
        raise ValueError("ToF config length mismatch")

    xpins = [Pin(p, Pin.OUT) for p in TOF_XSHUT]

    for p in xpins:
        p.value(0)

    time.sleep(0.05)

    sensors = [None] * len(TOF_NAMES)

    for i, (name, p, addr, enabled) in enumerate(zip(TOF_NAMES, xpins, TOF_ADDRESSES, TOF_ENABLED)):
        if not enabled:
            continue

        p.value(1)
        time.sleep(0.08)

        try:
            s = vl53l0x.VL53L0X(i2c, address=0x29)
            s.set_address(addr)
            sensors[i] = s
        except Exception:
            # Drop failed or unused slots back into shutdown so they do not
            # stay alive on the default address and block later sensors.
            p.value(0)

        time.sleep(0.02)

    ready_count = 0
    for i, s in enumerate(sensors):
        if s is None:
            continue
        try:
            s.start()
            ready_count += 1
        except Exception:
            xpins[i].value(0)
            sensors[i] = None

    if ready_count <= 0:
        raise RuntimeError("No ToF sensors initialized")

    return sensors


def _select_heading_rate(gx, gy, gz):
    if HEADING_AXIS == "x":
        return gx
    if HEADING_AXIS == "y":
        return gy
    return gz


def _clear_tof_mm(mm):
    for i in range(len(mm)):
        mm[i] = 0


def _try_init_imu(do_idle_cal=True):
    try:
        i2c = I2C(1, scl=Pin(IMU_SCL), sda=Pin(IMU_SDA), freq=400000)
        imu = LSM6DS3_GyroOnly(i2c)
        imu_state["ok"] = True
        print("[IMU] init ok")

        if do_idle_cal:
            _calibrate_imu_bias(imu, reset_heading=False, label="idle calibration")

        return imu

    except Exception as e:
        print("[IMU] init failed:", e)
        imu_state["ok"] = False
        return None


def _try_init_tof():
    try:
        i2c = I2C(0, scl=Pin(TOF_SCL), sda=Pin(TOF_SDA), freq=400000)
        tof = _tof_setup(i2c)
        tof_state["ok"] = True
        active = [TOF_NAMES[i] for i, s in enumerate(tof) if s is not None]
        print("[ToF] ok, active:", active)
        return tof
    except Exception as e:
        print("[ToF] init failed:", e)
        tof_state["ok"] = False
        _clear_tof_mm(tof_state["mm"])
        tof_state["min"] = 0
        return []


def _calibrate_imu_bias(imu, reset_heading=True, label="calibration"):
    if imu is None or not imu_state["ok"]:
        print("[IMU] {} skipped (imu not ready)".format(label))
        imu_state["calibrate_requested"] = False
        imu_state["calibrating"] = False
        return

    print("[IMU] {} started".format(label))
    imu_state["calibrating"] = True

    total_x = 0.0
    total_y = 0.0
    total_z = 0.0
    count = 0

    try:
        for _ in range(IMU_CAL_SAMPLES):
            try:
                gx, gy, gz = imu.read_gyro_xyz_dps_raw()
                total_x += gx
                total_y += gy
                total_z += gz
                count += 1
            except Exception as e:
                print("[IMU] {} read failed:".format(label), e)
                imu_state["ok"] = False
                imu_state["calibrating"] = False
                imu_state["calibrate_requested"] = False
                return

            time.sleep_ms(IMU_CAL_DELAY_MS)

        if count > 0:
            imu_state["bias_x_dps"] = total_x / count
            imu_state["bias_y_dps"] = total_y / count
            imu_state["bias_z_dps"] = total_z / count
        else:
            imu_state["bias_x_dps"] = 0.0
            imu_state["bias_y_dps"] = 0.0
            imu_state["bias_z_dps"] = 0.0

        imu_state["gx_dps"] = 0.0
        imu_state["gy_dps"] = 0.0
        imu_state["gz_dps"] = 0.0
        imu_state["turn_rate_dps"] = 0.0

        if reset_heading:
            imu_state["heading"] = 0.0

        print(
            "[IMU] {} done | bias x/y/z =".format(label),
            imu_state["bias_x_dps"],
            imu_state["bias_y_dps"],
            imu_state["bias_z_dps"]
        )

    finally:
        imu_state["calibrating"] = False
        imu_state["calibrate_requested"] = False

# ======================================================
# Sensor thread
# ======================================================

def sensor_thread():
    global _log_last_ms, _log_rows_since_flush

    adc_left = ADC(IR_LEFT_ADC_PIN)
    adc_right = ADC(IR_RIGHT_ADC_PIN)

    imu = None
    tof = []

    last_imu_try_ms = time.ticks_add(time.ticks_ms(), -IMU_RETRY_MS)
    last_tof_try_ms = time.ticks_add(time.ticks_ms(), -TOF_RETRY_MS)
    last_tof_read_ms = time.ticks_add(time.ticks_ms(), -TOF_POLL_MS)

    imu_initialized_once = False
    sensors_were_enabled = False

    last_ms = time.ticks_ms()
    mm = tof_state["mm"]

    while True:
        now = time.ticks_ms()
        sensor_runtime_state["last_loop_ms"] = now
        sensor_runtime_state["enabled"] = bool(_sensors_enabled)

        dt_ms = time.ticks_diff(now, last_ms)
        dt = dt_ms / 1000 if dt_ms > 0 else 0.01
        last_ms = now

        if dt <= 0:
            dt = 0.01
            dt_ms = 10

        hz = 1000.0 / dt_ms if dt_ms > 0 else 0.0

        if not _sensors_enabled:
            if sensors_were_enabled:
                imu = None
                tof = []
                _tof_shutdown_pins()
                _clear_tof_mm(mm)
                tof_state["ok"] = False
                tof_state["min"] = 0

                imu_state["ok"] = False
                imu_state["heading"] = 0.0
                imu_state["gx_dps"] = 0.0
                imu_state["gy_dps"] = 0.0
                imu_state["gz_dps"] = 0.0
                imu_state["turn_rate_dps"] = 0.0
                imu_state["calibrating"] = False
                imu_state["calibrate_requested"] = False
                imu_initialized_once = False

            sensors_were_enabled = False
            time.sleep(0.01)
            continue

        if not sensors_were_enabled:
            last_imu_try_ms = time.ticks_add(now, -IMU_RETRY_MS)
            last_tof_try_ms = time.ticks_add(now, -TOF_RETRY_MS)
            last_tof_read_ms = time.ticks_add(now, -TOF_POLL_MS)
            sensors_were_enabled = True

        if (imu is None or not imu_state["ok"]) and time.ticks_diff(now, last_imu_try_ms) >= IMU_RETRY_MS:
            last_imu_try_ms = now
            imu = _try_init_imu(do_idle_cal=not imu_initialized_once)
            if imu is not None:
                imu_initialized_once = True

        if ((not tof) or (not tof_state["ok"])) and time.ticks_diff(now, last_tof_try_ms) >= TOF_RETRY_MS:
            last_tof_try_ms = now
            tof = _try_init_tof()
            if tof and tof_state["ok"]:
                last_tof_read_ms = time.ticks_add(now, -TOF_POLL_MS)

        if imu_state.get("calibrate_requested", False) and imu is not None and imu_state["ok"]:
            _calibrate_imu_bias(imu, reset_heading=True, label="button calibration")
            last_ms = time.ticks_ms()
            now = last_ms
            dt_ms = 10
            dt = 0.01
            hz = 100.0

        # IR
        left_raw = adc_left.read_u16()
        right_raw = adc_right.read_u16()

        boundary_state["left"] = left_raw
        boundary_state["right"] = right_raw

        boundary_state["left_sumo"] = (left_raw < BOUNDARY_BLUE_THRESHOLD)
        boundary_state["right_sumo"] = (right_raw < BOUNDARY_BLUE_THRESHOLD)

        left_dark = left_raw >= TUG_BLUE_L_THRESHOLD
        right_dark = right_raw >= TUG_BLUE_R_THRESHOLD

        boundary_state["left_tug"] = left_dark
        boundary_state["right_tug"] = right_dark

        left_black = left_raw >= TUG_BLACK_THRESHOLD
        right_black = right_raw >= TUG_BLACK_THRESHOLD

        boundary_state["left_black"] = left_black
        boundary_state["right_black"] = right_black

        boundary_state["left_blue"] = left_dark and not left_black
        boundary_state["right_blue"] = right_dark and not right_black

        # ToF
        if tof and tof_state["ok"]:
            if time.ticks_diff(now, last_tof_read_ms) >= TOF_POLL_MS:
                last_tof_read_ms = now
                any_valid = False
                min_valid = 0

                for i in range(len(mm)):
                    if i < len(tof) and tof[i] is not None:
                        try:
                            d = int(tof[i].read())
                        except Exception:
                            d = 0
                    else:
                        d = 0

                    mm[i] = d
                    if d > 0:
                        any_valid = True
                        if min_valid == 0 or d < min_valid:
                            min_valid = d

                if not any_valid:
                    print("[ToF] read failure -> marking not ok, will retry")
                    tof_state["ok"] = False
                    _clear_tof_mm(mm)
                    tof_state["min"] = 0
                    tof = []
                else:
                    tof_state["min"] = min_valid
        else:
            _clear_tof_mm(mm)
            tof_state["min"] = 0

        # IMU
        if imu and imu_state["ok"] and not imu_state.get("calibrating", False):
            try:
                gx_raw, gy_raw, gz_raw = imu.read_gyro_xyz_dps_raw()

                gx = gx_raw - imu_state["bias_x_dps"]
                gy = gy_raw - imu_state["bias_y_dps"]
                gz = gz_raw - imu_state["bias_z_dps"]

                if abs(gx) < IMU_GYRO_DEADBAND_DPS:
                    gx = 0.0
                if abs(gy) < IMU_GYRO_DEADBAND_DPS:
                    gy = 0.0
                if abs(gz) < IMU_GYRO_DEADBAND_DPS:
                    gz = 0.0

                prev_turn = imu_state["turn_rate_dps"]
                raw_turn = _select_heading_rate(gx, gy, gz)
                alpha = IMU_HEADING_FILTER
                turn = alpha * raw_turn + (1 - alpha) * prev_turn

                imu_state["gx_dps"] = gx
                imu_state["gy_dps"] = gy
                imu_state["gz_dps"] = gz
                imu_state["turn_rate_dps"] = turn
                imu_state["heading"] = _angle_wrap_360(
                    imu_state["heading"] + turn * dt
                )

            except Exception as e:
                print("[IMU] read failure -> marking not ok, will retry:", e)
                imu_state["ok"] = False
                imu = None

        # File log
        if _log_enabled and _log_fp is not None:
            if _log_last_ms == 0 or time.ticks_diff(now, _log_last_ms) >= _log_period_ms:
                _log_last_ms = now

                try:
                    _log_fp.write(
                        "{},{},{:.2f},{},{},{},{},{},{},{}\n".format(
                            now,
                            dt_ms,
                            hz,
                            left_raw,
                            right_raw,
                            mm[0], mm[1], mm[2], mm[3], mm[4]
                        )
                    )

                    _log_rows_since_flush += 1
                    if _log_rows_since_flush >= _log_flush_every:
                        _log_fp.flush()
                        _log_rows_since_flush = 0

                except Exception as e:
                    print("[LOG] write failed:", e)
                    stop_file_logging()

        time.sleep(0.01)


def start_sensor_core():
    global _started

    if _started:
        return boundary_state, imu_state, tof_state

    _started = True
    _thread.start_new_thread(sensor_thread, ())
    return boundary_state, imu_state, tof_state

