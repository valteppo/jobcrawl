import requests
import json
import time
import os

class AI:
    def __init__(self):
        self.ask_counter = 0
        self.time_spent = 0
        self.cv = self._load_cv()
        self.ai_instructions = self._load_ai_instructions()

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
    
    def _load_cv(self):
        # load cv from applicant folder
        applicant_folder = "applicant"
        for filename in os.listdir(applicant_folder):
            if filename.endswith("cv.txt"):
                with open(os.path.join(applicant_folder, filename), "r", encoding="utf-8") as f:
                    self.cv = f.read()

    def _load_ai_instructions(self):
        # load ai instructions from applicant folder
        applicant_folder = "applicant"
        instructions = ""
        for filename in os.listdir(applicant_folder):
            if filename.endswith("ai_instructions.txt"):
                with open(os.path.join(applicant_folder, filename), "r", encoding="utf-8") as f:
                    instructions = f.read()
        return instructions
    
    def compress_description(self, job) -> dict:
        temp_job = job.copy()
        print(f"Compressing description: {job["id"]}")
        prompt = f"Given the following job description, shorten it to 200 words. \
                List all the technologies mentioned. Use plaintext formatting. \
                Answer in english. \
                Description begins: {job["description"]}"
        result = self.ask(model="deepseek-r1:1.5b", prompt=prompt)
        temp_job["compressed"] = result
        return temp_job
    
    def evaluate_job_listing(self, job) -> dict:
        temp_job = job.copy()
        print(f"Evaluating job listing: {job['url']}")
        prompt = f"Given the following CV:\n \
                {self.cv}\n\n \
                And the following job description:\n \
                {job['description']}\n\n \
                Is this job suitable for the CV? \
                Answer with one word: 'yes' or 'no'."
        primary_evaluation = self.ask(model="deepseek-r1:1.5b", prompt=prompt)
        print(primary_evaluation)
        # Set the "evaluated" field to True
        temp_job["evaluated"] = True
        if "yes" in primary_evaluation.lower():
            temp_job["suitable"] = True
        else:
            temp_job["suitable"] = False
        return temp_job
    
    def make_application_letter(self, job) -> None:
        print(f"Forming the application letter: {job["company"]}\t{job["id"]}")
        prompt = f"Given the following CV:\n \
                {self.cv}\n\n \
                And the following job description:\n \
                {job['description']}\n\n \
                Follow these instructions: \
                {self.ai_instructions}"
        result = self.ask(prompt=prompt)
        print("Done.")
        return result
    
    def save_application_letter(self, letter: str, listing_information: dict) -> None:
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, "output")
        output_dir = os.path.join(output_dir, "letters")
        os.makedirs(output_dir, exist_ok=True)
        company_dir = os.path.join(output_dir, listing_information["company"])
        os.makedirs(company_dir, exist_ok=True)
        listing_file_path = os.path.join(company_dir, f"{listing_information['id']}_motivation_letter.md")
        with open(listing_file_path, "w", encoding="utf-8") as f:
            f.write(letter)