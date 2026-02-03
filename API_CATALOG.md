# SDN-WISE Full Stack - Complete API Catalog

## Total APIs: 16 Endpoints

### MCP Server APIs: 10 endpoints
### ONOS Controller APIs: 6 endpoints

---

## MCP SERVER APIs (Application Layer)

Base URL: `http://localhost:8000`

### 1. Root Endpoint
```
GET /
```
**Purpose:** Service information and endpoint directory

**Response:**
```json
{
  "status": "healthy",
  "service": "SDN-WISE MCP Server",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "docs": "/docs",
    "tasks": "/tasks/*"
  }
}
```

**Use Case:** Check if server is running and discover available endpoints

---

### 2. Health Check
```
GET /health
```
**Purpose:** Verify server health and ONOS connectivity

**Response:**
```json
{
  "status": "healthy",
  "onos_url": "http://172.25.0.2:8181",
  "data_dir": "/application/mcp-server/data",
  "agents_available": true
}
```

**Use Case:** System monitoring, readiness probe

---

### 3. API Documentation
```
GET /docs
```
**Purpose:** Interactive Swagger UI

**Response:** HTML page with interactive API explorer

**Use Case:** API discovery, testing, and documentation

---

### 4. Device Orchestration
```
POST /tasks/device-orchestration
```
**Purpose:** Translate user intent into detailed execution plans

**Request:**
```json
{
  "action": "generate_plan",
  "intent": "Route temperature data to sink"
}
```

**Response:**
```json
{
  "plan_id": "plan-123",
  "devices": ["sensor-1", "sensor-2", "sink"],
  "steps": [...]
}
```

**Use Case:** Convert natural language commands to network actions

---

### 5. Deployment Monitoring
```
POST /tasks/deployment-monitoring
```
**Purpose:** Monitor device status, location, and connectivity

**Request:**
```json
{
  "action": "status"
}
```

**Response:**
```json
{
  "total_devices": 6,
  "online": 5,
  "offline": 1,
  "status_breakdown": {...}
}
```

**Use Case:** Track network health, device availability

---

### 6. Network Configuration
```
POST /tasks/network-configuration
```
**Purpose:** Configure network settings and OTA firmware updates

**Request:**
```json
{
  "action": "configure",
  "device_id": "sensor-1",
  "config": {
    "sample_rate": 60,
    "transmit_power": 15
  }
}
```

**Response:**
```json
{
  "status": "configured",
  "device_id": "sensor-1",
  "applied_config": {...}
}
```

**Use Case:** Remote device configuration, firmware management

---

### 7. Plan Validation
```
POST /tasks/plan-validation
```
**Purpose:** Validate plans against security, energy, location constraints

**Request:**
```json
{
  "action": "validate",
  "plan": {
    "flow_rules": [...],
    "affected_devices": [...]
  }
}
```

**Response:**
```json
{
  "valid": true,
  "constraints_checked": ["security", "energy", "location"],
  "violations": []
}
```

**Use Case:** Ensure plans meet policy requirements before execution

---

### 8. Plan Execution
```
POST /tasks/plan-execution
```
**Purpose:** Execute orchestration plans by translating to device commands

**Request:**
```json
{
  "action": "execute",
  "plan_id": "plan-123"
}
```

**Response:**
```json
{
  "execution_id": "exec-456",
  "status": "in_progress",
  "devices_affected": 5
}
```

**Use Case:** Deploy network configurations across WSN

---

### 9. Access Control
```
POST /tasks/access-control
```
**Purpose:** Manage user permissions, roles, and credentials

**Request:**
```json
{
  "action": "check",
  "user": "admin",
  "resource": "device-1",
  "permission": "write"
}
```

**Response:**
```json
{
  "allowed": true,
  "user": "admin",
  "roles": ["administrator"]
}
```

**Use Case:** Authorization, role-based access control

---

### 10. Algorithm Execution
```
POST /tasks/algorithm-execution
```
**Purpose:** Execute custom algorithms and data processing

**Request:**
```json
{
  "action": "execute",
  "algorithm": "clustering",
  "parameters": {
    "method": "k-means",
    "k": 3
  }
}
```

**Response:**
```json
{
  "result": {
    "clusters": [...],
    "execution_time_ms": 250
  }
}
```

**Use Case:** Run network optimization algorithms, data analytics

---

## ONOS CONTROLLER APIs (Control Plane)

Base URL: `http://172.25.0.2:8181`  
Authentication: Basic (onos/rocks)

### 11. Applications
```
GET /onos/v1/applications
```
**Purpose:** List all installed ONOS applications

