# Application Layer

This folder contains the **intelligence** and **interface** of the system. It is where the "Brain" of the network lives.

## Contents

- **mcp-server/**: The main application server.
  - Runs **FastAPI** to communicate with the outside world (like a web dashboard).
  - Uses **Multi-Agent Orchestration** agents to make decisions (e.g., "Route data from Sensor A to Sink B").
  - Translates human commands (e.g., "Monitor temperature") into technical actions.

## Role in Architecture
1. Receives commands from the User.
2. Thinks about how to execute them using Agents.
3. Sends technical instructions to the **Controller Layer**.
