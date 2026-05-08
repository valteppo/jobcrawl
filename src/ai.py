import requests
import os
import re

from data import JobListing

def ask(prompt: str, use_large: bool = True) -> str:
    url = "http://localhost:11434/api/chat"
    model = os.environ.get("AI_AGENT_HEAVY") if use_large else os.environ.get("AI_AGENT_LIGHT")
    
    if not model:
        return "DEBUG ERROR: Model name is missing. Check your environment variables."

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False 
    }

    try:
        r = requests.post(url, json=payload, timeout=300)
        if r.status_code != 200:
            return f"Ollama Error {r.status_code}: {r.text}"
        
        data = r.json()
        return data["message"]["content"]
    except Exception as e:
        return f"Connection Failed: {e}"

def extract_ranking(text: str) -> int | None:
    match = re.search(r'\d+', text)
    if match:
        val = int(match.group())
        return max(1, min(10, val))
    return None

def evaluate_job_listing(job: JobListing, cv: str):
    prompt = (
        "TASK: Rate the alignment between the CV and Job Description.\n"
        "FORMAT: Respond ONLY with a single integer between 1 and 10.\n"
        f"CV: {cv}\n"
        f"JOB: {job.description}"
        "Output strictly numeric. No prose. No explanation."
    )
    ai_response = ask(prompt, use_large=False)
    ranking = extract_ranking(ai_response)
    if ranking is not None:
        job.ranking = ranking
        job.evaluated = True
        job.save()
    return job

def make_application_letter(job: JobListing, cv: str):
    prompt = (
        "TASK: Write out an application letter for this job. Reason why the candidate is a good fit. Stay professional and use short concise sentences.\n"
        "FORMAT: Provide a Markdown file.\n"
        f"CV: {cv}\n"
        f"JOB: {job.description}"
    )
    job.application = ask(prompt)
    job.save()
