"""GGUF Model Downloader for VN-CPU

Fetches a tiny quantized model for the neural core.
"""
import os
import requests

MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
SAVE_PATH = "/app/vn-cpu/qwen2.5-0.5b-instruct-q4_k_m.gguf"

def download():
    if os.path.exists(SAVE_PATH):
        print(f"Model already exists: {SAVE_PATH}")
        return

    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    response.raise_for_status()
    
    with open(SAVE_PATH, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Download complete: {SAVE_PATH}")

if __name__ == "__main__":
    download()
