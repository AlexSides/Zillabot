# Sensor Priority Logic Snippet

This page is for a small portfolio excerpt that demonstrates how ZillaBot resolves competing sensor inputs.

## Representative Pseudocode

```text
if edge_sensor_triggered:
    perform_escape_behavior()
else if opponent_in_range:
    move_to_engage()
else if heading_is_uncertain:
    stabilize_or_recenter()
else:
    continue_search_pattern()
```

## Why This Matters

- Safety-related sensor inputs should override aggressive movement
- Priority rules make robot behavior easier to explain and debug
- This logic shows how the robot avoids reacting to every sensor equally

## Replace With Final Version

When ready, replace this pseudocode with:

- a short real code excerpt
- a note about the sensors involved
- a short explanation of why this priority order was chosen
