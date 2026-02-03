from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any
from ..utils import read_json, write_json, DATA_DIR
from ..agents import run_agent

access_router = APIRouter()


@access_router.post("/access-control")
def access_control(payload: Dict[str, Any], response: Response):
    """Check or modify access control policies."""
    access = read_json(DATA_DIR / "access.json")
    op = payload.get("op")
    if op == "check":
        user = payload.get("user")
        permission = payload.get("permission")
        user_obj = next((u for u in access.get("users", []) if u.get("userId") == user or u.get("name") == user), None)
        if not user_obj:
            raise HTTPException(status_code=404, detail="User not found")
        roles = user_obj.get("roles", [])
        allowed = False
        for r in roles:
            policy = next((p for p in access.get("policies", []) if p.get("role") == r), None)
            if policy and ("*" in policy.get("allow", []) or permission in policy.get("allow", [])):
                allowed = True

        result = {"allowed": allowed}
        try:
            agent_out = run_agent("access-control", payload)
            if agent_out is not None:
                result["agent"] = agent_out
                # detect both nested per-role dicts and single-agent outputs
                agents_used = []
                if isinstance(agent_out, dict):
                    agents_used.extend([v.get("agent") for v in agent_out.values() if isinstance(v, dict) and v.get("agent")])
                    if agent_out.get("agent"):
                        agents_used.append(agent_out.get("agent"))
                if agents_used:
                    response.headers["X-Server-Agent"] = ",".join(agents_used)
        except Exception:
            pass
        return result
    elif op == "grant":
        role = payload.get("role")
        permission = payload.get("permission")
        policy = next((p for p in access.get("policies", []) if p.get("role") == role), None)
        if not policy:
            access.setdefault("policies", []).append({"role": role, "allow": [permission]})
        else:
            if permission not in policy["allow"]:
                policy["allow"].append(permission)
        write_json(DATA_DIR / "access.json", access)
        result = {"ok": True, "role": role}
        try:
            agent_out = run_agent("access-control", payload)
            if agent_out is not None:
                result["agent"] = agent_out
                # detect both nested per-role dicts and single-agent outputs
                agents_used = []
                if isinstance(agent_out, dict):
                    agents_used.extend([v.get("agent") for v in agent_out.values() if isinstance(v, dict) and v.get("agent")])
                    if agent_out.get("agent"):
                        agents_used.append(agent_out.get("agent"))
                if agents_used:
                    response.headers["X-Server-Agent"] = ",".join(agents_used)
        except Exception:
            pass
        return result
    else:
        raise HTTPException(status_code=400, detail="Unsupported op")
