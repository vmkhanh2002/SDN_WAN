from fastapi.testclient import TestClient
from servers.app import app

client = TestClient(app)


def test_algorithm_options_endpoint():
    r = client.post("/tasks/algorithm-execution", json={"action": "options", "intent": "corridor monitoring"})
    assert r.status_code == 200
    body = r.json()
    assert "options" in body
    keys = [o.get("key") for o in body.get("options", [])]
    assert "naive_baseline" in keys
    assert "sequential_corridor" in keys


def test_build_plan_naive_baseline():
    r = client.post(
        "/tasks/algorithm-execution",
        json={"action": "build_plan", "algorithm_key": "naive_baseline", "t_active_seconds": 20}
    )
    assert r.status_code == 200
    body = r.json()
    plan = body.get("plan", {})
    assert plan.get("algorithm", {}).get("type") == "parallel"
    assert len(plan.get("algorithm", {}).get("steps", [])) > 0


def test_build_plan_sequential_corridor():
    r = client.post(
        "/tasks/algorithm-execution",
        json={"action": "build_plan", "algorithm_key": "sequential_corridor", "t_active_seconds": 10}
    )
    assert r.status_code == 200
    body = r.json()
    plan = body.get("plan", {})
    assert plan.get("algorithm", {}).get("type") == "sequential"
    assert len(plan.get("algorithm", {}).get("steps", [])) > 0


def test_plan_validation_executes_selected_algorithm_dry_run():
    # Validate a simple plan and request algorithm execution (dry_run)
    plan = {
        "plan_id": "algo-validate-test",
        "devices": [{"deviceId": "esp32-001", "type": "camera", "services": [{"name": "camera", "protocol": "HTTP/REST"}]}],
        "algorithm": {"type": "sequential"},
    }
    r = client.post(
        "/tasks/plan-validation",
        json={
            "action": "validate",
            "plan": plan,
            "selected_algorithm_key": "sequential_corridor",
            "t_active_seconds": 5,
            "execute_selected": False,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "algorithm_execution" in body
    exec_res = body.get("algorithm_execution", {})
    assert exec_res.get("status") in ["plan_ready", "completed", "failed"]
    assert exec_res.get("algorithm_key") == "sequential_corridor"
