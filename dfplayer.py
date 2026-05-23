from machine import Pin, UART
import time

UART_ID = 0
UART_BAUDRATE = 9600
UART_TX_PIN = 12
UART_RX_PIN = 13

STARTUP_DELAY_MS = 2000
DEFAULT_VOLUME = 20
POST_VOLUME_DELAY_MS = 100

CMD_PLAY_TRACK = 0x03
CMD_SET_VOLUME = 0x06
CMD_STOP = 0x16

_uart = None
_volume = DEFAULT_VOLUME


def _clamp_volume(volume):
    volume = int(volume)
    if volume < 0:
        return 0
    if volume > 30:
        return 30
    return volume


def init(volume=DEFAULT_VOLUME):
    global _uart, _volume

    if _uart is None:
        _uart = UART(
            UART_ID,
            baudrate=UART_BAUDRATE,
            tx=Pin(UART_TX_PIN),
            rx=Pin(UART_RX_PIN),
        )
        time.sleep_ms(STARTUP_DELAY_MS)

    _volume = _clamp_volume(volume)
    _send_command(CMD_SET_VOLUME, _volume)
    time.sleep_ms(POST_VOLUME_DELAY_MS)
    return True


def _send_command(cmd, param=0):
    if _uart is None:
        return False

    frame = bytearray(10)
    frame[0] = 0x7E
    frame[1] = 0xFF
    frame[2] = 0x06
    frame[3] = cmd & 0xFF
    frame[4] = 0x00
    frame[5] = (param >> 8) & 0xFF
    frame[6] = param & 0xFF

    checksum = (-sum(frame[1:7])) & 0xFFFF
    frame[7] = (checksum >> 8) & 0xFF
    frame[8] = checksum & 0xFF
    frame[9] = 0xEF

    _uart.write(frame)
    return True


def set_volume(volume):
    global _volume

    _volume = _clamp_volume(volume)
    if _uart is None:
        return False

    ok = _send_command(CMD_SET_VOLUME, _volume)
    time.sleep_ms(POST_VOLUME_DELAY_MS)
    return ok


def get_volume():
    return _volume


def play(track, volume=None):
    global _volume

    if volume is not None:
        set_volume(volume)

    if _uart is None:
        return False

    track = int(track)
    if track <= 0:
        return False

    return _send_command(CMD_PLAY_TRACK, track)


def stop():
    if _uart is None:
        return False
    return _send_command(CMD_STOP)

