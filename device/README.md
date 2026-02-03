# Device Layer

This folder allows for **physical hardware**. It is where code specific to real-world deployment goes.

## Contents

*Currently Empty / Placeholder*

In a future phase, this folder will contain:
- **Hardware-specific Drivers**: Code for Arduino Pico, ESP32, or XBee modules.
- **Physical Deployment Configs**: Settings for flashing real chips instead of the simulator.

## Role in Architecture
1. The physical "hands" and "eyes" of the system.
2. Collects data (temperature, heart rate, etc.) and sends it to the Controller.
3. Executes flow rules (routing instructions) sent by the Controller.
