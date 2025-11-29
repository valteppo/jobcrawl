import os
import json

class JobListing:
    def __init__(self, url: str):
        self.url = url
        self.id = self.url.split("/")[-1]
        self.company = None
        self.language = ""
        self.description = None
        self.publish_date = ""
        self.expiry_date  = ""
        self.evaluated = False
        self.ranking = -1
        self.application = ""
    
    def to_dict(self) -> dict:
        return {
            "url":self.url,
            "id":self.id,
            "company":self.company,
            "language":self.language,
            "description":self.description,
            "publish_date":self.publish_date,
            "expiry_date":self.expiry_date,
            "evaluated":self.evaluated,
            "ranking":self.ranking,
            "application":self.application
        }
    
    def load_from_json_ob(self, listing_data):
        self.company = listing_data["company"]
        self.language = listing_data["language"]
        self.description = listing_data["description"]
        self.publish_date = listing_data["publish_date"]
        self.expiry_date = listing_data["expiry_data"]
        self.evaluated = listing_data["evaluated"]
        self.ranking = listing_data["ranking"]
        self.application = listing_data["application"]

    def reload_from_dir(self):
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, "output")
        output_dir = os.path.join(output_dir, "listings")
        os.makedirs(output_dir, exist_ok=True)
        company_dir = os.path.join(output_dir, self.company)
        os.makedirs(company_dir, exist_ok=True)
        listing_file_path = os.path.join(company_dir, f"{self.id}.json")
        try:
            with open(listing_file_path, "r", encoding="utf-8") as f:
                listing_data = json.load(f)
                self.company = listing_data["company"]
                self.language = listing_data["language"]
                self.description = listing_data["description"]
                self.publish_date = listing_data["publish_date"]
                self.expiry_date = listing_data["expiry_data"]
                self.evaluated = listing_data["evaluated"]
                self.ranking = listing_data["ranking"]
                self.application = listing_data["application"]
                
        except FileNotFoundError:
            pass
    
    def save(self):
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, "output")
        output_dir = os.path.join(output_dir, "listings")
        os.makedirs(output_dir, exist_ok=True)
        company_dir = os.path.join(output_dir, self.company)
        os.makedirs(company_dir, exist_ok=True)
        listing_file_path = os.path.join(company_dir, f"{self.id}.json")
        with open(listing_file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)
    
    def reset(self):
        self.evaluated = False
        self.ranking = -1
        self.application = ""
        self.save()

def load_saved_listing_information() -> list[JobListing] | None:
    cwd = os.getcwd()
    input_dir = os.path.join(cwd, "output")
    input_dir = os.path.join(input_dir, "listings")
    result = []
    try:
        for company_dir in os.listdir(input_dir):
            company_path = os.path.join(input_dir, company_dir)
            if os.path.isdir(company_path):
                for listing_file in os.listdir(company_path):
                    file_path = os.path.join(company_path, listing_file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        listing_data = json.load(f)
                        job = JobListing(listing_data["url"])
                        job.load_from_json_ob(listing_data)
                        result.append(job)

    except FileNotFoundError:
        print(f"No existing listings found in {input_dir}.")
    
    if len(result) == 0:
        result = None
    return result
