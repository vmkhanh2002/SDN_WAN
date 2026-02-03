"""Topology Monitoring - Track WSN status"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from ..utils import onos_client

topology_router = APIRouter()

class TopologyRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = None

@topology_router.post("/topology-monitoring")
async def topology_monitoring(request: TopologyRequest):
    """Monitor WSN topology and node status"""
    
    if request.action == "status":
        topology = onos_client.get_topology()
        devices = onos_client.get_wsn_devices()
        return {
            "status": "success",
            "total_nodes": len(devices),
            "active_nodes": len([d for d in devices if d.get("type") == "sensor"]),
            "border_routers": len([d for d in devices if d.get("type") == "border-router"]),
            "topology": topology
        }
    
    elif request.action == "node_info":
        node_id = request.params.get("node_id") if request.params else None
        if not node_id:
            raise HTTPException(400, "node_id required")
        
        flows = onos_client.get_flows(node_id)
        return {
            "status": "success",
            "node_id": node_id,
            "flow_count": len(flows),
            "flows": flows
        }
    
    elif request.action == "active_nodes":
        devices = onos_client.get_wsn_devices()
        return {
            "status": "success",
            "nodes": devices
        }
    
    else:
        raise HTTPException(400, f"Unknown action: {request.action}")
