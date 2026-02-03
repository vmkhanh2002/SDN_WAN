from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List, Optional
from ..utils import read_json, DATA_DIR
from ..agents import run_agent
import logging
from datetime import datetime, timedelta

deployment_router = APIRouter()


class DeploymentMonitoringAgent:
    """
    Deployment Monitoring Agent responsible for maintaining an up-to-date data structure
    that records the status of each device and its connectivity within the deployment.
    
    For each device, it provides:
    - IP address
    - Status (active, inactive, idle, sleep, deep_sleep, etc.)
    - Location (x, y, z coordinates)
    - Services (microservices with protocol and details)
    - Connectivity information
    
    Schema:
    - Device: deviceId, IP, status, location (x,y,z), services
    - Services: name, protocol (HTTP/REST, MQTT, etc.), details
    - Connectivity: last_seen timestamp
    """

    def __init__(self, deployment_path: str = DATA_DIR / "deployment_monitoring.json"):
        self.deployment_path = deployment_path
        self.deployment_data = read_json(deployment_path)
        self.devices = self.deployment_data.get("devices", [])
        self.locations = self.deployment_data.get("locations", [])
        self.network_config = self.deployment_data.get("network_config", {})
        self.logger = logging.getLogger(__name__)

    def _load_and_enrich_devices(self) -> List[Dict[str, Any]]:
        """Load devices and enrich with deployment monitoring data."""
        devices = read_json(self.devices_path)
        
        # Ensure each device has complete monitoring information
        for device in devices:
            if "ip" not in device:
                device["ip"] = self._generate_ip(device.get("deviceId", "unknown"))
            if "location" not in device:
                device["location"] = {"x": 0, "y": 0, "z": 0}
            if "services" not in device:
                device["services"] = self._infer_services(device.get("type", "unknown"))
            if "connectivity" not in device:
                device["connectivity"] = {
                    "signal_strength": 100,
                    "last_heartbeat": device.get("lastSeen", ""),
                    "connection_type": "ethernet"
                }
        
        return devices

    def _generate_ip(self, device_id: str) -> str:
        """Generate a consistent IP address based on device ID."""
        hash_val = sum(ord(c) for c in device_id) % 256
        return f"192.168.1.{hash_val}"

    def _infer_services(self, device_type: str) -> List[Dict[str, Any]]:
        """Infer available services based on device type."""
        service_map = {
            "camera": [
                {
                    "name": "camera",
                    "path": "/camera",
                    "protocol": "HTTPS",
                    "details": {
                        "field_of_view": 90,
                        "detection_area": "corridor",
                        "resolution": "1920x1080",
                        "sampling_frequency": 30
                    }
                },
                {
                    "name": "health",
                    "path": "/health",
                    "protocol": "HTTP",
                    "details": {}
                }
            ],
            "sensor": [
                {
                    "name": "temperature",
                    "path": "/temperature",
                    "protocol": "MQTT",
                    "details": {
                        "unit": "celsius",
                        "sampling_frequency": 1
                    }
                },
                {
                    "name": "health",
                    "path": "/health",
                    "protocol": "HTTP",
                    "details": {}
                }
            ],
            "actuator": [
                {
                    "name": "control",
                    "path": "/control",
                    "protocol": "HTTP",
                    "details": {}
                },
                {
                    "name": "health",
                    "path": "/health",
                    "protocol": "HTTP",
                    "details": {}
                }
            ]
        }
        return service_map.get(device_type, [
            {
                "name": "health",
                "path": "/health",
                "protocol": "HTTP",
                "details": {}
            }
        ])

    def get_device_info(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get complete information about a specific device."""
        device = next((d for d in self.devices if d.get("deviceId") == device_id), None)
        return device

    def query_devices_by_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Query devices in a specific location."""
        results = []
        for device in self.devices:
            device_location = device.get("location", {})
            # Match by location_id or corridor/room references
            if (location_id.lower() in str(device.get("name", "")).lower() or
                location_id.lower() in str(device_location).lower()):
                results.append(device)
        return results

    def query_devices_by_service(self, service_name: str) -> List[Dict[str, Any]]:
        """Query devices that provide a specific service."""
        results = []
        for device in self.devices:
            services = device.get("services", [])
            for service in services:
                if service_name.lower() in service.get("name", "").lower():
                    results.append(device)
                    break
        return results

    def query_devices_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Query devices by their current status."""
        return [d for d in self.devices if d.get("status", "").lower() == status.lower()]

    def query_devices_by_location_and_capability(
        self, 
        location: Optional[str] = None,
        capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query devices by location and capability.
        
        Examples:
        - "Which devices are available in the corridor and can stream video?"
        - location="corridor", capability="video"
        """
        results = []
        
        for device in self.devices:
            # Check location match
            if location:
                device_location = device.get("location", {})
                location_str = str(device.get("name", "")).lower()
                if location.lower() not in location_str:
                    continue
            
            # Check capability match
            if capability:
                services = device.get("services", [])
                has_capability = any(
                    capability.lower() in service.get("name", "").lower() or
                    capability.lower() in str(service.get("details", "")).lower()
                    for service in services
                )
                if not has_capability:
                    continue
            
            # Add matching device
            results.append(device)
        
        return results

    def get_active_devices(self, minutes: int = 5) -> List[Dict[str, Any]]:
        """Get devices that have been active within the specified time window."""
        now = datetime.utcnow()
        active_devices = []
        
        for device in self.devices:
            last_seen_str = device.get("last_seen", "")
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                if (now - last_seen) < timedelta(minutes=minutes):
                    active_devices.append(device)
            except:
                pass
        
        return active_devices

    def get_device_connectivity(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed connectivity information for a device."""
        device = self.get_device_info(device_id)
        if not device:
            return None
        
        last_seen_str = device.get("last_seen", "")
        try:
            last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
            time_since_seen = datetime.utcnow() - last_seen.replace(tzinfo=None)
            is_online = time_since_seen < timedelta(minutes=5)
        except:
            is_online = False
            time_since_seen = None
        
        return {
            "deviceId": device_id,
            "ip": device.get("ip"),
            "status": device.get("status"),
            "last_seen": last_seen_str,
            "time_since_seen": str(time_since_seen) if time_since_seen else None,
            "is_online": is_online,
            "location": device.get("location")
        }

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get overall deployment status with statistics."""
        total_devices = len(self.devices)
        
        # Count devices by status
        status_counts = {}
        for device in self.devices:
            status = device.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Check connectivity - devices last seen within 5 minutes are considered active
        now = datetime.utcnow()
        active_count = 0
        for device in self.devices:
            last_seen_str = device.get("last_seen", "")
            try:
                last_seen = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                if (now - last_seen) < timedelta(minutes=5):
                    active_count += 1
            except:
                pass
        
        return {
            "total_devices": total_devices,
            "status_breakdown": status_counts,
            "recently_active": active_count,
            "devices": self.devices,
            "network_config": self.network_config,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def monitor(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main monitoring method to handle various deployment queries."""
        action = payload.get("action", "status")
        
        if action == "status":
            return self.get_deployment_status()
        
        elif action == "device_info":
            device_id = payload.get("device_id")
            if not device_id:
                raise ValueError("device_id required for device_info action")
            device_info = self.get_device_info(device_id)
            if not device_info:
                raise ValueError(f"Device {device_id} not found")
            return {"device": device_info}
        
        elif action == "connectivity":
            device_id = payload.get("device_id")
            if not device_id:
                raise ValueError("device_id required for connectivity action")
            connectivity = self.get_device_connectivity(device_id)
            if not connectivity:
                raise ValueError(f"Device {device_id} not found")
            return connectivity
        
        elif action == "query_location":
            location_id = payload.get("location_id")
            if not location_id:
                raise ValueError("location_id required for query_location action")
            devices = self.query_devices_by_location(location_id)
            return {
                "location_id": location_id,
                "devices": devices,
                "count": len(devices)
            }
        
        elif action == "query_service":
            service_name = payload.get("service_name")
            if not service_name:
                raise ValueError("service_name required for query_service action")
            devices = self.query_devices_by_service(service_name)
            return {
                "service_name": service_name,
                "devices": devices,
                "count": len(devices)
            }
        
        elif action == "query_status":
            status = payload.get("status")
            if not status:
                raise ValueError("status required for query_status action")
            devices = self.query_devices_by_status(status)
            return {
                "status": status,
                "devices": devices,
                "count": len(devices)
            }
        
        elif action == "query_capability":
            location_id = payload.get("location_id")
            capability = payload.get("capability")
            if not location_id or not capability:
                raise ValueError("location_id and capability required for query_capability action")
            devices = self.query_devices_by_location_and_capability(location_id, capability)
            return {
                "location_id": location_id,
                "capability": capability,
                "devices": devices,
                "count": len(devices)
            }
        
        elif action == "active_devices":
            minutes = payload.get("minutes", 5)
            devices = self.get_active_devices(minutes)
            return {
                "time_window_minutes": minutes,
                "devices": devices,
                "count": len(devices)
            }
        
        elif action == "query":
            # Legacy query action for backward compatibility
            query = payload.get("query", "")
            location = payload.get("location")
            capability = payload.get("capability")
            
            # Parse natural language queries
            if "corridor" in query.lower():
                location = "corridor"
            if "video" in query.lower() or "camera" in query.lower():
                capability = "camera"
            if "temperature" in query.lower():
                capability = "temperature"
            
            devices = self.query_devices_by_location_and_capability(location, capability)
            return {
                "query": query,
                "location": location,
                "capability": capability,
                "matching_devices": devices,
                "count": len(devices)
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")


@deployment_router.post("/deployment-monitoring")
def deployment_monitoring(payload: Dict[str, Any], response: Response):
    """
    Deployment Monitoring endpoint.
    
    Provides deployment status, device connectivity, and service availability.
    
    Supports actions:
    - status: Get overall deployment status
    - device_info: Get info about a specific device
    - connectivity: Get connectivity info for a device
    - query_location: Get devices in a location
    - query_service: Get devices with a service
    - query_status: Get devices by status
    - query_capability: Get devices by location and capability
    - active_devices: Get recently active devices
    - query (legacy): Natural language query support
    """
    try:
        agent = DeploymentMonitoringAgent()
        result = agent.monitor(payload)
        
        # Add agent name to response
        result["agent"] = "deployment-monitoring-agent"
        
        # Try to run the agent (if available) for additional insights
        try:
            agent_out = run_agent("deployment-monitoring", payload)
            if agent_out is not None:
                result["agent_insights"] = agent_out
                # Detect agent identifiers
                agents_used = []
                if isinstance(agent_out, dict):
                    agents_used.extend([v.get("agent") for v in agent_out.values() if isinstance(v, dict) and v.get("agent")])
                    if agent_out.get("agent"):
                        agents_used.append(agent_out.get("agent"))
                if agents_used:
                    response.headers["X-Server-Agent"] = ",".join(agents_used)
        except Exception as e:
            logging.debug(f"Agent execution optional; continuing: {e}")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.exception("Deployment monitoring error")
        raise HTTPException(status_code=500, detail="Internal server error")
