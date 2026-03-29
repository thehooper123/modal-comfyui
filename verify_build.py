#!/usr/bin/env python3
"""
DEPLOYMENT CHECKLIST — FitSweetTreat LTX-2.3-22B Modal/ComfyUI Pipeline

Use this script to verify all components are correctly configured before deployment.
"""

import json
import sys
from pathlib import Path


def check_files():
    """Verify all required files exist and are properly formatted."""
    checks = {}
    
    files_to_check = {
        "models.py": "Model configuration",
        "plugins.py": "Custom node plugins",
        "workflow_api.json": "Video generation workflow",
        "comfyui.py": "Modal app definition",
        "inference.py": "Testing & diagnostics",
        "FitSweetTreat_Build.md": "Documentation",
    }
    
    root = Path(__file__).parent
    
    for filename, description in files_to_check.items():
        filepath = root / filename
        checks[filename] = filepath.exists()
        status = "✅" if checks[filename] else "❌"
        print(f"{status} {description:40s} {filename}")
    
    return all(checks.values())


def check_workflow():
    """Validate workflow_api.json structure and critical fixes."""
    print("\n" + "=" * 70)
    print("WORKFLOW VALIDATION")
    print("=" * 70)
    
    filepath = Path(__file__).parent / "workflow_api.json"
    
    try:
        with open(filepath) as f:
            workflow = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse workflow_api.json: {e}")
        return False
    
    # Check Node 9 (STGGuiderAdvanced) fix
    node_9 = workflow.get("9", {})
    if node_9.get("class_type") == "STGGuiderAdvanced":
        sigmas = node_9.get("inputs", {}).get("sigmas")
        if isinstance(sigmas, str):
            print(f"✅ Node 9 (STGGuiderAdvanced): sigmas is STRING")
            print(f"   Value: '{sigmas[:50]}...'")
        else:
            print(f"❌ Node 9 (STGGuiderAdvanced): sigmas is {type(sigmas)} (should be STRING)")
            return False
    else:
        print(f"⚠️  Node 9 not found or wrong type")
    
    # Check Node 14 (LTXVSpatioTemporalTiledVAEDecode) fixes
    node_14 = workflow.get("14", {})
    if node_14.get("class_type") == "LTXVSpatioTemporalTiledVAEDecode":
        inputs = node_14.get("inputs", {})
        
        device = inputs.get("working_device")
        dtype = inputs.get("working_dtype")
        
        device_ok = device == "auto"
        dtype_ok = dtype == "auto"
        
        device_status = "✅" if device_ok else "❌"
        dtype_status = "✅" if dtype_ok else "❌"
        
        print(f"{device_status} Node 14 (LTXVSpatioTemporalTiledVAEDecode):")
        print(f"   working_device: '{device}' {'(correct)' if device_ok else '(WRONG!)'}")
        print(f"   working_dtype: '{dtype}' {'(correct)' if dtype_ok else '(WRONG!)'}")
        
        return device_ok and dtype_ok
    else:
        print(f"⚠️  Node 14 not found or wrong type")
        return False


def check_config_files():
    """Check models and plugins configuration."""
    print("\n" + "=" * 70)
    print("CONFIGURATION FILES")
    print("=" * 70)
    
    root = Path(__file__).parent
    
    # Check models.py
    try:
        import sys
        sys.path.insert(0, str(root))
        from models import models, models_ext
        
        print(f"✅ models.py loaded")
        print(f"   Models: {len(models)} configured")
        for model in models:
            print(f"      - {model['filename']}")
        
        print(f"   External models: {len(models_ext)} configured")
        for model in models_ext:
            print(f"      - {model['filename']}")
    except Exception as e:
        print(f"❌ Failed to load models.py: {e}")
        return False
    
    # Check plugins.py
    try:
        from plugins import comfy_plugins
        print(f"✅ plugins.py loaded")
        print(f"   Plugins: {len(comfy_plugins)} configured")
        for plugin in comfy_plugins:
            print(f"      - {plugin}")
    except Exception as e:
        print(f"❌ Failed to load plugins.py: {e}")
        return False
    
    return True


def main():
    print("=" * 70)
    print("FitSweetTreat Build Checklist")
    print("=" * 70)
    print()
    
    # Check 1: Files
    print("FILES PRESENT")
    print("=" * 70)
    files_ok = check_files()
    
    # Check 2: Configuration
    config_ok = check_config_files()
    
    # Check 3: Workflow
    workflow_ok = check_workflow()
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    all_ok = files_ok and config_ok and workflow_ok
    
    if all_ok:
        print("✅ All checks passed! Ready for deployment.")
        print("\nNext steps:")
        print("1. Run: modal setup")
        print("2. Run: modal deploy comfyui.py")
        print("3. Wait for model downloads (~20-30 minutes)")
        print("4. Run: python inference.py")
        return 0
    else:
        print("❌ Some checks failed. Review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
