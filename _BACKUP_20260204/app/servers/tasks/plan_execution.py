from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List, Optional
from ..utils import read_json, write_json, DATA_DIR
from ..agents import run_agent
import json
import time
import logging
import requests
from datetime import datetime

execution_router = APIRouter()
logger = logging.getLogger(__name__)


class PlanExecutionAgent:
    """
    Plan Execution Agent responsible for executing orchestration plans.
    
    Translates high-level orchestration plan instructions into concrete device commands:
    - HTTP/REST requests for camera streams, sensor reads, actuator controls
    - MQTT messages for sensor queries and device status
    - Device-specific service invocations with parameter mapping
    
    Flow:
    1. Receive execution plan with list of devices, services, and instructions
    2. For each instruction in sequence:
       a. Resolve device IP and service endpoint
       b. Translate instruction to device protocol (HTTP, MQTT, etc.)
       c. Execute command with parameters
       d. Collect response/status
       e. Update execution history
    3. Monitor execution and handle failures/timeouts
    4. Return execution results with device responses
    """

    def __init__(
        self,
        devices_path: str = DATA_DIR / "devices.json",
        deployment_monitoring_path: str = DATA_DIR / "deployment_monitoring.json",
        execution_history_path: str = DATA_DIR / "execution_history.json"
    ):
        self.devices_path = devices_path
        self.deployment_monitoring_path = deployment_monitoring_path
        self.execution_history_path = execution_history_path
        
        # Load device registry
        self.devices = read_json(devices_path)
        self.deployment = read_json(deployment_monitoring_path)
        self.execution_history = read_json(execution_history_path) if self._file_exists(execution_history_path) else {"executions": []}

    def _file_exists(self, path):
        """Check if file exists."""
        try:
            from pathlib import Path
            return Path(path).exists()
        except:
            return False

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an orchestration plan.
        
        Plan structure:
        {
            "plan_id": "...",
            "devices": [...],
            "algorithm": {
                "type": "sequential|parallel",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {...},
                        "timeout_ms": 5000
                    }
                ]
            }
        }
        """
        plan_id = plan.get("plan_id")
        logger.info(f"Executing plan: {plan_id}")
        
        execution_id = f"exec-{datetime.utcnow().timestamp()}"
        execution_start = datetime.utcnow()
        
        results = {
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "executing",
            "start_time": execution_start.isoformat() + "Z",
            "steps_completed": 0,
            "steps_total": 0,
            "step_results": [],
            "errors": [],
            "device_responses": {}
        }
        
        try:
            algorithm = plan.get("algorithm", {})
            steps = algorithm.get("steps", [])
            execution_type = algorithm.get("type", "sequential")
            
            results["steps_total"] = len(steps)
            results["execution_type"] = execution_type
            
            if execution_type == "parallel":
                results["step_results"] = self._execute_parallel(steps, results)
            else:
                results["step_results"] = self._execute_sequential(steps, results)
            
            results["status"] = "completed"
            results["steps_completed"] = len(results["step_results"])
            
        except Exception as e:
            logger.exception(f"Plan execution failed: {e}")
            results["status"] = "failed"
            results["errors"].append(str(e))
        
        finally:
            execution_end = datetime.utcnow()
            results["end_time"] = execution_end.isoformat() + "Z"
            results["duration_ms"] = int((execution_end - execution_start).total_seconds() * 1000)
            
            # Save execution history
            self._save_execution_history(results)
        
        return results

    def _execute_sequential(self, steps: List[Dict], results: Dict) -> List[Dict]:
        """Execute steps sequentially."""
        step_results = []
        
        for idx, step in enumerate(steps):
            step_id = f"step-{idx}"
            try:
                step_start = time.time()
                step_result = self._execute_step(step, step_id)
                step_duration = time.time() - step_start
                
                step_result["step_index"] = idx
                step_result["duration_ms"] = int(step_duration * 1000)
                step_results.append(step_result)
                
                # Update device responses
                device_id = step.get("id")
                if device_id and step_result.get("status") == "success":
                    if device_id not in results["device_responses"]:
                        results["device_responses"][device_id] = []
                    results["device_responses"][device_id].append({
                        "service": step.get("service"),
                        "response": step_result.get("response")
                    })
                
                logger.info(f"Step {idx} completed: {step_result['status']}")
                
                # Stop on failure if required
                if step_result["status"] == "failed" and step.get("stop_on_error", False):
                    logger.warning(f"Stopping plan execution due to failed step: {step_id}")
                    break
                    
            except Exception as e:
                logger.exception(f"Error executing step {step_id}: {e}")
                step_results.append({
                    "step_id": step_id,
                    "status": "failed",
                    "error": str(e),
                    "step_index": idx
                })
                results["errors"].append(f"Step {idx}: {str(e)}")
        
        return step_results

    def _execute_parallel(self, steps: List[Dict], results: Dict) -> List[Dict]:
        """
        Execute steps in parallel (for independent device operations).
        Note: Simplified version using sequential execution with threading.
        For full parallel execution, use asyncio or ThreadPoolExecutor.
        """
        # For now, execute sequentially but mark as parallel execution
        step_results = []
        
        for idx, step in enumerate(steps):
            step_id = f"step-{idx}"
            try:
                step_start = time.time()
                step_result = self._execute_step(step, step_id)
                step_duration = time.time() - step_start
                
                step_result["step_index"] = idx
                step_result["duration_ms"] = int(step_duration * 1000)
                step_results.append(step_result)
                
                # Update device responses
                device_id = step.get("device_id")
                if device_id and step_result.get("status") == "success":
                    if device_id not in results["device_responses"]:
                        results["device_responses"][device_id] = []
                    results["device_responses"][device_id].append({
                        "service": step.get("service"),
                        "response": step_result.get("response")
                    })
                    
            except Exception as e:
                logger.exception(f"Error executing step {step_id}: {e}")
                step_results.append({
                    "step_id": step_id,
                    "status": "failed",
                    "error": str(e),
                    "step_index": idx
                })
                results["errors"].append(f"Step {idx}: {str(e)}")
        
        return step_results

    def _execute_step(self, step: Dict, step_id: str) -> Dict[str, Any]:
        """Execute a single step."""
        instruction = step.get("instruction")
        device_id = step.get("device_id")
        service = step.get("service")
        parameters = step.get("parameters", {})
        timeout_ms = step.get("timeout_ms", 5000)
        
        logger.info(f"Executing step {step_id}: {instruction} on {device_id}/{service}")
        
        # Resolve device
        device = self._find_device(device_id)
        if not device:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "failed",
                "error": f"Device {device_id} not found"
            }
        
        # Find service in device
        service_info = self._find_service(device, service)
        if not service_info:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "failed",
                "error": f"Service {service} not found on device {device_id}"
            }
        
        # Execute based on service protocol
        protocol = service_info.get("protocol", "HTTP/REST")
        
        if protocol.upper() in ["HTTP", "HTTP/REST"]:
            return self._execute_http(step, step_id, device, service_info, parameters, timeout_ms)
        elif protocol.upper() == "MQTT":
            return self._execute_mqtt(step, step_id, device, service_info, parameters, timeout_ms)
        else:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "failed",
                "error": f"Unsupported protocol: {protocol}"
            }

    def _execute_http(self, step: Dict, step_id: str, device: Dict, service_info: Dict, 
                     parameters: Dict, timeout_ms: int) -> Dict[str, Any]:
        """Execute HTTP/REST request to device service."""
        instruction = step.get("instruction")
        device_id = device.get("device_id") or device.get("deviceId")
        service = step.get("service")
        ip = device.get("ip")
        
        # Build service endpoint URL
        protocol = step.get("protocol", "http")
        port = step.get("port", 80)
        url = f"{protocol}://{ip}:{port}/{service}"
        
        # Map instruction to HTTP method and parameters
        if instruction == "activate_service":
            method = "POST"
            payload = {"command": "activate", **parameters}
        elif instruction == "query_service":
            method = "GET"
            payload = parameters
        elif instruction == "deactivate_service":
            method = "POST"
            payload = {"command": "deactivate", **parameters}
        else:
            method = "POST"
            payload = parameters
        
        try:
            logger.info(f"HTTP {method} to {url} with timeout {timeout_ms}ms")
            
            if method == "GET":
                response = requests.get(url, params=payload, timeout=timeout_ms/1000.0)
            else:
                response = requests.post(url, json=payload, timeout=timeout_ms/1000.0)
            
            if response.status_code in [200, 201, 202]:
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                return {
                    "step_id": step_id,
                    "instruction": instruction,
                    "device_id": device_id,
                    "service": service,
                    "status": "success",
                    "method": method,
                    "url": url,
                    "response_code": response.status_code,
                    "response": response_data
                }
            else:
                return {
                    "step_id": step_id,
                    "instruction": instruction,
                    "device_id": device_id,
                    "service": service,
                    "status": "failed",
                    "method": method,
                    "url": url,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.Timeout:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "timeout",
                "error": f"Request timeout after {timeout_ms}ms",
                "url": url
            }
        except Exception as e:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "failed",
                "error": str(e),
                "url": url
            }

    def _execute_mqtt(self, step: Dict, step_id: str, device: Dict, service_info: Dict,
                     parameters: Dict, timeout_ms: int) -> Dict[str, Any]:
        """
        Execute MQTT command to device.
        Note: This is a mock implementation. Real MQTT execution would require
        an MQTT client and connection to broker.
        """
        instruction = step.get("instruction")
        device_id = device.get("device_id") or device.get("deviceId")
        service = step.get("service")
        
        # Build MQTT topic: device_id/service/command
        topic = f"{device_id}/{service}/command"
        
        try:
            # Mock MQTT execution
            logger.info(f"MQTT publish to {topic} with timeout {timeout_ms}ms")
            
            payload = {
                "instruction": instruction,
                "parameters": parameters,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # In real implementation, would use paho-mqtt or similar
            logger.info(f"Mock MQTT: {topic} = {json.dumps(payload)}")
            
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "success",
                "protocol": "MQTT",
                "topic": topic,
                "payload": payload,
                "response": f"MQTT published to {topic}"
            }
        except Exception as e:
            return {
                "step_id": step_id,
                "instruction": instruction,
                "device_id": device_id,
                "service": service,
                "status": "failed",
                "error": str(e),
                "protocol": "MQTT"
            }

    def _find_device(self, device_id: str) -> Optional[Dict]:
        """Find device by device_id."""
        # Check in devices list
        for device in self.devices:
            if device.get("device_id") == device_id or device.get("deviceId") == device_id:
                # Normalize id field for compatibility with tests
                if "id" not in device:
                    device["id"] = device.get("device_id") or device.get("deviceId")
                return device
        
        # Check in deployment monitoring
        if "devices" in self.deployment:
            for device in self.deployment["devices"]:
                if device.get("deviceId") == device_id:
                    if "id" not in device:
                        device["id"] = device.get("deviceId")
                    return device
        
        return None

    def _find_service(self, device: Dict, service_name: str) -> Optional[Dict]:
        """Find service in device."""
        services = device.get("services", [])
        for service in services:
            if service.get("name") == service_name:
                return service
        return None

    def _save_execution_history(self, execution_result: Dict):
        """Save execution result to history."""
        try:
            history = self.execution_history
            history["executions"].append(execution_result)
            
            # Keep only last 100 executions
            if len(history["executions"]) > 100:
                history["executions"] = history["executions"][-100:]
            
            history["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            # Save to file if possible
            try:
                write_json(self.execution_history_path, history)
            except:
                logger.debug("Could not save execution history to file")
                
        except Exception as e:
            logger.warning(f"Could not save execution history: {e}")

    def get_execution_history(self, plan_id: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """Get execution history, optionally filtered by plan_id."""
        executions = self.execution_history.get("executions", [])
        
        if plan_id:
            executions = [e for e in executions if e.get("plan_id") == plan_id]
        
        # Return most recent first
        executions = sorted(executions, key=lambda x: x.get("start_time", ""), reverse=True)[:limit]
        
        return {
            "total": len(self.execution_history.get("executions", [])),
            "filtered": len(executions),
            "executions": executions
        }

    def monitor_execution(self, execution_id: str) -> Dict[str, Any]:
        """Monitor a specific execution."""
        executions = self.execution_history.get("executions", [])
        
        for execution in executions:
            if execution.get("execution_id") == execution_id:
                return execution
        
        return {"error": f"Execution {execution_id} not found"}


@execution_router.post("/plan-execution")
def plan_execution(payload: Dict[str, Any], response: Response):
    """
    Plan Execution endpoint for executing orchestration plans.
    
    Translates high-level instructions into concrete device commands:
    - HTTP/REST requests for camera streams, sensor reads, actuator controls
    - MQTT messages for device communication
    - Parallel/sequential execution modes
    
    Supports actions:
    - execute: Execute a plan step-by-step
    - execute_and_monitor: Execute plan and return monitoring info
    - get_history: Retrieve execution history
    - monitor: Monitor a specific execution
    - request_stream: Request camera/sensor stream from a device
    
    Example payload for executing a plan:
    {
        "action": "execute",
        "plan": {
            "plan_id": "fall-detection-corridor",
            "devices": [...],
            "algorithm": {
                "type": "sequential",
                "steps": [...]
            }
        }
    }
    
    Example payload for requesting a stream:
    {
        "action": "request_stream",
        "target": "camera-hallway-1",
        "parameters": {
            "stream_type": "camera"
        }
    }
    """
    try:
        # Accept multiple field names for action: "action", "command", "command_name"
        action = payload.get("action") or payload.get("command") or payload.get("command_name") or payload.get("device_command") or payload.get("request_camera_stream")
        
        # Normalize action names (handle variations like stream_request, request_stream, stream)
        action_lower = action.lower().replace(" ", "_")
        if "stream" in action_lower or "request" in action_lower:
            action = "request_stream"
        
        agent = PlanExecutionAgent()
        
        if action == "execute":
            # Execute a plan
            plan = payload.get("plan")
            if not plan:
                raise ValueError("Plan required for execute action")
            
            result = agent.execute_plan(plan)
            
        elif action == "execute_and_monitor":
            # Execute and provide monitoring info
            plan = payload.get("plan")
            if not plan:
                raise ValueError("Plan required for execute_and_monitor action")
            
            result = agent.execute_plan(plan)
            result["monitoring"] = {
                "status_check_interval_ms": 1000,
                "estimated_completion_ms": result.get("duration_ms", 0)
            }
            
        elif action == "get_history":
            # Get execution history
            plan_id = payload.get("plan_id")
            limit = payload.get("limit", 10)
            result = agent.get_execution_history(plan_id, limit)
            
        elif action == "monitor":
            # Monitor specific execution
            execution_id = payload.get("execution_id")
            if not execution_id:
                raise ValueError("execution_id required for monitor action")
            
            result = agent.monitor_execution(execution_id)
            
        elif action == "request_stream":
            # Handle camera/sensor stream requests from CrewAI
            # Accept multiple field names for target device
            target_device = (payload.get("target") or 
                           payload.get("target_id") or 
                           payload.get("target_device") or
                           payload.get("device_id") or
                           payload.get("parameters", {}).get("device_id"))
            if not target_device:
                raise ValueError("target device required for stream request action")
            
            # Get stream type from multiple possible locations
            stream_type = (payload.get("stream_type") or
                         payload.get("parameters", {}).get("stream_type") or 
                         payload.get("resource", "camera"))
            
            # Find device in registry
            device = agent._find_device(target_device)
            if not device:
                raise ValueError(f"Device not found: {target_device}")
            
            # Get device IP (try both 'ipAddress' and 'ip' field names)
            device_ip = device.get("ipAddress") or device.get("ip")
            if not device_ip:
                raise ValueError(f"Device {target_device} has no IP address")
            
            # Find the service to get its path
            service_info = agent._find_service(device, stream_type)
            if service_info:
                service_path = f"/{stream_type}"
            else:
                service_path = f"/{stream_type}"
            
            # Get device capabilities
            capabilities = device.get("capabilities", [])
            resolution = "1920x1080"  # default
            fps = 30  # default
            
            # Try to extract resolution and fps from service details
            if service_info and "details" in service_info:
                details = service_info["details"]
                if "resolution" in details:
                    resolution = details["resolution"]
                if "sampling_frequency" in details:
                    fps = details["sampling_frequency"]
            
            # Return stream URL and connection info
            result = {
                "action": "request_stream",
                "device_id": target_device,
                "device_name": device.get("name", target_device),
                "stream_type": stream_type,
                "device_info": {
                    "device_id": device.get("deviceId"),
                    "name": device.get("name"),
                    "type": device.get("device_type") or device.get("type"),
                    "location": device.get("location"),
                    "ip_address": device_ip,
                    "status": device.get("status"),
                    "battery": device.get("battery")
                },
                "stream_urls": {
                    "http": f"http://{device_ip}:8080{service_path}/stream",
                    "rtsp": f"rtsp://{device_ip}:554{service_path}",
                    "mjpeg": f"http://{device_ip}:8080{service_path}/mjpeg"
                },
                "protocol": device.get("protocol", "HTTP"),
                "available_formats": ["H.264", "MJPEG", "RTSP"],
                "resolution": resolution,
                "fps": fps,
                "capabilities": capabilities,
                "authentication": {
                    "method": "basic",
                    "username": "admin"
                },
                "status": "stream_ready"
            }
            logger.info(f"Stream request for device {target_device}: {stream_type}")
            
        else:
            raise ValueError(f"Unknown action: {action}")
        
        # Add agent metadata
        result["execution_agent"] = "plan-execution-agent"
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Try to run the LLM agent (if available) for enhanced insights
        try:
            agent_out = run_agent("plan-execution", payload)
            if agent_out is not None:
                result["llm_insights"] = agent_out
                agents_used = []
                if isinstance(agent_out, dict):
                    agents_used.extend([v.get("agent") for v in agent_out.values() if isinstance(v, dict) and v.get("agent")])
                    if agent_out.get("agent"):
                        agents_used.append(agent_out.get("agent"))
                if agents_used:
                    response.headers["X-Server-Agent"] = ",".join(agents_used)
        except Exception as e:
            logger.debug(f"LLM agent optional; continuing: {e}")
        
        return result
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Plan execution error")
        raise HTTPException(status_code=500, detail="Internal server error")
