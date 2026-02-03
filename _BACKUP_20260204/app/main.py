"""
SDN-WISE MCP Server
Main entry point for the FastAPI server
"""
import uvicorn
from servers.app import app

if __name__ == "__main__":
    print("=" * 50)
    print("SDN-WISE MCP Server")
    print("Intent-Based Wireless Sensor Network")
    print("Orchestration with Gemini LLM")
    print("=" * 50)
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
