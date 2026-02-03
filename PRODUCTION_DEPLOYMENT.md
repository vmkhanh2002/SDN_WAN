# SDN-WISE Production Deployment Guide

## Overview

This guide covers deploying SDN-WISE Full Stack to real hardware in production environment.

---

## Deployment Options

### Option 1: Simulation Mode (Current)
- **Status:** Ready
- **Hardware:** Docker containers only
- **Use Case:** Development, testing, demo
- **Sensors:** Cooja simulation (Contiki-NG)
- **Network:** Mininet emulation

### Option 2: Production Hardware
- **Status:** Ready for deployment
- **Hardware:** Physical sensor nodes required
- **Use Case:** Real deployment, field testing
- **Sensors:** Arduino Pico, ESP32 with XBee
- **Network:** Actual WSN with border router

---

## Production Hardware Deployment

### Step 1: Hardware Requirements

**Control Plane (Server):**
- Linux server (Ubuntu 20.04+)
- 4GB RAM minimum
- Docker and Docker Compose
- Ethernet connection

**Sensor Nodes (minimum 3 nodes):**
- Arduino Pico (RP2040) or ESP32
- XBee IEEE 802.15.4 radio transceiver
- Sensors (temperature, humidity, etc.)
- Power supply (battery or USB)

**Border Router (Sink Node):**
- Arduino/ESP32 board
- XBee radio for WSN
- Ethernet shield or WiFi for IP network
- USB connection to server

**Network:**
- IEEE 802.15.4 wireless network
- Ethernet/WiFi for server connectivity

---

### Step 2: Flash Sensor Firmware

#### Compile Contiki-NG for Hardware

```bash
# Navigate to sensor code
cd controller/onos-simulation/contiki-workspace/sensor

# For Arduino Pico (example)
make TARGET=arduino-pico sensor.hex

# For ESP32 with Contiki port
make TARGET=esp32 sensor.bin

# For Zolertia RE-Mote
make TARGET=zoul sensor
```

#### Flash to Hardware

```bash
# Arduino Pico via USB
avrdude -p atmega2560 -c wiring -P /dev/ttyUSB0 -b 115200 -U flash:w:sensor.hex

# ESP32 via esptool
esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash 0x10000 sensor.bin

# Zolertia via cc2538-bsl
python cc2538-bsl.py -e -w -v sensor.bin -p /dev/ttyUSB1
```

---

### Step 3: Configure Border Router

#### Flash Border Router Firmware

```bash
cd controller/onos-simulation/contiki-workspace/border-router

# Compile for hardware
make TARGET=arduino-pico border-router.hex

# Flash to device
avrdude -p atmega2560 -c wiring -P /dev/ttyUSB2 -b 115200 -U flash:w:border-router.hex
```

#### Start Tunslip6 (IPv6 Bridge)

```bash
# Create IPv6 tunnel between WSN and server
sudo tunslip6 -s /dev/ttyUSB2 fd00::1/64

# This creates tun0 interface bridging:
# - WSN (IEEE 802.15.4) ↔ Border Router ↔ IPv6 (tun0) ↔ Server
```

---

### Step 4: Deploy Docker Stack

#### Update docker-compose.yaml for Production

```yaml
version: '3.8'
services:
  onos-sdn:
    image: onosproject/onos:2.7.0
    container_name: onos-sdn
    network_mode: "host"  # Access tun0 interface
    environment:
      - ONOS_APPS=drivers,openflow,proxyarp,mobility
    volumes:
      - ./controller/onos-apps/wisesdn/target/wisesdn-1.0-SNAPSHOT.oar:/root/onos/apache-karaf-4.2.14/deploy/

  mcp-ia-agent:
    build:
      context: ./application/mcp-server
    container_name: mcp-ia-agent
    network_mode: "host"
    environment:
      - ONOS_URL=http://localhost:8181
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./application/mcp-server/data:/app/data
```

#### Start Production Stack

```bash
# Build and deploy ONOS app
cd controller/onos-apps/wisesdn
mvn clean install
./build-and-deploy.sh

# Start containers
docker-compose -f docker-compose.production.yaml up -d

# Verify
docker ps
curl http://localhost:8181/onos/v1/applications
curl http://localhost:8000/health
```

---

### Step 5: Network Configuration

#### Configure IPv6 Routes

```bash
# Route WSN subnet through tunnel
sudo ip -6 route add fd00::/64 dev tun0

# Verify routing
ping6 fd00::212:7401:1:101  # Example sensor node
```

#### Configure ONOS for SDN-WISE

```bash
# Activate SDN-WISE application
curl -u onos:rocks -X POST \
  http://localhost:8181/onos/v1/applications/org.onosproject.wisesdn/active

# Configure WSN controller port
curl -u onos:rocks -X POST \
  http://localhost:8181/onos/wisesdn/api/config \
  -H "Content-Type: application/json" \
  -d '{"listen_port": 9999}'
```

---

### Step 6: Verify Deployment

#### Check Sensor Connectivity

```bash
# View border router logs
sudo screen /dev/ttyUSB2 115200

# Should see:
# [INFO] SDN-WISE Agent started
# [INFO] Registered with controller at fd00::1
# [INFO] Topology update: 3 nodes discovered
```

