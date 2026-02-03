"""
Flow Orchestration Task Router
Translates user intent into flow rules for wireless sensor networks
Adapted from device_orchestration.py in ehr-aiot
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging

from ..utils import onos_client, read_json, write_json
from ..agents import run_agent

flow_router = APIRouter()

class FlowRequest(BaseModel):
    action: str
    intent: Optional[str] = None
    node_id: Optional[int] = None
    params: Optional[Dict[str, Any]] = None


@flow_router.post("/flow-orchestration")
async def flow_orchestration(request: FlowRequest):
    """
    Flow orchestration endpoint
    
    Actions:
    - generate_plan: Create flow plan from user intent
    - execute_intent: End-to-end flow installation
    - list_plans: Get available flow plans  
    - analyze: Analyze flow plan
    - query_nodes: Query sensor nodes
    """
    
    action = request.action
    logging.info(f"Flow orchestration action: {action}")
    
    if action == "generate_plan":
        return await generate_flow_plan(request.intent, request.params)
    
    elif action == "execute_intent":
        return await execute_intent(request.intent)
    
    elif action == "list_plans":
        return await list_flow_plans()
    
    elif action == "analyze":
        return await analyze_plan(request.params)
    
    elif action == "query_nodes":
        return await query_nodes(request.params)
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")


async def generate_flow_plan(intent: str, params: Optional[Dict] = None) -> Dict:
    """Generate flow plan from user intent using Gemini LLM"""
    
    if not intent:
        raise HTTPException(status_code=400, detail="Intent is required")
    
    # Get current topology
    topology = onos_client.get_topology()
    devices = onos_client.get_wsn_devices()
    
    # Prepare context for Gemini
    context = {
        "intent": intent,
        "topology": topology,
        "devices": devices,
        "params": params or {}
    }
    
    # Run CrewAI agent with Gemini
    result = run_agent("flow-orchestration", context)
    
    # If using stub agent, generate mock plan
    if result.get("status") == "stub_response":
        return generate_mock_flow_plan(intent, topology, devices)
    
    return result


def generate_mock_flow_plan(intent: str, topology: Dict, devices: List[Dict]) -> Dict:
    """Generate mock flow plan for testing without LLM"""
    
    # Simple intent parsing
    intent_lower = intent.lower()
    
    # Default: route all sensor data to sink
    src_nodes = [d["nodeId"] for d in devices if d.get("type") == "sensor"]
    dst_node = next((d["nodeId"] for d in devices if d.get("type") == "border-router"), 1)
    
    flows = []
    for src in src_nodes:
        flows.append({
            "nodeId": src,
            "srcAddr": src,
            "dstAddr": dst_node,
            "action": 1,  # FORWARD
            "nextHop": dst_node,
            "description": f"Route from sensor {src} to sink {dst_node}"
        })
    
    plan = {
        "status": "success",
        "intent": intent,
       "plan_id": "plan-001",
        "flows": flows,
        "summary": f"Generated {len(flows)} flow rules to route sensor data to sink",
        "mock": True
    }
    
    # Save plan
    plans = read_json("flow_plans.json")
    plans[plan["plan_id"]] = plan
    write_json("flow_plans.json", plans)
    
    return plan


async def execute_intent(intent: str) -> Dict:
    """Execute intent end-to-end: generate + validate + install"""
    
    # 1. Generate plan
    plan_result = await generate_flow_plan(intent, None)
    
    if not plan_result.get("flows"):
        return {"status": "error", "message": "No flows generated"}
    
    # 2. Validate (placeholder - will implement in flow_validation)
    # For now, assume valid
    
    # 3. Execute flows
    installed = 0
    errors = []
    
    for flow in plan_result["flows"]:
        try:
            result = onos_client.install_flow(flow)
            if result.get("status") == "success":
                installed += 1
            else:
                errors.append(f"Flow {flow['nodeId']}: {result.get('message')}")
        except Exception as e:
            errors.append(f"Flow {flow['nodeId']}: {str(e)}")
    
    return {
        "status": "success" if installed > 0 else "error",
        "intent": intent,
        "flows_installed": installed,
        "total_flows": len(plan_result["flows"]),
        "errors": errors if errors else None
    }


async def list_flow_plans() -> Dict:
    """List all saved flow plans"""
    plans = read_json("flow_plans.json")
    
    return {
        "status": "success",
        "plans": [
            {
                "plan_id": plan_id,
                "intent": plan.get("intent"),
                "flow_count": len(plan.get("flows", []))
            }
            for plan_id, plan in plans.items()
        ]
    }


async def analyze_plan(params: Optional[Dict]) -> Dict:
    """Analyze a flow plan"""
    
    if not params or "plan_id" not in params:
        raise HTTPException(status_code=400, detail="plan_id required")
    
    plans = read_json("flow_plans.json")
    plan = plans.get(params["plan_id"])
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # Simple analysis
    flows = plan.get("flows", [])
    src_nodes = set(f["srcAddr"] for f in flows)
    dst_nodes = set(f["dstAddr"] for f in flows)
    
    return {
        "status": "success",
        "plan_id": params["plan_id"],
        "analysis": {
            "total_flows": len(flows),
            "source_nodes": len(src_nodes),
            "destination_nodes": len(dst_nodes),
            "estimated_energy_cost": len(flows) * 0.1,  # Mock calculation
            "estimated_latency_ms": 50  # Mock value
        }
    }


async def query_nodes(params: Optional[Dict]) -> Dict:
    """Query sensor nodes based on criteria"""
    
    devices = onos_client.get_wsn_devices()
    
    # Filter by type if specified
    if params and "type" in params:
        devices = [d for d in devices if d.get("type") == params["type"]]
    
    return {
        "status": "success",
        "nodes": devices,
        "count": len(devices)
    }
