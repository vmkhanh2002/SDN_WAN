# How to Run SDN-WISE Full Stack

**Quick Start Guide** — Get the project running in under 5 minutes

---

## Prerequisites

Before starting, ensure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Docker Compose** (included with Docker Desktop)
- ✅ **Windows PowerShell** or **Git Bash**
- ✅ At least **8GB RAM** available for containers
- ✅ Ports available: **8000**, **8181**, **8101**, **6653**, **5900**, **6000**

---

## Quick Start (5 Minutes)

### 1. Start All Services

```powershell
# Navigate to project directory
cd c:\Users\boyva\Downloads\Lab\SDN_WAN

# Start all Docker containers
docker-compose up -d

# Wait ~60 seconds for ONOS healthcheck to pass
# Other services will start automatically after ONOS is healthy
```

### 2. Verify Services Are Running

```powershell
# Check container status
docker ps

# You should see 4 containers running:
# - onos-sdn (172.28.0.2)
# - mininet-sdn (172.28.0.3)
# - cooja-simulator (172.28.0.4)
# - mcp-ia-agent (172.28.0.5)
```

### 3. Test the APIs

```powershell
# Test MCP Server health
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Test ONOS Controller
Invoke-WebRequest -Uri "http://localhost:8181/onos/v1/applications" -Credential (Get-Credential)
# Username: onos
# Password: rocks
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MCP Server API** | http://localhost:8000 | None |
| **MCP API Docs** | http://localhost:8000/docs | None |
| **ONOS GUI** | http://localhost:8181/onos/ui | onos / rocks |
| **ONOS REST API** | http://localhost:8181/onos/v1 | onos / rocks |
| **Cooja VNC** | vnc://localhost:5900 | None |

---

## Detailed Service Access

### MCP Server (Application Layer)

The MCP Server provides intelligent orchestration via REST APIs.

**Access API Documentation:**
```powershell
# Open in browser
start http://localhost:8000/docs
```

**Test Endpoint:**
```powershell
# Get deployment status
$body = '{"action":"status"}'
Invoke-WebRequest -Uri "http://localhost:8000/tasks/deployment-monitoring" `
  -Method POST -Body $body -ContentType "application/json"
```

---

### ONOS Controller (Control Plane)

ONOS provides SDN controller functionality.

**Access Web GUI:**
```powershell
# Open in browser (credentials: onos/rocks)
start http://localhost:8181/onos/ui
```

**Query Devices:**
```powershell
# List all network devices
curl -u onos:rocks http://localhost:8181/onos/v1/devices
```

**Query Applications:**
```powershell
# List installed ONOS applications
curl -u onos:rocks http://localhost:8181/onos/v1/applications
```

---

### Mininet (Network Emulation)

Mininet emulates network topologies for testing.

**Access Container:**
```powershell
docker exec -it mininet-sdn bash
```

**Create Test Topology:**
```bash
# Inside mininet container
mn --controller=remote,ip=172.28.0.2 --topo=tree,2

# Test connectivity
mininet> pingall
mininet> exit
```

---

### Cooja Simulator (WSN Simulation)

Cooja simulates wireless sensor networks using Contiki-NG.

**Access Container:**
```powershell
docker exec -it cooja-simulator bash
```

**Compile Sensor Code:**
```bash
# Inside cooja container
cd /workspace
make TARGET=cooja sensor-node.c
```

**Run Simulation (with GUI via VNC):**
1. Connect to VNC: `localhost:5900`
2. Launch Cooja simulator
3. Load simulation: `/root/simulations/wsn-topology.csc`

---

## Running Tests

### Full API Test Suite

Run comprehensive tests for all 16 API endpoints:

```powershell
cd c:\Users\boyva\Downloads\Lab\SDN_WAN\tests
.\test_all_apis.ps1
```

This will test:
- 9 MCP Server endpoints
- 6 ONOS Controller endpoints
- 1 API documentation endpoint

### Python Test Suite

```powershell
# Run all Python tests
cd c:\Users\boyva\Downloads\Lab\SDN_WAN\tests
python test_suite.py
```

---

## Common Tasks

### View Container Logs

```powershell
# View MCP server logs
docker-compose logs -f mcp-ia-agent

# View ONOS logs
docker-compose logs -f onos-sdn

# View all logs
docker-compose logs -f
```

### Restart a Service

```powershell
# Restart ONOS (useful if OpenFlow port 6653 not listening)
docker-compose restart onos-sdn

# Wait 60 seconds for healthcheck
Start-Sleep -Seconds 60

# Restart MCP server
docker-compose restart mcp-ia-agent
```

### Rebuild Containers

```powershell
# Rebuild and restart all services
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Stopping Services

### Stop All Services

```powershell
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps data volumes)
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```

---

## Troubleshooting

### Issue: ONOS OpenFlow Port 6653 Not Listening

**Symptom:** Mininet switches can't connect, `devices` list is empty

**Fix:**
```powershell
# Restart ONOS container
docker-compose restart onos-sdn
Start-Sleep -Seconds 60

# Verify port is listening
docker exec onos-sdn netstat -tuln | Select-String "6653"
```

---

### Issue: MCP Server Can't Connect to ONOS

**Symptom:** MCP health endpoint shows ONOS connection error

**Fix:**
```powershell
# Check ONOS is healthy
docker exec onos-sdn curl -u onos:rocks http://localhost:8181/onos/v1/applications

# Check network connectivity
docker exec mcp-ia-agent ping -c 3 172.28.0.2

# Restart MCP server
docker-compose restart mcp-ia-agent
```

---

### Issue: Custom REST API Returns 404

**Symptom:** `/onos/wisesdn/...` endpoints return 404 Not Found

**Status:** Known issue - OSGi Web Context not mounting properly

**Workaround:** Use standard ONOS REST API (`/onos/v1/*`) instead, or manage custom logic in MCP layer

---

### Issue: Port Already in Use

**Symptom:** Error "port is already allocated" when starting containers

**Fix:**
```powershell
# Find what's using the port (example for port 8000)
netstat -ano | Select-String ":8000"

# Stop the conflicting process or change port in docker-compose.yaml
```

---

### Issue: Containers Keep Restarting

**Fix:**
```powershell
# Check container logs for errors
docker-compose logs

# Check system resources
docker stats

# Ensure sufficient disk space and memory
```

---

## Network Information

All containers run on the `sdn-network` bridge network:

| Container | IP Address | Hostname |
|-----------|------------|----------|
| onos-sdn | 172.28.0.2 | onos |
| mininet-sdn | 172.28.0.3 | mininet |
| cooja-simulator | 172.28.0.4 | cooja |
| mcp-ia-agent | 172.28.0.5 | mcp |

**Gateway:** 172.28.0.1  
**Subnet:** 172.28.0.0/24

---

## Next Steps

Once everything is running:

1. ✅ **Explore the API** — Visit http://localhost:8000/docs
2. ✅ **Check ONOS GUI** — Visit http://localhost:8181/onos/ui
3. ✅ **Run Tests** — Execute `.\tests\test_all_apis.ps1`
4. ✅ **Read Documentation** — See [README.md](README.md) for architecture details
5. ✅ **Check Status** — See [PROJECT_STATUS.md](PROJECT_STATUS.md) for known issues

---

## Additional Resources

- **Full Architecture**: [README.md](README.md)
- **API Catalog**: [API_CATALOG.md](API_CATALOG.md) (16 endpoints)
- **Project Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Production Deployment**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)


---

**Last Updated:** 2026-02-10  
**Status:** Ready to Run ✅
