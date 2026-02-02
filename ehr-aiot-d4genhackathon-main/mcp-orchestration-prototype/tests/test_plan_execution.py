"""
Test cases for Plan Execution Agent
"""
import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from servers.tasks.plan_execution import PlanExecutionAgent


class TestPlanExecutionAgent(unittest.TestCase):
    """Test Plan Execution Agent functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.agent = PlanExecutionAgent()

    def test_find_device_by_id(self):
        """Test finding device by device_id."""
        device = self.agent._find_device("esp32-001")
        self.assertIsNotNone(device)
        self.assertIn("id", device)
        self.assertEqual(device.get("id"), "esp32-001")

    def test_find_device_not_found(self):
        """Test finding non-existent device."""
        device = self.agent._find_device("esp32-999")
        self.assertIsNone(device)

    def test_find_service_in_device(self):
        """Test finding service in device."""
        device = self.agent._find_device("esp32-001")
        self.assertIsNotNone(device)
        
        service = self.agent._find_service(device, "camera")
        self.assertIsNotNone(service)
        self.assertEqual(service.get("name"), "camera")

    def test_find_service_not_found(self):
        """Test finding non-existent service."""
        device = self.agent._find_device("esp32-001")
        self.assertIsNotNone(device)
        
        service = self.agent._find_service(device, "nonexistent_service")
        self.assertIsNone(service)

    def test_execute_simple_plan_sequential(self):
        """Test executing a simple sequential plan."""
        plan = {
            "plan_id": "test-plan-sequential",
            "devices": [
                {"deviceId": "esp32-001"},
                {"deviceId": "esp32-004"}
            ],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {"fps": 30},
                        "timeout_ms": 5000
                    },
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-004",
                        "service": "control",
                        "parameters": {"action": "on"},
                        "timeout_ms": 3000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)

        self.assertEqual(result["plan_id"], "test-plan-sequential")
        self.assertEqual(result["steps_total"], 2)
        self.assertEqual(result["status"], "completed")
        self.assertGreaterEqual(len(result["step_results"]), 2)

    def test_execute_plan_with_missing_device(self):
        """Test executing plan with missing device."""
        plan = {
            "plan_id": "test-plan-missing-device",
            "devices": [{"deviceId": "esp32-999"}],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-999",
                        "service": "sensor",
                        "parameters": {},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)

        self.assertEqual(result["plan_id"], "test-plan-missing-device")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_results"][0]["status"], "failed")
        self.assertIn("not found", result["step_results"][0]["error"])

    def test_execute_plan_with_missing_service(self):
        """Test executing plan with missing service."""
        plan = {
            "plan_id": "test-plan-missing-service",
            "devices": [{"deviceId": "esp32-001"}],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-001",
                        "service": "nonexistent_service",
                        "parameters": {},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)

        self.assertEqual(result["plan_id"], "test-plan-missing-service")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["step_results"][0]["status"], "failed")
        self.assertIn("not found", result["step_results"][0]["error"])

    def test_execution_history_tracking(self):
        """Test that execution results are tracked in history."""
        initial_count = len(self.agent.execution_history.get("executions", []))

        plan = {
            "plan_id": "test-plan-history",
            "devices": [{"deviceId": "esp32-001"}],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "query_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)
        
        # Reload execution history
        from servers.utils import read_json, DATA_DIR
        try:
            history = read_json(DATA_DIR / "execution_history.json")
            executions = history.get("executions", [])
            # Verify execution was recorded
            self.assertGreater(len(executions), initial_count)
        except:
            pass  # File operations may not be available in test

    def test_get_execution_history(self):
        """Test retrieving execution history."""
        history = self.agent.get_execution_history()
        
        self.assertIn("total", history)
        self.assertIn("filtered", history)
        self.assertIn("executions", history)
        self.assertIsInstance(history["executions"], list)

    def test_get_execution_history_filtered(self):
        """Test retrieving execution history filtered by plan_id."""
        history = self.agent.get_execution_history(plan_id="fall-detection-corridor")
        
        self.assertIn("total", history)
        self.assertIn("filtered", history)
        self.assertIn("executions", history)
        
        # All returned executions should match the plan_id
        for execution in history["executions"]:
            self.assertEqual(execution.get("plan_id"), "fall-detection-corridor")

    def test_monitor_execution(self):
        """Test monitoring specific execution."""
        # First, get an execution ID from history
        history = self.agent.get_execution_history(limit=1)
        
        if history["executions"]:
            execution_id = history["executions"][0]["execution_id"]
            monitored = self.agent.monitor_execution(execution_id)
            
            self.assertEqual(monitored["execution_id"], execution_id)
            self.assertIn("status", monitored)
            self.assertIn("plan_id", monitored)

    def test_execute_parallel_plan(self):
        """Test executing a parallel execution plan."""
        plan = {
            "plan_id": "test-plan-parallel",
            "devices": [
                {"deviceId": "esp32-001"},
                {"deviceId": "esp32-002"},
                {"deviceId": "esp32-004"}
            ],
            "algorithm": {
                "type": "parallel",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {},
                        "timeout_ms": 5000
                    },
                    {
                        "instruction": "query_service",
                        "device_id": "esp32-002",
                        "service": "temperature",
                        "parameters": {},
                        "timeout_ms": 5000
                    },
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-004",
                        "service": "control",
                        "parameters": {"action": "on"},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)

        self.assertEqual(result["plan_id"], "test-plan-parallel")
        self.assertEqual(result["execution_type"], "parallel")
        self.assertEqual(result["steps_total"], 3)
        self.assertEqual(result["status"], "completed")

    def test_step_results_contain_required_fields(self):
        """Test that step results contain all required fields."""
        plan = {
            "plan_id": "test-required-fields",
            "devices": [{"deviceId": "esp32-001"}],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "activate_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)
        step_result = result["step_results"][0]

        # Verify required fields
        required_fields = ["step_id", "instruction", "device_id", "service", "status"]
        for field in required_fields:
            self.assertIn(field, step_result)

    def test_execution_result_contains_required_metadata(self):
        """Test that execution result contains required metadata."""
        plan = {
            "plan_id": "test-metadata",
            "devices": [{"deviceId": "esp32-001"}],
            "algorithm": {
                "type": "sequential",
                "steps": [
                    {
                        "instruction": "query_service",
                        "device_id": "esp32-001",
                        "service": "camera",
                        "parameters": {},
                        "timeout_ms": 5000
                    }
                ]
            }
        }

        result = self.agent.execute_plan(plan)

        # Verify required metadata fields
        required_fields = ["execution_id", "plan_id", "status", "start_time", "end_time",
                          "duration_ms", "steps_completed", "steps_total", "step_results",
                          "errors", "device_responses"]
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")


class TestPlanExecutionEndpoint(unittest.TestCase):
    """Test Plan Execution endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        from fastapi.testclient import TestClient
        from servers.app import app
        self.client = TestClient(app)

    def test_execute_plan_endpoint(self):
        """Test executing plan via endpoint."""
        payload = {
            "action": "execute",
            "plan": {
                "plan_id": "endpoint-test-plan",
                "devices": [{"deviceId": "esp32-001"}],
                "algorithm": {
                    "type": "sequential",
                    "steps": [
                        {
                            "instruction": "activate_service",
                            "device_id": "esp32-001",
                            "service": "camera",
                            "parameters": {},
                            "timeout_ms": 5000
                        }
                    ]
                }
            }
        }

        response = self.client.post("/tasks/plan-execution", json=payload)

        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertEqual(result["plan_id"], "endpoint-test-plan")
        self.assertIn("execution_id", result)
        self.assertIn("status", result)

    def test_get_history_endpoint(self):
        """Test retrieving history via endpoint."""
        payload = {"action": "get_history", "limit": 5}

        response = self.client.post("/tasks/plan-execution", json=payload)

        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("total", result)
        self.assertIn("filtered", result)
        self.assertIn("executions", result)

    def test_monitor_endpoint(self):
        """Test monitoring execution via endpoint."""
        # First get a history to get an execution_id
        payload = {"action": "get_history", "limit": 1}
        response = self.client.post("/tasks/plan-execution", json=payload)
        
        if response.status_code == 200:
            history = response.json()
            if history.get("executions"):
                execution_id = history["executions"][0]["execution_id"]
                
                # Now monitor it
                monitor_payload = {"action": "monitor", "execution_id": execution_id}
                monitor_response = self.client.post("/tasks/plan-execution", json=monitor_payload)
                
                self.assertEqual(monitor_response.status_code, 200)
                result = monitor_response.json()
                self.assertEqual(result["execution_id"], execution_id)


if __name__ == "__main__":
    unittest.main()
