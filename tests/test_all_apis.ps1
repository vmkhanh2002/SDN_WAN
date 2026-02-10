# SDN-WISE Full Stack - Complete API Testing Script
# Tests all MCP Server and ONOS Controller endpoints

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "SDN-WISE API Testing Suite" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$MCP_BASE = "http://localhost:8000"
$ONOS_BASE = "http://localhost:8181"
$ONOS_AUTH = @{
    Username = 'onos'
    Password = 'rocks'
}

$testResults = @()
$testCount = 0
$passCount = 0

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [string]$Body = $null,
        [hashtable]$Auth = $null,
        [string]$Description
    )
    
    $script:testCount++
    Write-Host "[$script:testCount] Testing: $Name" -ForegroundColor Yellow
    Write-Host "    Purpose: $Description" -ForegroundColor Gray
    Write-Host "    URL: $Method $Url" -ForegroundColor Gray
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = 10
            Headers = @{ 
                "Accept" = "application/json"
            }
        }

        if ($Method -in @("POST", "PUT")) {
            $params.Headers["Content-Type"] = "application/json"
        }
        
        if ($Auth) {
            $secPassword = ConvertTo-SecureString $Auth.Password -AsPlainText -Force
            $credential = New-Object System.Management.Automation.PSCredential($Auth.Username, $secPassword)
            $params.Credential = $credential
        }
        
        if ($Body) {
            $params.Body = $Body
        }
        
        $response = Invoke-RestMethod @params
        
        Write-Host "    [PASS] Status: 200 OK" -ForegroundColor Green
        Write-Host "    Response: $($response | ConvertTo-Json -Compress -Depth 2)" -ForegroundColor Gray
        Write-Host ""
        
        $script:passCount++
        $script:testResults += @{
            Name = $Name
            Status = "PASS"
            Response = $response
        }
        
        return $response
    }
    catch {
        Write-Host "    [FAIL] Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
             # Try to read error details from response stream
             $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
             $errBody = $reader.ReadToEnd()
             Write-Host "    Server Response: $errBody" -ForegroundColor Red
        }
        Write-Host ""
        
        $script:testResults += @{
            Name = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
        }
        
        return $null
    }
}

Write-Host "=== MCP SERVER APIs (Total: 10 endpoints) ===" -ForegroundColor Magenta
Write-Host ""

# 1. Root endpoint
Test-Endpoint `
    -Name "MCP Root" `
    -Url "$MCP_BASE/" `
    -Description "Get service information and available endpoints"

# 2. Health check
Test-Endpoint `
    -Name "MCP Health Check" `
    -Url "$MCP_BASE/health" `
    -Description "Verify MCP server is running and check ONOS connectivity"

# 3. API Documentation
Write-Host "[3] API Documentation" -ForegroundColor Yellow
Write-Host "    Purpose: Interactive Swagger UI for all endpoints" -ForegroundColor Gray
Write-Host "    URL: GET $MCP_BASE/docs" -ForegroundColor Gray
Write-Host "    [INFO] Open in browser to view" -ForegroundColor Cyan
Write-Host ""

# 4. Device Orchestration
Test-Endpoint `
    -Name "Device Orchestration" `
    -Url "$MCP_BASE/tasks/device-orchestration" `
    -Method "POST" `
    -Body '{"action":"list_plans"}' `
    -Description "Translate user intent into device execution plans"

# 5. Deployment Monitoring
Test-Endpoint `
    -Name "Deployment Monitoring" `
    -Url "$MCP_BASE/tasks/deployment-monitoring" `
    -Method "POST" `
    -Body '{"action":"status"}' `
    -Description "Monitor device status, IP addresses, location, and connectivity"