**Response:**
```json
{
  "applications": [
    {
      "name": "org.onosproject.openflow",
      "id": 1,
      "version": "2.7.0",
      "state": "ACTIVE"
    },
    ...
  ]
}
```

**Use Case:** Verify ONOS app deployment status

---

### 12. Devices
```
GET /onos/v1/devices
```
**Purpose:** Discover all network devices

**Response:**
```json
{
  "devices": [
    {
      "id": "of:0000000000000001",
      "type": "SWITCH",
      "available": true,
      "role": "MASTER"
    },
    ...
  ]
}
```

**Use Case:** Network topology discovery, device inventory

---

### 13. Flow Rules
```
GET /onos/v1/flows
POST /onos/v1/flows
```
**Purpose:** Manage flow rules on devices

**GET Response:**
```json
{
  "flows": [
    {
      "deviceId": "of:0000000000000001",
      "tableId": 0,
      "priority": 100,
      "selector": {...},
      "treatment": {...}
    },
    ...
  ]
}
```

**POST Request:**
```json
{
  "flows": [
    {
      "deviceId": "of:0000000000000001",
      "priority": 100,
      "selector": {
        "criteria": [
          {"type": "ETH_TYPE", "ethType": "0x0800"}
        ]
      },
      "treatment": {
        "instructions": [
          {"type": "OUTPUT", "port": "2"}
        ]
      }
    }
  ]
}
```

**Use Case:** Install forwarding rules, control packet routing

---

### 14. Topology
```
GET /onos/v1/topology
```
**Purpose:** Get network topology graph

**Response:**
```json
{
  "time": 1706636400000,
  "devices": 4,
  "links": 6,
  "clusters": 1
}
```

**Use Case:** Visualize network structure, path computation

---

### 15. Hosts
```
GET /onos/v1/hosts
```
**Purpose:** List discovered end hosts

**Response:**
```json
{
  "hosts": [
    {
      "id": "00:00:00:00:00:01/None",
      "mac": "00:00:00:00:00:01",
      "vlan": "None",
      "ipAddresses": ["10.0.0.1"],
      "locations": [
        {
          "elementId": "of:0000000000000001",
          "port": "1"
        }
      ]
    },
    ...
  ]
}
```

**Use Case:** Track end devices, MAC-IP mapping

---

### 16. Links
```
GET /onos/v1/links
```
**Purpose:** List network links between devices

**Response:**
```json
{
  "links": [
    {
      "src": {
        "device": "of:0000000000000001",
        "port": "2"
      },
      "dst": {
        "device": "of:0000000000000002",
        "port": "1"
      },
      "type": "DIRECT",
      "state": "ACTIVE"
    },
    ...
  ]
}
```

**Use Case:** Topology visualization, link failure detection

---

## API Usage Flow

### Typical Workflow:

1. **User Intent** → POST `/tasks/device-orchestration`
   - Translate "Route sensor data" to execution plan

2. **Validate Plan** → POST `/tasks/plan-validation`
   - Check against constraints

3. **Execute Plan** → POST `/tasks/plan-execution`
   - Deploy configuration

4. **Monitor Status** → POST `/tasks/deployment-monitoring`
   - Track execution progress

5. **Install Flows** → POST `/onos/v1/flows`
   - Push rules to ONOS controller

6. **Verify Topology** → GET `/onos/v1/topology`
   - Confirm network state

---

## Testing All APIs

Run comprehensive test:
```powershell
.\tests\test_all_apis.ps1
```

This will:
- Test all 16 endpoints
- Show pass/fail status
- Display response samples
- Generate summary report

---

## API Categories

### **Control APIs** (3)
- `/` - Service info
- `/health` - Health check
- `/docs` - Documentation

### **Orchestration APIs** (7)
- `/tasks/device-orchestration` - Intent translation
- `/tasks/deployment-monitoring` - Status monitoring
- `/tasks/network-configuration` - Device config
- `/tasks/plan-validation` - Constraint checking
- `/tasks/plan-execution` - Plan deployment
- `/tasks/access-control` - Permission management
- `/tasks/algorithm-execution` - Algorithm running

### **SDN Controller APIs** (6)
- `/onos/v1/applications` - App management
- `/onos/v1/devices` - Device discovery
- `/onos/v1/flows` - Flow management
- `/onos/v1/topology` - Network graph
- `/onos/v1/hosts` - Host tracking
- `/onos/v1/links` - Link discovery

---

## Authentication

### MCP Server
No authentication (development mode)

### ONOS Controller
HTTP Basic Authentication
- Username: `onos`
- Password: `rocks`

---

Last Updated: 2026-01-30
