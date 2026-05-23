# ======================================================
# core1_navigation.py
# ZillaBot V3 - Navigation (SUMO + TUG)
# ======================================================

import time
import core0_motor as motors
from core0_sensors import boundary_state, imu_state, tof_state

from config import (
    MODE_1_SUMO,
    MODE_2_TUG,
    ENABLE_NAV_DEBUG_PRINTS,

    STATE_SEARCH,
    STATE_AVOID,
    STATE_PURSUE,

    SEARCH_SPEED,
    AVOID_REVERSE_SPEED,
    AVOID_REVERSE_TIME,
    IMU_TURN_SPEED,

    HUNT_BASE_SPEED,
    HUNT_ATTACK_SPEED,
    HUNT_ALIGN_SPEED,
    HUNT_BURST_SPEED,
    HUNT_ATTACK_RAMP_MM,
    HUNT_BURST_DIST_MM,
    HUNT_CENTER_LOCK_MS,
    HUNT_BURST_MS,
    SUMO_EDGE_CONFIRM_MS,
    SUMO_STALEMATE_DIST_MM,
    SUMO_STALEMATE_DELTA_MM,
    SUMO_STALEMATE_MS,
    SUMO_SHOULDER_BREAK_INNER_SPEED,
    SUMO_SHOULDER_BREAK_OUTER_SPEED,
    SUMO_SHOULDER_BREAK_MS,
    SUMO_SHOULDER_BREAK_MAX_DEG,
    SUMO_SHOULDER_BIAS_MM,

    TUG_BASE_SPEED,
    TUG_HEADING_KP,
    TUG_MAX_CORRECTION,
    TUG_HEADING_DEADBAND_DEG,
    TUG_CORRECTION_SMOOTHING,
    TUG_BOTH_DARK_CONFIRM_MS,
    TUG_ONE_SIDE_CONFIRM_MS,
    TUG_ONE_SIDE_RECOVER,
    TUG_EDGE_RECOVERY_BIAS,
    TUG_TOTAL_TIMEOUT_S,
    TUG_ARM_CLEAR_MS,
    TUG_EDGE_BACKOFF_S,
    TUG_EDGE_BACKOFF_SPEED,
    TOF_NAMES,
)

# ======================================================
# Turn config
# ======================================================

TURN_TOLERANCE = 5.0
TURN_TIMEOUT_S = 3.5
TURN_MIN_MS = 120
IMU_TURN_SIGN = 1

# ======================================================
# SUMO tuning
# ======================================================

PRINT_MS = 200
EDGE_CONFIRM_MS = SUMO_EDGE_CONFIRM_MS
AVOID_TURN_DEG_LEFT_EDGE  = +60.0
AVOID_TURN_DEG_RIGHT_EDGE = -60.0
AVOID_TURN_DEG_BOTH_EDGE  = +60.0

POST_AVOID_FORWARD_MS = 300
POST_AVOID_IGNORE_EDGE_MS = 180
POST_AVOID_IGNORE_TOF_MS  = 300

CMD_EPSILON = 0.02

# ======================================================
# Pursue behavior tuning
# ======================================================

SIDE_PIVOT_DIST_MM = 150
PURSUE_45_INNER_SCALE_FAR = 0.45

# ======================================================
# ToF mapping
# ======================================================

TOF_MAX_MM = 600
TOF_MIN_VALID_MM = 1
TOF_INVALID_MIN = 8000
TOF_REVERSED = False

# ======================================================
# Globals
# ======================================================

current_mode = None
_last_left_cmd = None
_last_right_cmd = None

# callback for active-run telemetry
_RUN_TELEM_CB = None

# ======================================================
# Live navigation telemetry state
# ======================================================

nav_state = {
    "mode": "",
    "state": 0,
    "state_name": "IDLE",
    "best_i": -1,
    "best_name": "",
    "best_d": 0,
    "edge_left": 0,
    "edge_right": 0,
    "heading": 0.0,
    "target_heading": 0.0,
    "heading_error": 0.0,
    "tof": [0] * len(TOF_NAMES),
}


def _nav_debug(*args):
    if ENABLE_NAV_DEBUG_PRINTS:
        print(*args)


