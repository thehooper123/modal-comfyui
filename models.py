# FitSweetTreat LTX-2.3-22B Modal/ComfyUI Pipeline
# Model configuration for video generation workflow

models = [
    {
        "repo_id": "Lightricks/LTX-Video",
        "filename": "ltx-2.3-22b-dev.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/checkpoints",
    },
    {
        "repo_id": "google/gemma-3-12b-it",
        "filename": "comfy_gemma_3_12B_it.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/text_encoders",
    },
]

models_ext = [
    {
        "url": "https://huggingface.co/Lightricks/LTX-Video/resolve/main/loras/ltxv/ltx2/ltx-2.3-22b-distilled-lora-384.safetensors",
        "filename": "ltx-2.3-22b-distilled-lora-384.safetensors",
        "model_dir": "/root/comfy/ComfyUI/models/loras/ltxv/ltx2",
    },
]
