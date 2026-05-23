# ZillaBot Senior Design Portfolio

ZillaBot is an autonomous senior design robot built for sumo-style pushing and tug-of-war competition. The robot combines a two-wheel rear-drive platform, floor-facing boundary sensors, front-facing time-of-flight sensors, IMU feedback, a custom CAD chassis, and an integrated PCB to support real-time navigation decisions.

![Final ZillaBot build](images/progression/04-final-build.jpg)

## What This Repository Shows

- Autonomous robot design for sumo and tug-of-war match formats
- Mechanical progression from breadboard prototype to enclosed 3D-printed robot
- Sensor-driven navigation using boundary, object-detection, and orientation inputs
- PCB, CAD, and chassis assets from the senior design build
- Test evidence, demo videos, and selected code examples

## Project Highlights

| Area | Evidence |
| --- | --- |
| Final robot build | [Build progression gallery](docs/media-gallery.md) |
| Demo footage | [Video evidence](docs/media-gallery.md#demo-videos) |
| Chassis and enclosure design | [Hardware assets](docs/hardware-assets.md) |
| PCB and wiring architecture | [PCB layout image](images/design/pcb-layout.png) and [Gerber package](hardware/pcb/zillabot-gerber.zip) |
| Navigation design | [Navigation subsystem](docs/navigation-subsystem.md) and [state machine snippet](code-snippets/navigation-state-machine.md) |
| Testing summary | [Testing results](docs/testing-results.md) |

## Visual Design Progression

| Prototype wiring | Integrated prototype | Final enclosure |
| --- | --- | --- |
| ![Early breadboard prototype](images/progression/01-early-prototype.jpg) | ![Integrated prototype](images/progression/03-integrated-prototype.jpg) | ![Final enclosed ZillaBot](images/progression/04-final-build.jpg) |

## Repository Structure

- `docs/` contains the project overview, subsystem writeups, media gallery, hardware asset index, testing notes, and reflection.
- `images/` contains build photos, CAD renders, PCB imagery, chassis revisions, and testing visuals.
- `videos/` contains short demo clips.
- `hardware/` contains selected CAD, drawing, and PCB fabrication assets.
- `code-snippets/` contains portfolio-friendly excerpts that explain important logic.
- Root Python files contain the current working implementation snapshot and may be revised as the full source release is cleaned up.

## Demo Videos

- [April 13 final 5-second demo highlight](videos/2026-04-13-demo-run.mp4)
- [Short demonstration clip](videos/short-demo-clip.mp4)

## Current Status

This repository is being shaped as a public engineering portfolio. It includes source files, selected design assets, photos, videos, and documentation pages. Exact measured performance values are still left as placeholders unless they came directly from the project source materials.

## Wi-Fi Secrets

This repo does not track `wifi_secrets.py`.

Create a local `wifi_secrets.py` from `wifi_secrets.example.py` only when you are ready to run telemetry locally.
