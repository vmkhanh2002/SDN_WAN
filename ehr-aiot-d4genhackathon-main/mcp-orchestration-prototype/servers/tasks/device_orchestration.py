from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List, Optional
from ..utils import read_json, write_json, DATA_DIR
from ..agents import run_agent
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from .algorithm_execution import AlgorithmExecutionAgent

device_router = APIRouter()
logger = logging.getLogger(__name__)


class LLMOrchestrationAgent:
    """
    LLM-based Orchestration Agent responsible for translating user intent into detailed execution plans.
    
    Flow:
    1. User provides intent (e.g., "activate all high-precision sensors")
    2. Agent queries deployment monitoring for available devices and services
    3. Agent generates a detailed execution plan containing:
       - List of devices that will participate
       - Services requested from each device
       - Exact sequence of instructions
       - Algorithm (naive_baseline, sequential_corridor, etc.)
       - Expected outcomes
    4. Agent executes the plan and tracks results
    """

    def __init__(
        self,
        deployment_monitoring_endpoint: Optional[str] = None,
        orchestration_plans_path: str = DATA_DIR / "orchestration_plans.json",
        devices_path: str = DATA_DIR / "devices.json"
    ):
        self.orchestration_plans_path = orchestration_plans_path
        self.devices_path = devices_path
        self.deployment_monitoring_endpoint = deployment_monitoring_endpoint
        
        # Load orchestration plans and devices
        self.plans = read_json(orchestration_plans_path)
        self.devices = read_json(devices_path)
        self.execution_history = []

    def generate_plan_from_intent(self, user_intent: str) -> Dict[str, Any]:
        """
        Generate an execution plan from user intent.
        This would typically be done by an LLM in a real system.
        For now, we provide a template-based approach.
        """
        logger.info(f"Generating plan from intent: {user_intent}")
        
        # Map intents to predefined plans
        intent_lower = user_intent.lower()
        
        if "high-precision" in intent_lower or "sensors" in intent_lower:
            return self._find_plan_by_id("activate-sensors-high-precision")
        elif "corridor" in intent_lower and "video" in intent_lower:
            return self._find_plan_by_id("camera-corridor-monitoring")
        elif "environmental" in intent_lower or "monitoring" in intent_lower:
            return self._find_plan_by_id("environmental-monitoring")
        else:
            # Create a generic plan
            return self._create_generic_plan(user_intent)

    def _find_plan_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Find a plan by its ID."""
        for plan in self.plans.get("orchestration_plans", []):
            if plan.get("plan_id") == plan_id:
                return plan
        return None

    def _create_generic_plan(self, user_intent: str) -> Dict[str, Any]:
        """Create a generic plan from user intent."""
        return {
            "plan_id": f"plan-{datetime.utcnow().timestamp()}",
            "name": "User-Generated Plan",
            "description": user_intent,
            "user_intent": user_intent,
            "status": "generated",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "devices": self.devices,
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "step_id": 1,
                        "type": "initialize",
                        "description": "Initialize devices based on intent"
                    }
                ]
            },
            "expected_outcome": {}
        }

    def query_deployment_status(self) -> Dict[str, Any]:
        """Query deployment monitoring agent for current status."""
        # In a real system, this would call the deployment monitoring endpoint
        logger.info("Querying deployment status")
        return {
            "total_devices": len(self.devices),
            "devices": self.devices
        }

    def analyze_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a plan and extract key information:
        - Devices involved
        - Services required
        - Execution sequence
        """
        devices_involved = plan.get("devices", [])
        algorithm = plan.get("algorithm", {})
        steps = algorithm.get("steps", [])
        
        analysis = {
            "plan_id": plan.get("plan_id"),
            "total_devices": len(devices_involved),
            "devices": [d.get("deviceId") for d in devices_involved],
            "execution_mode": algorithm.get("type", "sequential"),
            "total_steps": len(steps),
            "services": self._extract_services(devices_involved),
            "timeline_estimate_ms": self._estimate_execution_time(steps)
        }
        
        return analysis

    def _extract_services(self, devices: List[Dict]) -> Dict[str, List[str]]:
        """Extract all services from devices in the plan."""
        services = {}
        for device in devices:
            device_services = [s.get("name") for s in device.get("services", [])]
            services[device.get("deviceId")] = device_services
        return services

    def _estimate_execution_time(self, steps: List[Dict]) -> int:
        """Estimate total execution time based on steps."""
        total_time = 0
        for step in steps:
            # Assume 1000ms per step by default
            timeout = step.get("timeout_ms", 1000)
            total_time += timeout
        return total_time

    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the orchestration plan."""
        plan_id = plan.get("plan_id")
        logger.info(f"Executing plan: {plan_id}")
        
        execution_record = {
            "plan_id": plan_id,
            "execution_start": datetime.utcnow().isoformat() + "Z",
            "steps_executed": [],
            "devices_activated": [],
            "status": "executing"
        }
        
        algorithm = plan.get("algorithm", {})
        steps = algorithm.get("steps", [])
        execution_mode = algorithm.get("type", "sequential")
        
        try:
            # Execute steps according to algorithm type
            if execution_mode == "parallel":
                results = self._execute_parallel(steps, plan)
            else:
                results = self._execute_sequential(steps, plan)
            
            execution_record["steps_executed"] = results
            execution_record["devices_activated"] = plan.get("devices", [])
            execution_record["status"] = "completed"
            execution_record["execution_end"] = datetime.utcnow().isoformat() + "Z"
            
            # Save execution record
            self.execution_history.append(execution_record)
            
            return {
                "plan_id": plan_id,
                "status": "success",
                "execution": execution_record,
                "expected_outcome": plan.get("expected_outcome", {})
            }
        
        except Exception as e:
            logger.exception(f"Plan execution failed: {e}")
            execution_record["status"] = "failed"
            execution_record["error"] = str(e)
            self.execution_history.append(execution_record)
            raise

    def _execute_sequential(self, steps: List[Dict], plan: Dict) -> List[Dict]:
        """Execute steps sequentially."""
        results = []
        
        for step in steps:
            step_id = step.get("step_id")
            step_type = step.get("type")
            description = step.get("description")
            
            logger.info(f"Step {step_id}: {step_type} - {description}")
            
            result = {
                "step_id": step_id,
                "type": step_type,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Execute different step types
            if step_type == "request_service":
                result["actions"] = self._execute_service_request(step, plan)
            elif step_type == "verify":
                result["verification"] = self._verify_status(step, plan)
            elif step_type == "configure":
                result["configuration"] = self._configure_devices(step, plan)
            elif step_type == "initialize":
                result["initialization"] = self._initialize_devices(step, plan)
            elif step_type == "monitor":
                result["monitoring"] = self._start_monitoring(step, plan)
            
            results.append(result)
            # Simulate execution time
            time.sleep(0.5)
        
        return results

    def _execute_parallel(self, steps: List[Dict], plan: Dict) -> List[Dict]:
        """Execute steps in parallel (simulated)."""
        results = []
        
        for step in steps:
            step_id = step.get("step_id")
            step_type = step.get("type")
            description = step.get("description")
            
            logger.info(f"[PARALLEL] Step {step_id}: {step_type} - {description}")
            
            result = {
                "step_id": step_id,
                "type": step_type,
                "status": "completed",
                "execution_mode": "parallel",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            # Execute different step types
            if step_type == "request_service":
                result["actions"] = self._execute_service_request(step, plan)
            elif step_type == "verify":
                result["verification"] = self._verify_status(step, plan)
            
            results.append(result)
        
        return results

    def _execute_service_request(self, step: Dict, plan: Dict) -> List[Dict]:
        """Execute a service request step."""
        actions = []
        devices = plan.get("devices", [])
        
        # Get target devices
        target_device_ids = step.get("device") or step.get("devices", [])
        if target_device_ids == "all":
            target_device_ids = [d.get("deviceId") for d in devices]
        elif isinstance(target_device_ids, str):
            target_device_ids = [target_device_ids]
        
        # Execute for each target device
        for device_id in target_device_ids:
            device = next((d for d in devices if d.get("deviceId") == device_id), None)
            if not device:
                continue
            
            device_actions = step.get("actions", [])
            service = step.get("service")
            command = step.get("command", "activate")
            parameters = step.get("parameters", {})
            
            action = {
                "device": device_id,
                "service": service or "all",
                "command": command,
                "parameters": parameters,
                "status": "success",
                "execution_time_ms": 150
            }
            actions.append(action)
            logger.info(f"  → Device {device_id}: {command} {service or 'all services'}")
        
        return actions

    def _verify_status(self, step: Dict, plan: Dict) -> Dict[str, Any]:
        """Verify device status after execution."""
        devices = plan.get("devices", [])
        expected_status = step.get("expected_status", "active")
        
        verification = {
            "expected_status": expected_status,
            "devices_verified": len(devices),
            "all_passed": True
        }
        
        for device in devices:
            logger.info(f"  ✓ Verified {device.get('deviceId')} - status: {expected_status}")
        
        return verification

    def _configure_devices(self, step: Dict, plan: Dict) -> Dict[str, Any]:
        """Configure devices based on step parameters."""
        devices = plan.get("devices", [])
        action = step.get("action")
        
        configuration = {
            "action": action,
            "devices_configured": len(devices),
            "details": []
        }
        
        for device in devices:
            logger.info(f"  ⚙ Configuring {device.get('deviceId')}: {action}")
            configuration["details"].append({
                "device": device.get("deviceId"),
                "action": action,
                "status": "applied"
            })
        
        return configuration

    def _initialize_devices(self, step: Dict, plan: Dict) -> Dict[str, Any]:
        """Initialize devices before execution."""
        devices = plan.get("devices", [])
        action = step.get("action")
        
        initialization = {
            "action": action,
            "devices_initialized": len(devices)
        }
        
        for device in devices:
            logger.info(f"  ⚡ Initializing {device.get('deviceId')}")
        
        return initialization

    def _start_monitoring(self, step: Dict, plan: Dict) -> Dict[str, Any]:
        """Start monitoring devices."""
        devices = plan.get("devices", [])
        frequency = step.get("monitoring_frequency_ms", 1000)
        
        monitoring = {
            "frequency_ms": frequency,
            "devices_monitored": len(devices),
            "status": "monitoring"
        }
        
        logger.info(f"  📊 Started monitoring {len(devices)} devices at {frequency}ms frequency")
        
        return monitoring

    def orchestrate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main orchestration method."""
        user_intent = payload.get("intent", "")
        action = payload.get("action", "execute_plan")
        
        if action == "query_devices":
            # Query devices with filters
            filters = payload.get("parameters", {}).get("filters", {})
            requested_fields = payload.get("parameters", {}).get("fields", [])
            
            results = []
            for device in self.devices:
                match = True
                
                # Apply location filter
                if "location" in filters and device.get("location") != filters["location"]:
                    match = False
                
                # Apply capabilities filter
                if "capabilities" in filters:
                    device_caps = device.get("capabilities", [])
                    required_caps = filters["capabilities"]
                    if not all(cap in device_caps for cap in required_caps):
                        match = False
                
                if match:
                    # Build response with requested fields
                    device_result = {}
                    for field in requested_fields or ["device_id", "device_type", "location", "capabilities"]:
                        if field == "device_id":
                            device_result["device_id"] = device.get("device_id", device.get("deviceId"))
                        elif field == "device_type":
                            device_result["device_type"] = device.get("device_type", device.get("type"))
                        elif field == "location":
                            device_result["location"] = device.get("location")
                        elif field == "capabilities":
                            device_result["capabilities"] = device.get("capabilities", [])
                        elif field == "status":
                            device_result["status"] = device.get("status", "active")
                    results.append(device_result)
            
            return {
                "action": "query_devices",
                "filters": filters,
                "matching_devices": len(results),
                "devices": results
            }
        
        elif action == "generate_plan":
            # Generate plan from user intent
            plan = self.generate_plan_from_intent(user_intent)
            analysis = self.analyze_plan(plan)
            algo_opts = AlgorithmExecutionAgent().get_algorithm_options(user_intent).get("options", [])
            return {
                "action": "generate_plan",
                "plan": plan,
                "analysis": analysis,
                "recommendation_options": algo_opts,
                "status": "ready_for_execution"
            }
        
        elif action == "analyze":
            # Analyze an existing plan
            plan_id = payload.get("plan_id")
            plan = self._find_plan_by_id(plan_id)
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            analysis = self.analyze_plan(plan)
            return {
                "action": "analyze",
                "plan_id": plan_id,
                "analysis": analysis
            }
        
        elif action == "execute":
            # Execute a plan
            plan_id = payload.get("plan_id")
            plan = self._find_plan_by_id(plan_id)
            if not plan:
                # Try to generate from intent
                plan = self.generate_plan_from_intent(user_intent)
            
            execution_result = self.execute_plan(plan)
            return execution_result
        
        elif action == "execute_intent":
            # Generate and execute plan from intent
            plan = self.generate_plan_from_intent(user_intent)
            analysis = self.analyze_plan(plan)
            execution_result = self.execute_plan(plan)
            algo_opts = AlgorithmExecutionAgent().get_algorithm_options(user_intent).get("options", [])
            
            return {
                "user_intent": user_intent,
                "generated_plan": plan,
                "plan_analysis": analysis,
                "recommendation_options": algo_opts,
                "execution": execution_result
            }
        
        elif action == "list_plans":
            # List available plans
            return {
                "total_plans": len(self.plans.get("orchestration_plans", [])),
                "plans": self.plans.get("orchestration_plans", [])
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")


@device_router.post("/device-orchestration")
def device_orchestration(payload: Dict[str, Any], response: Response):
    """
    Orchestration endpoint for LLM-based device orchestration.
    
    Supports actions:
    - query_devices: Query devices with filters (location, capabilities, etc.)
    - generate_plan: Generate execution plan from user intent
    - analyze: Analyze an existing plan
    - execute: Execute a specific plan
    - execute_intent: Generate and execute plan from intent
    - list_plans: List available orchestration plans
    
    Example payload for querying devices:
    {
        "action": "query_devices",
        "parameters": {
            "filters": {"location": "corridor", "capabilities": ["video_streaming"]},
            "fields": ["device_id", "device_type", "location", "capabilities", "status"]
        }
    }
    
    Example payload for generating plan:
    {
        "action": "generate_plan",
        "intent": "Activate all high-precision sensors simultaneously"
    }
    """
    try:
        agent = LLMOrchestrationAgent()
        result = agent.orchestrate(payload)
        
        # Add agent metadata
        result["orchestration_agent"] = "llm-based-orchestration-agent"
        result["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Try to run the LLM agent (if available) for enhanced insights
        try:
            agent_out = run_agent("device-orchestration", payload)
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
        logger.exception("Orchestration error")
        raise HTTPException(status_code=500, detail="Internal server error")
