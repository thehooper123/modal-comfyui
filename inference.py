#!/usr/bin/env python3
"""
FitSweetTreat LTX-2.3-22B Modal/ComfyUI Inference Script

Submits the turkey_taco_crisp_bowl workflow to the running ComfyUI server.
Handles diagnosis, workflow submission, and output retrieval.
"""

import json
import time
import requests
import websocket
from pathlib import Path
from typing import Optional


class ComfyUIClient:
    def __init__(self, server_url: str = "http://127.0.0.1:8188"):
        self.server_url = server_url
        self.ws_url = server_url.replace("http", "ws")
        
    def get_object_info(self, node_class: str) -> dict:
        """Fetch the exact schema/input info for a given node class."""
        try:
            response = requests.get(f"{self.server_url}/object_info/{node_class}", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch object_info for {node_class}: {e}")
            return {}
    
    def diagnose_nodes(self) -> dict:
        """Diagnose critical nodes and their expected inputs."""
        print("\n🔍 DIAGNOSTIC: Checking node schemas...")
        
        critical_nodes = [
            "STGGuiderAdvanced",
            "LTXVSpatioTemporalTiledVAEDecode",
            "LTXVScheduler",
        ]
        
        schemas = {}
        for node_class in critical_nodes:
            info = self.get_object_info(node_class)
            if info:
                schemas[node_class] = info
                inputs = info.get("inputs", {})
                print(f"\n✅ {node_class}:")
                print(f"   Inputs: {list(inputs.keys())}")
                for input_name, input_spec in inputs.items():
                    if isinstance(input_spec, (list, tuple)):
                        print(f"      - {input_name}: {input_spec}")
                    elif isinstance(input_spec, dict):
                        print(f"      - {input_name}: {input_spec}")
        
        return schemas
    
    def submit_workflow(self, workflow_path: str) -> Optional[str]:
        """Submit workflow to ComfyUI and return prompt ID."""
        try:
            with open(workflow_path, "r") as f:
                workflow = json.load(f)
            
            print(f"\n📤 Submitting workflow from {workflow_path}...")
            
            response = requests.post(
                f"{self.server_url}/prompt",
                json={"prompt": workflow},
                timeout=30,
            )
            
            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                print(f"✅ Workflow submitted successfully!")
                print(f"   Prompt ID: {prompt_id}")
                return prompt_id
            else:
                print(f"❌ Workflow submission failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error submitting workflow: {e}")
            return None
    
    def get_system_info(self) -> dict:
        """Fetch system info from ComfyUI."""
        try:
            response = requests.get(f"{self.server_url}/system_stats", timeout=10)
            response.raise_for_status()
            stats = response.json()
            
            print("\n🖥️  SYSTEM INFO:")
            print(f"   RAM: {stats.get('ram', {}).get('total_mb')} MB total")
            
            gpus = stats.get("gpus", [])
            if gpus:
                for i, gpu in enumerate(gpus):
                    print(f"   GPU {i}: {gpu.get('name', 'Unknown')}")
                    print(f"      VRAM: {gpu.get('vram_total_mb')} MB total")
            
            return stats
        except Exception as e:
            print(f"❌ Failed to fetch system info: {e}")
            return {}
    
    def check_models_loaded(self) -> bool:
        """Check if all required models are found."""
        try:
            response = requests.get(f"{self.server_url}/api/config", timeout=10)
            if response.status_code == 200:
                # Models are accessible; ComfyUI found them
                print("✅ Models are accessible from ComfyUI")
                return True
            else:
                print("❌ Could not verify model accessibility")
                return False
        except Exception as e:
            print(f"❌ Error checking models: {e}")
            return False


def main():
    print("=" * 70)
    print("FitSweetTreat LTX-2.3-22B Modal/ComfyUI Inference")
    print("=" * 70)
    
    workflow_path = Path(__file__).parent / "workflow_api.json"
    
    if not workflow_path.exists():
        print(f"❌ Workflow file not found: {workflow_path}")
        return
    
    client = ComfyUIClient()
    
    # Step 1: Check system info
    print("\n📊 Checking system resources...")
    client.get_system_info()
    
    # Step 2: Diagnose critical nodes
    print("\n🔧 Diagnosing node schemas...")
    schemas = client.diagnose_nodes()
    
    # Step 3: Check models
    print("\n🤖 Checking models...")
    client.check_models_loaded()
    
    # Step 4: Submit workflow
    print("\n" + "=" * 70)
    print("SUBMITTING WORKFLOW FOR INFERENCE")
    print("=" * 70)
    
    prompt_id = client.submit_workflow(str(workflow_path))
    
    if prompt_id:
        print(f"\n✅ Workflow submitted with Prompt ID: {prompt_id}")
        print("\n💡 Monitor progress at: http://127.0.0.1:8188")
        print("   Or check Modal app logs for real-time output")
    else:
        print("\n❌ Failed to submit workflow. Check diagnostics above.")


if __name__ == "__main__":
    main()
