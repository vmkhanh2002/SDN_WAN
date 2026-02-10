from pathlib import Path
import json
import threading

DATA_DIR = Path(__file__).parent / ".." / "data"
DATA_DIR = DATA_DIR.resolve()


_write_lock = threading.Lock()

def read_json(path: Path):
    if not path.exists():
        return {}
    return json.loads(path.read_text())

def write_json(path: Path, data):
    with _write_lock:
        path.write_text(json.dumps(data, indent=2))

import requests
import os
import logging

logger = logging.getLogger(__name__)

class ONOSClient:
    def __init__(self, base_url=None, auth=None):
        self.base_url = base_url or os.getenv("ONOS_URL", "http://172.28.0.2:8181")
        self.auth = auth or (os.getenv("ONOS_USER", "onos"), os.getenv("ONOS_PASSWORD", "rocks"))
    
    def install_flow(self, flow: dict):
        """Install a flow rule using standard ONOS API"""
        url = f"{self.base_url}/onos/v1/flows"
        
        # deviceId logic: prefer "deviceId" string (of:...), fallback to "nodeId" int
        device_id = flow.get("deviceId")
        if not device_id:
             node_id_int = flow.get("nodeId")
             if node_id_int:
                 # Convert int to hex "of:000...01"
                 device_id = f"of:{int(node_id_int):016x}"
        
        if not device_id:
            return {"status": "error", "message": "Missing deviceId or nodeId"}

        # Construct ONOS flow rule payload 
        # API expects: {"flows": [ ... ]} or directly the flow object?
        # Actually POST /onos/v1/flows expects:
        # { "flows": [ { "priority": 40000, "timeout": 0, "isPermanent": true, "deviceId": "...", "treatment": {...}, "selector": {...} } ] }
        
        payload = {
            "flows": [
                {
                    "deviceId": device_id,
                    "priority": flow.get("priority", 40000),
                    "isPermanent": True,
                    "timeout": 0,
                    "selector": flow.get("selector", {"criteria": []}),
                    "treatment": flow.get("treatment", {"instructions": []})
                }
            ]
        }
        
        try:
            logger.info(f"Installing flow to {device_id}")
            response = requests.post(url, json=payload, auth=self.auth, timeout=5)
            response.raise_for_status()
            return {"status": "success", "message": "Flow installed", "response": response.json()}
        except Exception as e:
            logger.error(f"Failed to install flow: {e}")
            return {"status": "error", "message": str(e)}

# Export singleton
onos_client = ONOSClient()
