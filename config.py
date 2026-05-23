# ================================================================
# config.py
# CONFIG — ZillaBot V3
# New board + new pin layout
# ================================================================

# -------------------------
# Modes
# -------------------------
MODE_1_SUMO = 1
MODE_2_TUG  = 2

# -------------------------
# States
# -------------------------
STATE_SEARCH = 0
STATE_AVOID  = 1
STATE_SCAN   = 2
STATE_PURSUE = 3
STATE_TUG    = 4

# -------------------------
# Audio tracks
# -------------------------
# 1 = roar
# 2 = sumo1_welcome-to-the-jungle
# 3 = sumo2_kung-fu-fighting
# 4 = sumo3_iron-man
# 5 = blockpull_gonna-fly-now
# 6 = tug1_immigrant-song
# 7 = tug2_seven-nation-army
TRACK_COUNTDOWN_ROAR = 1
SUMO_SELECTED_TRACK = 2
TUG_SELECTED_TRACK = 6
MODE_2_SELECTED_TRACK = TUG_SELECTED_TRACK  # compatibility alias

# -------------------------
# Motor pins
# -------------------------
LEFT_MOTOR_PWM = 8
LEFT_MOTOR_IN1 = 7
LEFT_MOTOR_IN2 = 6

RIGHT_MOTOR_PWM = 3
RIGHT_MOTOR_IN1 = 4
RIGHT_MOTOR_IN2 = 5

# -------------------------
# Runtime feature flags
# -------------------------
# Disable sensor CSV logging by default so flash writes never slow
# the sensor thread during a match.
ENABLE_SENSOR_FILE_LOGGING = False

# Disable Wi-Fi / UDP telemetry by default so data collection never
# steals time from the control loop.
ENABLE_TELEMETRY = False

# Keep navigation hot-loop prints off by default. Serial output can
# block on MicroPython and add jitter during a match.
ENABLE_NAV_DEBUG_PRINTS = False

# Poll the ToF array more slowly than the 100 Hz sensor loop and reuse
# the previous reading between polls.
TOF_POLL_MS = 40

# If telemetry is re-enabled later, keep run telemetry light enough to
# avoid churn in the motion loop.
TELEMETRY_RUN_MS = 75

# -------------------------
# IR boundary sensors
# -------------------------
IR_LEFT_ADC_PIN  = 27
IR_RIGHT_ADC_PIN = 26

# SUMO thresholds
# Measured roughly:
#   mat  ~35k
#   blue ~39k–40k
# In SUMO, blue tape means edge hit.
SUMO_BLUE_L_THRESHOLD = 38200
SUMO_BLUE_R_THRESHOLD = 37400

# Legacy / compatibility
BOUNDARY_BLUE_THRESHOLD = 38500

# SUMO wander timing
SUMO_SEARCH_TURN_S  = 0.22
SUMO_SEARCH_BURST_S = 0.15

# TUG thresholds
# Measured roughly:
#   mat   ~35k
#   blue  ~39k–40k
#   black ~54k–56k
TUG_BLUE_L_THRESHOLD = 30000
TUG_BLUE_R_THRESHOLD = 30000
TUG_BLACK_THRESHOLD = 52000

# Legacy / unused
BOUNDARY_BLACK_THRESHOLD = 55000
BOUNDARY_BROWN_THRESHOLD = 34500

# -------------------------
# ToF
# -------------------------
TOF_SDA = 16
TOF_SCL = 17

# Keep the logical slot order fixed as:
# [L90, L45, C, R45, R90]
#
# The outer slots stay listed so their XSHUT pins can still be driven low
# when those sensors are plugged in but not used on the 3-sensor bot.
# Set the first/last entries to True to re-enable L90 and R90 later.
TOF_NAMES     = ["L90", "L45", "C", "R45", "R90"]
TOF_XSHUT     = [18, 19, 20, 21, 22]
TOF_ADDRESSES = [0x31, 0x32, 0x33, 0x34, 0x35]
TOF_ENABLED   = [True, True, True, True, True]

