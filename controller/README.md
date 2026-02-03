# Controller Layer

This folder contains the **management logs** and **simulation tools** of the network. It is the "Control Room" that executes orders.

## Contents

- **onos-apps/**: Custom applications for the ONOS Controller.
  - **wisesdn**: A Java application that teaches ONOS how to speak the **SDN-WISE** protocol used by our wireless sensors.
  
- **onos-simulation/**: virtual playground for testing.
  - **contiki-workspace/**: The C code covering the "Firmware" that runs on the sensors.
  - **cooja-simulations/**: Configuration files for the **Cooja Simulator**, which lets us test hundreds of virtual sensors on a computer.

- **scripts/**: Utility scripts to help build, deploy, or run simulations.

## Role in Architecture
1. Receives instructions from the **Application Layer**.
2. Talks directly to the devices (real or simulated) to configure them (e.g., "Change path", "Sleep", "Wake up").
3. Reports network status back to the Application.
