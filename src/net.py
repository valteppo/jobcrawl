import requests
import os
import json
import aiohttp
import asyncio

import data

class Netparser:
    def __init__(self, selected_job_field: str = "ohjelmisto_ala", skip_download: bool = False):
        self.job_field_base_urls = {
            "ohjelmisto_ala": "https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys"
        }
        self.selected_job_field = selected_job_field
        self.base_url = self.job_field_base_urls[self.selected_job_field]
        self.already_downloaded_listing_urls = self._load_all_downloaded_data()
        self.field_listing_urls = []
        self.current_page_content = []
        self.listing_information = []
        self._load_listing_information()

    def download(self):
        """
        This downloads the jobs not found on the folder and saves them.
        """
        self.form_listing_urls()
        web_data = self._bulk_download(self.field_listing_urls)
        for web_content in web_data:
            company_name = self._job_listing_company_extraction(web_content)
            language, job_description = self._job_listing_description_extraction(web_content)
            publish_date = self._job_listing_publish_date_extraction(web_content)
            expiry_date = self._job_listing_expiry_date_extraction(web_content)
            listing_information = {
                "url": job_url,
                "company": company_name,
                "language": language,
                "id": job_id,
                "description": job_description,
                "publish_date": publish_date,
                "expiry_date": expiry_date,
                "evaluated": False,
                "ranking": 0,
            }

    def form_listing_urls(self) -> list[str] | None:
        """
        This checks what listings have not been downloaded yet and adds them as urls to 
        self.field_listing_urls
        """

        # Get the main page to Ala.
        main_page = self._single_download(self.base_url)
        if not main_page:
            print("Error on main page fetch: ", self.base_url)
            return
        
        # Get max pagination and form urls
        page_count = self._find_max_pagination(main_page)
        page_urls = []
        for page in range(2, page_count+1):
            url = self.base_url + f"?sivu={page}"
            page_urls.append(url)
        
        # Launch queries to get the paginated content
        listed_jobs_in_pages = self._bulk_download(page_urls)

        # Extract the listing url displayed on each page.
        res = []
        temp = self._get_job_listings(main_page)
        [res.append(i) for i in temp]
        for page_content in listed_jobs_in_pages:
            temp = self._get_job_listings(page_content)
            [res.append(i) for i in temp]

        # If url not already handled, put it to query
        for url in res:
            if url not in self.already_downloaded_listing_urls:
               self.field_listing_urls

    def _load_all_downloaded_data(self):
        jobs = data.load_saved_listing_information()
        urls = []
        for job in jobs:
            urls.append(job.url)
        return urls
    
    def _single_download(self, url) -> list[str] | None:
        # Returns the website as list[str]
        req = requests.get(url)
        if req.status_code == 200:
            return req.text.splitlines()
        else:
            return None
        
    def _bulk_download(self, list_of_urls) -> list[list[str]] | None:
        # Returns a list of websites
        async def fetch_url(session: aiohttp.ClientSession, url: str)-> list[str] | None:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()  
                    return await response.text().splitlines()
            except aiohttp.ClientError as e:  
                print(f"Error fetching {url}: {e}")
                return None 
            
        async def query_urls_async(urls: list[str]) -> list[str | None]:
            async with aiohttp.ClientSession() as session:  
                tasks = [fetch_url(session, url) for url in urls]
                results = await asyncio.gather(*tasks)  
                filtered = []
                for res in results:
                    if res != None:
                        filtered.append(res)
                if len(filtered) == 0:
                    return None
                return filtered
        
        return asyncio.run(query_urls_async(list_of_urls))


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
                "expiry_date": expiry_date,
                "evaluated": False,
                "ranking": 0,
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

    def _remove_divclass_from_description(self, description: str) -> str:
        # remove <div class=\" ... ">
        while '<div class="' in description:
            start_index = description.find('<div class="')
            end_index = description.find('">', start_index) + 2
            description = description[:start_index] + description[end_index:]
        return description.strip()
    
    def _remove_anchor_tags_from_description(self, description: str) -> str:
        # remove <a " ... ">" tags and remove closing </a>
        while '<a ' in description:
            start_index = description.find('<a ')
            end_index = description.find('>', start_index) + 1
            description = description[:start_index] + description[end_index:]
        while '</a>' in description:
            description = description.replace('</a>', '')
        return description.strip()

    def _job_listing_id_extraction(self, url) -> str:
        return url.split("/")[-1]

    def _job_listing_company_extraction(self, web_content) -> str:
        for line in web_content:
            if '<meta property="article:author" content="' in line:
                start_index = line.find('content="') + len('content="')
                end_index = line.find('"', start_index)
                company_name = line[start_index:end_index]

                # remove characters that are not allowed in folder names
                invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
                for char in invalid_chars:
                    company_name = company_name.replace(char, '')
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
        description_lines = []
        capture = False
        div_counter = 0
        for line in web_content:
            if 'om jobbet</h2>' in line.lower():
                lang = "sv"
                div_counter += 1
                capture = True
                continue
            if 'työpaikkakuvaus</h2>' in line.lower():
                lang = "fi"
                div_counter += 1
                capture = True
                continue
            if 'job description</h2>' in line.lower():
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

        # Replace </p> and <br> with newlines
        result = result.replace("</p>", "\n").replace("<br>", "\n")

        # Replacs \u00e4 and \u00f6 with ä and ö
        result = result.replace("\u00e4", "ä").replace("\u00f6", "ö")

        # Replace U+00a0 with space
        result = result.replace("\u00a0", " ")

        # Trim excessive newlines
        result = "\n".join([line for line in result.splitlines() if line.strip() != ""])

        result = self._remove_divclass_from_description(result)
        result = self._remove_anchor_tags_from_description(result)

        # Remove any remaining HTML tags
        if '<' in result and '>' in result:
            cleaned_result = ""
            inside_tag = False
            for char in result:
                if char == '<':
                    inside_tag = True
                elif char == '>':
                    inside_tag = False
                elif not inside_tag:
                    cleaned_result += char
            result = cleaned_result.strip()

        return lang, result
    
    
    def _find_max_pagination(self, page_web_content):
        res = 0
        for line in page_web_content:
            if '"class="pagination__pagenum' in line:
                start_index = line.find('"class="pagination__pagenum') + len('"class="pagination__pagenum')
                limiter_start = line.find(">", start_index)
                limiter_end = line.find("<", limiter_start)
                page = int(line[limiter_start:limiter_end])
                if page > res:
                    res = page
        return res

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
    