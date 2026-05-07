import requests
import json
import os

from data import JobListing

def ask(prompt: str, use_large: bool = True) -> str:
    url = "http://localhost:11434/api/chat"
    if use_large:
        model = os.environ.get("AI_AGENT_HEAVY")
    else:
        model = os.environ.get("AI_AGENT_LIGHT")

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response_text = ""
    with requests.post(url, json=payload, stream=True) as r:
        for line in r.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "message" in data and "content" in data["message"]:
                    response_text += data["message"]["content"]
    return response_text

def evaluate_job_listing(job: JobListing, cv: str):
    prompt = f"Given the following concise CV:\n \
            {cv}\n\n \
            And the following job description:\n \
            {job.description}\n\n \
            Would the candidate's skillset and interests align with this company's position?\
            Answer with integer number from 1 to 10."
    primary_evaluation = ask(prompt)
    job.evaluated = True
    ranking = int(primary_evaluation)
    if ranking == None:
        job.evaluated = False
    else:
        job.ranking = ranking
    job.save()
    return 

