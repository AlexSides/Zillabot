# Testing Results

## Testing Overview

This page summarizes available testing evidence for ZillaBot. The source material includes a documented test plan, D2 final design review results, sensor and navigation testing notes, arena photos, and demonstration videos.

Exact measured values are only included when they are present in the available public records. Several performance values were not formally measured in the public materials, so they are documented as qualitative observations.

## Test Categories

- Functional tests
- Sensor validation
- Navigation behavior tests
- Reliability or repeatability tests
- Competition-style trials

## Documented Test Areas

| Test ID | Objective | Method | Result | Evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| T-01 | Live navigation telemetry stream | Stream and record robot sensor/state data during operation | PASS in source report | Source test report | Source report notes live IR, ToF, IMU, motor, and state data updates |
| T-02 | Boundary detection validation | Test floor-facing sensors against white, black, and brown surfaces | PASS in D2 final design review | [TCRT distance image](../images/testing/tcrt-distance.png) | IR averages and stability values are listed below |
| T-03 | Object detection validation | Test front time-of-flight sensing against targets and out-of-range conditions | Mixed: out-of-range PASS, within-10-mm accuracy FAIL | [ToF reflection note](../images/testing/tof-reflections.jpeg) | ToF response-time sampling passed; one accuracy requirement did not |
| T-04 | Competition/demo behavior | Run robot in arena or demonstration setup | Demonstrated in available video evidence | [Demo videos](media-gallery.md#demo-videos) | Public videos show demonstration activity; formal match outcomes are not documented here |

## Performance Metrics

| Metric | Measured Value | Test Condition | Notes |
| --- | --- | --- | --- |
| Startup delay | 5 seconds | Start button pressed before active match behavior | Product specification describes a five-second countdown before match behavior begins |
| Configured ToF detection range | 1000 mm | Navigation configuration setting test | Listed as PASS in the final design review |
| ToF sampling response | Slowest average sampling frequency: 33.22 Hz; maximum loop-time difference: 3 ms | ToF response-time test | Listed as PASS in the final design review |
| Run consistency | not formally measured in the available public records | Demo and competition-style runs | Available evidence is video-based rather than a formal trial table |

## Sensor and Navigation Test Evidence

### Boundary Detection

The D2 final design review reported the following boundary-sensor analog test averages. The source slide describes the values as averages of 10 readings.

| Surface Condition | Left IR Reading | Right IR Reading | Outcome |
| --- | --- | --- | --- |
| White field/boundary reference | 2040 | 2059.2 | PASS |
| Black surface reference | 58721.2 | 58732.4 | PASS |
| Brown surface reference | 2070.4 | 2062.4 | PASS |

The same review reported a 47.6 Hz IR sampling rate. Stability was reported as 1.6% on white for both sensors, 0.55% on black for the left sensor, and 0.66% on black for the right sensor.

### Object Detection

The D2 final design review reported that the VL53L0X ToF sensors returned out-of-range values near 8190: 8190, 8191, 8189, 8190, and 8190. That requirement passed.

The ToF accuracy requirement of reading within 10 mm at each distance did not fully pass. The reported maximum deviations were 40 mm, 12 mm, 12 mm, 17 mm, and 18 mm across the sensor positions. The source notes that testing was performed from 20 cm to 4 cm and that all sensors met the 10 mm target except the right 45-degree sensor.

The ToF response-time test passed. The final design review reported a maximum loop-time difference of 3 ms, maximum consecutive sampling-frequency deviation of 4 Hz, and slowest sampling frequency of 33.22 Hz.

### Navigation Configuration

| Requirement | Measured or Tuned Result | Outcome |
| --- | --- | --- |
| Boundary thresholds | Left: 38200, Right: 37400 | PASS |
| ToF detection | Range: 1000 mm | PASS |
| Search behavior | Turn: 0.22 s, Burst: 0.15 s, Speed: 0.4 | PASS |
| Avoid behavior | Reverse: -0.6 for 0.6 s, Turn: 0.2 for 0.2 s | PASS |
| Pursuit behavior | Base: 0.6, Attack: 0.8, Align: 0.9 | PASS |
| IMU turning | Filter: 0.10, Turn speed: 0.8 | PASS |

The source review notes that the configuration values were tuned through repeated live robot trials and selected based on ring stability, pursuit behavior, and avoid-state performance. It also notes that higher speeds improved response time but increased self-ring-out risk.

### Runtime Estimates

The final design review included estimated runtime values by operating mode.

| Operation Mode | Estimated Runtime |
| --- | --- |
| Standby | 11.59 hours |
| Sumo search | 8.50 hours |
| Sumo push at 1500 g | 4.75 hours |
| Tug at 1000 g | 6.10 hours |

These values are presented as design-review runtime estimates, not independently repeated public endurance trials.

## Traction and Push Testing

The wheel traction test compared the original wheel setup against a revised silicone tread design. The revised tread was tighter-fitting and thicker than the previous tread. The goal of the test was to evaluate whether the robot could maintain traction while pushing increasing loads.

### Push Test Results

| Test Load | Old Wheels Pass Rate | New Silicone Tread Pass Rate |
| --- | --- | --- |
| 1500 g | 98% | 100% |
| 1750 g | 54% | 100% |
| 2250 g | 1% | 100% |
| 2500 g | Failed / did not pass | 100% |
| 3000 g | Not tested in available old-wheel data | 100% |

### Test Context and Limitations

- Old wheel results were based on about 20 tests per weight.
- New silicone tread results were based on about 3 tests per weight.
- The 100% pass rates for the new tread are promising, but they are based on a smaller sample size than the old-wheel data.
- The tighter and thicker silicone tread greatly improved traction during push testing.
- The added traction also made the robot faster and more aggressive during attacks, which meant the navigation thresholds needed retuning because the robot could drive out of the arena during attack behavior.

## Test Evidence

Current visual evidence:

- [Arena test setup](../images/testing/build-test-setup.jpg)
- [April 13 demo run](../videos/2026-04-13-demo-run.mp4)
- [May 10 competition run](../videos/2026-05-10-competition-run.mp4)
- [Short demonstration clip](../videos/short-demo-clip.mp4)

## Observations

- The project source materials describe telemetry as useful for debugging live sensor and state behavior.
- Boundary detection and object detection were treated as separate validation areas during the test planning process, with D2 final design review values available for both.
- Demonstration videos provide public evidence of the robot operating, but they do not replace a controlled test table with repeated trials.
- The traction/push test provides useful engineering evidence, while broader match repeatability statistics are still not formally published in this repository.

## Summary

The available public records support that ZillaBot was tested through subsystem checks, telemetry-assisted debugging, sensor validation, navigation configuration tuning, traction/push testing, and demonstration runs. The traction data shows a clear improvement from the revised silicone tread, while the smaller sample size for the new wheels should be considered when interpreting the 100% pass rates. The D2 test evidence also shows honest limitations: ToF out-of-range and response-time behavior passed, but one ToF accuracy requirement did not fully pass.
