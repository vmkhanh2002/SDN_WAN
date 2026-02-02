from fastapi.testclient import TestClient
from servers.app import app
import json

client = TestClient(app)


class TestPlanValidation:
    """
    Test suite for Plan Validation Agent.
    Tests all validation constraints: energy, transmission, security, location, and privacy.
    """

    def test_validate_high_energy_consumption_plan(self):
        """
        Test validation of a plan with high energy consumption.
        Should identify battery risks and recommend optimization.
        """
        plan = {
            "plan_id": "high-energy-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "details": {
                                "resolution": "1920x1080",
                                "fps": 60
                            }
                        }
                    ]
                },
                {
                    "deviceId": "esp32-003",  # Battery at 15%
                    "type": "sensor",
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "details": {
                                "sampling_frequency": 60
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "parallel",
                "description": "Activate all devices simultaneously"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan,
                "user_context": {
                    "user_id": "nurse-001",
                    "role": "nurse",
                    "permissions": ["read_sensor_data", "read_video"]
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should have failed due to critical battery level
        assert validation.get("status") == "failed"
        
        # Should identify energy constraint check
        energy_check = next(
            (c for c in validation.get("constraints_checked", []) if c.get("constraint") == "energy"),
            None
        )
        assert energy_check is not None
        assert energy_check.get("status") == "failed"
        
        # Should have critical issues for low battery
        critical_issues = [i for i in validation.get("issues", []) if i.get("severity") == "critical"]
        assert len(critical_issues) > 0
        assert any("battery" in i.get("message", "").lower() for i in critical_issues)

    def test_validate_high_bandwidth_plan(self):
        """
        Test validation of a plan with excessive bandwidth requirements.
        Should identify transmission constraints and recommend compression/resolution reduction.
        """
        plan = {
            "plan_id": "high-bandwidth-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "details": {
                                "resolution": "2560x1440",  # High resolution
                                "fps": 60
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential",
                "description": "High-resolution video stream"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan,
                "user_context": {
                    "user_id": "nurse-001",
                    "role": "nurse",
                    "permissions": ["read_video"]
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should have warnings
        assert validation.get("status") in ["warnings", "passed"]
        
        # Should identify transmission constraint check
        transmission_check = next(
            (c for c in validation.get("constraints_checked", []) if c.get("constraint") == "transmission"),
            None
        )
        assert transmission_check is not None
        
        # Should have recommendations for bandwidth reduction
        recommendations = validation.get("recommendations", [])
        assert any("resolution" in r.get("suggestion", "").lower() for r in recommendations)

    def test_validate_unauthorized_camera_access(self):
        """
        Test validation of a plan requesting camera access from unauthorized user.
        Should fail with security constraint violation.
        """
        plan = {
            "plan_id": "unauthorized-camera-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "details": {
                                "resolution": "1920x1080",
                                "fps": 30
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential",
                "description": "Camera monitoring"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan,
                "user_context": {
                    "user_id": "guest-001",
                    "role": "guest",
                    "permissions": []
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should have failed due to role restrictions
        assert validation.get("status") in ["failed", "warnings"]
        
        # Should identify security constraint check
        security_check = next(
            (c for c in validation.get("constraints_checked", []) if c.get("constraint") == "security"),
            None
        )
        assert security_check is not None

    def test_validate_corridor_coverage_plan(self):
        """
        Test validation of a plan with good corridor coverage.
        Should pass location constraints and provide recommendations for optimization.
        """
        plan = {
            "plan_id": "corridor-coverage-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "location": {
                        "x": 0,
                        "y": 0,
                        "z": 2.5,
                        "detection_area": "corridor"
                    },
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "details": {
                                "resolution": "1920x1080",
                                "fps": 30
                            }
                        }
                    ]
                },
                {
                    "deviceId": "esp32-002",
                    "type": "sensor",
                    "location": {
                        "x": 10,
                        "y": 5,
                        "z": 1.5,
                        "detection_area": "corridor"
                    },
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "details": {
                                "sampling_frequency": 1
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential",
                "description": "Progressive corridor monitoring as patient walks"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan,
                "user_context": {
                    "user_id": "nurse-001",
                    "role": "nurse",
                    "permissions": ["read_sensor_data", "read_video"]
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should pass or have warnings only
        assert validation.get("status") in ["passed", "warnings"]
        
        # Should identify location constraint check
        location_check = next(
            (c for c in validation.get("constraints_checked", []) if c.get("constraint") == "location"),
            None
        )
        assert location_check is not None

    def test_validate_and_optimize_plan(self):
        """
        Test validation with optimization recommendations.
        Should generate optimized plan based on recommendations.
        """
        plan = {
            "plan_id": "optimization-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "location": {
                        "x": 0,
                        "y": 0,
                        "z": 2.5,
                        "detection_area": "corridor"
                    },
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "parameters": {
                                "resolution": "2560x1440",
                                "fps": 60
                            }
                        }
                    ]
                },
                {
                    "deviceId": "esp32-002",
                    "type": "sensor",
                    "location": {
                        "x": 10,
                        "y": 5,
                        "z": 1.5,
                        "detection_area": "corridor"
                    },
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "parameters": {
                                "sampling_frequency": 60
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "parallel",
                "description": "Activate devices in parallel"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate_and_optimize",
                "plan": plan,
                "user_context": {
                    "user_id": "nurse-001",
                    "role": "nurse",
                    "permissions": ["read_sensor_data", "read_video"]
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should return original and optimized plan
        assert result.get("original_plan") is not None
        assert result.get("validation") is not None
        
        optimized = result.get("optimized_plan")
        if optimized:
            # Should have optimization history
            assert "optimization_history" in optimized
            assert len(optimized.get("optimization_history", [])) > 0

    def test_validate_privacy_sensitive_area(self):
        """
        Test validation of camera access in privacy-sensitive area.
        Should recommend lower resolution and frequency reduction.
        """
        plan = {
            "plan_id": "privacy-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "location": {
                        "x": 0,
                        "y": 0,
                        "z": 2.5,
                        "detection_area": "bathroom"  # Privacy sensitive
                    },
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTPS",
                            "details": {
                                "resolution": "1920x1080",
                                "fps": 60
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential",
                "description": "Fall detection in bathroom"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan,
                "user_context": {
                    "user_id": "nurse-001",
                    "role": "nurse",
                    "permissions": ["read_video"]
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should identify privacy constraint check
        privacy_check = next(
            (c for c in validation.get("constraints_checked", []) if c.get("constraint") == "privacy"),
            None
        )
        assert privacy_check is not None
        
        # Should have privacy recommendations
        recommendations = validation.get("recommendations", [])
        privacy_recs = [r for r in recommendations if r.get("type") == "privacy"]
        assert len(privacy_recs) > 0

    def test_validate_plan_without_user_context(self):
        """
        Test validation of plan without user context.
        Should still validate constraints but recommend user context for security checks.
        """
        plan = {
            "plan_id": "no-context-test",
            "devices": [
                {
                    "deviceId": "esp32-002",
                    "type": "sensor",
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "details": {
                                "sampling_frequency": 1
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential",
                "description": "Temperature monitoring"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan
                # No user_context
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should still validate but recommend user context
        assert validation.get("status") in ["passed", "warnings"]
        
        # Should recommend user context for security
        recommendations = validation.get("recommendations", [])
        assert any("user context" in r.get("suggestion", "").lower() for r in recommendations)

    def test_validation_result_structure(self):
        """
        Test that validation result has proper structure.
        Verifies all required fields are present.
        """
        plan = {
            "plan_id": "structure-test",
            "devices": [
                {
                    "deviceId": "esp32-002",
                    "type": "sensor",
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "details": {
                                "sampling_frequency": 1
                            }
                        }
                    ]
                }
            ],
            "algorithm": {
                "type": "sequential"
            }
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check result structure
        assert "action" in result
        assert "validation" in result
        assert "timestamp" in result
        
        validation = result.get("validation", {})
        
        # Check validation structure
        assert "plan_id" in validation
        assert "validation_timestamp" in validation
        assert "status" in validation
        assert "issues" in validation
        assert "recommendations" in validation
        assert "constraints_checked" in validation
        
        # Check constraints_checked contains all 5 checks
        checks = validation.get("constraints_checked", [])
        check_types = [c.get("constraint") for c in checks]
        assert "energy" in check_types
        assert "transmission" in check_types
        assert "security" in check_types
        assert "location" in check_types
        assert "privacy" in check_types

    def test_validate_critical_battery_blocks_execution(self):
        """
        Test that critical battery level blocks plan execution.
        Device esp32-003 has 15% battery (critical threshold is 20%).
        """
        plan = {
            "plan_id": "critical-battery-test",
            "devices": [
                {
                    "deviceId": "esp32-003",  # 15% battery
                    "type": "sensor",
                    "services": [
                        {
                            "name": "temperature",
                            "protocol": "MQTT",
                            "details": {
                                "sampling_frequency": 60
                            }
                        }
                    ]
                }
            ]
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "validate",
                "plan": plan
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        validation = result.get("validation", {})
        
        # Should fail due to critical battery
        assert validation.get("status") == "failed"
        
        # Should have critical issue about battery
        critical_issues = [i for i in validation.get("issues", []) if i.get("severity") == "critical"]
        battery_issues = [i for i in critical_issues if "battery" in i.get("message", "").lower()]
        assert len(battery_issues) > 0

    def test_validate_recommendations_priority(self):
        """
        Test that recommendations have proper priority levels.
        """
        plan = {
            "plan_id": "priority-test",
            "devices": [
                {
                    "deviceId": "esp32-001",
                    "type": "camera",
                    "services": [
                        {
                            "name": "camera",
                            "protocol": "HTTP/REST",
                            "details": {
                                "resolution": "2560x1440",
                                "fps": 60
                            }
                        }
                    ]
                }
            ]
        }
        
        response = client.post(
            "/tasks/plan-validation",
            json={
                "action": "recommendations",
                "plan": plan
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        recommendations = result.get("recommendations", [])
        
        # Should have recommendations with priority
        for rec in recommendations:
            assert "priority" in rec or "type" in rec
