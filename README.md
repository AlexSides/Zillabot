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
| Architecture diagrams | [Rendered system and state diagrams](docs/architecture-diagrams.md) |
| Bill of materials | [BOM and cost summary](docs/bill-of-materials.md) |
| Navigation design | [Navigation subsystem](docs/navigation-subsystem.md), [state machine snippet](code-snippets/navigation-state-machine.md), and [source walkthrough](docs/source-code-walkthrough.md) |
| Testing summary | [Testing results](docs/testing-results.md) |

## Testing Evidence

The [testing results](docs/testing-results.md) page summarizes available subsystem, demo, and traction/push-test evidence. The revised tighter and thicker silicone tread improved push-test pass rates across the tested loads, though the new tread results used a smaller sample size and should be read with that limitation in mind.

## Key Engineering Takeaways

- Stronger traction can improve pushing force but also changes navigation behavior.
- Boundary detection needs to remain the highest-priority safety behavior.
- Live telemetry made sensor and state debugging easier during integration.
- Dual-core organization helped separate fast safety/motor behavior from higher-level navigation.
- Real-world robot testing revealed issues that were not obvious from code alone.

## Visual Design Progression

| Prototype wiring | Integrated prototype | Final enclosure |
| --- | --- | --- |
| ![Early breadboard prototype](images/progression/01-early-prototype.jpg) | ![Integrated prototype](images/progression/03-integrated-prototype.jpg) | ![Final enclosed ZillaBot](images/progression/04-final-build.jpg) |

## Repository Structure

- `docs/` contains the project overview, subsystem writeups, media gallery, hardware asset index, testing notes, and reflection.
- `images/` contains build photos, CAD renders, PCB imagery, chassis revisions, architecture diagrams, and testing visuals.
- `videos/` contains short demo clips.
- `hardware/` contains selected CAD, drawing, and PCB fabrication assets.
- `code-snippets/` contains portfolio-friendly excerpts that explain important logic.
- Root Python files contain the public project source snapshot included with this portfolio.

## Demo Videos

- [April 13 demo run](videos/2026-04-13-demo-run.mp4)
- [May 10 competition run](videos/2026-05-10-competition-run.mp4)
- [Short demonstration clip](videos/short-demo-clip.mp4)

## Current Status

This repository contains the public project source snapshot, selected hardware assets, photos, demo videos, and documentation from the ZillaBot senior design build. Some performance areas were documented qualitatively when formal measured data was not available.

## Wi-Fi Secrets

This repo does not track `wifi_secrets.py`.

Create a local `wifi_secrets.py` from `wifi_secrets.example.py` only when you are ready to run telemetry locally.