def _copy_tof(dest, src):
    src_len = len(src)
    for i in range(len(dest)):
        dest[i] = src[i] if i < src_len else 0

def set_run_telemetry_callback(cb):
    global _RUN_TELEM_CB
    _RUN_TELEM_CB = cb

def _run_telem_tick():
    if _RUN_TELEM_CB:
        try:
            _RUN_TELEM_CB()
        except Exception:
            pass

def _nav_reset(mode_name=""):
    tof_mm = tof_state.get("mm", [0] * len(TOF_NAMES))
    nav_state["mode"] = mode_name
    nav_state["state"] = 0
    nav_state["state_name"] = "IDLE"
    nav_state["best_i"] = -1
    nav_state["best_name"] = ""
    nav_state["best_d"] = 0
    nav_state["edge_left"] = 0
    nav_state["edge_right"] = 0
    nav_state["heading"] = float(imu_state.get("heading", 0.0))
    nav_state["target_heading"] = 0.0
    nav_state["heading_error"] = 0.0
    _copy_tof(nav_state["tof"], tof_mm)

def _nav_update(
    mode_name=None,
    state=None,
    state_name=None,
    best_i=None,
    best_name=None,
    best_d=None,
    edge_left=None,
    edge_right=None,
    heading=None,
    target_heading=None,
    heading_error=None,
    tof=None,
):
    if mode_name is not None:
        nav_state["mode"] = mode_name
    if state is not None:
        nav_state["state"] = state
    if state_name is not None:
        nav_state["state_name"] = state_name
    if best_i is not None:
        nav_state["best_i"] = best_i
    if best_name is not None:
        nav_state["best_name"] = best_name
    if best_d is not None:
        nav_state["best_d"] = best_d
    if edge_left is not None:
        nav_state["edge_left"] = 1 if edge_left else 0
    if edge_right is not None:
        nav_state["edge_right"] = 1 if edge_right else 0
    if heading is not None:
        nav_state["heading"] = float(heading)
    if target_heading is not None:
        nav_state["target_heading"] = float(target_heading)
    if heading_error is not None:
        nav_state["heading_error"] = float(heading_error)
    if tof is not None:
        _copy_tof(nav_state["tof"], tof)

# ======================================================
# Basic helpers
# ======================================================

def set_mode(mode):
    global current_mode
    current_mode = mode

def _angle_error(target, current):
    return ((target - current + 180) % 360) - 180

def _clamp01(x):
    return 0 if x < 0 else 1 if x > 1 else x

def _ticks_ms():
    return time.ticks_ms()

def _ticks_diff(a, b):
    return time.ticks_diff(a, b)

# ======================================================
# Motor helpers
# ======================================================

def _drive_lr(left, right):
    global _last_left_cmd, _last_right_cmd

    if _last_left_cmd is not None and _last_right_cmd is not None:
        if abs(left - _last_left_cmd) < CMD_EPSILON and abs(right - _last_right_cmd) < CMD_EPSILON:
            return

    motors.set_wheels(left, right)
    _last_left_cmd = left
    _last_right_cmd = right

def _stop():
    global _last_left_cmd, _last_right_cmd
    motors.stop()
    _last_left_cmd = None
    _last_right_cmd = None

def _forward(speed):
    _drive_lr(speed, speed)

def _reverse(speed):
    _drive_lr(-speed, -speed)

def _spin_left(speed):
    _drive_lr(-speed, +speed)

def _spin_right(speed):
    _drive_lr(+speed, -speed)

# ======================================================
# IMU turn
# ======================================================

