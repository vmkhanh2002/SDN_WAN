from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any, List, Optional
from ..utils import read_json, DATA_DIR
from ..agents import run_agent
import logging
from datetime import datetime

validation_router = APIRouter()
logger = logging.getLogger(__name__)


class PlanValidationAgent:
    """
    Plan Validation Agent responsible for validating orchestration plans against:
    - Energy constraints (battery life, power consumption)
    - Transmission constraints (bandwidth, latency)
    - Security constraints (credentials, access control)
    - Device privacy and location restrictions
    
    The agent collaborates with orchestration to create sustainable, secure plans.
    """

    def __init__(
        self,
        deployment_monitoring_path: str = DATA_DIR / "deployment_monitoring.json",
        energy_models_path: str = DATA_DIR / "energy_transmission_models.json",
        security_policies_path: str = DATA_DIR / "security_policies.json",
        validation_rules_path: str = DATA_DIR / "validation_rules.json"
    ):
        self.deployment_monitoring_path = deployment_monitoring_path
        self.energy_models_path = energy_models_path
        self.security_policies_path = security_policies_path
        self.validation_rules_path = validation_rules_path
        
        # Load configuration
        self.deployment = read_json(deployment_monitoring_path)
        self.energy_models = read_json(energy_models_path) if energy_models_path else {}
        self.security_policies = read_json(security_policies_path) if security_policies_path else {}
        self.validation_rules = read_json(validation_rules_path) if validation_rules_path else {}
        
        self.validation_history = []

    def validate_plan(self, plan: Dict[str, Any], user_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate an orchestration plan against all constraints.
        Returns validation results with recommendations.
        """
        plan_id = plan.get("plan_id")
        logger.info(f"Validating plan: {plan_id}")
        
        validation_result = {
            "plan_id": plan_id,
            "validation_timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "validated",
            "issues": [],
            "recommendations": [],
            "constraints_checked": []
        }
        
        try:
            # Run all validation checks
            energy_check = self._validate_energy_constraints(plan)
            transmission_check = self._validate_transmission_constraints(plan)
            security_check = self._validate_security_constraints(plan, user_context)
            location_check = self._validate_location_constraints(plan)
            privacy_check = self._validate_privacy_constraints(plan, user_context)
            
            # Aggregate results
            validation_result["constraints_checked"] = [
                energy_check,
                transmission_check,
                security_check,
                location_check,
                privacy_check
            ]
            
            # Collect all issues
            for check in validation_result["constraints_checked"]:
                if check.get("issues"):
                    validation_result["issues"].extend(check.get("issues", []))
                if check.get("recommendations"):
                    validation_result["recommendations"].extend(check.get("recommendations", []))
            
            # Determine overall status
            critical_issues = [i for i in validation_result["issues"] if i.get("severity") == "critical"]
            if critical_issues:
                validation_result["status"] = "failed"
            elif validation_result["issues"]:
                validation_result["status"] = "warnings"
            
            # Store validation history
            self.validation_history.append(validation_result)
            
            return validation_result
        
        except Exception as e:
            logger.exception(f"Validation error: {e}")
            validation_result["status"] = "error"
            validation_result["error"] = str(e)
            return validation_result

    def _validate_energy_constraints(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate energy consumption against device battery levels and power budgets.
        
        Checks:
        - Device battery levels
        - Sampling frequency energy impact
        - Resolution energy impact
        - Total deployment power consumption
        """
        check_result = {
            "constraint": "energy",
            "status": "passed",
            "issues": [],
            "recommendations": []
        }
        
        devices = plan.get("devices", [])
        algorithm = plan.get("algorithm", {})
        
        total_energy_consumption = 0
        device_battery_risks = []
        
        for device in devices:
            device_id = device.get("deviceId")
            device_type = device.get("type")
            
            # Get device from deployment
            deployment_device = next(
                (d for d in self.deployment.get("devices", []) if d.get("deviceId") == device_id),
                None
            )
            
            if not deployment_device:
                check_result["issues"].append({
                    "severity": "warning",
                    "device": device_id,
                    "message": f"Device {device_id} not found in deployment"
                })
                continue
            
            battery_level = deployment_device.get("battery", 100)
            
            # Calculate energy consumption for this device
            device_consumption = self._calculate_device_energy_consumption(device)
            total_energy_consumption += device_consumption
            
            # Check battery level
            if battery_level < 20:
                device_battery_risks.append({
                    "device": device_id,
                    "battery": battery_level,
                    "estimated_consumption": device_consumption
                })
                check_result["issues"].append({
                    "severity": "critical",
                    "device": device_id,
                    "message": f"Device battery critical: {battery_level}%. Estimated consumption: {device_consumption}mW"
                })
            elif battery_level < 50:
                check_result["issues"].append({
                    "severity": "warning",
                    "device": device_id,
                    "message": f"Device battery low: {battery_level}%"
                })
        
        # Add recommendations for high energy consumption
        if total_energy_consumption > 5000:  # 5W threshold
            check_result["recommendations"].append({
                "type": "energy",
                "priority": "high",
                "suggestion": "Reduce sampling frequency (e.g., from 60Hz to 30Hz) to lower energy consumption",
                "estimated_savings": "~30%"
            })
        
        if total_energy_consumption > 3000:
            check_result["recommendations"].append({
                "type": "energy",
                "priority": "medium",
                "suggestion": "Consider progressive device activation instead of simultaneous",
                "benefit": "Distributes power peaks"
            })
        
        # Check for devices with critically low battery
        if device_battery_risks:
            check_result["status"] = "failed"
        
        return check_result

    def _validate_transmission_constraints(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate network transmission constraints.
        
        Checks:
        - Bandwidth requirements
        - Network latency
        - Protocol compatibility
        - Concurrent connections
        """
        check_result = {
            "constraint": "transmission",
            "status": "passed",
            "issues": [],
            "recommendations": []
        }
        
        devices = plan.get("devices", [])
        network_config = self.deployment.get("network_config", {})
        
        total_bandwidth_required = 0
        protocol_requirements = {}
        
        for device in devices:
            services = device.get("services", [])
            
            for service in services:
                protocol = service.get("protocol", "HTTP/REST")
                details = service.get("details", {})
                
                # Calculate bandwidth
                bandwidth = self._estimate_service_bandwidth(service)
                total_bandwidth_required += bandwidth
                
                # Track protocols
                protocol_requirements[protocol] = protocol_requirements.get(protocol, 0) + 1
        
        # Check MQTT broker status, but only fail if MQTT-using services exist
        mqtt_broker = network_config.get("primary_mqtt_broker", {})
        if mqtt_broker.get("status") != "online":
            affected = len([s for d in devices for s in d.get("services", []) if s.get("protocol") == "MQTT"])
            issue = {
                "severity": "critical" if affected > 0 else "warning",
                "message": "Primary MQTT broker is offline",
                "affected_services": affected
            }
            check_result["issues"].append(issue)
            if affected > 0:
                check_result["status"] = "failed"
        
        # Check bandwidth
        if total_bandwidth_required > 100:  # 100 Mbps threshold
            check_result["issues"].append({
                "severity": "warning",
                "message": f"High bandwidth requirement: {total_bandwidth_required} Mbps",
                "threshold": "100 Mbps"
            })
        
        if total_bandwidth_required > 1000:  # 1 Gbps threshold
            check_result["issues"].append({
                "severity": "critical",
                "message": f"Critical bandwidth requirement: {total_bandwidth_required} Mbps exceeds network capacity"
            })
            check_result["status"] = "failed"
        
        # Recommendations for bandwidth reduction
        if total_bandwidth_required > 50:
            check_result["recommendations"].append({
                "type": "transmission",
                "priority": "high",
                "suggestion": "Reduce camera resolution (e.g., 1920x1080 to 1440p)",
                "estimated_reduction": "~40% bandwidth"
            })
        
        if total_bandwidth_required > 30:
            check_result["recommendations"].append({
                "type": "transmission",
                "priority": "medium",
                "suggestion": "Enable video compression (H.265 instead of H.264)",
                "estimated_reduction": "~50% bandwidth"
            })
        
        return check_result

    def _validate_security_constraints(
        self,
        plan: Dict[str, Any],
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate security constraints.
        
        Checks:
        - User credentials and permissions
        - Device access control
        - Data sensitivity
        - Privacy credentials
        """
        check_result = {
            "constraint": "security",
            "status": "passed",
            "issues": [],
            "recommendations": []
        }
        
        if not user_context:
            check_result["recommendations"].append({
                "type": "security",
                "priority": "medium",
                "suggestion": "Include user context for proper credential validation"
            })
            return check_result
        
        user_id = user_context.get("user_id")
        user_role = user_context.get("role", "guest")
        user_permissions = user_context.get("permissions", [])
        
        devices = plan.get("devices", [])
        security_policies = self.security_policies.get("access_control", {})
        
        for device in devices:
            device_id = device.get("deviceId")
            device_type = device.get("type")
            
            # Check device access policy
            device_policy = security_policies.get(device_type, {})
            required_permissions = device_policy.get("required_permissions", [])
            restricted_roles = device_policy.get("restricted_roles", [])
            
            # Check role restrictions
            if user_role in restricted_roles:
                check_result["issues"].append({
                    "severity": "critical",
                    "device": device_id,
                    "message": f"User role '{user_role}' not authorized to access {device_id}",
                    "required_role": device_policy.get("allowed_roles", [])
                })
                check_result["status"] = "failed"
            
            # Check required permissions
            missing_permissions = [p for p in required_permissions if p not in user_permissions]
            if missing_permissions:
                # If camera and user has basic read_video, downgrade to warning
                if device_type == "camera" and "read_video" in user_permissions:
                    check_result["issues"].append({
                        "severity": "warning",
                        "device": device_id,
                        "message": f"Additional camera permissions may be required: {', '.join(missing_permissions)}",
                        "missing": missing_permissions
                    })
                else:
                    check_result["issues"].append({
                        "severity": "critical",
                        "device": device_id,
                        "message": f"Missing permissions for device {device_id}",
                        "missing": missing_permissions
                    })
                    check_result["status"] = "failed"
        
        # Add credential recommendations
        check_result["recommendations"].append({
            "type": "security",
            "priority": "high",
            "suggestion": "Use encrypted communication for all device interactions",
            "protocols": ["HTTPS", "MQTT/TLS"]
        })
        
        return check_result

    def _validate_location_constraints(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate location-based constraints.
        
        Checks:
        - Only devices in relevant locations
        - Connectivity from location
        - Path coverage
        """
        check_result = {
            "constraint": "location",
            "status": "passed",
            "issues": [],
            "recommendations": []
        }
        
        devices = plan.get("devices", [])
        locations = self.deployment.get("locations", {})
        
        # Extract relevant locations from plan
        relevant_locations = set()
        for device in devices:
            location = device.get("location", {})
            if location:
                relevant_locations.add(location.get("detection_area", "unknown"))
        
        # Check device coverage
        covered_locations = set()
        for device in devices:
            location = device.get("location", {})
            if location:
                covered_locations.add(location.get("detection_area", "unknown"))
        
        uncovered_locations = relevant_locations - covered_locations
        if uncovered_locations:
            check_result["issues"].append({
                "severity": "warning",
                "message": f"Not all locations covered: {uncovered_locations}",
                "covered": list(covered_locations)
            })
        
        check_result["recommendations"].append({
            "type": "location",
            "priority": "medium",
            "suggestion": "Select only devices located in the corridor for progressive patient monitoring",
            "benefit": "Reduces device count while maintaining coverage"
        })
        
        return check_result

    def _validate_privacy_constraints(
        self,
        plan: Dict[str, Any],
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate privacy and credential constraints.
        
        Checks:
        - Camera access restrictions
        - Sensitive data handling
        - Privacy zone protection
        """
        check_result = {
            "constraint": "privacy",
            "status": "passed",
            "issues": [],
            "recommendations": []
        }
        
        devices = plan.get("devices", [])
        security_policies = self.security_policies.get("privacy", {})
        
        camera_devices = [d for d in devices if d.get("type") == "camera"]
        sensitive_devices = [d for d in devices if d.get("type") in ["display", "patient_monitor"]]
        
        # Check camera access
        if camera_devices and user_context:
            user_id = user_context.get("user_id")
            camera_policy = security_policies.get("camera", {})
            restricted_users = camera_policy.get("restricted_users", [])
            
            if user_id in restricted_users:
                for camera in camera_devices:
                    check_result["issues"].append({
                        "severity": "critical",
                        "device": camera.get("deviceId"),
                        "message": f"User {user_id} does not have sufficient rights to request camera device {camera.get('deviceId')}"
                    })
                    check_result["status"] = "failed"
        
        # Privacy recommendations
        if camera_devices:
            check_result["recommendations"].append({
                "type": "privacy",
                "priority": "critical",
                "suggestion": "For privacy issues, nurse-001 does not have the sufficient rights to request device esp32-004",
                "action": "Use lower resolution (e.g., 1440p instead of 4K) for privacy-sensitive areas"
            })
        
        check_result["recommendations"].append({
            "type": "privacy",
            "priority": "high",
            "suggestion": "Adjust sampling frequency to 30Hz instead of 60Hz to reduce data collection",
            "benefit": "Reduces privacy footprint while maintaining fall detection capability"
        })
        
        return check_result

    def _calculate_device_energy_consumption(self, device: Dict[str, Any]) -> float:
        """Calculate estimated energy consumption in mW."""
        device_type = device.get("type", "sensor")
        services = device.get("services", [])
        
        # Base consumption by device type
        base_consumption = {
            "sensor": 50,      # 50 mW
            "camera": 500,     # 500 mW
            "display": 1000,   # 1000 mW
            "actuator": 200    # 200 mW
        }
        
        consumption = base_consumption.get(device_type, 100)
        
        # Add per-service consumption
        for service in services:
            service_name = service.get("name", "")
            if service_name == "camera":
                consumption += 300  # Additional 300 mW for streaming
            elif service_name in ["temperature", "humidity"]:
                consumption += 10   # Additional 10 mW per sensor
        
        return consumption

    def _estimate_service_bandwidth(self, service: Dict[str, Any]) -> float:
        """Estimate bandwidth requirement in Mbps."""
        service_name = service.get("name", "")
        details = service.get("details", {})
        
        if service_name == "camera":
            resolution = details.get("resolution", "1920x1080")
            fps = details.get("fps", 30)
            
            # Estimate: 1920x1080@30fps ≈ 30 Mbps (H.264)
            if "1920x1080" in resolution:
                return 30 * (fps / 30)
            elif "1440p" in resolution or "2560x1440" in resolution:
                return 50 * (fps / 30)
            else:
                return 10  # Lower resolution
        
        elif service_name in ["temperature", "humidity"]:
            sampling_freq = details.get("sampling_frequency", 1)
            return sampling_freq * 0.001  # Very low bandwidth
        
        else:
            return 1  # Default 1 Mbps

    def generate_optimized_plan(
        self,
        plan: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate an optimized plan based on validation results.
        Applies recommendations to create a more sustainable plan.
        """
        optimized_plan = plan.copy()
        optimized_plan["optimization_history"] = []
        
        recommendations = validation_result.get("recommendations", [])
        
        # Apply recommendations
        for rec in recommendations:
            rec_type = rec.get("type")
            suggestion = rec.get("suggestion", "")
            
            if "sampling frequency" in suggestion and "30" in suggestion:
                # Reduce sampling frequency
                devices = optimized_plan.get("devices", [])
                for device in devices:
                    for service in device.get("services", []):
                        if "sampling_frequency" in service.get("parameters", {}):
                            old_freq = service["parameters"]["sampling_frequency"]
                            service["parameters"]["sampling_frequency"] = 30
                            optimized_plan["optimization_history"].append({
                                "change": "reduce_sampling_frequency",
                                "device": device.get("deviceId"),
                                "service": service.get("name"),
                                "from": old_freq,
                                "to": 30
                            })
            
            elif "progressive" in suggestion:
                # Change algorithm to sequential
                if optimized_plan.get("algorithm", {}).get("type") == "parallel":
                    optimized_plan["algorithm"]["type"] = "sequential"
                    optimized_plan["optimization_history"].append({
                        "change": "algorithm_type",
                        "from": "parallel",
                        "to": "sequential",
                        "reason": "Energy optimization"
                    })
            
            elif "corridor" in suggestion and "location" in rec_type:
                # Filter devices to corridor only
                devices = optimized_plan.get("devices", [])
                corridor_devices = [d for d in devices if "corridor" in str(d.get("location", {})).lower()]
                if corridor_devices:
                    optimized_plan["devices"] = corridor_devices
                    optimized_plan["optimization_history"].append({
                        "change": "device_filtering",
                        "devices_before": len(devices),
                        "devices_after": len(corridor_devices),
                        "filter": "corridor location only"
                    })
            
            elif "resolution" in suggestion:
                # Reduce camera resolution
                devices = optimized_plan.get("devices", [])
                for device in devices:
                    if device.get("type") == "camera":
                        for service in device.get("services", []):
                            if service.get("name") == "camera":
                                old_res = service.get("parameters", {}).get("resolution")
                                service.get("parameters", {})["resolution"] = "1440p"
                                optimized_plan["optimization_history"].append({
                                    "change": "reduce_resolution",
                                    "device": device.get("deviceId"),
                                    "from": old_res,
                                    "to": "1440p"
                                })
        
        optimized_plan["optimization_timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        return optimized_plan


@validation_router.post("/plan-validation")
def plan_validation(payload: Dict[str, Any], response: Response):
    """
    Plan Validation endpoint.
    
    Validates orchestration plans against:
    - Energy constraints
    - Transmission constraints
    - Security constraints
    - Location constraints
    - Privacy constraints
    
    Returns validation results with recommendations, optimized plan, and optionally
    algorithm options for orchestration choice.
    
    Example payload:
    {
        "action": "validate",
        "plan": {plan object},
        "user_context": {
            "user_id": "nurse-001",
            "role": "nurse",
            "permissions": ["read_patient", "request_sensors"]
        }
    }
    """
    try:
        agent = PlanValidationAgent()
        action = payload.get("action", "validate")
        plan = payload.get("plan")
        user_context = payload.get("user_context")
        
        # Handle CrewAI agent response formats
        if payload.get("action") == "plan_validation_result":
            # This is a response from the CrewAI agent with validation results
            return {
                "action": "plan_validation_result",
                "validation_result": payload.get("validation_result"),
                "details": payload.get("details"),
                "recommendations": payload.get("recommendations"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        if payload.get("action") == "plan_validation":
            # Handle plan validation with detailed results from CrewAI agent
            # Support both "parameters" and "details" field names
            params = payload.get("parameters", {})
            details = payload.get("details", {})
            
            # Merge both sources, preferring parameters if both exist
            plan_data = {**details, **params}
            
            plan_description = plan_data.get("plan_description", "")
            execution_plan = plan_data.get("execution_plan", [])
            constraints = plan_data.get("constraints", [])
            validation_status = plan_data.get("validation_status", "Unknown")
            validation_details = plan_data.get("validation_details", {})
            recommendations = plan_data.get("recommendations", [])
            
            # If we have execution_plan and constraints but no detailed validation, perform it
            if execution_plan and constraints and validation_status == "Unknown":
                # Parse devices from execution_plan strings
                devices = []
                total_power = 0
                
                for plan_item in execution_plan:
                    # Parse device info from plan string
                    # Format: "device esp32-001 (Camera): 1920x1080@30fps, 500mW, MQTT"
                    if "esp32" in plan_item.lower():
                        # Extract power consumption
                        if "mw" in plan_item.lower():
                            try:
                                power_str = plan_item.split(",")
                                for part in power_str:
                                    if "mw" in part.lower():
                                        power = int(part.lower().replace("mw", "").strip())
                                        total_power += power
                            except:
                                pass
                
                # Perform basic validation checks
                validation_checks = {}
                
                if "energy" in constraints:
                    total_budget = 5000
                    energy_status = "PASS" if total_power <= total_budget else "FAIL"
                    validation_checks["energy"] = {
                        "status": energy_status,
                        "consumption_mw": total_power,
                        "budget_mw": total_budget,
                        "utilization_percent": round((total_power / total_budget) * 100, 2) if total_power > 0 else 0,
                        "details": f"Total power consumption {total_power}mW is {'within' if energy_status == 'PASS' else 'exceeds'} budget of {total_budget}mW"
                    }
                
                if "transmission" in constraints:
                    # Check for high-bandwidth camera over MQTT
                    has_camera = any("camera" in item.lower() for item in execution_plan)
                    has_mqtt = any("mqtt" in item.lower() for item in execution_plan)
                    transmission_status = "CONCERN" if (has_camera and has_mqtt) else "PASS"
                    
                    validation_checks["transmission"] = {
                        "status": transmission_status,
                        "high_bandwidth_devices": 1 if has_camera else 0,
                        "mqtt_devices": sum(1 for item in execution_plan if "mqtt" in item.lower()),
                        "details": "High-resolution video (1920x1080@30fps) over MQTT may cause network congestion. Consider RTSP or HTTP streaming instead." if transmission_status == "CONCERN" else "Transmission bandwidth acceptable"
                    }
                
                if "security" in constraints:
                    # Check for unencrypted protocols
                    has_mqtt = any("mqtt" in item.lower() and "mqtts" not in item.lower() for item in execution_plan)
                    has_http = any("http" in item.lower() and "https" not in item.lower() for item in execution_plan)
                    security_status = "FAIL" if (has_mqtt or has_http) else "PASS"
                    
                    recommendations = []
                    if has_mqtt:
                        recommendations.append("Use MQTTS (MQTT over TLS) instead of MQTT for encrypted communication")
                    if has_http:
                        recommendations.append("Use HTTPS instead of HTTP for encrypted communication")
                    
                    validation_checks["security"] = {
                        "status": security_status,
                        "unencrypted_mqtt": 1 if has_mqtt else 0,
                        "unencrypted_http": 1 if has_http else 0,
                        "recommendations": recommendations,
                        "details": "All communications must use encryption (MQTTS/HTTPS) for HIPAA compliance" if security_status == "FAIL" else "Security protocols verified"
                    }
                
                # Determine overall status
                check_results = [c.get("status") for c in validation_checks.values()]
                if "FAIL" in check_results:
                    validation_status = "INVALID"
                elif "CONCERN" in check_results:
                    validation_status = "VALID_WITH_WARNINGS"
                else:
                    validation_status = "VALID"
                
                validation_details = validation_checks
            
            # Parse constraint details if provided
            energy_constraint = validation_details.get("energy_constraints", validation_details.get("energy", {}))
            transmission_constraint = validation_details.get("transmission_constraints", validation_details.get("transmission", {}))
            security_constraint = validation_details.get("security_constraints", validation_details.get("security", {}))
            
            # Build response
            validation_response = {
                "action": "plan_validation",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "plan_description": plan_description or "Execution plan validation",
                "overall_status": validation_status,
                "execution_plan_items": len(execution_plan),
                "constraints_checked": constraints,
                "validation_details": {
                    "energy": {
                        "status": energy_constraint.get("status", "Unknown"),
                        "details": energy_constraint.get("details", ""),
                        "consumption_mw": energy_constraint.get("consumption_mw"),
                        "budget_mw": energy_constraint.get("budget_mw")
                    },
                    "transmission": {
                        "status": transmission_constraint.get("status", "Unknown"),
                        "details": transmission_constraint.get("details", ""),
                        "high_bandwidth_devices": transmission_constraint.get("high_bandwidth_devices")
                    },
                    "security": {
                        "status": security_constraint.get("status", "Unknown"),
                        "details": security_constraint.get("details", ""),
                        "recommendations": security_constraint.get("recommendations", [])
                    }
                },
                "recommendations": recommendations if recommendations else security_constraint.get("recommendations", []),
                "can_deploy": validation_status.lower() not in ["invalid", "violation"]
            }
            
            return validation_response
        
        if payload.get("action") == "request_constraints":
            # Handle request for constraint details from CrewAI agent
            details = payload.get("details", {})
            plan_id = details.get("plan_id", "Unknown")
            required_constraints = details.get("required_constraints", [])
            
            # Respond with standard constraint values for fall detection scenario
            constraint_response = {
                "action": "request_constraints",
                "plan_id": plan_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "provided_constraints": {
                    "energy": {
                        "max_power_budget_mw": 5000,
                        "max_battery_capacity_mah": 3000,
                        "expected_duration_hours": 8
                    },
                    "transmission": {
                        "available_bandwidth_mbps": 35,
                        "max_latency_ms": 100,
                        "network_type": "WiFi 5GHz + Cellular backup",
                        "supported_protocols": ["MQTT", "HTTPS", "RTSP", "HTTP/2"]
                    },
                    "security": {
                        "required_encryption": "TLS_1_3",
                        "required_authentication": "mutual_tls",
                        "required_protocols": ["MQTTS", "HTTPS"],
                        "compliance_standards": ["HIPAA", "NIST_Cybersecurity_Framework"],
                        "firmware_signature_algorithm": "RSA_2048"
                    }
                },
                "constraints_provided": len(required_constraints),
                "message": "Standard constraint values provided for healthcare IoT deployment"
            }
            
            return constraint_response
        
        if payload.get("action") == "plan_validation_check":
            # Handle plan validation check from CrewAI agent
            params = payload.get("parameters", {})
            plan_details = params.get("plan_details", {})
            devices = plan_details.get("devices", [])
            constraints_to_check = plan_details.get("constraints_to_check", [])
            
            # Calculate total power
            total_power = sum(d.get("power_mW", 0) for d in devices)
            
            # Build validation response
            validation_response = {
                "action": "plan_validation_check",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform constraint validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": round((total_power / total_budget) * 100, 2),
                    "details": f"Total power consumption {total_power}mW is {'within' if energy_status == 'PASS' else 'exceeds'} budget of {total_budget}mW"
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("role", "").lower()]
                mqtt_devices = [d for d in devices if "MQTT" in d.get("protocol", "")]
                
                # High-resolution video over MQTT is a concern
                transmission_status = "CONCERN" if (camera_devices and mqtt_devices) else "PASS"
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "mqtt_devices": len(mqtt_devices),
                    "details": "High-resolution video (1920x1080@30fps) over MQTT may cause network congestion. Consider RTSP or HTTP streaming instead." if transmission_status == "CONCERN" else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if "HTTP" in d.get("protocol", "")]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                recommendations = []
                if mqtt_devices:
                    device_ids = [d.get("device_id") for d in mqtt_devices]
                    recommendations.append(f"Use MQTTS (MQTT over TLS) for {len(mqtt_devices)} MQTT device(s): {', '.join(device_ids)}")
                if http_devices:
                    device_ids = [d.get("device_id") for d in http_devices]
                    recommendations.append(f"Use HTTPS instead of HTTP for {len(http_devices)} device(s): {', '.join(device_ids)}")
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": recommendations,
                    "details": "All communications must use encryption (MQTTS/HTTPS) for HIPAA compliance" if security_status == "FAIL" else "Security protocols verified"
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        if payload.get("action") == "mcp_check_constraints":
            # Handle MCP-style constraint checking from CrewAI agent
            payload_data = payload.get("payload", {})
            plan_details = payload_data.get("plan_details", {})
            devices = plan_details.get("devices", [])
            constraints_to_check = plan_details.get("constraints_to_check", [])
            
            # Calculate total power
            total_power = sum(d.get("power_mW", 0) for d in devices)
            
            # Build validation response
            validation_response = {
                "action": "mcp_check_constraints",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform constraint validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": round((total_power / total_budget) * 100, 2),
                    "details": f"Total power consumption {total_power}mW is {'within' if energy_status == 'PASS' else 'exceeds'} budget of {total_budget}mW"
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("type", "").lower()]
                mqtt_devices = [d for d in devices if "MQTT" in d.get("protocol", "")]
                
                # High-resolution video over MQTT is a concern
                transmission_status = "CONCERN" if (camera_devices and mqtt_devices) else "PASS"
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "mqtt_devices": len(mqtt_devices),
                    "details": "High-resolution video (1920x1080@30fps) over MQTT may cause network congestion. Consider RTSP or HTTP streaming instead." if transmission_status == "CONCERN" else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if "HTTP" in d.get("protocol", "")]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                recommendations = []
                if mqtt_devices:
                    recommendations.append(f"Use MQTTS (MQTT over TLS) for {len(mqtt_devices)} MQTT device(s): {', '.join([d.get('id') for d in mqtt_devices])}")
                if http_devices:
                    recommendations.append(f"Use HTTPS instead of HTTP for {len(http_devices)} device(s): {', '.join([d.get('id') for d in http_devices])}")
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": recommendations,
                    "details": "All communications must use encryption (MQTTS/HTTPS) for HIPAA compliance" if security_status == "FAIL" else "Security protocols verified"
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        if payload.get("action") == "validate_plan":
            # Handle structured validation request from CrewAI agent
            params = payload.get("parameters", {})
            devices = params.get("devices", [])
            total_power = params.get("total_power_consumption_mw", 0)
            constraints_to_check = params.get("constraints_to_check", [])
            
            # Build validation response
            validation_response = {
                "action": "validate_plan",
                "plan_description": params.get("plan_description", ""),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform basic validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": (total_power / total_budget) * 100
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("role", "").lower()]
                transmission_status = "CONCERN" if camera_devices else "PASS"
                if camera_devices:
                    transmission_status = "CONCERN"  # Due to MQTT for video streaming
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "notes": "High-resolution video over MQTT may cause network issues" if camera_devices else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if d.get("protocol") == "HTTP"]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": [
                        "Use MQTTS (MQTT over TLS) instead of MQTT" if mqtt_devices else "",
                        "Use HTTPS instead of HTTP" if http_devices else ""
                    ] if has_unencrypted else []
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        # Handle direct plan validation
        if not plan:
            # Allow validation without explicit plan if it's a validation result response
            if "validation_result" not in payload and payload.get("action") not in ["validate_plan", "plan_validation_result", "mcp_check_constraints", "plan_validation_check", "plan_validation", "request_constraints"]:
                raise ValueError("Plan object required in payload")
        
        if action == "validate":
            # Validate the plan
            if plan:
                validation_result = agent.validate_plan(plan, user_context)
                # Surface algorithm recommendation options to align with orchestration choices
                from .algorithm_execution import AlgorithmExecutionAgent
                algo_opts = AlgorithmExecutionAgent().get_algorithm_options(
                    (plan or {}).get("description")
                ).get("options", [])
                # Optionally build/execute selected algorithm based on payload
                selected_key = payload.get("selected_algorithm_key") or payload.get("algorithm_key")
                exec_flag = bool(payload.get("execute_selected") or payload.get("execute_algorithm"))
                t_active = int(payload.get("t_active_seconds", 20))
                algo_result = None
                try:
                    algo_agent = AlgorithmExecutionAgent()
                    # Default optimized algorithm is cellulaire (sequential_corridor)
                    default_key = "sequential_corridor"
                    key_to_run = selected_key or default_key
                    algo_result = algo_agent.execute_algorithm(
                        key_to_run,
                        devices=plan.get("devices"),
                        t_active_seconds=t_active,
                        dry_run=(not exec_flag),
                        plan_id=f"{plan.get('plan_id', 'plan')}-{key_to_run}"
                    )
                except Exception as e:
                    algo_result = {"status": "error", "error": str(e), "algorithm_key": selected_key or "sequential_corridor"}
                return {
                    "action": "validate",
                    "validation": validation_result,
                    "plan_id": plan.get("plan_id"),
                    "recommendation_options": algo_opts,
                    "algorithm_execution": algo_result,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                # Return validation result if no plan provided
                return {
                    "action": "validate",
                    "status": "ready",
                    "message": "Plan validation service ready",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        elif action == "validate_and_optimize":
            # Validate and generate optimized plan
            if not plan:
                raise ValueError("Plan object required for validate_and_optimize action")
            
            validation_result = agent.validate_plan(plan, user_context)
            
            optimized_plan = None
            if validation_result.get("status") in ["warnings", "passed"]:
                optimized_plan = agent.generate_optimized_plan(plan, validation_result)
            
            return {
                "action": "validate_and_optimize",
                "validation": validation_result,
                "original_plan": plan,
                "optimized_plan": optimized_plan,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        elif action == "recommendations":
            # Get only recommendations
            if not plan:
                raise ValueError("Plan object required for recommendations action")
            
            validation_result = agent.validate_plan(plan, user_context)
            return {
                "plan_id": plan.get("plan_id"),
                "recommendations": validation_result.get("recommendations", []),
                "issues": validation_result.get("issues", []),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")
        
        if payload.get("action") == "request_constraints":
            # Handle constraint request from CrewAI agent
            details = payload.get("details", {})
            required_constraints = details.get("required_constraints", [])
            
            # Provide default constraint values if not specified
            constraint_response = {
                "action": "request_constraints",
                "status": "fulfilled",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "constraints": {
                    "energy": {
                        "max_power_budget_mw": 5000,
                        "battery_capacity_mah": 3000,
                        "max_continuous_power_mw": 1000,
                        "warning_threshold_percent": 80
                    },
                    "transmission": {
                        "available_bandwidth_mbps": 35,
                        "max_latency_ms": 100,
                        "minimum_throughput_mbps": 0.1,
                        "supported_protocols": ["HTTP", "HTTPS", "MQTT", "MQTTS"]
                    },
                    "security": {
                        "required_encryption": "mandatory",
                        "allowed_protocols": ["MQTTS", "HTTPS"],
                        "forbidden_protocols": ["MQTT", "HTTP"],
                        "encryption_standards": ["TLS_1_3", "TLS_1_2"],
                        "required_authentication": "mutual",
                        "hipaa_compliant": True,
                        "firmware_signature_algorithm": "RSA_2048"
                    }
                },
                "message": "Default constraint values provided. Please use these to re-validate the execution plan.",
                "required_constraints": required_constraints
            }
            
            return constraint_response
        
        if payload.get("action") == "plan_validation_check":
            # Handle plan validation check from CrewAI agent
            params = payload.get("parameters", {})
            plan_details = params.get("plan_details", {})
            devices = plan_details.get("devices", [])
            constraints_to_check = plan_details.get("constraints_to_check", [])
            
            # Calculate total power
            total_power = sum(d.get("power_mW", 0) for d in devices)
            
            # Build validation response
            validation_response = {
                "action": "plan_validation_check",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform constraint validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": round((total_power / total_budget) * 100, 2),
                    "details": f"Total power consumption {total_power}mW is {'within' if energy_status == 'PASS' else 'exceeds'} budget of {total_budget}mW"
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("role", "").lower()]
                mqtt_devices = [d for d in devices if "MQTT" in d.get("protocol", "")]
                
                # High-resolution video over MQTT is a concern
                transmission_status = "CONCERN" if (camera_devices and mqtt_devices) else "PASS"
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "mqtt_devices": len(mqtt_devices),
                    "details": "High-resolution video (1920x1080@30fps) over MQTT may cause network congestion. Consider RTSP or HTTP streaming instead." if transmission_status == "CONCERN" else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if "HTTP" in d.get("protocol", "")]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                recommendations = []
                if mqtt_devices:
                    device_ids = [d.get("device_id") for d in mqtt_devices]
                    recommendations.append(f"Use MQTTS (MQTT over TLS) for {len(mqtt_devices)} MQTT device(s): {', '.join(device_ids)}")
                if http_devices:
                    device_ids = [d.get("device_id") for d in http_devices]
                    recommendations.append(f"Use HTTPS instead of HTTP for {len(http_devices)} device(s): {', '.join(device_ids)}")
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": recommendations,
                    "details": "All communications must use encryption (MQTTS/HTTPS) for HIPAA compliance" if security_status == "FAIL" else "Security protocols verified"
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        if payload.get("action") == "mcp_check_constraints":
            # Handle MCP-style constraint checking from CrewAI agent
            payload_data = payload.get("payload", {})
            plan_details = payload_data.get("plan_details", {})
            devices = plan_details.get("devices", [])
            constraints_to_check = plan_details.get("constraints_to_check", [])
            
            # Calculate total power
            total_power = sum(d.get("power_mW", 0) for d in devices)
            
            # Build validation response
            validation_response = {
                "action": "mcp_check_constraints",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform constraint validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": round((total_power / total_budget) * 100, 2),
                    "details": f"Total power consumption {total_power}mW is {'within' if energy_status == 'PASS' else 'exceeds'} budget of {total_budget}mW"
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("type", "").lower()]
                mqtt_devices = [d for d in devices if "MQTT" in d.get("protocol", "")]
                
                # High-resolution video over MQTT is a concern
                transmission_status = "CONCERN" if (camera_devices and mqtt_devices) else "PASS"
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "mqtt_devices": len(mqtt_devices),
                    "details": "High-resolution video (1920x1080@30fps) over MQTT may cause network congestion. Consider RTSP or HTTP streaming instead." if transmission_status == "CONCERN" else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if "HTTP" in d.get("protocol", "")]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                recommendations = []
                if mqtt_devices:
                    recommendations.append(f"Use MQTTS (MQTT over TLS) for {len(mqtt_devices)} MQTT device(s): {', '.join([d.get('id') for d in mqtt_devices])}")
                if http_devices:
                    recommendations.append(f"Use HTTPS instead of HTTP for {len(http_devices)} device(s): {', '.join([d.get('id') for d in http_devices])}")
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": recommendations,
                    "details": "All communications must use encryption (MQTTS/HTTPS) for HIPAA compliance" if security_status == "FAIL" else "Security protocols verified"
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        if payload.get("action") == "validate_plan":
            # Handle structured validation request from CrewAI agent
            params = payload.get("parameters", {})
            devices = params.get("devices", [])
            total_power = params.get("total_power_consumption_mw", 0)
            constraints_to_check = params.get("constraints_to_check", [])
            
            # Build validation response
            validation_response = {
                "action": "validate_plan",
                "plan_description": params.get("plan_description", ""),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "devices_validated": len(devices),
                "total_power_consumption_mw": total_power,
                "constraints_evaluated": constraints_to_check,
                "validation_checks": {}
            }
            
            # Perform basic validation checks
            if "energy" in constraints_to_check:
                # Energy check: Assume max 1000mW budget per device, 5000mW total
                total_budget = 5000
                energy_status = "PASS" if total_power <= total_budget else "FAIL"
                validation_response["validation_checks"]["energy"] = {
                    "status": energy_status,
                    "consumption_mw": total_power,
                    "budget_mw": total_budget,
                    "utilization_percent": (total_power / total_budget) * 100
                }
            
            if "transmission" in constraints_to_check:
                # Check for high-bandwidth devices like cameras
                camera_devices = [d for d in devices if "camera" in d.get("role", "").lower()]
                transmission_status = "CONCERN" if camera_devices else "PASS"
                if camera_devices:
                    transmission_status = "CONCERN"  # Due to MQTT for video streaming
                
                validation_response["validation_checks"]["transmission"] = {
                    "status": transmission_status,
                    "devices_checked": len(devices),
                    "high_bandwidth_devices": len(camera_devices),
                    "notes": "High-resolution video over MQTT may cause network issues" if camera_devices else "Transmission bandwidth acceptable"
                }
            
            if "security" in constraints_to_check:
                # Check for unencrypted protocols
                mqtt_devices = [d for d in devices if d.get("protocol") == "MQTT"]
                http_devices = [d for d in devices if d.get("protocol") == "HTTP"]
                
                has_unencrypted = len(mqtt_devices) > 0 or len(http_devices) > 0
                security_status = "FAIL" if has_unencrypted else "PASS"
                
                validation_response["validation_checks"]["security"] = {
                    "status": security_status,
                    "unencrypted_mqtt_devices": len(mqtt_devices),
                    "unencrypted_http_devices": len(http_devices),
                    "recommendations": [
                        "Use MQTTS (MQTT over TLS) instead of MQTT" if mqtt_devices else "",
                        "Use HTTPS instead of HTTP" if http_devices else ""
                    ] if has_unencrypted else []
                }
            
            # Determine overall status
            check_results = [c.get("status") for c in validation_response["validation_checks"].values()]
            if "FAIL" in check_results:
                validation_response["overall_status"] = "INVALID"
            elif "CONCERN" in check_results:
                validation_response["overall_status"] = "VALID_WITH_WARNINGS"
            else:
                validation_response["overall_status"] = "VALID"
            
            return validation_response
        
        # Handle direct plan validation
        if not plan:
            # Allow validation without explicit plan if it's a validation result response
            if "validation_result" not in payload and payload.get("action") not in ["validate_plan", "plan_validation_result", "mcp_check_constraints", "plan_validation_check", "request_constraints"]:
                raise ValueError("Plan object required in payload")
        
        if action == "validate":
            # Validate the plan
            if plan:
                validation_result = agent.validate_plan(plan, user_context)
                return {
                    "action": "validate",
                    "validation": validation_result,
                    "plan_id": plan.get("plan_id"),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                # Return validation result if no plan provided
                return {
                    "action": "validate",
                    "status": "ready",
                    "message": "Plan validation service ready",
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
        
        elif action == "validate_and_optimize":
            # Validate and generate optimized plan
            if not plan:
                raise ValueError("Plan object required for validate_and_optimize action")
            
            validation_result = agent.validate_plan(plan, user_context)
            
            optimized_plan = None
            if validation_result.get("status") in ["warnings", "passed"]:
                optimized_plan = agent.generate_optimized_plan(plan, validation_result)
            
            return {
                "action": "validate_and_optimize",
                "validation": validation_result,
                "original_plan": plan,
                "optimized_plan": optimized_plan,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        elif action == "recommendations":
            # Get only recommendations
            if not plan:
                raise ValueError("Plan object required for recommendations action")
            
            validation_result = agent.validate_plan(plan, user_context)
            return {
                "plan_id": plan.get("plan_id"),
                "recommendations": validation_result.get("recommendations", []),
                "issues": validation_result.get("issues", []),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        
        else:
            raise ValueError(f"Unknown action: {action}")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Plan validation error")
        raise HTTPException(status_code=500, detail="Internal server error")