TOF_DETECT_RANGE = 1000  # mm

# -------------------------
# IMU (LSM6DS3)
# -------------------------
IMU_SDA = 14
IMU_SCL = 15

IMU_HEADING_FILTER = 0.10
IMU_TURN_SPEED     = 0.8   # slightly stronger for bigger avoid turns

# -------------------------
# SUMO navigation tuning
# -------------------------
SEARCH_SPEED        = 0.4
AVOID_REVERSE_SPEED = -0.6
AVOID_TURN_SPEED    = 0.2
AVOID_REVERSE_TIME  = 0.6
AVOID_TURN_TIME     = 0.2

# Centered target attack profile:
# far target -> HUNT_BASE_SPEED
# mid target -> ramp up toward HUNT_ATTACK_SPEED
# close stable target -> short HUNT_BURST_SPEED launch
HUNT_BASE_SPEED       = 0.6
HUNT_ATTACK_SPEED     = 0.9
HUNT_ALIGN_SPEED      = 0.75
HUNT_BURST_SPEED      = 1.0
HUNT_ATTACK_RAMP_MM   = 320
HUNT_BURST_DIST_MM    = 160
HUNT_CENTER_LOCK_MS   = 80
HUNT_BURST_MS         = 140
SUMO_EDGE_CONFIRM_MS  = 12

# Face-lock breakout:
# if the center target stays close and distance barely changes,
# do a short forward-biased shoulder break to slip onto a 45 sensor.
SUMO_STALEMATE_DIST_MM          = 170
SUMO_STALEMATE_DELTA_MM         = 18
SUMO_STALEMATE_MS               = 320
SUMO_SHOULDER_BREAK_INNER_SPEED = 0.55
SUMO_SHOULDER_BREAK_OUTER_SPEED = 0.92
SUMO_SHOULDER_BREAK_MS          = 180
SUMO_SHOULDER_BREAK_MAX_DEG     = 18.0
SUMO_SHOULDER_BIAS_MM           = 35

# Legacy / older motion values
TUG_REVERSE_SPEED = -0.70
TURN_SPEED        = 0.55
PATTERN_SPEED     = 0.60

# -------------------------
# TUG mode tuning
# -------------------------

# Legacy / not used for finish anymore
TUG_TARGET_BLUE_LINES = 18

# Forward drive + heading correction
TUG_BASE_SPEED     = 0.65
TUG_HEADING_KP     = 0.020
TUG_MAX_CORRECTION = 0.25
TUG_HEADING_DEADBAND_DEG = 2.0
TUG_CORRECTION_SMOOTHING = 0.25
TUG_BOTH_DARK_CONFIRM_MS = 200
TUG_ONE_SIDE_CONFIRM_MS  = 300
TUG_ONE_SIDE_RECOVER     = True
TUG_EDGE_RECOVERY_BIAS   = 0.18

# TUG mode profile controls
# Use the same TUG mode for block pull or tug-of-war by changing these settings.
# Defaults preserve the current behavior until you intentionally tune them.
TUG_START_SPEED       = TUG_BASE_SPEED
TUG_PULL_SPEED        = TUG_BASE_SPEED
TUG_STARTUP_MS        = 0
TUG_DISABLE_AUTO_STOP = True

# Compatibility aliases
MODE_2_START_SPEED       = TUG_START_SPEED
MODE_2_PULL_SPEED        = TUG_PULL_SPEED
MODE_2_STARTUP_MS        = TUG_STARTUP_MS
MODE_2_DISABLE_AUTO_STOP = TUG_DISABLE_AUTO_STOP

# Timing / safety
TUG_TOTAL_TIMEOUT_S = 30.0
TUG_STALL_TIMEOUT_S = 999.0

# Ignore black border until we've been off-black this long
TUG_ARM_CLEAR_MS = 200

# Blue counting debounce
TUG_LINE_COOLDOWN_MS = 120

# If black border is hit while armed, back up briefly then stop
TUG_EDGE_BACKOFF_S     = 0.15
TUG_EDGE_BACKOFF_SPEED = 0.60

