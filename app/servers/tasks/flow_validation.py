"""Flow Validation - Validate flow constraints"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

validation_router = APIRouter()

class ValidationRequest(BaseModel):
    action: str
    flow_plan: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None

@validation_router.post("/flow-validation")
async def flow_validation(request: ValidationRequest):
    """Validate flow plans against WSN constraints"""
    
    if request.action == "validate":
        if not request.flow_plan:
            raise HTTPException(400, "flow_plan required")
        
        flows = request.flow_plan.get("flows", [])
        issues = []
        
        # Energy constraint: limit flows per node
        node_flows = {}
        for f in flows:
            node_id = f.get("nodeId")
            node_flows[node_id] = node_flows.get(node_id, 0) + 1
            if node_flows[node_id] > 10:  # Max 10 flows per node
                issues.append(f"Node {node_id} exceeds flow table capacity")
        
        # Bandwidth: simple check
        if len(flows) > 50:
            issues.append("Too many flows - may exceed bandwidth")
        
        return {
            "status": "valid" if not issues else "invalid",
            "flows_validated": len(flows),
            "issues": issues
        }
    
    elif request.action == "recommendations":
        return {
            "status": "success",
            "recommendations": [
                "Consider aggregating sensor data",
                "Use sampling to reduce traffic",
                "Implement sleep schedules for energy savings"
            ]
        }
    
    else:
        raise HTTPException(400, f"Unknown action: {request.action}")
