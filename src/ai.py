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

    def ask(self, model: str = "gemma2:9b", prompt: str = "") -> str:
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
                    cv = f.read()
        return cv

    def _load_ai_instructions(self):
        # load ai instructions from applicant folder
        applicant_folder = "applicant"
        instructions = ""
        for filename in os.listdir(applicant_folder):
            if filename.endswith("ai_instructions.txt"):
                with open(os.path.join(applicant_folder, filename), "r", encoding="utf-8") as f:
                    instructions = f.read()
        return instructions
    
    def __find_first_int_len1_or2(self, s):
        for i in range(len(s)):
            # Check 2-digit window first
            if i + 2 <= len(s) and s[i:i+2].isdigit():
                return int(s[i:i+2])
            # Check 1-digit window
            if s[i].isdigit():
                return int(s[i])
        return None
    
    def evaluate_job_listing(self, job) -> dict:
        temp_job = job.copy()
        print(f"Evaluating job listing: {job['url']}")
        prompt = f"Given the following concise CV:\n \
                {self.cv}\n\n \
                And the following job description:\n \
                {job['description']}\n\n \
                Candidate IS NOT applying for this job, but interested in a trainee position in the company.\
                Would the candidate's skillset and interests align with this company's position?\
                Answer with integer number from 1 to 10."
        primary_evaluation = self.ask(prompt=prompt)
        print(primary_evaluation)
        # Set the "evaluated" field to True
        temp_job["evaluated"] = True
        evaluation = self.__find_first_int_len1_or2(primary_evaluation)
        if evaluation != None:
            temp_job["ranking"] = evaluation
        return temp_job
    
    def make_application_letter(self, job) -> None:
        print(f"Forming the application letter: {job["company"]}\t{job["id"]}")
        prompt = f"Given the following CV and skills:\n \
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
            f.write(f"APPLICATION LINK: {listing_information["url"]}\nCOMPANY: {listing_information["company"]}\n##################\n\n\n{letter}")