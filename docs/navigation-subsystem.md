# Navigation Subsystem

## Purpose

The navigation subsystem determines how ZillaBot interprets sensor input and chooses movement actions in real time. Its goal is to keep the robot responsive during sumo and tug-of-war behavior while protecting against arena boundary conditions.

## Navigation Responsibilities

- Read and combine sensor information
- Identify the current operating situation
- Choose the next action or movement state
- Send movement intent to the motor control layer

## Inputs

- front-facing time-of-flight readings for opponent or object detection
- floor-facing boundary sensor readings for edge detection
- IMU values for orientation feedback
- mode selection inputs for switching between program, sumo, and tug behavior
- start input used before entering active match behavior

## Outputs

- movement intent sent to the motor control layer
- navigation state changes such as search, pursue, avoid, or tug behavior
- telemetry/debug outputs when enabled for testing

## Navigation Strategy

Document the high-level logic rather than every implementation detail.

- Search behavior: move or turn until the sensor array identifies a meaningful target condition
- Pursuit behavior: drive toward a detected object or opponent using front sensor readings
- Avoid or recovery behavior: prioritize edge detection and reverse/turn behavior before continuing
- Mode-specific behavior: support different competition behavior for sumo and tug-of-war operation

## State Machine Summary

The current portfolio snippet describes the state-machine concept here:

- [Navigation state machine snippet](../code-snippets/navigation-state-machine.md)

Suggested final additions:

- state transition diagram
- exact state names from the final implementation
- transition conditions from the tested code

## Sensor Fusion or Priority Rules

Boundary and safety-related readings should be treated as higher priority than pursuit behavior. This keeps the robot from continuing an aggressive movement when an edge or unsafe condition has been detected.

Helpful prompts:

- Which sensors have highest priority?
- What safety conditions override attack or pursuit behavior?
- How do you handle uncertain or noisy readings?

## Known Challenges

Use this section to explain what made navigation difficult.

- sensor readings can vary with surface, distance, and robot angle
- state transitions need to be fast enough for competition behavior
- motor response, battery level, and floor traction can change the observed behavior
- telemetry is helpful for debugging but should not slow down the control loop

## Future Improvements

- add a clean state transition diagram based on the final source
- include measured response-time data from match testing
- compare behavior across multiple floor or arena conditions
- add replay plots from saved telemetry logs if available
