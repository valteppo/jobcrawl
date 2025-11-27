import requests
import os
import json

class Netparser:
    def __init__(self, selected_job_field: str = "ohjelmisto_ala"):
        self.job_field_base_urls = {
            "ohjelmisto_ala": "https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys"
        }
        self.selected_job_field = selected_job_field
        self.field_listing_urls = []
        self.current_page_content = []
        self.listing_information = []
        self._load_listing_information()
        self._find_individual_listings()
        print(f"Total job offers found: {len(self.field_listing_urls)}")
        self._form_listing_information()

    def listings(self) -> list:
        return self.listing_information
    
    def _load_listing_information(self) -> None:
        cwd = os.getcwd()
        input_dir = os.path.join(cwd, "output")
        input_dir = os.path.join(input_dir, "listings")
        try:
            for company_dir in os.listdir(input_dir):
                company_path = os.path.join(input_dir, company_dir)
                if os.path.isdir(company_path):
                    for listing_file in os.listdir(company_path):
                        file_path = os.path.join(company_path, listing_file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            listing_data = json.load(f)
                            self.listing_information.append(listing_data)
        except FileNotFoundError:
            print(f"No existing listings found in {input_dir}. Starting fresh.")
    
    def _save_listing_information(self, listing_information) -> None:
        # Save individual listings as they are fetched
        cwd = os.getcwd()
        output_dir = os.path.join(cwd, "output")
        output_dir = os.path.join(output_dir, "listings")
        os.makedirs(output_dir, exist_ok=True)
        for listing in self.listing_information:
            company_dir = os.path.join(output_dir, listing["company"])
            os.makedirs(company_dir, exist_ok=True)
            listing_file_path = os.path.join(company_dir, f"{listing['id']}.json")
            with open(listing_file_path, "w", encoding="utf-8") as f:
                json.dump(listing, f, ensure_ascii=False, indent=4)

    def _form_listing_information(self) -> None:
        for job_url in self.field_listing_urls:
            # Check if listing already exists
            if any(listing["url"] == job_url for listing in self.listing_information):
                continue
            print(f"Fetching listing information for: {job_url}")
            web_content = requests.get(job_url).text.splitlines()
            company_name = self._job_listing_company_extraction(web_content)
            language, job_description = self._job_listing_description_extraction(web_content)
            job_id = self._job_listing_id_extraction(job_url)
            publish_date = self._job_listing_publish_date_extraction(web_content)
            expiry_date = self._job_listing_expiry_date_extraction(web_content)
            listing_information = {
                "url": job_url,
                "company": company_name,
                "language": language,
                "id": job_id,
                "description": job_description,
                "publish_date": publish_date,
                "expiry_date": expiry_date
            }
            self._save_listing_information(listing_information)
            if listing_information["company"] == "Unknown Company":
                print("Warning: Company name could not be extracted.")
                print(listing_information)
                return
            if len(listing_information["description"]) < 100:
                print("Warning: Job description seems too short.")
                print(listing_information)
                return
            self.listing_information.append(listing_information)


    def _find_individual_listings(self) -> None:
        self.field_listing_urls = self._get_field_listings()

    def _job_listing_id_extraction(self, url) -> str:
        return url.split("/")[-1]

    def _job_listing_company_extraction(self, web_content) -> str:
        for line in web_content:
            if '<meta property="article:author" content="' in line:
                start_index = line.find('content="') + len('content="')
                end_index = line.find('"', start_index)
                company_name = line[start_index:end_index]
                return company_name
        return "Unknown Company"
    
    def _job_listing_publish_date_extraction(self, web_content) -> str:
        for line in web_content:
            if '<meta property="article:published_time" content="' in line:
                start_index = line.find('content="') + len('content="')
                end_index = line.find('"', start_index)
                publish_date = line[start_index:end_index]
                return publish_date
        return "Unknown Date"
    
    def _job_listing_expiry_date_extraction(self, web_content) -> str:
        for line in web_content:
            if '<meta property="article:expiration_time" content="' in line:
                start_index = line.find('content="') + len('content="')
                end_index = line.find('"', start_index)
                expiry_date = line[start_index:end_index]
                return expiry_date
        return "Unknown Date"

    def _job_listing_description_extraction(self, web_content) -> tuple:
        strip_html_tags = \
            ["<li>",
            "</li>",
            "<ul>",
            "</ul>",
            "<div>", 
            "</div>", 
            "<br>", 
            "<br/>", 
            "<br />", 
            "<p>",  
            "<strong>",
            "</strong>", 
            "<em>", 
            "</em>"]
        description_lines = []
        capture = False
        div_counter = 0
        for line in web_content:
            if 'om jobbet' in line.lower():
                lang = "sv"
                div_counter += 1
                capture = True
                continue
            if 'työpaikkakuvaus' in line.lower():
                lang = "fi"
                div_counter += 1
                capture = True
                continue
            if 'job description' in line.lower():
                lang = "en"
                div_counter += 1
                capture = True
                continue
            if capture:
                description_lines.append(line.strip())
            if '<div' in line and capture:
                div_counter += 1
            if '</div>' in line and capture:
                div_counter -= 1
                if div_counter == 0:
                    break
        result = "\n".join(description_lines)

        # Strip HTML tags
        for tag in strip_html_tags:
            result = result.replace(tag, " ")
        
        # Replace < /p> with newlines
        result = result.replace("</p>", "\n")

        # Remove <a href="...">...</a> links
        while '<a href="' in result:
            start_index = result.find('<a href="')
            end_index = result.find('">', start_index) + 2
            link_text_start = end_index
            link_text_end = result.find('</a>', link_text_start)
            link_text = result[link_text_start:link_text_end]
            result = result[:start_index] + link_text + result[link_text_end + 4:]

        # Replacs \u00e4 and \u00f6 with ä and ö
        result = result.replace("\u00e4", "ä").replace("\u00f6", "ö")

        # Trim excessive newlines
        result = "\n".join([line for line in result.splitlines() if line.strip() != ""])

        return lang, result

    def _get_job_field_base_url(self) -> str:
        return self.job_field_base_urls[self.selected_job_field]
    
    def _get_field_listings(self) -> list:
        url = self._get_job_field_base_url()
        web_query = requests.get(url)
        page = 1
        result = []
        while web_query.status_code == 200:
            temp_listings = []
            page_content = web_query.text.splitlines()
            temp_listings = self._get_job_listings(page_content)
            result.extend([i for i in temp_listings if i not in result])
            page = page + 1
            web_query = requests.get(url + f"?sivu={page}")
        print(f"Total pages fetched: {page - 1}")
        return result

    def _get_job_listings(self, page_web_content) -> list:
        # if job listing already saved, skip it
        for listing in self.listing_information:
            if listing["url"] in page_web_content:
                return []

        job_marker = 'href="/tyopaikat/tyo/'
        job_listings = []
        for line in page_web_content:
            if "Duunitori suosittelee" in line:
                return job_listings
            if job_marker in line and "lisaa_suosikkeihin" not in line:
                # find the href link between href=" and </a>
                start_index = line.find('href="') + len('href="')
                end_index = line.find('">', start_index)
                job_link = line[start_index:end_index]
                job_link = "https://duunitori.fi" + job_link
                job_listings.append(job_link)
        return job_listings
    