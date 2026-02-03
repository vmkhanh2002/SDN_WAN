# SDN-WISE Full Stack Laboratory

**Intent-Based Wireless Sensor Network Orchestration with Gemini LLM**

[![Status](https://img.shields.io/badge/Status-MVP%20Complete-success)](/)
[![Progress](https://img.shields.io/badge/Progress-80%25-blue)](/)
[![License](https://img.shields.io/badge/License-MIT-green)](/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Status](#project-status)
- [Quick Start](#quick-start)
- [Components](#components)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)

---

## 🎯 Overview

SDN-WISE Full Stack is a **complete implementation** of an intent-based wireless sensor network (WSN) orchestration system using:

- **SDN-WISE Protocol** for sensor network management
- **ONOS Controller** for SDN control plane
- **MCP Architecture** (adapted from ehr-aiot) for multi-agent orchestration
- **Gemini LLM** for natural language intent processing
- **CrewAI Framework** for multi-agent coordination

### Key Features

- ✨ **Intent-Based Control** - Natural language → Network flows
- 🤖 **AI-Driven Orchestration** - Gemini LLM + CrewAI agents
- 📡 **WSN Management** - Full SDN-WISE protocol implementation
- 🏗️ **Modular Architecture** - 5 independent phases
- 🐳 **Containerized** - Docker-based deployment
- 📊 **REST APIs** - Complete programmatic control

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│           USER (Natural Language)               │
│      "Route temperature data to sink"           │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│         MCP Server (FastAPI + CrewAI)           │
│  ┌───────────────────────────────────────────┐  │
│  │ 6 Orchestration Agents:                   │  │
│  │ • flow-orchestration (Intent → Flows)     │  │
│  │ • topology-monitoring (WSN Status)        │  │
│  │ • flow-validation (Constraints)           │  │
│  │ • flow-execution (Install via ONOS)       │  │
│  │ • network-configuration (Border Router)   │  │
│  │ • access-control (Auth)                   │  │
│  └───────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │ REST API
                     ▼
┌─────────────────────────────────────────────────┐
│        ONOS Controller (SDN-WISE App)           │
│  • Parse SDN-WISE packets (UDP port 9999)       │
│  • Manage sensor flow tables                    │
│  • Track WSN topology                           │
│  • Expose REST API                              │
└────────────────────┬────────────────────────────┘
                     │ SDN-WISE Protocol
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
┌────────────┐ ┌──────────┐ ┌──────────┐
│   Border   │ │  Sensor  │ │  Sensor  │
│   Router   │ │  Node 2  │ │  Node 3  │
│  (Sink)    │ │          │ │          │
└────────────┘ └──────────┘ └──────────┘
    Cooja WSN Simulation (Contiki-NG)
```

---

## 🔧 Hardware Platform Support

### Sensor Nodes

Resource-constrained embedded devices running Contiki OS and SDN-WISE agent.

**Supported Hardware:**
- **Arduino Pico (RP2040)** - Microcontroller platform
- **ESP32** - With IEEE 802.15.4 radio transceiver  
- **XBee Modules** - Wireless communication (IEEE 802.15.4)
- **Zolertia RE-Mote** - WSN development platform
- **TelosB Sky Motes** - Traditional WSN hardware

**Operating System:**
- Contiki OS providing lightweight process management
- Networking stack with 6LoWPAN support
- Hardware abstraction layer

**Networking Layer:**
- SDN-WISE agent for flow-based forwarding
- Interaction with ONOS controller via border router
- IEEE 802.15.4 wireless protocol

### Sink Node (Border Router)

Contiki node acting as gateway between WSN and ONOS.

**Functionality:**
- Bridges wireless communication and IP-based networks
- IPv6 support via 6LoWPAN
- UDP/TCP communication over Ethernet
- Translates SDN-WISE packets to ONOS API calls

---

## 📊 Project Status

| Phase | Component | Status | Completion |
|-------|-----------|--------|------------|
| **Phase 1** | Docker Infrastructure | ✅ Complete | 100% |
| **Phase 2** | WSN Simulation (Contiki-NG) | 🟡 Code Complete | 90% |
| **Phase 3** | ONOS Custom App (Java) | ✅ Code Complete | 100% |
| **Phase 4** | MCP Servers (Python) | ✅ Complete | 100% |
| **Phase 5** | Integration & Testing | ⏳ Pending | 0% |
| **Overall** | - | 🟢 MVP Ready | **80%** |

### What's Working ✅

- Docker infrastructure configured
- MCP Server running (http://localhost:8000)
- 6 task routers operational
- WSN sensor code complete (C)
- ONOS Java app complete (7 classes)
- REST APIs defined
- Mock data mode functional

### What's Needed 🔧

- Docker containers to start
- ONOS app compilation & deployment
- Gemini API key (optional)
- Phase 5 integration testing

---

## 🚀 Quick Start

###  1. Prerequisites

```bash
# Required
- Docker & Docker Compose
- Python 3.11+
- Git

# Optional (for full features)
- Maven (for ONOS app build)
- JDK 11+ (for ONOS app)
- Gemini API Key (for LLM features)
```

### 2. Clone Repository

```bash
git clone <repository-url>
cd SDN_WAN
```

### 3. Start Infrastructure

```bash
# Start all containers
docker-compose up -d

# Verify
docker ps
# Should show: onos-sdn, mininet-sdn, cooja-simulator, mcp-ia-agent
```

### 4. Start MCP Server

```bash
cd app

# Install dependencies
pip install -r requirements.txt

# (Optional) Add Gemini API key
echo "GEMINI_API_KEY=your-key" >> .env

# Start server
python main.py
```

Server runs on: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

### 5. Test APIs

```powershell
# Health check
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Get topology
$body = '{"action": "status"}'
Invoke-WebRequest -Uri "http://localhost:8000/tasks/topology-monitoring" `
  -Method POST -Body $body -ContentType "application/json"
```

---

## 📦 Components

### Phase 1: Docker Infrastructure

**Location:** `docker-compose.yaml`, `Dockerfile.*`

**Services:**
- `onos-sdn` (172.25.0.2) - ONOS Controller
- `mininet-sdn` (172.25.0.3) - Network Emulation
- `cooja-simulator` (172.25.0.4) - WSN Simulation
- `mcp-ia-agent` (172.25.0.5) - Application Layer

**Network:** `sdn-network` (172.25.0.0/24)

### Phase 2: WSN Simulation

**Location:** `contiki-workspace/`

**Files:**
- `sdn-wise-agent.c` (290 lines) - SDN-WISE protocol
- `sensor-node.c` (141 lines) - Sensor application
- `Makefile` - Build configuration
- `cooja-simulations/wsn-topology.csc` - Network topology

**Status:** Code complete, ready for Cooja compilation

### Phase 3: ONOS Application

**Location:** `onos-apps/wisesdn/`

**Java Classes:**
- `AppComponent.java` - ONOS lifecycle
- `WisePacket.java` - Packet parser
- `WiseController.java` - Protocol logic
- `FlowTableManager.java` - Flow management
- `FlowRule.java` - Flow model
- `TopologyManager.java` - Network graph
- `WiseWebResource.java` - REST API

**Build:**
```bash
cd onos-apps/wisesdn
mvn clean install
# Generates: target/wisesdn-1.0-SNAPSHOT.oar
```

### Phase 4: MCP Server

**Location:** `app/`

**Structure:**
```
app/
├── main.py - Entry point
├── requirements.txt - Dependencies
├── servers/
│   ├── app.py - FastAPI server
│   ├── agents.py - CrewAI registry
│   ├── utils.py - ONOS client
│   └── tasks/ - 6 MCP routers
└── data/ - JSON storage
```

**Dependencies:**
- FastAPI 0.109.0
- CrewAI (latest)
- Uvicorn 0.27.0
- Pydantic 2.5.3
- Requests 2.31.0

---

## 📡 API Documentation

### MCP Server APIs (Port 8000)

#### 1. Flow Orchestration
```http
POST /tasks/flow-orchestration
Content-Type: application/json

{
  "action": "generate_plan",
  "intent": "Route all sensor data to sink"
}
```

#### 2. Topology Monitoring
```http
POST /tasks/topology-monitoring
Content-Type: application/json

{
  "action": "status"
}
```

#### 3. Flow Validation
```http
POST /tasks/flow-validation
Content-Type: application/json

{
  "action": "validate",
  "flow_plan": {...}
}
```

#### 4. Flow Execution
```http
POST /tasks/flow-execution
Content-Type: application/json

{
  "action": "execute",
  "flow_plan": {...}
}
```

### ONOS REST APIs (Port 8181)

#### Get WSN Devices
```bash
curl -u onos:rocks http://172.25.0.2:8181/onos/wisesdn/api/devices
```

#### Get Flows
```bash
curl -u onos:rocks http://172.25.0.2:8181/onos/wisesdn/api/flows/2
```

#### Install Flow
```bash
curl -u onos:rocks -X POST \
  -H "Content-Type: application/json" \
  -d '{"nodeId":2,"srcAddr":2,"dstAddr":1,"action":1,"nextHop":1}' \
  http://172.25.0.2:8181/onos/wisesdn/api/flows
```

---

## 🛠️ Development

### Project Structure

```
SDN_WAN/
├── app/ - MCP Server (Python)
├── contiki-workspace/ - WSN Code (C)
├── onos-apps/ - ONOS App (Java)
├── cooja-simulations/ - Simulation files
├── scripts/ - Utility scripts
├── docker-compose.yaml
├── Dockerfile.* - Container images
└── README.md
```

### Code Statistics

- **Python:** ~1,200 lines (MCP Server)
- **Java:** ~1,100 lines (ONOS App)
- **C:** ~431 lines (WSN Code)
- **Configuration:** ~200 lines (Docker, Maven)
- **Total:** ~3,000 lines

### Technologies

- **Languages:** Python, Java, C
- **Frameworks:** FastAPI, CrewAI, ONOS
- **Platforms:** Docker, Contiki-NG
- **Protocols:** SDN-WISE, OpenFlow, RPL, 6LoWPAN
- **LLM:** Google Gemini

---

## 🧪 Testing

### Automated Tests

```bash
# MCP Server health
curl http://localhost:8000/health

# Docker infrastructure
docker ps
docker network inspect sdn-network

# WSN code compilation (optional)
cd contiki-workspace
make TARGET=cooja
```

### Manual Test Scenarios

1. **Device Discovery**
   - Intent: "List all temperature sensors"
   - Expected: JSON list of sensor nodes

2. **Flow Installation**
   - Intent: "Route humidity data to sink"
   - Expected: Flow rules created

3. **Topology Visualization**
   - Action: Get network graph
   - Expected: Nodes and links JSON

### Integration Tests

See `PHASE5_TESTING.md` (to be created)

---

## 🚢 Deployment

### Development (Current)

```bash
# Start MCP server
cd app && python main.py

# Access API docs
open http://localhost:8000/docs
```

### Production (Future)

```bash
# Build ONOS app
cd onos-apps/wisesdn
./build-and-deploy.sh

# Deploy to ONOS
# App will be available at http://172.25.0.2:8181
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f mcp-ia-agent

# Stop services
docker-compose down
```

---

## 📚 Documentation

- **[Implementation Plan](brain/implementation_plan.md)** - 5-phase roadmap
- **[Task List](brain/task.md)** - Detailed checklist
- **[Walkthrough](brain/walkthrough.md)** - Development log
- **[Phase 3 Guide](PHASE3_ONOS_APP.md)** - ONOS app details
- **[Phase 2 Testing](PHASE2_TESTING.md)** - WSN testing guide

---

## 🤝 Contributing

This is a laboratory/educational project. Contributions welcome!

### Development Workflow

1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

---

## 📝 License

MIT License - See LICENSE file

---

## 👥 Authors

- **Original Concept:** SDN-WISE Protocol
- **MCP Architecture:** Adapted from ehr-aiot
- **Implementation:** SDN-WISE Full Stack Team

---

## 🙏 Acknowledgments

- ONOS Project
- Contiki-NG Community
- ehr-aiot Reference Architecture
- Google Gemini AI
- CrewAI Framework

---

## 📚 References

### Official Repositories

- **SDN-WISE ONOS:** https://github.com/sdnwiselab/onos
- **SDN-WISE Contiki:** https://github.com/sdnwiselab/sdn-wise-contiki
- **Arduino IPv6 Stack:** https://github.com/imt-atlantique/Arduino-IPv6Stack
- **MCP Architecture:** https://github.com/hazel260802/ehr-aiot-d4genhackathon

### Documentation

- ONOS Wiki: https://wiki.onosproject.org
- Contiki-NG: https://github.com/contiki-ng/contiki-ng
- FastAPI: https://fastapi.tiangolo.com
- Docker Compose: https://docs.docker.com/compose

---

## 👥 Credits

### Implementation

- **Application Layer:** MCP Server + IA Agent (vuminhkhanh102002)
- **Controller Layer:** ONOS SDN-WISE integration  
- **MCP Architecture:** Adapted from ehr-aiot-d4genhackathon (hazel260802)
- **Testing Suite:** Automated validation framework
- **Research Direction:** SDN-Based Orchestration for Clustered WSNs

### Technologies

- **SDN-WISE Protocol** - WSN SDN framework
- **ONOS Project** - SDN controller platform
- **Contiki-NG** - IoT operating system  
- **CrewAI** - Multi-agent framework
- **FastAPI** - Modern web framework

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check documentation in `brain/` directory
- Review API docs at `/docs` endpoint

---

**Last Updated:** 2026-01-30  
**Project Status:** MVP Complete (80%)  
**Version:** 1.0.0-alpha