#### Test Data Flow

```bash
# Send test command via MCP
curl -X POST http://localhost:8000/tasks/device-orchestration \
  -H "Content-Type: application/json" \
  -d '{
    "action": "send_command",
    "node_id": 2,
    "command": "read_sensor",
    "sensor_type": "temperature"
  }'

# Check ONOS topology
curl -u onos:rocks http://localhost:8181/onos/v1/topology
```

---

## Simulation Mode Testing

For development without hardware, use simulation mode.

### Run Simulation Tests

```bash
# Test Cooja simulator
docker exec cooja-simulator bash -c "cd /root/contiki-ng && make TARGET=cooja"

# Test Mininet network
docker exec mininet-sdn mn --test pingall

# Test complete stack
python tests/test_simulation.py
```

---

## Monitoring Production

### Metrics to Track

1. **WSN Health:**
   - Node uptime
   - Battery levels
   - Radio link quality (RSSI)
   - Packet delivery ratio

2. **Network Performance:**
   - End-to-end latency
   - Throughput
   - Flow table utilization

3. **System Status:**
   - MCP API response time
   - ONOS controller load
   - Docker container health

### Monitoring Commands

```bash
# Check sensor status
curl http://localhost:8000/tasks/deployment-monitoring \
  -X POST -H "Content-Type: application/json" \
  -d '{"action":"status"}'

# ONOS statistics
curl -u onos:rocks http://localhost:8181/onos/v1/statistics/flows

# Docker metrics
docker stats --no-stream
```

---

## Troubleshooting Production

### Sensor Not Connecting

**Check:**
1. Border router running: `ps aux | grep tunslip6`
2. IPv6 tunnel active: `ip -6 addr show tun0`
3. Firewall allows UDP 9999: `sudo ufw status`
4. Sensor firmware correct: Check serial output

**Fix:**
```bash
# Restart tunslip6
sudo pkill tunslip6
sudo tunslip6 -s /dev/ttyUSB2 fd00::1/64 &

# Reset ONOS flows
curl -u onos:rocks -X DELETE http://localhost:8181/onos/v1/flows
```

### High Latency

**Causes:**
- Radio interference
- Weak signal strength
- Network congestion

**Fix:**
```bash
# Adjust transmission power
curl -X POST http://localhost:8000/tasks/network-configuration \
  -d '{"action":"configure","node_id":2,"tx_power":20}'

# Change channel
curl -X POST http://localhost:8000/tasks/network-configuration \
  -d '{"action":"configure","channel":26}'
```

---

## Production Checklist

Before deploying to production:

- [ ] Hardware tested individually
- [ ] Firmware flashed and verified
- [ ] Border router configured
- [ ] IPv6 networking tested
- [ ] ONOS application deployed
- [ ] MCP server operational
- [ ] End-to-end test passed
- [ ] Monitoring configured
- [ ] Backup procedures established
- [ ] Rollback plan ready

---

## Security Considerations

### Production Security

1. **Authentication:**
   ```bash
   # Change ONOS credentials
   docker exec onos-sdn ./bin/onos-user-password onos NewSecurePassword123
   
   # Add MCP authentication
   # Update application/mcp-server/servers/app.py with JWT middleware
   ```

2. **Encryption:**
   - Enable HTTPS for MCP server
   - Use TLS for ONOS REST API
   - Encrypt WSN traffic (optional)

3. **Firewall:**
   ```bash
   # Allow only required ports
   sudo ufw allow 8000/tcp  # MCP
   sudo ufw allow 8181/tcp  # ONOS
   sudo ufw allow 9999/udp  # SDN-WISE
   ```

---

## Performance Tuning

### ONOS Optimization

```bash
# Increase heap size
docker exec onos-sdn \
  sed -i 's/JAVA_OPTS="-Xms2G -Xmx4G"/JAVA_OPTS="-Xms4G -Xmx8G"/' \
  /opt/onos/options

# Disable unused apps
curl -u onos:rocks -X DELETE \
  http://localhost:8181/onos/v1/applications/org.onosproject.mobility/active
```

### WSN Optimization

```python
# Adjust sample rate
{
  "node_id": 2,
  "sample_interval": 60,  # seconds
  "aggregation": true,
  "compression": "lz77"
}
```

---

## Backup and Recovery

### Backup Configuration

```bash
# Backup ONOS state
docker exec onos-sdn ./bin/onos "app-export" > onos-apps.json

# Backup MCP data
tar -czf mcp-data-backup.tar.gz application/mcp-server/data/

# Backup sensor configs
cp -r controller/onos-simulation/contiki-workspace/ backup/contiki-$(date +%Y%m%d)/
```

### Recovery

```bash
# Restore ONOS
docker exec onos-sdn ./bin/onos "app-import" < onos-apps.json

# Restore MCP data
tar -xzf mcp-data-backup.tar.gz -C application/mcp-server/

# Reflash sensors if needed
./controller/scripts/flash-all-sensors.sh
```

---

Last Updated: 2026-01-30
