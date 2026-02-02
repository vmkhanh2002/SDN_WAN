from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List, Optional
from ..utils import read_json, DATA_DIR
from .plan_execution import PlanExecutionAgent
from datetime import datetime

algorithm_router = APIRouter()


class AlgorithmExecutionAgent:
    """
    Builds and (optionally) executes device activation plans for predefined algorithms:
    - naive_baseline: activate all relevant devices/services continuously
    - sequential_corridor: activate corridor devices one-by-one for T_active seconds
    """

    def __init__(self, devices_path: str = DATA_DIR / "devices.json"):
        self.devices = read_json(devices_path)

    def get_algorithm_options(self, user_intent: Optional[str] = None) -> Dict[str, Any]:
        return {
            "intent": user_intent or "",
            "options": [
                {
                    "key": "naive_baseline",
                    "name": "Naive Sensor Activation (Baseline)",
                    "objective": "Continuous corridor monitoring with all devices/services always on.",
                    "assumptions": [
                        "Linear corridor deployment",
                        "Each device has motion sensor and ESP32 camera",
                        "Fixed local coverage; no prediction/optimization",
                    ],
                    "tradeoffs": {
                        "energy": "very high",
                        "redundancy": "high",
                        "latency": "low",
                    },
                },
                {
                    "key": "sequential_corridor",
                    "name": "Cellulaire Sequential Corridor Activation",
                    "objective": "Activate devices sequentially along corridor; request video on motion only.",
                    "assumptions": [
                        "Linear corridor deployment",
                        "Each device has motion sensor and ESP32 camera",
                        "Fixed local coverage; no prediction/optimization; 20s per device",
                    ],
                    "parameters": {"T_active_seconds": 20},
                    "tradeoffs": {
                        "energy": "high",
                        "redundancy": "medium",
                        "latency": "medium",
                    },
                },
            ],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _corridor_devices(self, devices: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        source = devices if devices is not None else self.devices
        return [d for d in source if str(d.get("location", "")).lower() == "corridor"]

    def build_plan(
        self,
        algorithm_key: str,
        devices: Optional[List[Dict[str, Any]]] = None,
        t_active_seconds: int = 20,
        plan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        corridor = self._corridor_devices(devices)
        if not corridor:
            # Fallback: include any camera-capable devices if corridor list is empty
            corridor = [d for d in (devices or self.devices) if any(s.get("name") == "camera" for s in d.get("services", []))]

        if algorithm_key == "naive_baseline":
            steps = []
            for dev in corridor:
                # Activate motion sensor if present
                motion_service = next((s for s in dev.get("services", []) if s.get("name") in ["motion", "motion_detection"]), None)
                if motion_service:
                    steps.append({
                        "instruction": "activate_service",
                        "device_id": dev.get("device_id") or dev.get("deviceId") or dev.get("id"),
                        "service": motion_service.get("name"),
                        "parameters": {"mode": "continuous"},
                        "timeout_ms": 5000,
                    })
                # Keep camera on to emulate immediate streaming on motion
                cam_service = next((s for s in dev.get("services", []) if s.get("name") == "camera"), None)
                if cam_service:
                    steps.append({
                        "instruction": "activate_service",
                        "device_id": dev.get("device_id") or dev.get("deviceId") or dev.get("id"),
                        "service": "camera",
                        "parameters": {"stream": "on"},
                        "timeout_ms": 5000,
                    })

            # Build execution schedule: all devices start at t=0 continuously
            schedule_entries = []
            for idx, dev in enumerate(corridor):
                dev_id = dev.get("device_id") or dev.get("deviceId") or dev.get("id")
                services = [s.get("name") for s in dev.get("services", []) if s.get("name") in ["motion", "motion_detection", "camera"]]
                schedule_entries.append({
                    "order": idx + 1,
                    "device_id": dev_id,
                    "start_offset_ms": 0,
                    "duration_ms": None,
                    "duration_label": "continuous",
                    "services": services,
                })

            plan = {
                "plan_id": plan_id or "naive-baseline-corridor",
                "devices": corridor,
                "algorithm": {
                    "type": "parallel",
                    "description": "All relevant devices/services activated continuously",
                    "steps": steps,
                    "schedule": {
                        "timeline_start": datetime.utcnow().isoformat() + "Z",
                        "entries": schedule_entries,
                        "timeline_total_ms": None,
                        "timeline_label": "continuous activation",
                    }
                },
            }
            return plan

        elif algorithm_key == "sequential_corridor":
            steps = []
            for dev in corridor:
                device_id = dev.get("device_id") or dev.get("deviceId")
                # Activate motion; if motion is detected, request video (modeled as camera activation with a longer timeout)
                motion_service = next((s for s in dev.get("services", []) if s.get("name") in ["motion", "motion_detection"]), None)
                if motion_service:
                    steps.append({
                        "instruction": "activate_service",
                        "device_id": device_id,
                        "service": motion_service.get("name"),
                        "parameters": {"mode": "monitor"},
                        "timeout_ms": t_active_seconds * 1000,
                    })
                cam_service = next((s for s in dev.get("services", []) if s.get("name") == "camera"), None)
                if cam_service:
                    steps.append({
                        "instruction": "activate_service",
                        "device_id": device_id,
                        "service": "camera",
                        "parameters": {"on_motion": True},
                        "timeout_ms": t_active_seconds * 1000,
                    })
                # Deactivate before moving to next
                if motion_service:
                    steps.append({
                        "instruction": "deactivate_service",
                        "device_id": device_id,
                        "service": motion_service.get("name"),
                        "parameters": {},
                        "timeout_ms": 2000,
                    })
                if cam_service:
                    steps.append({
                        "instruction": "deactivate_service",
                        "device_id": device_id,
                        "service": "camera",
                        "parameters": {},
                        "timeout_ms": 2000,
                    })
            # Build sequential execution schedule
            schedule_entries = []
            offset_ms = 0
            active_ms = t_active_seconds * 1000
            gap_ms = 2000
            for idx, dev in enumerate(corridor):
                dev_id = dev.get("device_id") or dev.get("deviceId")
                services = [s.get("name") for s in dev.get("services", []) if s.get("name") in ["motion", "motion_detection", "camera"]]
                schedule_entries.append({
                    "order": idx + 1,
                    "device_id": dev_id,
                    "start_offset_ms": offset_ms,
                    "duration_ms": active_ms,
                    "services": services,
                })
                offset_ms += active_ms + gap_ms

            plan = {
                "plan_id": plan_id or "sequential-corridor-activation",
                "devices": corridor,
                "algorithm": {
                    "type": "sequential",
                    "description": f"Activate corridor devices one-by-one for {t_active_seconds}s",
                    "steps": steps,
                    "schedule": {
                        "timeline_start": datetime.utcnow().isoformat() + "Z",
                        "entries": schedule_entries,
                        "timeline_total_ms": offset_ms,
                        "timeline_label": f"sequential {t_active_seconds}s per device (+{gap_ms}ms gaps)",
                    }
                },
            }
            return plan

        else:
            raise ValueError(f"Unknown algorithm key: {algorithm_key}")

    def execute_algorithm(
        self,
        algorithm_key: str,
        devices: Optional[List[Dict[str, Any]]] = None,
        t_active_seconds: int = 20,
        dry_run: bool = True,
        plan_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        plan = self.build_plan(algorithm_key, devices, t_active_seconds, plan_id)
        result: Dict[str, Any]
        if dry_run:
            result = {"status": "plan_ready", "plan": plan}
        else:
            executor = PlanExecutionAgent()
            result = executor.execute_plan(plan)
        result["algorithm_key"] = algorithm_key
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        return result


@algorithm_router.post("/algorithm-execution")
def algorithm_execution(payload: Dict[str, Any], response: Response):
    try:
        agent = AlgorithmExecutionAgent()
        action = payload.get("action", "options")

        if action == "options":
            intent = payload.get("intent")
            return agent.get_algorithm_options(intent)

        elif action == "build_plan":
            key = payload.get("algorithm_key")
            if not key:
                raise ValueError("algorithm_key is required for build_plan")
            t_active = int(payload.get("t_active_seconds", 20))
            devices = payload.get("devices")  # optional, allow caller filtering
            plan_id = payload.get("plan_id")
            plan = agent.build_plan(key, devices, t_active, plan_id)
            return {
                "action": "build_plan",
                "algorithm_key": key,
                "plan": plan,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }

        elif action == "execute":
            key = payload.get("algorithm_key")
            if not key:
                raise ValueError("algorithm_key is required for execute")
            t_active = int(payload.get("t_active_seconds", 20))
            devices = payload.get("devices")
            dry_run = bool(payload.get("dry_run", True))
            plan_id = payload.get("plan_id")
            result = agent.execute_algorithm(key, devices, t_active, dry_run, plan_id)
            result["action"] = "execute"
            return result

        else:
            raise ValueError(f"Unknown action: {action}")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
