from fastapi import FastAPI, HTTPException
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

app = FastAPI(title="FastMCP Prototype Server")


@app.on_event("startup")
def _initialize_agents_on_startup():
	# Initialize CrewAI agents (stubs if crewai isn't installed)
	try:
		from .agents import initialize_agents

		initialize_agents()
	except Exception:
		# Non-fatal; initialization failure should not block server start
		print("Failed to initialize agents; continuing without them")

# Task routers
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

from .utils import read_json, write_json
