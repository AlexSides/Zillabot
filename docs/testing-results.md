# Testing Results

## Testing Overview

This page summarizes available testing evidence for ZillaBot. The source material includes a documented test plan, sensor and navigation testing notes, arena photos, and demonstration videos.

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
| T-02 | Boundary detection validation | Test floor-facing sensors against arena edge conditions | not formally measured in the available public records | [TCRT distance image](../images/testing/tcrt-distance.png) | Public materials show design/testing context, but final thresholds are not published here |
| T-03 | Object detection validation | Test front time-of-flight sensing against targets | not formally measured in the available public records | [ToF reflection note](../images/testing/tof-reflections.jpeg) | Public materials show sensor considerations, but final range data is not published here |
| T-04 | Competition/demo behavior | Run robot in arena or demonstration setup | Demonstrated in available video evidence | [Demo videos](media-gallery.md#demo-videos) | Public videos show demonstration activity; formal match outcomes are not documented here |

## Performance Metrics

| Metric | Measured Value | Test Condition | Notes |
| --- | --- | --- | --- |
| Startup time | not formally measured in the available public records | Robot startup and match preparation | No timed startup record is available in the public materials |
| Detection range | not formally measured in the available public records | Boundary and object detection testing | Source materials discuss sensor validation but do not publish final range values here |
| Response time | not formally measured in the available public records | Navigation state response | Telemetry was used during development, but final timing numbers are not published here |
| Run consistency | not formally measured in the available public records | Demo and competition-style runs | Available evidence is video-based rather than a formal trial table |

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
- Boundary detection and object detection were treated as separate validation areas during the test planning process.
- Demonstration videos provide public evidence of the robot operating, but they do not replace a controlled test table with repeated trials.
- The traction/push test provides useful engineering evidence, while navigation timing, final sensor thresholds, and broader repeatability statistics are still not formally published in this repository.

## Summary

The available public records support that ZillaBot was tested through subsystem checks, telemetry-assisted debugging, traction/push testing, and demonstration runs. The traction data shows a clear improvement from the revised silicone tread, while the smaller sample size for the new wheels should be considered when interpreting the 100% pass rates.
