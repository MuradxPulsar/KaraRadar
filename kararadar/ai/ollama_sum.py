"""Optional local Ollama summary (OFF by default)."""
import json
import requests

def summarize(results):
    try:
        prompt = "Summarize these suspicious domains briefly:\n" + json.dumps(results, default=str)[:4000]
        r = requests.post("http://localhost:11434/api/generate",
                          json={"model": "llama3", "prompt": prompt, "stream": False},
                          timeout=30)
        r.raise_for_status()
        return r.json().get("response", "(no response)")
    except Exception as e:
        return f"(Ollama unavailable: {e})"