<#
.SYNOPSIS
    Monitors and fixes ONOS OpenFlow port 6653 connectivity issues.
.DESCRIPTION
    Checks if ONOS container is listening on port 6653. 
    If not, it automatically restarts the container until the port is open.
    This resolves the "Mininet switches cannot connect" issue.
#>

$ContainerName = "onos-sdn"
$MaxRetries = 5
$RetryCount = 0

function Check-Port {
    Write-Host "Checking OpenFlow port 6653..." -NoNewline
    $result = docker exec $ContainerName netstat -tuln 2>$null | Select-String ":6653"
    
    if ($result) {
        Write-Host " [OK] (Port Open)" -ForegroundColor Green
        return $true
    } else {
        Write-Host " [FAIL] (Port Closed)" -ForegroundColor Red
        return $false
    }
}

Write-Host "=== ONOS OpenFlow Port Fixer ===" -ForegroundColor Cyan

# Check if container is running
$status = docker inspect -f '{{.State.Running}}' $ContainerName 2>$null
if ($status -ne "true") {
    Write-Host "Container '$ContainerName' is not running. Starting it..." -ForegroundColor Yellow
    docker-compose up -d $ContainerName
    Start-Sleep -Seconds 10
}

while ($RetryCount -lt $MaxRetries) {
    if (Check-Port) {
        Write-Host "`nSUCCESS: ONOS is ready for Mininet connections!" -ForegroundColor Green
        exit 0
    }

    $RetryCount++
    Write-Host "Attempt $RetryCount/$MaxRetries: Restarting ONOS container..." -ForegroundColor Yellow
    docker restart $ContainerName
    
    Write-Host "Waiting 30 seconds for startup..." -ForegroundColor Gray
    Start-Sleep -Seconds 30
}

Write-Host "`nERROR: Failed to open port 6653 after $MaxRetries attempts." -ForegroundColor Red
Write-Host "Please check container logs: docker logs $ContainerName" -ForegroundColor Red
exit 1
