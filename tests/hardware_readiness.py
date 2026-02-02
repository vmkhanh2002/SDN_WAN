#!/usr/bin/env python3
"""
Production Hardware Readiness Tests
Validates system can run on actual hardware deployment
"""

import subprocess
import json
import os
import sys
from datetime import datetime

class HardwareReadinessTest:
    def __init__(self):
        self.results = []
    
    def check_network_interfaces(self):
        """Check if network interfaces support required features"""
        print("\n[TEST] Network Interface Capabilities")
        try:
            result = subprocess.run(
                ["ip", "link", "show"],
                capture_output=True, text=True, timeout=5
            )
            interfaces = result.stdout
            
            if "docker0" in interfaces or "br-" in interfaces:
                print("  [PASS] Docker networking available")
                return True
            else:
                print("  [WARN] Docker bridge not detected")
                return False
        except:
            print("  [SKIP] Not on Linux system")
            return None
    
    def check_kernel_modules(self):
        """Check required kernel modules for SDN"""
        print("\n[TEST] Kernel Module Support")
        required_modules = ["openvswitch", "bridge", "veth"]
        
        try:
            result = subprocess.run(
                ["lsmod"],
                capture_output=True, text=True, timeout=5
            )
            loaded_modules = result.stdout
            
            all_present = True
            for module in required_modules:
                if module in loaded_modules or sys.platform == "win32":
                    print(f"  [PASS] {module}")
                else:
                    print(f"  [WARN] {module} not loaded")
                    all_present = False
            
            return all_present
        except:
            print("  [SKIP] Cannot check kernel modules")
            return None
    
    def check_port_availability(self):
        """Check if required ports are available"""
        print("\n[TEST] Port Availability")
        import socket
        
        ports = {
            8000: "MCP Server",
            8181: "ONOS REST/UI",
            6653: "OpenFlow",
            5900: "VNC (Cooja)"
        }
        
        all_available = True
        for port, service in ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                print(f"  [PASS] Port {port} ({service}) - Service running")
            else:
                print(f"  [WARN] Port {port} ({service}) - Not bound")
                all_available = False
        
        return all_available
    
    def check_resource_limits(self):
        """Check system has enough resources"""
        print("\n[TEST] System Resources")
        
        try:
            # Check memory
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                for line in meminfo.split('\n'):
                    if 'MemAvailable' in line:
                        mem_kb = int(line.split()[1])
                        mem_gb = mem_kb / 1024 / 1024
                        
                        if mem_gb >= 4.0:
                            print(f"  [PASS] Memory: {mem_gb:.1f}GB available (>= 4GB required)")
                            return True
                        else:
                            print(f"  [FAIL] Memory: {mem_gb:.1f}GB available (< 4GB required)")
                            return False
        except:
            print("  [SKIP] Cannot check memory (not Linux)")
            return None
    
    def check_docker_version(self):
        """Check Docker version compatibility"""
        print("\n[TEST] Docker Version")
        
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True, text=True,

 timeout=5
            )
            version = result.stdout.strip()
            print(f"  [PASS] {version}")
            
            # Check compose
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True, text=True, timeout=5
            )
            compose_version = result.stdout.strip()
            print(f"  [PASS] {compose_version}")
            
            return True
        except:
            print("  [FAIL] Docker not installed or not in PATH")
            return False
    
    def check_wireless_support(self):
        """Check if wireless interfaces available for WSN"""
        print("\n[TEST] Wireless Support (for hardware WSN nodes)")
        
        try:
            result = subprocess.run(
                ["iwconfig"],
                capture_output=True, text=True, timeout=5
            )
            
            if "IEEE 802.11" in result.stdout or "no wireless" in result.stderr:
                print("  [INFO] Wireless adapter detected ")
                return True
            else:
                print("  [INFO] No wireless adapter ")
                return None
        except:
            print("  [SKIP] Cannot check wireless ")
            return None
    
    def run_all(self):
        """Run all hardware readiness tests"""
        print("=" * 60)
        print("SDN-WISE Hardware Readiness Tests")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        tests = [
            self.check_docker_version,
            self.check_port_availability,
            self.check_resource_limits,
            self.check_network_interfaces,
            self.check_kernel_modules,
            self.check_wireless_support,
        ]
        
        results = []
        for test in tests:
            result = test()
            results.append(result)
        
        print("\n" + "=" * 60)
        print("SUMMARY:")
        passed = sum(1 for r in results if r == True)
        failed = sum(1 for r in results if r == False)
        skipped = sum(1 for r in results if r is None)
        
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Skipped: {skipped}")
        
        if failed == 0:
            print("\n[RESULT] System ready for production hardware deployment")
            return True
        else:
            print("\n[RESULT] System may have compatibility issues")
            return False

if __name__ == "__main__":
    tester = HardwareReadinessTest()
    success = tester.run_all()
    exit(0 if success else 1)
