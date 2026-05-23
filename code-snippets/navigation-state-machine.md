# Navigation State Machine Snippet

This page uses representative pseudocode to explain the navigation approach without publishing every implementation detail. It is intended to show the design pattern behind ZillaBot's state-based behavior.

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

## Notes

The exact production state transitions are not fully documented in the public records. This simplified version is included to make the navigation concept readable for reviewers.