def imu_turn(angle_deg):
    start = float(imu_state.get("heading", 0.0))
    target = (start + angle_deg) % 360.0
    t0 = time.ticks_ms()
    last_dbg = t0

    _nav_update(
        state=STATE_AVOID,
        state_name="TURN",
        heading=start,
        target_heading=target,
        heading_error=_angle_error(target, start),
        tof=_tof_readings(),
    )

    _nav_debug("[TURN] start:", start, "angle:", angle_deg, "target:", target)

    while True:
        now = time.ticks_ms()
        _run_telem_tick()

        if time.ticks_diff(now, t0) > int(TURN_TIMEOUT_S * 1000):
            _nav_debug("[TURN] timeout")
            break

        current = float(imu_state.get("heading", 0.0))
        err = _angle_error(target, current)

        _nav_update(
            state=STATE_AVOID,
            state_name="TURN",
            heading=current,
            target_heading=target,
            heading_error=err,
            tof=_tof_readings(),
        )

        if abs(err) <= TURN_TOLERANCE and time.ticks_diff(now, t0) >= TURN_MIN_MS:
            _nav_debug("[TURN] done | current:", current, "| err:", err)
            break

        if err * IMU_TURN_SIGN > 0:
            _spin_left(IMU_TURN_SPEED)
        else:
            _spin_right(IMU_TURN_SPEED)

        if time.ticks_diff(now, last_dbg) >= 100:
            last_dbg = now
            _nav_debug(
                "[TURN] current:", current,
                "| target:", target,
                "| err:", err,
                "| turn:", float(imu_state.get("turn_rate_dps", 0.0))
            )

        time.sleep(0.01)

    _stop()

# ======================================================
# ToF helpers
# ======================================================

def _tof_readings():
    mm = tof_state.get("mm", [0] * len(TOF_NAMES))
    if TOF_REVERSED:
        mm = list(reversed(mm))
    return mm

def _tof_best():
    mm = _tof_readings()
    best_i = None
    best_d = None

    for i, d in enumerate(mm):
        if d <= 0:
            continue
        if d < TOF_MIN_VALID_MM:
            continue
        if d >= TOF_INVALID_MIN:
            continue
        if d > TOF_MAX_MM:
            continue

        if best_d is None or d < best_d:
            best_d = d
            best_i = i

    return best_i, best_d, mm

# ======================================================
# Boundary helpers
# ======================================================

def _edge_code():
    left_edge = bool(boundary_state.get("left_sumo", False))
    right_edge = bool(boundary_state.get("right_sumo", False))

    if left_edge and right_edge:
        return 2, left_edge, right_edge
    if left_edge:
        return -1, left_edge, right_edge
    if right_edge:
        return +1, left_edge, right_edge

    return 0, left_edge, right_edge

def _edge_turn_angle(edge_code):
    if edge_code == -1:
        return AVOID_TURN_DEG_LEFT_EDGE
    if edge_code == +1:
        return AVOID_TURN_DEG_RIGHT_EDGE
    return AVOID_TURN_DEG_BOTH_EDGE

# ======================================================
# SUMO steering helpers
# ======================================================

def _pursue_left(best_i, best_d):
    if best_i == 0:
        _spin_left(HUNT_ALIGN_SPEED)
        return

    if best_d is not None and best_d <= SIDE_PIVOT_DIST_MM:
        _spin_left(HUNT_ALIGN_SPEED)
    else:
        inner = HUNT_ALIGN_SPEED * PURSUE_45_INNER_SCALE_FAR
        _drive_lr(inner, HUNT_ALIGN_SPEED)

def _pursue_right(best_i, best_d):
    if best_i == 4:
        _spin_right(HUNT_ALIGN_SPEED)
        return

    if best_d is not None and best_d <= SIDE_PIVOT_DIST_MM:
        _spin_right(HUNT_ALIGN_SPEED)
    else:
        inner = HUNT_ALIGN_SPEED * PURSUE_45_INNER_SCALE_FAR
        _drive_lr(HUNT_ALIGN_SPEED, inner)


def _center_attack_profile(best_d, burst_active):
    if burst_active:
        return HUNT_BURST_SPEED, "ATTACK_BURST"

    if best_d is None or best_d <= 0:
        return HUNT_BASE_SPEED, "CENTER_TRACK"

    if best_d <= HUNT_BURST_DIST_MM:
        return HUNT_ATTACK_SPEED, "ATTACK"

    if best_d >= HUNT_ATTACK_RAMP_MM:
        return HUNT_BASE_SPEED, "CENTER_FAR"

    span = HUNT_ATTACK_RAMP_MM - HUNT_BURST_DIST_MM
    if span <= 0:
        return HUNT_ATTACK_SPEED, "ATTACK"

    closeness = float(HUNT_ATTACK_RAMP_MM - best_d) / float(span)
    speed = HUNT_BASE_SPEED + ((HUNT_ATTACK_SPEED - HUNT_BASE_SPEED) * closeness)
    return speed, "CENTER_TRACK"


