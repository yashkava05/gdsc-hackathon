import requests

response = requests.post("http://localhost:11434/api/generate", json={
    "model": "gemma2:2b",
    "prompt": "Hello, are you working?",
    "stream": False
})

print(response.json()["response"])