#!/usr/bin/env python3
"""
SDN-WISE Full Stack - Automated Test Suite
Comprehensive testing with HTML visualization reports
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple
import os

class TestResult:
    def __init__(self, name: str, status: str, duration: float, details: str = ""):
        self.name = name
        self.status = status  # PASS, FAIL, SKIP
        self.duration = duration
        self.details = details

class SDNWiseTestSuite:
    def __init__(self, base_url: str = "http://localhost:8000", 
                 onos_url: str = "http://172.25.0.2:8181"):
        self.base_url = base_url
        self.onos_url = onos_url
        self.onos_auth = ("onos", "rocks")
        self.results: List[TestResult] = []
        
    def log(self, message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        
    def test_container_health(self) -> TestResult:
        """Test: All Docker containers running"""
        start = time.time()
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}:{{.Status}}"],
                capture_output=True, text=True, timeout=10
            )
            containers = result.stdout.strip().split('\n')
            
            required = ["onos-sdn", "mininet-sdn", "cooja-simulator", "mcp-ia-agent"]
            running = [c.split(':')[0] for c in containers if c]
            
            missing = [c for c in required if c not in running]
            if missing:
                return TestResult(
                    "Container Health Check",
                    "FAIL",
                    time.time() - start,
                    f"Missing containers: {', '.join(missing)}"
                )
            
            return TestResult(
                "Container Health Check",
                "PASS",
                time.time() - start,
                f"All 4 containers running: {', '.join(required)}"
            )
        except Exception as e:
            return TestResult(
                "Container Health Check",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_mcp_root_endpoint(self) -> TestResult:
        """Test: MCP root endpoint"""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'healthy':
                return TestResult(
                    "MCP Root Endpoint",
                    "PASS",
                    time.time() - start,
                    f"Service: {data.get('service', 'Unknown')}"
                )
            else:
                return TestResult(
                    "MCP Root Endpoint",
                    "FAIL",
                    time.time() - start,
                    f"Status code: {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                "MCP Root Endpoint",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_mcp_health(self) -> TestResult:
        """Test: MCP health check"""
        start = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'healthy':
                return TestResult(
                    "MCP Health Check",
                    "PASS",
                    time.time() - start,
                    f"ONOS: {data.get('onos_url', 'N/A')}, Agents: {data.get('agents_available', False)}"
                )
            else:
                return TestResult(
                    "MCP Health Check",
                    "FAIL",
                    time.time() - start,
                    f"Status: {data.get('status', 'unknown')}"
                )
        except Exception as e:
            return TestResult(
                "MCP Health Check",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_onos_applications(self) -> TestResult:
        """Test: ONOS applications endpoint"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.onos_url}/onos/v1/applications",
                auth=self.onos_auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                app_count = len(data.get('applications', []))
                return TestResult(
                    "ONOS Applications API",
                    "PASS",
                    time.time() - start,
                    f"Connected to ONOS, {app_count} applications loaded"
                )
            else:
                return TestResult(
                    "ONOS Applications API",
                    "FAIL",
                    time.time() - start,
                    f"Status code: {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                "ONOS Applications API",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_onos_devices(self) -> TestResult:
        """Test: ONOS devices endpoint"""
        start = time.time()
        try:
            response = requests.get(
                f"{self.onos_url}/onos/v1/devices",
                auth=self.onos_auth,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                device_count = len(data.get('devices', []))
                return TestResult(
                    "ONOS Devices API",
                    "PASS",
                    time.time() - start,
                    f"Device discovery working, {device_count} devices"
                )
            else:
                return TestResult(
                    "ONOS Devices API",
                    "FAIL",
                    time.time() - start,
                    f"Status code: {response.status_code}"
                )
        except Exception as e:
            return TestResult(
                "ONOS Devices API",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_task_endpoint(self, endpoint: str, action: str) -> TestResult:
        """Test: MCP task endpoint"""
        start = time.time()
        try:
            response = requests.post(
                f"{self.base_url}/tasks/{endpoint}",
                json={"action": action},
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                return TestResult(
                    f"Task: {endpoint}",
                    "PASS",
                    time.time() - start,
                    f"Action '{action}' processed successfully"
                )
            else:
                return TestResult(
                    f"Task: {endpoint}",
                    "FAIL",
                    time.time() - start,
                    f"Status: {response.status_code}, Response: {response.text[:100]}"
                )
        except Exception as e:
            return TestResult(
                f"Task: {endpoint}",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def test_response_time(self) -> TestResult:
        """Test: API response time performance"""
        start = time.time()
        try:
            times = []
            for _ in range(5):
                t0 = time.time()
                requests.get(f"{self.base_url}/health", timeout=5)
                times.append(time.time() - t0)
            
            avg_time = sum(times) * 1000 / len(times)  # Convert to ms
            
            if avg_time < 200:
                return TestResult(
                    "Response Time Performance",
                    "PASS",
                    time.time() - start,
                    f"Average: {avg_time:.2f}ms (threshold: 200ms)"
                )
            else:
                return TestResult(
                    "Response Time Performance",
                    "FAIL",
                    time.time() - start,
                    f"Average: {avg_time:.2f}ms exceeds 200ms threshold"
                )
        except Exception as e:
            return TestResult(
                "Response Time Performance",
                "FAIL",
                time.time() - start,
                str(e)
            )
    
    def generate_html_report(self, filename: str = "test_report.html"):
        """Generate HTML visualization report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>SDN-WISE Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            padding: 40px;
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .timestamp {{
            color: #666;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-card.total {{ background: #f0f0f0; }}
        .stat-card.pass {{ background: #d4edda; color: #155724; }}
        .stat-card.fail {{ background: #f8d7da; color: #721c24; }}
        .stat-card.skip {{ background: #fff3cd; color: #856404; }}
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 14px;
            text-transform: uppercase;
            opacity: 0.8;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #f0f0f0;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 40px;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
            font-weight: 600;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status {{
            padding: 6px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
        }}
        .status.PASS {{
            background: #d4edda;
            color: #155724;
        }}
        .status.FAIL {{
            background: #f8d7da;
            color: #721c24;
        }}
        .status.SKIP {{
            background: #fff3cd;
            color: #856404;
        }}
        .details {{
            color: #666;
            font-size: 13px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>SDN-WISE Full Stack - Test Report</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="summary">
            <div class="stat-card total">
                <div class="stat-label">Total Tests</div>
                <div class="stat-number">{total}</div>
            </div>
            <div class="stat-card pass">
                <div class="stat-label">Passed</div>
                <div class="stat-number">{passed}</div>
            </div>
            <div class="stat-card fail">
                <div class="stat-label">Failed</div>
                <div class="stat-number">{failed}</div>
            </div>
            <div class="stat-card skip">
                <div class="stat-label">Skipped</div>
                <div class="stat-number">{skipped}</div>
            </div>
        </div>
        
        <div class="progress-bar">
            <div class="progress-fill" style="width: {pass_rate}%">
                {pass_rate:.1f}% Pass Rate
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Status</th>
                    <th>Duration</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in self.results:
            html += f"""
                <tr>
                    <td>{result.name}</td>
                    <td><span class="status {result.status}">{result.status}</span></td>
                    <td>{result.duration:.3f}s</td>
                    <td class="details">{result.details}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
        
        <div class="footer">
            SDN-WISE Full Stack - Production Readiness Testing<br>
            Intent-Based Wireless Sensor Network Orchestration
        </div>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html)
        
        self.log(f"HTML report generated: {filename}")
        return os.path.abspath(filename)
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.log("Starting SDN-WISE Test Suite...")
        self.log("=" * 60)
        
        # Infrastructure tests
        self.log("\nInfrastructure Tests:")
        self.results.append(self.test_container_health())
        
        # MCP Server tests
        self.log("\nMCP Server Tests:")
        self.results.append(self.test_mcp_root_endpoint())
        self.results.append(self.test_mcp_health())
        
        # ONOS Controller tests
        self.log("\nONOS Controller Tests:")
        self.results.append(self.test_onos_applications())
        self.results.append(self.test_onos_devices())
        
        # Task endpoint tests
        self.log("\nTask Endpoint Tests:")
        task_endpoints = [
            ("deployment-monitoring", "status"),
            ("network-configuration", "status"),
            ("plan-validation", "validate"),
            ("access-control", "check"),
        ]
        for endpoint, action in task_endpoints:
            self.results.append(self.test_task_endpoint(endpoint, action))
        
        # Performance tests
        self.log("\nPerformance Tests:")
        self.results.append(self.test_response_time())
        
        # Summary
        self.log("\n" + "=" * 60)
        total = len(self.results)
        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        
        self.log(f"Test Summary: {passed}/{total} passed, {failed} failed")
        
        for result in self.results:
            status_symbol = "PASS" if result.status == "PASS" else "FAIL"
            self.log(f"  [{status_symbol}] {result.name} ({result.duration:.3f}s)")
        
        return passed == total

if __name__ == "__main__":
    suite = SDNWiseTestSuite()
    success = suite.run_all_tests()
    
    # Generate HTML report
    report_path = suite.generate_html_report()
    print(f"\nHTML Report: file://{report_path}")
    
    # Exit with appropriate code
    exit(0 if success else 1)
