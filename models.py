# FitSweetTreat LTX-2.3-22B Modal/ComfyUI Pipeline
# Model configuration for video generation workflow

models = [
    # LTX-2.3-22B Model (46 GB)
    {
        "repo_id": "lightricks/ltx",
        "filename": "ltx-2.3-22b-dev.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/checkpoints",
    },
    # Gemma-3 12B Text Encoder (13 GB)
    {
        "repo_id": "google/gemma-3-12b-it",
        "filename": "model.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/text_encoders",
    },
]

models_ext = [
    # Distilled LoRA for inference acceleration (7.6 GB)
    {
        "url": "https://huggingface.co/lightricks/ltx/resolve/main/ltx-2.3-22b-distilled-lora-384.safetensors",
        "filename": "ltx-2.3-22b-distilled-lora-384.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/loras/ltxv/ltx2",
    },
]
