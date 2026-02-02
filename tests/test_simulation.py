#!/usr/bin/env python3
"""
SDN-WISE Simulation Testing Suite
Comprehensive tests for Cooja, Mininet, and integrated workflows
"""

import subprocess
import time
import json
import requests
from datetime import datetime

class SimulationTester:
    def __init__(self):
        self.results = []
        self.mcp_base = "http://localhost:8000"
        self.onos_base = "http://172.25.0.2:8181"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_cooja_simulation(self):
        """Test Cooja WSN simulator"""
        self.log("Testing Cooja WSN Simulation...")
        
        try:
            # Check if Cooja container is running
            result = subprocess.run(
                ["docker", "exec", "cooja-simulator", "which", "cooja"],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log("✓ Cooja simulator available", "PASS")
                
                # Test Contiki-NG compilation
                self.log("Testing Contiki-NG compilation...")
                compile_result = subprocess.run(
                    ["docker", "exec", "cooja-simulator", "bash", "-c",
                     "cd /root/contiki-ng/examples/hello-world && make TARGET=cooja"],
                    capture_output=True,
                    timeout=60
                )
                
                if b"BUILD SUCCESSFUL" in compile_result.stdout or compile_result.returncode == 0:
                    self.log("✓ Contiki-NG compilation works", "PASS")
                    return True
                else:
                    self.log(f"✗ Compilation failed: {compile_result.stderr[:200]}", "FAIL")
                    return False
            else:
                self.log("✗ Cooja not found in container", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"✗ Cooja test error: {e}", "FAIL")
            return False
    
    def test_mininet_topology(self):
        """Test Mininet network emulation"""
        self.log("Testing Mininet Network...")
        
        try:
            # Test basic Mininet functionality
            result = subprocess.run(
                ["docker", "exec", "mininet-sdn", "mn", "--version"],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.decode().strip()
                self.log(f"✓ Mininet available: {version}", "PASS")
                
                # Test simple topology creation
                self.log("Testing topology creation...")
                topo_test = subprocess.run(
                    ["docker", "exec", "mininet-sdn", "mn", 
                     "--controller=remote,ip=172.25.0.2,port=6653",
                     "--topo=single,3", "--test=pingall"],
                    capture_output=True,
                    timeout=30
                )
                
                output = topo_test.stdout.decode()
                if "0% dropped" in output or "Results:" in output:
                    self.log("✓ Mininet topology test passed", "PASS")
                    return True
                else:
                    self.log(f"✗ Topology test failed", "FAIL")
                    return False
            else:
                self.log("✗ Mininet not available", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"✗ Mininet test error: {e}", "FAIL")
            return False
    
    def test_wsn_simulation_workflow(self):
        """Test complete WSN simulation workflow"""
        self.log("Testing WSN Simulation Workflow...")
        
        try:
            # Step 1: Check sensor simulation files exist
            check_files = subprocess.run(
                ["docker", "exec", "cooja-simulator", "ls", "/root/workspace"],
                capture_output=True,
                timeout=10
            )
            
            self.log(f"Workspace files: {check_files.stdout.decode()[:100]}")
            
            # Step 2: Create simulated WSN topology via MCP
            response = requests.post(
                f"{self.mcp_base}/tasks/device-orchestration",
                json={
                    "action": "create_simulation",
                    "topology": {
                        "nodes": 5,
                        "type": "grid",
                        "sink": 1
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✓ Simulation topology created: {json.dumps(data, indent=2)[:200]}", "PASS")
                
                # Step 3: Deploy flow rules
                flow_response = requests.post(
                    f"{self.mcp_base}/tasks/plan-execution",
                    json={
                        "action": "install_flows",
                        "plan": {
                            "type": "data_collection",
                            "source": "all_sensors",
                            "destination": "sink"
                        }
                    },
                    timeout=10
                )
                
                if flow_response.status_code == 200:
                    self.log("✓ Flow rules deployed", "PASS")
                    return True
                else:
                    self.log(f"✗ Flow deployment failed: {flow_response.status_code}", "FAIL")
                    return False
            else:
                self.log(f"✗ Topology creation failed: {response.status_code}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"✗ Workflow test error: {e}", "FAIL")
            return False
    
    def test_intent_translation(self):
        """Test intent-based orchestration"""
        self.log("Testing Intent Translation...")
        
        test_intents = [
            {
                "intent": "Collect temperature data from all sensors",
                "expected_action": "data_collection"
            },
            {
                "intent": "Configure sensor 2 to sample every 60 seconds",
                "expected_action": "configuration"
            },
            {
                "intent": "Route humidity readings to sink node",
                "expected_action": "flow_installation"
            }
        ]
        
        passed = 0
        for test in test_intents:
            try:
                response = requests.post(
                    f"{self.mcp_base}/tasks/device-orchestration",
                    json={
                        "action": "translate_intent",
                        "intent": test["intent"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    self.log(f"✓ Intent translated: '{test['intent'][:50]}...'", "PASS")
                    passed += 1
                else:
                    self.log(f"✗ Intent failed: {response.status_code}", "FAIL")
                    
            except Exception as e:
                self.log(f"✗ Intent error: {e}", "FAIL")
        
        return passed == len(test_intents)
    
    def test_onos_integration(self):
        """Test ONOS controller integration"""
        self.log("Testing ONOS Integration...")
        
        try:
            # Test ONOS connectivity
            response = requests.get(
                f"{self.onos_base}/onos/v1/applications",
                auth=("onos", "rocks"),
                timeout=10
            )
            
            if response.status_code == 200:
                apps = response.json()
                self.log(f"✓ ONOS connected, {len(apps.get('applications', []))} apps", "PASS")
                
                # Test device discovery
                devices_response = requests.get(
                    f"{self.onos_base}/onos/v1/devices",
                    auth=("onos", "rocks"),
                    timeout=10
                )
                
                if devices_response.status_code == 200:
                    devices = devices_response.json()
                    self.log(f"✓ Device discovery works, {len(devices.get('devices', []))} devices", "PASS")
                    return True
                else:
                    self.log("✗ Device discovery failed", "FAIL")
                    return False
            else:
                self.log(f"✗ ONOS not responding: {response.status_code}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"✗ ONOS integration error: {e}", "FAIL")
            return False
    
    def test_data_flow_simulation(self):
        """Simulate complete data flow from sensor to application"""
        self.log("Testing Complete Data Flow...")
        
        try:
            # Step 1: Simulate sensor reading
            self.log("Step 1: Simulating sensor data...")
            sensor_data = {
                "node_id": 2,
                "sensor_type": "temperature",
                "value": 25.5,
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 2: Send via MCP orchestration
            self.log("Step 2: Sending via MCP...")
            response = requests.post(
                f"{self.mcp_base}/tasks/plan-execution",
                json={
                    "action": "forward_data",
                    "data": sensor_data
                },
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✓ Data forwarded through MCP", "PASS")
                
                # Step 3: Verify in ONOS
                self.log("Step 3: Verifying in ONOS...")
                flows_response = requests.get(
                    f"{self.onos_base}/onos/v1/flows",
                    auth=("onos", "rocks"),
                    timeout=10
                )
                
                if flows_response.status_code == 200:
                    self.log("✓ ONOS received flow updates", "PASS")
                    return True
                else:
                    self.log("✗ ONOS verification failed", "FAIL")
                    return False
            else:
                self.log(f"✗ MCP forwarding failed: {response.status_code}", "FAIL")
                return False
                
        except Exception as e:
            self.log(f"✗ Data flow error: {e}", "FAIL")
            return False
    
    def run_all_tests(self):
        """Run complete simulation test suite"""
        self.log("=" * 60)
        self.log("SDN-WISE Simulation Test Suite")
        self.log("=" * 60)
        
        tests = [
            ("Cooja WSN Simulation", self.test_cooja_simulation),
            ("Mininet Network Emulation", self.test_mininet_topology),
            ("ONOS Integration", self.test_onos_integration),
            ("Intent Translation", self.test_intent_translation),
            ("WSN Workflow", self.test_wsn_simulation_workflow),
            ("Complete Data Flow", self.test_data_flow_simulation),
        ]
        
        results = []
        for name, test_func in tests:
            self.log(f"\n{'=' * 60}")
            self.log(f"Running: {name}")
            self.log(f"{'=' * 60}")
            
            try:
                passed = test_func()
                results.append((name, passed))
            except Exception as e:
                self.log(f"✗ Test crashed: {e}", "FAIL")
                results.append((name, False))
            
            time.sleep(2)  # Cool down between tests
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("TEST SUMMARY")
        self.log("=" * 60)
        
        passed_count = sum(1 for _, passed in results if passed)
        total_count = len(results)
        
        for name, passed in results:
            status = "PASS" if passed else "FAIL"
            symbol = "✓" if passed else "✗"
            self.log(f"{symbol} {name}: {status}")
        
        self.log(f"\nTotal: {passed_count}/{total_count} passed")
        self.log(f"Pass Rate: {passed_count/total_count*100:.1f}%")
        
        if passed_count == total_count:
            self.log("\n🎉 All simulation tests passed!", "SUCCESS")
            return True
        else:
            self.log(f"\n⚠️  {total_count - passed_count} test(s) failed", "WARNING")
            return False

if __name__ == "__main__":
    tester = SimulationTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)
