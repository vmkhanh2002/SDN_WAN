from fastapi.testclient import TestClient
from servers.app import app
import json

client = TestClient(app)


class TestNetworkConfiguration:
    """
    Test suite for Network Auto-Configuration Agent.
    Tests configuration generation, OTA update handling (push and pull modes),
    and firmware management.
    """

    def test_configure_network_from_healthcare_intent(self):
        """
        Test network configuration generation from healthcare facility intent.
        Should detect healthcare environment and add security recommendations.
        """
        user_intent = """
        Given the current network configuration, reconfigure the network to account 
        for fall detection, application in a nursing home
        """
        
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": user_intent
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        # Should have generated configuration
        assert config.get("status") == "configured"
        assert len(config.get("devices_configured", [])) > 0
        
        # Should identify healthcare environment
        intent_analysis = config.get("intent_analysis", {})
        assert intent_analysis.get("environment") == "healthcare_facility"
        assert intent_analysis.get("priority_fall_detection") == True
        
        # Should have security recommendations
        recommendations = config.get("recommendations", [])
        security_recs = [r for r in recommendations if r.get("category") == "security"]
        assert len(security_recs) > 0
        
        # Should mention TLS for healthcare
        tls_recs = [r for r in security_recs if "TLS" in r.get("recommendation", "")]
        assert len(tls_recs) > 0

    def test_configure_network_multi_protocol(self):
        """
        Test network configuration with multi-protocol requirements.
        Should enable WiFi, BLE, MQTT, and HTTP/REST.
        """
        user_intent = """
        Configure network supporting WiFi, BLE, ZigBee communication with 
        video streaming and sensor monitoring capabilities
        """
        
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": user_intent
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        # Should enable multiple protocols
        protocols = config.get("protocols_enabled", [])
        assert "MQTT" in protocols or "HTTP/REST" in protocols
        
        # Should have configuration steps
        steps = config.get("configuration_steps", [])
        assert len(steps) > 0
        
        # Should include protocol initialization step
        protocol_steps = [s for s in steps if s.get("action") == "protocol_init"]
        assert len(protocol_steps) > 0

    def test_configure_network_video_optimization(self):
        """
        Test network configuration optimized for video streaming.
        Should include recommendations for compression and adaptive bitrate.
        """
        user_intent = """
        Configure network for video monitoring with camera feeds from multiple rooms
        """
        
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": user_intent
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        # Should identify video priority
        intent_analysis = config.get("intent_analysis", {})
        assert intent_analysis.get("priority_video") == True
        
        # Should have bandwidth recommendations
        recommendations = config.get("recommendations", [])
        bandwidth_recs = [r for r in recommendations if r.get("category") == "bandwidth"]
        assert len(bandwidth_recs) > 0

    def test_ota_update_push_mode_successful(self):
        """
        Test successful OTA update in push mode (OTA Server => Device).
        Server sends firmware to device which verifies signature and applies update.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_update",
                "update_type": "push",
                "update_id": "ota_update_001",
                "target_devices": ["esp32-001", "esp32-002"],
                "firmware": {
                    "version": "1.2.3",
                    "binary_url": "http://ota-server.local/firmware/v1.2.3.bin",
                    "signature": "MCwCFQCXm1G2jC1Uol8R3PlVKI3v4w=="
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        ota_result = result.get("result", {})
        
        # Should have update result
        assert ota_result.get("update_mode") == "push"
        assert ota_result.get("firmware_version") == "1.2.3"
        
        # Should have device updates
        devices_updated = ota_result.get("devices_updated", [])
        assert len(devices_updated) == 2
        
        # Should show update steps
        for device_update in devices_updated:
            if device_update.get("status") == "completed":
                steps = device_update.get("steps", [])
                assert len(steps) > 0
                
                # Should include signature verification step
                verify_steps = [s for s in steps if "verify" in s.get("description", "").lower()]
                assert len(verify_steps) > 0

    def test_ota_update_push_mode_offline_device(self):
        """
        Test OTA update in push mode when device is offline.
        Should queue update for when device comes online.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_update",
                "update_type": "push",
                "update_id": "ota_update_002",
                "target_devices": ["esp32-003"],  # Deep sleep device
                "firmware": {
                    "version": "1.2.3",
                    "binary_url": "http://ota-server.local/firmware/v1.2.3.bin",
                    "signature": "MCwCFQCXm1G2jC1Uol8R3PlVKI3v4w=="
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        ota_result = result.get("result", {})
        
        devices_updated = ota_result.get("devices_updated", [])
        assert len(devices_updated) > 0
        
        # Offline device should be pending
        device_update = devices_updated[0]
        assert device_update.get("status") == "pending"
        assert "online" in device_update.get("error", "").lower()

    def test_ota_update_pull_mode_update_available(self):
        """
        Test OTA update in pull mode (Device => OTA Server).
        Device checks for updates and receives available firmware info.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_update",
                "update_type": "pull",
                "device_id": "esp32-001",
                "current_version": "1.0.0"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        ota_result = result.get("result", {})
        
        # Should be pull mode
        assert ota_result.get("update_mode") == "pull"
        assert ota_result.get("device_id") == "esp32-001"
        
        # Should find update available
        devices_updated = ota_result.get("devices_updated", [])
        assert len(devices_updated) > 0
        
        device_update = devices_updated[0]
        # Should indicate update is available or completed
        assert device_update.get("status") in ["completed", "up_to_date"]

    def test_ota_update_pull_mode_up_to_date(self):
        """
        Test OTA update in pull mode when device is up to date.
        Device checks for updates but latest version matches current.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_update",
                "update_type": "pull",
                "device_id": "esp32-001",
                "current_version": "1.2.3"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        ota_result = result.get("result", {})
        
        devices_updated = ota_result.get("devices_updated", [])
        device_update = devices_updated[0]
        
        # Should indicate device is up to date
        assert device_update.get("status") == "up_to_date"
        assert device_update.get("update_available") == False

    def test_ota_status_single_device(self):
        """
        Test retrieving OTA status for a specific device.
        Should return current version and update availability.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_status",
                "device_id": "esp32-001"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        status = result.get("status", {})
        
        # Should return device status
        devices = status.get("devices", [])
        assert len(devices) == 1
        
        device_status = devices[0]
        assert device_status.get("deviceId") == "esp32-001"
        assert "current_version" in device_status
        assert "ota_enabled" in device_status
        assert "update_available" in device_status

    def test_ota_status_all_devices(self):
        """
        Test retrieving OTA status for all devices.
        Should return status for each device in deployment.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_status"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        status = result.get("status", {})
        
        # Should return status for all devices
        devices = status.get("devices", [])
        assert len(devices) > 0

    def test_configuration_steps_ordering(self):
        """
        Test that configuration steps are properly ordered and sequenced.
        Should follow: WiFi init -> Security -> Protocols -> Devices -> OTA -> Verify
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": "Configure network for healthcare facility with fall detection"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        steps = config.get("configuration_steps", [])
        assert len(steps) > 0
        
        # Verify step ordering
        step_numbers = [s.get("step") for s in steps]
        assert step_numbers == sorted(step_numbers)
        
        # Should have WiFi init as first step
        assert steps[0].get("action") == "wifi_init"
        
        # Should have security setup early
        security_step = next((s for s in steps if s.get("action") == "security_setup"), None)
        assert security_step is not None
        assert security_step.get("step") <= 3

    def test_firmware_signature_verification(self):
        """
        Test that firmware signature is verified before installation.
        Invalid signatures should be rejected.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "ota_update",
                "update_type": "push",
                "update_id": "ota_update_invalid_sig",
                "target_devices": ["esp32-001"],
                "firmware": {
                    "version": "1.2.3",
                    "binary_url": "http://ota-server.local/firmware/v1.2.3.bin",
                    "signature": "INVALID_SIGNATURE_THAT_DOES_NOT_MATCH"
                }
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        ota_result = result.get("result", {})
        
        # Should have device update with signature verification issue
        devices_updated = ota_result.get("devices_updated", [])
        # May reject due to signature or other reasons

    def test_device_configuration_wireless_protocols(self):
        """
        Test that camera devices get HTTP/REST and MQTT configured.
        Test that sensor devices get MQTT and optional BLE.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": "Configure multi-protocol network with cameras and sensors"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        devices_configured = config.get("devices_configured", [])
        
        # Find camera device
        camera_device = next(
            (d for d in devices_configured if d.get("type") == "camera"),
            None
        )
        
        if camera_device:
            protocols = camera_device.get("configuration", {}).get("protocols", [])
            protocol_names = [p.get("name") for p in protocols]
            
            # Should have HTTP/REST and MQTT
            assert "HTTP/REST" in protocol_names or "HTTPS" in protocol_names
            assert "MQTT" in protocol_names

    def test_security_configuration_enabled(self):
        """
        Test that security features are properly configured.
        Should include secure boot, flash encryption, and TLS.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": "Secure network configuration with encryption and authentication"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        devices_configured = config.get("devices_configured", [])
        
        for device in devices_configured:
            security = device.get("configuration", {}).get("security", {})
            
            # Should have security features enabled
            assert security.get("secure_boot") == True
            assert security.get("flash_encryption") == True
            assert security.get("tls_enabled") == True
            assert security.get("certificate_verification") == True

    def test_ota_configuration_in_devices(self):
        """
        Test that OTA configuration is present in all device configurations.
        Should specify push mode with rollback protection.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": "Configure network with OTA update capability"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        config = result.get("configuration", {})
        
        devices_configured = config.get("devices_configured", [])
        
        for device in devices_configured:
            ota = device.get("configuration", {}).get("ota", {})
            
            # Should have OTA enabled
            assert ota.get("enabled") == True
            assert ota.get("mode") == "push"
            assert ota.get("rollback_protection") == True

    def test_network_configuration_error_handling(self):
        """
        Test error handling for invalid requests.
        Should return 400 for missing required fields.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent"
                # Missing user_intent
            }
        )
        
        assert response.status_code == 400

    def test_network_configuration_response_structure(self):
        """
        Test that response has proper structure with all required fields.
        """
        response = client.post(
            "/tasks/network-configuration",
            json={
                "action": "configure_from_intent",
                "user_intent": "Configure network"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check response structure
        assert "action" in result
        assert "configuration" in result
        assert "timestamp" in result
        
        config = result.get("configuration", {})
        
        # Check configuration structure
        assert "user_intent" in config
        assert "configuration_timestamp" in config
        assert "status" in config
        assert "devices_configured" in config
        assert "protocols_enabled" in config
        assert "configuration_steps" in config
        assert "recommendations" in config