# 6. Network Configuration
Test-Endpoint `
    -Name "Network Configuration" `
    -Url "$MCP_BASE/tasks/network-configuration" `
    -Method "POST" `
    -Body '{"action":"ota_status"}' `
    -Description "Configure network settings and manage OTA firmware updates"

# 7. Plan Validation
Test-Endpoint `
    -Name "Plan Validation" `
    -Url "$MCP_BASE/tasks/plan-validation" `
    -Method "POST" `
    -Body '{"action":"validate","plan":{"plan_id":"test-plan","devices":[]},"user_context":{"user_id":"test-user"}}' `
    -Description "Validate plans against security, energy, and location constraints"

# 8. Plan Execution
Test-Endpoint `
    -Name "Plan Execution" `
    -Url "$MCP_BASE/tasks/plan-execution" `
    -Method "POST" `
    -Body '{"action":"get_history"}' `
    -Description "Execute orchestration plans by translating to device commands"

# 9. Flow Execution (New)
Test-Endpoint `
    -Name "Flow Execution" `
    -Url "$MCP_BASE/tasks/flow-execution" `
    -Method "POST" `
    -Body '{"action":"get_history"}' `
    -Description "Manage SDN flow rules via ONOS"

# 10. Access Control
Test-Endpoint `
    -Name "Access Control" `
    -Url "$MCP_BASE/tasks/access-control" `
    -Method "POST" `
    -Body '{"op":"grant","role":"admin","permission":"read"}' `
    -Description "Manage user permissions, roles, and credentials"

# 10. Algorithm Execution
Test-Endpoint `
    -Name "Algorithm Execution" `
    -Url "$MCP_BASE/tasks/algorithm-execution" `
    -Method "POST" `
    -Body '{"action":"options"}' `
    -Description "Execute custom algorithms and data processing tasks"

Write-Host ""
Write-Host "=== ONOS CONTROLLER APIs (Total: 6 endpoints) ===" -ForegroundColor Magenta
Write-Host ""

# 11. ONOS Applications
Test-Endpoint `
    -Name "ONOS Applications" `
    -Url "$ONOS_BASE/onos/v1/applications" `
    -Auth $ONOS_AUTH `
    -Description "List all installed ONOS applications"

# 12. ONOS Devices
Test-Endpoint `
    -Name "ONOS Devices" `
    -Url "$ONOS_BASE/onos/v1/devices" `
    -Auth $ONOS_AUTH `
    -Description "List all discovered network devices"

# 13. ONOS Flows
Test-Endpoint `
    -Name "ONOS Flow Rules" `
    -Url "$ONOS_BASE/onos/v1/flows" `
    -Auth $ONOS_AUTH `
    -Description "List all installed flow rules across devices"

# 14. ONOS Topology
Test-Endpoint `
    -Name "ONOS Topology" `
    -Url "$ONOS_BASE/onos/v1/topology" `
    -Auth $ONOS_AUTH `
    -Description "Get network topology graph (devices, links, hosts)"

# 15. ONOS Hosts
Test-Endpoint `
    -Name "ONOS Hosts" `
    -Url "$ONOS_BASE/onos/v1/hosts" `
    -Auth $ONOS_AUTH `
    -Description "List all discovered end hosts in the network"

# 16. ONOS Links
Test-Endpoint `
    -Name "ONOS Links" `
    -Url "$ONOS_BASE/onos/v1/links" `
    -Auth $ONOS_AUTH `
    -Description "List all discovered links between devices"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "TEST SUMMARY" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total APIs Tested: $testCount" -ForegroundColor White
Write-Host "Total APIs Available: 16 (9 MCP + 6 ONOS + 1 Docs)" -ForegroundColor White
Write-Host "Passed: $passCount" -ForegroundColor Green
Write-Host "Failed: $($testCount - $passCount)" -ForegroundColor Red
Write-Host "Pass Rate: $([math]::Round($passCount / $testCount * 100, 2))%" -ForegroundColor $(if ($passCount -eq $testCount) { "Green" } else { "Yellow" })
Write-Host ""

# Generate detailed report
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "DETAILED API CATALOG" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "MCP SERVER APIs (Application Layer)" -ForegroundColor Magenta
Write-Host "Base URL: $MCP_BASE" -ForegroundColor Gray
Write-Host ""