def _choose_shoulder_break_side(mm, last_side):
    left45 = mm[1] if len(mm) > 1 else 0
    right45 = mm[3] if len(mm) > 3 else 0

    left_ok = (left45 >= TOF_MIN_VALID_MM) and (left45 < TOF_INVALID_MIN) and (left45 <= TOF_MAX_MM)
    right_ok = (right45 >= TOF_MIN_VALID_MM) and (right45 < TOF_INVALID_MIN) and (right45 <= TOF_MAX_MM)

    if left_ok and right_ok:
        if abs(left45 - right45) >= SUMO_SHOULDER_BIAS_MM:
            return -1 if left45 < right45 else +1
    elif left_ok:
        return -1
    elif right_ok:
        return +1

    if last_side == 0:
        return -1
    return -last_side


def _begin_shoulder_break(now, mm, last_side):
    side = _choose_shoulder_break_side(mm, last_side)
    heading_now = float(imu_state.get("heading", 0.0))
    delta = SUMO_SHOULDER_BREAK_MAX_DEG if side < 0 else -SUMO_SHOULDER_BREAK_MAX_DEG
    target_heading = (heading_now + delta) % 360.0
    until = time.ticks_add(now, SUMO_SHOULDER_BREAK_MS)
    return side, target_heading, until


def _apply_shoulder_break(side):
    if side < 0:
        _drive_lr(SUMO_SHOULDER_BREAK_INNER_SPEED, SUMO_SHOULDER_BREAK_OUTER_SPEED)
    else:
        _drive_lr(SUMO_SHOULDER_BREAK_OUTER_SPEED, SUMO_SHOULDER_BREAK_INNER_SPEED)

# ======================================================
# MODE 1 — SUMO
# ======================================================

