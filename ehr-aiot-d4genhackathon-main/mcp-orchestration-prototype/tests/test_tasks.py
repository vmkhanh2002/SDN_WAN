import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from servers.app import app
import json

client = TestClient(app)

# Test cases aligned with task implementations
test_cases = [
    # ============ LLM-based Orchestration Tests ============
    {
        "name": "Orchestration - Generate Plan from Intent",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "generate_plan",
            "intent": "Activate all high-precision sensors with simultaneous high-frequency sampling"
        }
    },
    {
        "name": "Orchestration - Execute Intent (Generate & Execute)",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "execute_intent",
            "intent": "Which devices are available in the corridor and can stream video?"
        }
    },
    {
        "name": "Orchestration - Execute Specific Plan",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "execute",
            "plan_id": "environmental-monitoring"
        }
    },
    {
        "name": "Orchestration - List Available Plans",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "list_plans"
        }
    },
    {
        "name": "Orchestration - Analyze Plan",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "analyze",
            "plan_id": "camera-corridor-monitoring"
        }
    },
    
    # ============ Deployment Monitoring Tests ============
    {
        "name": "Deployment Monitoring - Get Status",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "status"
        }
    },
    {
        "name": "Deployment Monitoring - Query by Capability",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "query_capability",
            "location_id": "corridor",
            "capability": "camera"
        }
    },
    {
        "name": "Deployment Monitoring - Query by Service",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "query_service",
            "service_name": "temperature"
        }
    },
    {
        "name": "Deployment Monitoring - Query by Status",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "query_status",
            "status": "active"
        }
    },
    {
        "name": "Deployment Monitoring - Get Device Info",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "device_info",
            "device_id": "esp32-001"
        }
    },
    {
        "name": "Deployment Monitoring - Get Connectivity",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "connectivity",
            "device_id": "esp32-002"
        }
    },
    {
        "name": "Deployment Monitoring - Active Devices",
        "endpoint": "/tasks/deployment-monitoring",
        "payload": {
            "action": "active_devices",
            "minutes": 5
        }
    },
    
    # ============ Legacy Device Orchestration Tests ============
    {
        "name": "Legacy: Device Orchestration - Restart Device",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "restart",
            "deviceId": "iot-001"
        }
    },
    {
        "name": "Legacy: Device Orchestration - Provision Device",
        "endpoint": "/tasks/device-orchestration",
        "payload": {
            "action": "provision",
            "deviceId": "iot-002"
        }
    },
    {
        "name": "Network Monitoring",
        "endpoint": "/tasks/network-monitoring",
        "payload": {}
    },
    {
        "name": "Verification",
        "endpoint": "/tasks/verification",
        "payload": {}
    }
]

for test in test_cases:
    r = client.post(test["endpoint"], json=test["payload"])
    print("\n" + "="*50)
    print(f"Test: {test['name']}")
    print(f"Endpoint: {test['endpoint']}")
    print(f"Status: {r.status_code}")
    agent_header = r.headers.get('X-Server-Agent', 'N/A')
    print(f"Agent(s): {agent_header}")
    try:
        body = r.json()
        print("\nResponse:")
        print(json.dumps(body, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"\nResponse (text):")
        print(r.text)
    print("="*50 + "\n")
