# Current Project Status Analysis

**Date:** 2026-02-04
**Architecture:** 3-Layer SDN-WISE IoT Orchestration

## Layer 3: Application (Infrastructure)
**Location:** `application/`
- **MCP Server (`application/mcp-server`)**:
  - Python-based orchestration server using FastAPI and CrewAI.
  - Hosts intelligent agents for Flow Orchestration, Topology Monitoring, Flow Validation, etc.
  - Connects to ONOS Controller API.
- **Docker Service**: `mcp-ia-agent` (Port 8000).

## Layer 2: Controller (Control Plane & Simulation)
**Location:** `controller/`
- **ONOS Controller**:
  - Centralized SDN controller (Docker `onos-sdn`, Port 8181).
- **SDN-WISE Application (`controller/onos-apps/wisesdn`)**:
  - Java-based ONOS application implementing the SDN-WISE protocol.
  - Handles Packet parsing (`WisePacket`), Flow management (`FlowTableManager`), and Topology tracking.
- **Simulation Environment (`controller/onos-simulation`)**:
  - **Cooja Simulator**: Docker container `cooja-simulator` running Contiki-NG simulations.
  - **Sensor Firmware (`contiki-workspace`)**: C code for `sdn-wise-agent` and `sensor-node`.
  - **Topology (`cooja-simulations`)**: `.csc` simulation files defining the WSN network.
- **Mininet (`controller/mininet`)**:
  - Network emulator for the wired/backbone segments interaction.

## Layer 1: Device (Physical)
**Location:** `device/`
- **Current State**: Placeholder for physical device integration.
- **Future Work**: Integration of physical Arduino/ESP32 sensors running the code currently simulated in Layer 2.

## Infrastructure & Deployment
- **Docker Compose**: Orchestrates the 4-container stack (`onos-sdn`, `mininet-sdn`, `cooja-simulator`, `mcp-ia-agent`).
- **Networking**: `sdn-network` (Bridge 172.25.0.0/24).

## Summary
The project has been successfully restructured into a clean 3-layer architecture. 
- **Application Logic** is isolated in `application/`.
- **Controller Logic & Simulation** are consolidated in `controller/`.
- **Device Support** is prepared in `device/`.
- **Backup**: Stored in `_BACKUP_20260204`.