def run_mode_1_sumo():
    _nav_debug("[MODE 1] SUMO forward search + turn-priority pursue + attack + boundary")
    _nav_reset("SUMO")

    last_print = 0
    state = STATE_SEARCH

    edge_candidate = 0
    edge_candidate_since = 0

    force_forward_until = 0
    ignore_edge_until = 0
    ignore_tof_until = 0
    center_lock_started_ms = None
    center_burst_fired = False
    burst_until = 0
    center_stall_since_ms = None
    center_stall_last_d = None
    shoulder_break_side = 0
    shoulder_break_heading = 0.0
    shoulder_break_until = 0
    last_shoulder_break_side = +1

    while True:
        now = _ticks_ms()
        _run_telem_tick()

        if _ticks_diff(force_forward_until, now) > 0:
            left_edge = bool(boundary_state.get("left_sumo", False))
            right_edge = bool(boundary_state.get("right_sumo", False))

            # Abort the blind recovery shove immediately if the line reappears.
            if left_edge or right_edge:
                force_forward_until = 0
                ignore_edge_until = 0
                ignore_tof_until = 0
            else:
                state = STATE_SEARCH
                state_name = "SEARCH_RECOVER"
                _forward(SEARCH_SPEED)

                mm = _tof_readings()

                _nav_update(
                    mode_name="SUMO",
                    state=state,
                    state_name=state_name,
                    best_i=-1,
                    best_name="",
                    best_d=0,
                    edge_left=left_edge,
                    edge_right=right_edge,
                    heading=float(imu_state.get("heading", 0.0)),
                    tof=mm,
                )

                if _ticks_diff(now, last_print) > PRINT_MS:
                    last_print = now
                    _nav_debug("State:", state_name, "| ToF:", mm, "| Edge:", int(left_edge), int(right_edge))

                time.sleep(0.01)
                continue

        left_edge = bool(boundary_state.get("left_sumo", False))
        right_edge = bool(boundary_state.get("right_sumo", False))

        if _ticks_diff(ignore_edge_until, now) > 0:
            edge_now = 0
        else:
            edge_now, left_edge, right_edge = _edge_code()

        if edge_now != 0:
            if edge_candidate != edge_now:
                edge_candidate = edge_now
                edge_candidate_since = now
                center_lock_started_ms = None
                center_burst_fired = False
                burst_until = 0
                center_stall_since_ms = None
                center_stall_last_d = None
                shoulder_break_side = 0

                state = STATE_AVOID
                state_name = "EDGE_BRAKE"
                mm = _tof_readings()
                _stop()
                _nav_update(
                    mode_name="SUMO",
                    state=state,
                    state_name=state_name,
                    best_i=-1,
                    best_name="",
                    best_d=0,
                    edge_left=left_edge,
                    edge_right=right_edge,
                    heading=float(imu_state.get("heading", 0.0)),
                    tof=mm,
                )
                time.sleep(0.01)
                continue
            else:
                if _ticks_diff(now, edge_candidate_since) >= EDGE_CONFIRM_MS:
                    _nav_debug("[SUMO] EDGE CONFIRMED! reversing + turn")

                    state = STATE_AVOID

                    _nav_update(
                        mode_name="SUMO",
                        state=state,
                        state_name="AVOID",
                        best_i=-1,
                        best_name="",
                        best_d=0,
                        edge_left=left_edge,
                        edge_right=right_edge,
                        heading=float(imu_state.get("heading", 0.0)),
                        tof=tof_state.get("mm", [0] * len(TOF_NAMES)),
                    )

                    _reverse(abs(AVOID_REVERSE_SPEED))
                    time.sleep(AVOID_REVERSE_TIME)
                    _stop()

                    imu_turn(_edge_turn_angle(edge_candidate))

                    now = _ticks_ms()
                    force_forward_until = time.ticks_add(now, POST_AVOID_FORWARD_MS)
                    ignore_edge_until = time.ticks_add(now, POST_AVOID_IGNORE_EDGE_MS)
                    ignore_tof_until = time.ticks_add(now, POST_AVOID_IGNORE_TOF_MS)
                    center_lock_started_ms = None
                    center_burst_fired = False
                    burst_until = 0
                    center_stall_since_ms = None
                    center_stall_last_d = None
                    shoulder_break_side = 0

                    edge_candidate = 0
                    edge_candidate_since = 0

                    _nav_debug("[SUMO] avoid finished")
                    time.sleep(0.02)
                    continue

                state = STATE_AVOID
                state_name = "EDGE_BRAKE"
                mm = _tof_readings()
                _stop()
                _nav_update(
                    mode_name="SUMO",
                    state=state,
                    state_name=state_name,
                    best_i=-1,
                    best_name="",
                    best_d=0,
                    edge_left=left_edge,
                    edge_right=right_edge,
                    heading=float(imu_state.get("heading", 0.0)),
                    tof=mm,
                )
                time.sleep(0.01)
                continue
        else:
            edge_candidate = 0
            edge_candidate_since = 0

        if _ticks_diff(ignore_tof_until, now) > 0:
            best_i = None
            best_d = None
            mm = _tof_readings()
        else:
            best_i, best_d, mm = _tof_best()

        shoulder_break_active = False
        if shoulder_break_side != 0:
            heading_err = _angle_error(shoulder_break_heading, float(imu_state.get("heading", 0.0)))
            if (_ticks_diff(shoulder_break_until, now) > 0) and (abs(heading_err) > TURN_TOLERANCE):
                shoulder_break_active = True
            else:
                shoulder_break_side = 0

        if shoulder_break_active:
            center_lock_started_ms = None
            center_burst_fired = False
            burst_until = 0
            center_stall_since_ms = None
            center_stall_last_d = None
            state = STATE_PURSUE
            state_name = "SHOULDER_BREAK_L" if shoulder_break_side < 0 else "SHOULDER_BREAK_R"
            _apply_shoulder_break(shoulder_break_side)

        elif best_i is None:
            center_lock_started_ms = None
            center_burst_fired = False
            burst_until = 0
            center_stall_since_ms = None
            center_stall_last_d = None
            state = STATE_SEARCH
            state_name = "SEARCH"
            _forward(SEARCH_SPEED)

        elif best_i in (0, 1):
            center_lock_started_ms = None
            center_burst_fired = False
            burst_until = 0
            center_stall_since_ms = None
            center_stall_last_d = None
            state = STATE_PURSUE
            state_name = "PURSUE_LEFT"
            _pursue_left(best_i, best_d)

        elif best_i == 2:
            close_center = (
                (best_d is not None)
                and (best_d > 0)
                and (best_d <= HUNT_BURST_DIST_MM)
            )
            stall_candidate = (
                (best_d is not None)
                and (best_d > 0)
                and (best_d <= SUMO_STALEMATE_DIST_MM)
            )

            started_shoulder_break = False
            if stall_candidate:
                if (
                    center_stall_since_ms is None
                    or center_stall_last_d is None
                    or abs(best_d - center_stall_last_d) > SUMO_STALEMATE_DELTA_MM
                ):
                    center_stall_since_ms = now
                elif time.ticks_diff(now, center_stall_since_ms) >= SUMO_STALEMATE_MS:
                    shoulder_break_side, shoulder_break_heading, shoulder_break_until = _begin_shoulder_break(
                        now, mm, last_shoulder_break_side
                    )
                    last_shoulder_break_side = shoulder_break_side
                    center_lock_started_ms = None
                    center_burst_fired = False
                    burst_until = 0
                    center_stall_since_ms = None
                    center_stall_last_d = None
                    state = STATE_PURSUE
                    state_name = "SHOULDER_BREAK_L" if shoulder_break_side < 0 else "SHOULDER_BREAK_R"
                    _apply_shoulder_break(shoulder_break_side)
                    started_shoulder_break = True

                center_stall_last_d = best_d
            else:
                center_stall_since_ms = None
                center_stall_last_d = None

            if started_shoulder_break:
                pass
            else:
                if close_center:
                    if center_lock_started_ms is None:
                        center_lock_started_ms = now
                else:
                    center_lock_started_ms = None

                burst_active = (_ticks_diff(burst_until, now) > 0)
                if (
                    close_center
                    and (center_lock_started_ms is not None)
                    and (time.ticks_diff(now, center_lock_started_ms) >= HUNT_CENTER_LOCK_MS)
                    and (not center_burst_fired)
                ):
                    burst_until = time.ticks_add(now, HUNT_BURST_MS)
                    center_burst_fired = True
                    burst_active = True

                state = 5
                attack_speed, state_name = _center_attack_profile(best_d, burst_active)
                _forward(attack_speed)

        elif best_i in (3, 4):
            center_lock_started_ms = None
            center_burst_fired = False
            burst_until = 0
            center_stall_since_ms = None
            center_stall_last_d = None
            state = STATE_PURSUE
            state_name = "PURSUE_RIGHT"
            _pursue_right(best_i, best_d)

        else:
            center_lock_started_ms = None
            center_burst_fired = False
            burst_until = 0
            center_stall_since_ms = None
            center_stall_last_d = None
            state = STATE_SEARCH
            state_name = "SEARCH"
            _forward(SEARCH_SPEED)

        _nav_update(
            mode_name="SUMO",
            state=state,
            state_name=state_name,
            best_i=-1 if best_i is None else best_i,
            best_name="" if best_i is None else TOF_NAMES[best_i],
            best_d=0 if best_d is None else best_d,
            edge_left=left_edge,
            edge_right=right_edge,
            heading=float(imu_state.get("heading", 0.0)),
            target_heading=0.0,
            heading_error=0.0,
            tof=mm,
        )

        if _ticks_diff(now, last_print) > PRINT_MS:
            last_print = now
            name = "NONE" if best_i is None else TOF_NAMES[best_i]
            dist = 0 if best_d is None else best_d
            _nav_debug(
                "State:", state_name,
                "| ToF:", mm,
                "| Best:", name,
                "| Dist:", dist,
                "| Edge:", int(left_edge), int(right_edge),
                "| Heading:", float(imu_state.get("heading", 0.0))
            )

        time.sleep(0.01)

