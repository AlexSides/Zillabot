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
| T-02 | Boundary detection validation | Test floor-facing sensors against arena edge conditions | Not formally measured in the available public records | [TCRT distance image](../images/testing/tcrt-distance.png) | Public materials show design/testing context, but final thresholds are not published here |
| T-03 | Object detection validation | Test front time-of-flight sensing against targets | Not formally measured in the available public records | [ToF reflection note](../images/testing/tof-reflections.jpeg) | Public materials show sensor considerations, but final range data is not published here |
| T-04 | Competition/demo behavior | Run robot in arena or demonstration setup | Demonstrated in available video evidence | [Demo videos](media-gallery.md#demo-videos) | Public videos show demonstration activity; formal match outcomes are not documented here |

## Performance Metrics

| Metric | Measured Value | Test Condition | Notes |
| --- | --- | --- | --- |
| Startup time | Not formally measured in the available public records | Robot startup and match preparation | Keep as qualitative unless final timed data is recovered |
| Detection range | Not formally measured in the available public records | Boundary and object detection testing | Source materials discuss sensor validation but do not publish final range values here |
| Response time | Not formally measured in the available public records | Navigation state response | Telemetry was used during development, but final timing numbers are not published here |
| Run consistency | Not formally measured in the available public records | Demo and competition-style runs | Available evidence is video-based rather than a formal trial table |

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
- Final quantitative thresholds, timing data, and repeatability statistics are not published in this repository.

## Summary

The available public records support that ZillaBot was tested through subsystem checks, telemetry-assisted debugging, and demonstration runs. This page intentionally avoids unsupported performance claims where final measured values are not available.
