from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
from datetime import datetime
import threading
import os

DATA_DIR = Path(__file__).parent / ".." / "data"
DATA_DIR = DATA_DIR.resolve()
DEVICES_FILE = DATA_DIR / "devices.json"
ACCESS_FILE = DATA_DIR / "access.json"

app = FastAPI(title="SDN-WISE MCP Server - Intent-Based WSN Orchestration")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _initialize_agents_on_startup():
	# Initialize CrewAI agents (stubs if crewai isn't installed)
	try:
		from .agents import initialize_agents
		initialize_agents()
	except Exception as e:
		# Non-fatal; initialization failure should not block server start
		print(f"⚠️  Failed to initialize agents: {e}")
		print("📦 Continuing with stub agents")

# Root endpoint for health
@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "SDN-WISE MCP Server",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "tasks": "/tasks/*"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "onos_url": os.getenv("ONOS_URL", "http://172.25.0.2:8181"),
        "data_dir": str(DATA_DIR),
        "agents_available": True
    }

# Task routers from ehr-aiot
from .tasks.device_orchestration import device_router
from .tasks.deployment_monitoring import deployment_router
from .tasks.network_configuration import network_config_router
from .tasks.plan_validation import validation_router
from .tasks.plan_execution import execution_router
from .tasks.access_control import access_router
from .tasks.algorithm_execution import algorithm_router

app.include_router(device_router, prefix="/tasks")
app.include_router(deployment_router, prefix="/tasks")
app.include_router(network_config_router, prefix="/tasks")
app.include_router(validation_router, prefix="/tasks")
app.include_router(execution_router, prefix="/tasks")
app.include_router(access_router, prefix="/tasks")
app.include_router(algorithm_router, prefix="/tasks")

# Explicitly import and include flow_execution router with a unique alias to avoid conflict
from .tasks.flow_execution import execution_router as flow_router
app.include_router(flow_router, prefix="/tasks")

from .utils import read_json, write_json