# ======================================================
# MODE 2 — TUG
# ======================================================

def run_mode_2_tug_once():
    _nav_debug("[MODE 2] TUG starting")
    _nav_reset("TUG")

    start_ms = time.ticks_ms()
    target_heading = float(imu_state.get("heading", 0))
    _nav_debug("[TUG] target heading:", target_heading)

    both_dark_since = None
    one_dark_since = None
    filtered_correction = 0.0

    while True:
        now = time.ticks_ms()
        _run_telem_tick()

        if time.ticks_diff(now, start_ms) / 1000 > TUG_TOTAL_TIMEOUT_S:
            _nav_debug("[TUG] timeout")
            _nav_update(
                mode_name="TUG",
                state=0,
                state_name="TIMEOUT",
                heading=float(imu_state.get("heading", 0.0)),
                target_heading=target_heading,
                heading_error=_angle_error(target_heading, float(imu_state.get("heading", 0.0))),
                tof=_tof_readings(),
            )
            _stop()
            return

        left_dark = bool(boundary_state.get("left_tug", False))
        right_dark = bool(boundary_state.get("right_tug", False))

        if left_dark and right_dark:
            if both_dark_since is None:
                both_dark_since = now
            elif time.ticks_diff(now, both_dark_since) >= TUG_BOTH_DARK_CONFIRM_MS:
                _nav_debug("[TUG] sustained both-dark -> STOP")
                _nav_update(
                    mode_name="TUG",
                    state=0,
                    state_name="STOP_BOTH_DARK",
                    edge_left=left_dark,
                    edge_right=right_dark,
                    heading=float(imu_state.get("heading", 0.0)),
                    target_heading=target_heading,
                    heading_error=_angle_error(target_heading, float(imu_state.get("heading", 0.0))),
                    tof=_tof_readings(),
                )
                _stop()
                return
        else:
            both_dark_since = None

        edge_recover = 0.0
        state_name = "HEADING_HOLD"

        if left_dark ^ right_dark:
            if one_dark_since is None:
                one_dark_since = now
            elif time.ticks_diff(now, one_dark_since) >= TUG_ONE_SIDE_CONFIRM_MS:
                if TUG_ONE_SIDE_RECOVER:
                    if left_dark:
                        edge_recover = -abs(TUG_EDGE_RECOVERY_BIAS)
                        state_name = "RECOVER_RIGHT"
                    else:
                        edge_recover = abs(TUG_EDGE_RECOVERY_BIAS)
                        state_name = "RECOVER_LEFT"
                else:
                    _nav_debug("[TUG] sustained one-side dark -> STOP")
                    _nav_update(
                        mode_name="TUG",
                        state=0,
                        state_name="STOP_ONE_DARK",
                        edge_left=left_dark,
                        edge_right=right_dark,
                        heading=float(imu_state.get("heading", 0.0)),
                        target_heading=target_heading,
                        heading_error=_angle_error(target_heading, float(imu_state.get("heading", 0.0))),
                        tof=_tof_readings(),
                    )
                    _stop()
                    return
        else:
            one_dark_since = None

        current = float(imu_state.get("heading", 0))
        err = _angle_error(target_heading, current)
        if abs(err) <= TUG_HEADING_DEADBAND_DEG:
            err = 0.0

        desired_correction = (TUG_HEADING_KP * err) + edge_recover
        desired_correction = max(-TUG_MAX_CORRECTION, min(TUG_MAX_CORRECTION, desired_correction))

        smoothing = TUG_CORRECTION_SMOOTHING
        if smoothing < 0:
            smoothing = 0
        elif smoothing > 1:
            smoothing = 1

        filtered_correction += (desired_correction - filtered_correction) * smoothing
        correction = max(-TUG_MAX_CORRECTION, min(TUG_MAX_CORRECTION, filtered_correction))

        left_cmd = _clamp01(TUG_BASE_SPEED - correction)
        right_cmd = _clamp01(TUG_BASE_SPEED + correction)

        _drive_lr(left_cmd, right_cmd)

        _nav_update(
            mode_name="TUG",
            state=0,
            state_name=state_name,
            best_i=-1,
            best_name="",
            best_d=0,
            edge_left=left_dark,
            edge_right=right_dark,
            heading=current,
            target_heading=target_heading,
            heading_error=err,
            tof=_tof_readings(),
        )

        _nav_debug(
            "[TUG] dark:", int(left_dark), int(right_dark),
            "| heading:", current,
            "| err:", err,
            "| corr:", correction,
            "| edge:", edge_recover,
        )

        time.sleep(0.01)

# ======================================================
# Dispatcher
# ======================================================

def run_selected_mode():
    if current_mode == MODE_1_SUMO:
        run_mode_1_sumo()
        return

    if current_mode == MODE_2_TUG:
        run_mode_2_tug_once()
        return

    _nav_reset("")
    _stop()


