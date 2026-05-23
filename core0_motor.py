from machine import Pin, PWM
from config import (
    LEFT_MOTOR_PWM,
    LEFT_MOTOR_IN1,
    LEFT_MOTOR_IN2,
    RIGHT_MOTOR_PWM,
    RIGHT_MOTOR_IN1,
    RIGHT_MOTOR_IN2,
)

# ======================================================
# MOTOR DRIVER: TB6612FNG
# ======================================================

# Calibration
MIN_DUTY = 0.22
DEADBAND = 0.05

LEFT_GAIN = 1.00
RIGHT_GAIN = 1.00

# ======================================================
# Telemetry-visible motor state
# Values are normalized command values in range -1.0 .. +1.0
# ======================================================

motor_state = {
    "left_cmd": 0.0,
    "right_cmd": 0.0,
    "move_cmd": 0.0,
    "active": False,
}

# ======================================================
# PWM setup
# ======================================================

pwm_left = PWM(Pin(LEFT_MOTOR_PWM))
pwm_right = PWM(Pin(RIGHT_MOTOR_PWM))

pwm_left.freq(20000)
pwm_right.freq(20000)

# ======================================================
# Direction pins
# ======================================================

ain1 = Pin(LEFT_MOTOR_IN1, Pin.OUT)
ain2 = Pin(LEFT_MOTOR_IN2, Pin.OUT)
bin1 = Pin(RIGHT_MOTOR_IN1, Pin.OUT)
bin2 = Pin(RIGHT_MOTOR_IN2, Pin.OUT)

# Safety off on import
ain1.value(0)
ain2.value(0)
bin1.value(0)
bin2.value(0)

pwm_left.duty_u16(0)
pwm_right.duty_u16(0)

# ======================================================
# Helpers
# ======================================================

def _clamp_cmd(x):
    x = float(x)
    if x > 1.0:
        return 1.0
    if x < -1.0:
        return -1.0
    return x


def _update_motor_state(left_cmd, right_cmd):
    left_cmd = _clamp_cmd(left_cmd)
    right_cmd = _clamp_cmd(right_cmd)

    motor_state["left_cmd"] = left_cmd
    motor_state["right_cmd"] = right_cmd
    motor_state["move_cmd"] = (left_cmd + right_cmd) / 2.0
    motor_state["active"] = (abs(left_cmd) > 0.001 or abs(right_cmd) > 0.001)


def _set_speed(pwm, speed):
    speed = float(speed)
    speed = max(0.0, min(1.0, speed))

    if speed < DEADBAND:
        speed = 0.0
    elif speed < MIN_DUTY:
        speed = MIN_DUTY

    pwm.duty_u16(int(65535 * speed))


# ======================================================
# Basic drive functions
# ======================================================

def stop():
    _set_speed(pwm_left, 0)
    _set_speed(pwm_right, 0)

    ain1.value(0)
    ain2.value(0)
    bin1.value(0)
    bin2.value(0)

    _update_motor_state(0.0, 0.0)


def forward(speed):
    speed = _clamp_cmd(speed)

    ain1.value(1)
    ain2.value(0)
    bin1.value(1)
    bin2.value(0)

    _set_speed(pwm_left, speed * LEFT_GAIN)
    _set_speed(pwm_right, speed * RIGHT_GAIN)

    _update_motor_state(speed, speed)


def reverse(speed):
    speed = abs(_clamp_cmd(speed))

    ain1.value(0)
    ain2.value(1)
    bin1.value(0)
    bin2.value(1)

    _set_speed(pwm_left, speed * LEFT_GAIN)
    _set_speed(pwm_right, speed * RIGHT_GAIN)

    _update_motor_state(-speed, -speed)


def turn_left(speed):
    speed = abs(_clamp_cmd(speed))

    ain1.value(0)
    ain2.value(1)
    bin1.value(1)
    bin2.value(0)

    _set_speed(pwm_left, speed * LEFT_GAIN)
    _set_speed(pwm_right, speed * RIGHT_GAIN)

    _update_motor_state(-speed, speed)


def turn_right(speed):
    speed = abs(_clamp_cmd(speed))

    ain1.value(1)
    ain2.value(0)
    bin1.value(0)
    bin2.value(1)

    _set_speed(pwm_left, speed * LEFT_GAIN)
    _set_speed(pwm_right, speed * RIGHT_GAIN)

    _update_motor_state(speed, -speed)


# ======================================================
# Independent wheel control
# left_speed, right_speed in range -1.0 .. +1.0
# ======================================================

def set_wheels(left_speed, right_speed):
    left_speed = _clamp_cmd(left_speed)
    right_speed = _clamp_cmd(right_speed)

    # LEFT
    if left_speed >= 0:
        ain1.value(1)
        ain2.value(0)
        _set_speed(pwm_left, left_speed * LEFT_GAIN)
    else:
        ain1.value(0)
        ain2.value(1)
        _set_speed(pwm_left, -left_speed * LEFT_GAIN)

    # RIGHT
    if right_speed >= 0:
        bin1.value(1)
        bin2.value(0)
        _set_speed(pwm_right, right_speed * RIGHT_GAIN)
    else:
        bin1.value(0)
        bin2.value(1)
        _set_speed(pwm_right, -right_speed * RIGHT_GAIN)

    _update_motor_state(left_speed, right_speed)