# Navigation State Machine Snippet

This page is meant for a portfolio-friendly excerpt, not the full production implementation.

Replace the example below with a real snippet from your project when you are ready.

## Representative Pseudocode

```text
state = IDLE

loop:
    read sensors

    if boundary_detected:
        state = AVOID
    else if target_detected:
        state = PURSUE
    else:
        state = SEARCH

    if state == SEARCH:
        rotate_or_scan()
    else if state == PURSUE:
        drive_toward_target()
    else if state == AVOID:
        reverse_and_turn()
```

## What This Snippet Shows

- state-based decision making
- priority of safety conditions
- separation between sensing and action selection

## Replace With Final Version

When your full code is ready, paste a short excerpt here and add:

- where it lives in the project
- what the snippet is responsible for
- why this design choice mattered
