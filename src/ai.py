import requests
import json
import time

class AI:
    def __init__(self):
        self.ask_counter = 0
        self.time_spent = 0
        pass

    def ask(self, model: str = "deepseek-r1:14b", prompt: str = "") -> str:
        url = "http://localhost:11434/api/chat"

        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        start_time = time.time()
        response_text = ""
        with requests.post(url, json=payload, stream=True) as r:
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    # Streamed chunks contain "message" only when tokenized content arrives
                    if "message" in data and "content" in data["message"]:
                        response_text += data["message"]["content"]
                        print(".", end="", flush=True)
        self.ask_counter += 1
        self.time_spent += time.time() - start_time
        return response_text