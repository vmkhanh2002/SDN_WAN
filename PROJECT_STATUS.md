# Project Status — SDN-WISE IoT Platform
**Last Updated**: 2026-02-10 09:47

## Quick Start

**Want to run the project?** See [HOW_TO_RUN.md](HOW_TO_RUN.md) for step-by-step instructions.

**TL;DR**: `docker-compose up -d` → wait 60s → visit http://localhost:8000/docs

---

## Overall Health: 🟡 Mostly Working

✅ **What's Working:**
- Docker infrastructure (all 4 containers start correctly)
- MCP Server (FastAPI + Uvicorn) on port 8000
- ONOS standard REST API (`/onos/v1/*`)
- Mininet network emulation (L3 connectivity)
- Cooja simulator environment ready
- Test suite (16 API endpoints)

⚠️ **Known Issues:**
- ONOS Custom REST API returns 404 (`/onos/wisesdn/*` endpoints)
- OpenFlow port 6653 intermittently fails to listen
- SDN-WISE WAB context not registering properly

📊 **Overall Status:** 80% complete — Core infrastructure ready, integration pending

---

## Architecture (3-Layer)

```
SDN_WAN/
├── application/          # Layer 3 — MCP Server + AI Agents
│   ├── mcp-server/       #   FastAPI server (Python)
│   ├── ai-agents/        #   Agent logic (placeholder)
│   └── api-gateway/      #   Gateway (placeholder)
├── controller/           # Layer 2 — SDN Controller
│   ├── onos-apps/wisesdn/#   ONOS SDN-WISE Java App (8 source files)
│   ├── onos-simulation/  #   Contiki-NG workspace + Cooja simulations
│   ├── scripts/          #   Entrypoint scripts (mininet, cooja)
│   └── mininet/          #   Mininet topologies (placeholder)
├── device/               # Layer 1 — Sensor Nodes (placeholder)
├── tests/                # Test scripts (Python + PowerShell)
└── docs/                 # Documentation
```

## Docker Services

| Service | Container | Image | Ports | IP |
|---------|-----------|-------|-------|----|
| ONOS Controller | `onos-sdn` | `onosproject/onos:2.7.0` | 8181, 8101, 6653 | 172.28.0.2 |
| Mininet | `mininet-sdn` | Custom (`Dockerfile.mininet`) | — | 172.28.0.3 |
| Cooja Simulator | `cooja-simulator` | Custom (`Dockerfile.contiki`) | 5900, 6000 | 172.28.0.4 |
| MCP Server | `mcp-ia-agent` | Custom (`application/mcp-server/Dockerfile`) | 8000 | 172.28.0.5 |

**Network**: `sdn-network` — `172.28.0.0/24`

### How to Start
```bash
docker-compose up -d
```
Wait ~60s for ONOS healthcheck, then all dependent services start automatically.

### How to Stop
```bash
docker-compose down
```

## Component Status

### ONOS Controller (`onos-sdn`) — Partial
| Feature | Status | Notes |
|---------|--------|-------|
| Container startup | OK | Healthy via REST healthcheck |
| Standard REST API (`/onos/v1/...`) | OK | Devices, Apps, Flows all respond |
| OpenFlow listener (port 6653) | **Issue** | Port not always listening; Mininet switches may fail to connect |
| Custom REST API (`/onos/wisesdn/...`) | **Issue** | Returns 404 — OSGi Web Context not activating |
| SDN-WISE Java Logic | OK | `WiseController` compiled, bundle loads in Karaf |

**SDN-WISE App** (`controller/onos-apps/wisesdn/`):
- 8 Java classes: `AppComponent`, `WiseController`, `WiseWebResource`, `WiseWebApplication`, `WisePacket`, `FlowRule`, `FlowTableManager`, `TopologyManager`
- Build: `docker run --rm -v ./controller/onos-apps/wisesdn:/usr/src/app -w /usr/src/app maven:3.8-openjdk-11 mvn clean install -DskipTests`
- Deploy: Hot-deploy JAR to `/root/onos/apache-karaf-4.2.9/deploy/` inside container

### Mininet (`mininet-sdn`) — Partial
| Feature | Status | Notes |
|---------|--------|-------|
| Container startup | OK | OVS ready |
| L3 connectivity to ONOS | OK | `ping 172.28.0.2` works |
| L2 OpenFlow control plane | **Issue** | Depends on ONOS OpenFlow listener |
| Topology creation | Manual | Run `mn --controller=remote,ip=172.28.0.2 --topo=tree,2` inside container |

### Cooja Simulator (`cooja-simulator`) — Ready
| Feature | Status | Notes |
|---------|--------|-------|
| Container startup | OK | Contiki-NG environment ready |
| Simulation file | OK | `wsn-topology.csc` present |
| GUI access | Manual | VNC on port 5900 or X11 on 6000 |

### MCP Server (`mcp-ia-agent`) — OK
| Feature | Status | Notes |
|---------|--------|-------|
| Container startup | OK | FastAPI + Uvicorn |
| Health endpoint | OK | `GET :8000/health` returns healthy |
| ONOS connectivity | OK | Configured to `http://172.28.0.2:8181` |

## Known Issues

### 1. ONOS Custom REST API — 404
The `wisesdn` bundle registers in OSGi but the Web Application Bundle (WAB) context (`/onos/wisesdn/`) does not mount. Jersey/Pax Web integration issue in ONOS 2.7.0 container.

**Impact**: Custom endpoints (`/api/policy/consent`, `/api/policy/register`) are unreachable.
**Workaround**: Use standard ONOS REST API (`/onos/v1/devices`) and manage consent state in MCP Agent layer.

### 2. OpenFlow Port 6653
ONOS intermittently fails to listen on 6653, preventing Mininet switches from connecting.

**Impact**: `devices` list empty, `pingall` fails.
**Workaround**: Restart ONOS container (`docker-compose restart onos-sdn`), wait 60s.

## Implementation Progress

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Infrastructure (Docker, networking) | **Done** |
| Phase 2 | Controller Logic (Java — consent, policy, identity) | **Done** (code), **Partial** (deployment) |
| Phase 3 | Application Layer (MCP Tools + Agents) | Not started |
| Phase 4 | Device Layer (Contiki firmware) | Not started |
| Phase 5 | Integration & End-to-End Testing | Not started |

## Credentials
- **ONOS**: `onos` / `rocks`
- **MCP Server**: No auth (development)
