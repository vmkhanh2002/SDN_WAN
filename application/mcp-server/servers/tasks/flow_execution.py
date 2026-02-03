"""Flow Execution - Install flows via ONOS"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from ..utils import onos_client, read_json, write_json
from datetime import datetime

execution_router = APIRouter()

class ExecutionRequest(BaseModel):
    action: str
    flow_plan: Optional[Dict[str, Any]] = None
    flow_id: Optional[str] = None

@execution_router.post("/flow-execution")
async def flow_execution(request: ExecutionRequest):
    """Execute flow installation via ONOS"""
    
    if request.action == "execute":
        if not request.flow_plan:
            raise HTTPException(400, "flow_plan required")
        
        flows = request.flow_plan.get("flows", [])
        results = []
        
        for flow in flows:
            try:
                result = onos_client.install_flow(flow)
                results.append({
                    "node_id": flow.get("nodeId"),
                    "status": result.get("status", "success"),
                    "message": result.get("message", "Flow installed")
                })
            except Exception as e:
                results.append({
                    "node_id": flow.get("nodeId"),
                    "status": "error",
                    "message": str(e)
                })
        
        # Record execution
        history = read_json("execution_history.json")
        execution_id = f"exec-{int(datetime.utcnow().timestamp())}"
        history[execution_id] = {
            "timestamp": datetime.utcnow().isoformat(),
            "flows": len(flows),
            "results": results
        }
        write_json("execution_history.json", history)
        
        return {
            "status": "success",
            "execution_id": execution_id,
            "flows_installed": len([r for r in results if r["status"] == "success"]),
            "results": results
        }
    
    elif request.action == "get_history":
        history = read_json("execution_history.json")
        return {
            "status": "success",
            "history": history
        }
    
    else:
        raise HTTPException(400, f"Unknown action: {request.action}")
