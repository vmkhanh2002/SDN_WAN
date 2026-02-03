import requests
import time
import socket
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_port(host, port):
    """Check if a TCP port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logging.error(f"Error checking {host}:{port}: {e}")
        return False

def check_http(url, auth=None):
    """Check if an HTTP endpoint returns 200 OK."""
    try:
        response = requests.get(url, auth=auth, timeout=5)
        if response.status_code == 200:
            return True, response.json() if 'json' in response.headers.get('Content-Type', '') else response.text
        return False, f"Status code: {response.status_code}"
    except Exception as e:
        return False, str(e)

def verify_infrastructure():
    logging.info("Starting Infrastructure Verification...")
    
    services = [
        ("ONOS Controller", "localhost", 8181, "http://localhost:8181/onos/v1/applications", ("onos", "rocks")),
        ("MCP Server", "localhost", 8000, "http://localhost:8000/health", None),
        ("Cooja VNC", "localhost", 5900, None, None)
    ]
    
    all_passed = True
    
    for name, host, port, url, auth in services:
        logging.info(f"Checking {name}...")
        
        # 1. Port Check
        if check_port(host, port):
            logging.info(f"  [PASS] Port {port} is open.")
        else:
            logging.error(f"  [FAIL] Port {port} is closed!")
            all_passed = False
            continue
            
        # 2. API Check (if applicable)
        if url:
            success, data = check_http(url, auth)
            if success:
                logging.info(f"  [PASS] API is responsive.")
            else:
                logging.error(f"  [FAIL] API check failed: {data}")
                all_passed = False
    
    if all_passed:
        logging.info("\n✅ ALL INFRASTRUCTURE CHECKS PASSED!")
    else:
        logging.error("\n❌ SOME CHECKS FAILED. See logs above.")

if __name__ == "__main__":
    # Wait a bit for services to settle if running immediately after startup
    verify_infrastructure()
