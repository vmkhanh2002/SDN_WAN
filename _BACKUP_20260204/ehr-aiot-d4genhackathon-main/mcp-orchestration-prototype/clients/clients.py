"""
FastMCP Client using CrewAI + Gemini LLM
"""

import argparse
import json
import os
import requests
from typing import Optional

from crewai import Agent, Task, Crew
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()
# =====================================================
# Configuration
# =====================================================

BASE = os.environ.get("FASTMCP_BASE", "http://127.0.0.1:8000")
FASTMCP_API_KEY = os.environ.get("FASTMCP_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

HEADERS = {}
if FASTMCP_API_KEY:
    HEADERS["X-API-Key"] = FASTMCP_API_KEY

KNOWN_AGENTS = [
    "device-orchestration",
    "deployment-monitoring",
    "network-configuration",
    "plan-validation",
    "plan-execution",
    "access-control",
]

# =====================================================
# LLM (Client-side brain)
# =====================================================

llm = LLM(
    model="gemini/gemini-flash-latest",
    api_key=GEMINI_API_KEY,
    temperature=0.2,
)

# =====================================================
# MCP Communication
# =====================================================

def call_mcp(path: str, payload: dict):
    url = BASE.rstrip("/") + path
    r = requests.post(url, json=payload, headers=HEADERS)
    print(f"POST {url} -> {r.status_code}")
    try:
        return r.json()
    except Exception:
        return r.text


# =====================================================
# CrewAI Agent Wrapper
# =====================================================

def build_agent(name: str):
    return Agent(
        role=name,
        goal=f"Assist with {name.replace('-', ' ')} operations using MCP tools.",
        backstory=f"You are an AI agent responsible for {name}.",
        llm=llm,
        verbose=True,
    )


def run_agent(agent_name: str, user_message: str):
    agent = build_agent(agent_name)

    task = Task(
        description=f"""
        User request:
        {user_message}

        Decide what MCP action is required and produce
        a JSON payload for the MCP endpoint.
        """,
        expected_output="Valid JSON payload for MCP API",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )

    result = crew.kickoff()

    # Extract the agent output text
    if hasattr(result, "tasks") and result.tasks:
        first_task = result.tasks[0]
        if hasattr(first_task, "result"):
            output_text = first_task.result
        else:
            output_text = str(first_task)
    else:
        output_text = str(result)

    # Try parsing JSON from agent output
    try:
        payload = json.loads(output_text)
    except Exception:
        payload = {"message": output_text}
    return payload


# =====================================================
# CLI Operations
# =====================================================

def send_message(agent: str, message: str):
    payload = run_agent(agent, message)
    return call_mcp(f"/tasks/{agent}", payload)


def interactive_chat(agent: str):
    print(f"Chatting with agent: {agent}")
    while True:
        msg = input("you> ").strip()
        if msg.lower() in ("quit", "exit"):
            break
        response = send_message(agent, msg)
        print(json.dumps(response, indent=2))


def interactive_menu():
    agent_descriptions = {
        "device-orchestration": "Convert user intent into orchestration plans",
        "deployment-monitoring": "Track real-time device status and connectivity",
        "plan-validation": "Validate plans against constraints (energy, security, privacy, etc.)",
        "plan-execution": "Execute orchestration plans by translating to device commands (HTTP/MQTT)",
        "network-configuration": "Configure networks from intent & manage OTA updates",
        "access-control": "Enforce role-based access control and permissions",
    }
    
    task_actions = {
        "device-orchestration": [
            "generate_plan - Create plan from intent",
            "execute_intent - End-to-end execution",
            "execute - Run specific plan",
            "list_plans - Get available plans",
            "analyze - Detailed plan analysis",
            "query_devices - Query devices with filters",
        ],
        "deployment-monitoring": [
            "status - Overall deployment health",
            "device_info - Device specifications",
            "query_location - Find devices by location",
            "query_service - Find devices with service",
            "query_status - Find devices by status",
            "query_capability - Find devices by capability",
            "active_devices - List all active devices",
            "connectivity - Network health metrics",
        ],
        "plan-validation": [
            "validate - Check plan constraints",
            "validate_and_optimize - Validation + optimization",
            "recommendations - Get improvement suggestions",
        ],
        "plan-execution": [
            "execute - Execute a plan on devices",
            "execute_and_monitor - Execute with monitoring info",
            "get_history - Retrieve execution history",
            "monitor - Monitor specific execution by ID",
        ],
        "network-configuration": [
            "configure_from_intent - Generate network config",
            "ota_update - Handle firmware updates",
            "ota_status - Monitor OTA status",
        ],
        "access-control": [
            "check - Verify user permissions",
            "grant - Grant device access to role",
            "revoke - Revoke device access from role",
        ],
    }
    
    while True:
        print("\n" + "="*60)
        print("FastMCP + CrewAI Client - Intent-Based IoT Orchestration")
        print("="*60)
        print("\n1) Chat with agent (AI-powered)")
        print("2) Run MCP task directly (JSON payload)")
        print("3) View agent information")
        print("4) View task actions")
        print("5) Quit")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            print("\n" + "-"*60)
            print("Available Agents:")
            for i, agent in enumerate(KNOWN_AGENTS, 1):
                print(f"{i}) {agent.upper()}")
                print(f"   → {agent_descriptions.get(agent, 'N/A')}")
            
            agent = input("\nEnter agent name (or number): ").strip()
            
            # Support numeric selection
            if agent.isdigit():
                idx = int(agent) - 1
                if 0 <= idx < len(KNOWN_AGENTS):
                    agent = KNOWN_AGENTS[idx]
                else:
                    print("Invalid selection")
                    continue
            
            if agent not in KNOWN_AGENTS:
                print("Invalid agent")
                continue
            
            print(f"\n Chatting with {agent.upper()}")
            print("(Type 'quit' or 'exit' to return to main menu)")
            interactive_chat(agent)

        elif choice == "2":
            print("\n" + "-"*60)
            print("Available Tasks:")
            for agent in KNOWN_AGENTS:
                print(f"\n  /tasks/{agent}")
                for action in task_actions.get(agent, []):
                    print(f"    • {action}")

            path = input("\nTask path (e.g., /tasks/device-orchestration): ").strip()
            
            # Validate path format
            if not path.startswith("/tasks/"):
                path = f"/tasks/{path}"
            
            agent_name = path.split("/")[-1]
            if agent_name not in KNOWN_AGENTS:
                print(f"Unknown agent: {agent_name}")
                continue
            
            print(f"\nActions for {agent_name}:")
            for action in task_actions.get(agent_name, []):
                print(f"  • {action}")
            
            payload = input("\nJSON payload (empty for {}): ").strip()
            try:
                payload = json.loads(payload) if payload else {}
            except Exception as e:
                print(f"Invalid JSON: {e}")
                continue

            print(f"\n Sending request to {path}...")
            result = call_mcp(path, payload)
            print("\n Response:")
            print(json.dumps(result, indent=2))

        elif choice == "3":
            print("\n" + "-"*60)
            print("Agent Information")
            print("-"*60)
            for agent in KNOWN_AGENTS:
                print(f"\n {agent.upper()}")
                print(f"   Description: {agent_descriptions.get(agent, 'N/A')}")
                print(f"   Available actions:")
                for action in task_actions.get(agent, []):
                    print(f"     • {action}")

        elif choice == "4":
            print("\n" + "-"*60)
            print("Task Actions by Agent")
            print("-"*60)
            for agent in KNOWN_AGENTS:
                print(f"\n🔧 /tasks/{agent}")
                for action in task_actions.get(agent, []):
                    print(f"  • {action}")

        elif choice == "5":
            print("\n Exiting.")
            break
        
        else:
            print("Invalid option. Please try again.")


# =====================================================
# CLI Entrypoint
# =====================================================

def main():
    parser = argparse.ArgumentParser("FastMCP + CrewAI client")
    parser.add_argument("--interactive", action="store_true")

    args = parser.parse_args()

    if args.interactive:
        interactive_menu()
    else:
        print("Run with --interactive")


if __name__ == "__main__":
    main()