$mcpApis = @(
    @{Endpoint="/"; Method="GET"; Purpose="Service information"},
    @{Endpoint="/health"; Method="GET"; Purpose="Health check and system status"},
    @{Endpoint="/docs"; Method="GET"; Purpose="Interactive API documentation (Swagger UI)"},
    @{Endpoint="/tasks/device-orchestration"; Method="POST"; Purpose="Intent → Execution plan translation"},
    @{Endpoint="/tasks/deployment-monitoring"; Method="POST"; Purpose="Device status monitoring"},
    @{Endpoint="/tasks/network-configuration"; Method="POST"; Purpose="Network config & OTA updates"},
    @{Endpoint="/tasks/plan-validation"; Method="POST"; Purpose="Constraint validation"},
    @{Endpoint="/tasks/plan-execution"; Method="POST"; Purpose="Execute orchestration plans"},
    @{Endpoint="/tasks/access-control"; Method="POST"; Purpose="Permission management"},
    @{Endpoint="/tasks/algorithm-execution"; Method="POST"; Purpose="Custom algorithm execution"}
)

$mcpApis | Format-Table -Property @{Label="Endpoint"; Expression={$_.Endpoint}; Width=40}, 
                                  @{Label="Method"; Expression={$_.Method}; Width=8},
                                  @{Label="Purpose"; Expression={$_.Purpose}; Width=50} -Wrap

Write-Host ""
Write-Host "ONOS CONTROLLER APIs (Control Plane)" -ForegroundColor Magenta
Write-Host "Base URL: $ONOS_BASE" -ForegroundColor Gray
Write-Host "Authentication: Basic (onos/rocks)" -ForegroundColor Gray
Write-Host ""

$onosApis = @(
    @{Endpoint="/onos/v1/applications"; Method="GET"; Purpose="List ONOS apps"},
    @{Endpoint="/onos/v1/devices"; Method="GET"; Purpose="Discover network devices"},
    @{Endpoint="/onos/v1/flows"; Method="GET/POST"; Purpose="Manage flow rules"},
    @{Endpoint="/onos/v1/topology"; Method="GET"; Purpose="Network topology graph"},
    @{Endpoint="/onos/v1/hosts"; Method="GET"; Purpose="List end hosts"},
    @{Endpoint="/onos/v1/links"; Method="GET"; Purpose="List device links"}
)

$onosApis | Format-Table -Property @{Label="Endpoint"; Expression={$_.Endpoint}; Width=35}, 
                                   @{Label="Method"; Expression={$_.Method}; Width=12},
                                   @{Label="Purpose"; Expression={$_.Purpose}; Width=40} -Wrap

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "API USAGE EXAMPLES" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Example 1: Check system health" -ForegroundColor Yellow
Write-Host '  curl http://localhost:8000/health' -ForegroundColor Gray
Write-Host ""

Write-Host "Example 2: Monitor deployment" -ForegroundColor Yellow
Write-Host '  $body = ''{"action":"status"}''' -ForegroundColor Gray
Write-Host '  Invoke-RestMethod -Uri "http://localhost:8000/tasks/deployment-monitoring" -Method POST -Body $body -ContentType "application/json"' -ForegroundColor Gray
Write-Host ""

Write-Host "Example 3: Get ONOS devices" -ForegroundColor Yellow
Write-Host '  curl -u onos:rocks http://172.25.0.2:8181/onos/v1/devices' -ForegroundColor Gray
Write-Host ""

Write-Host "Example 4: Install flow rule via ONOS" -ForegroundColor Yellow
Write-Host '  curl -u onos:rocks -X POST http://172.25.0.2:8181/onos/v1/flows -H "Content-Type: application/json" -d ''{"flows":[...]}''' -ForegroundColor Gray
Write-Host ""

Write-Host "Testing complete! Check test_report.html for detailed results." -ForegroundColor Green
