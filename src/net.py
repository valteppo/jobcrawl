import requests

import data
from data import JobListing

class Netparser:
    def __init__(self, selected_job_field: str = "ohjelmisto_ala"):
        self.job_field_base_urls = {
            "ohjelmisto_ala": "https://duunitori.fi/tyopaikat/ala/ohjelmointi-ja-ohjelmistokehitys"
        }
        self.selected_job_field = selected_job_field
        self.base_url = self.job_field_base_urls[self.selected_job_field]
        self.already_downloaded_listing_urls = self._load_all_downloaded_data()
        self.field_listing_urls = []
        self.current_page_content = []
        self.listing_information = []

    def download_n(self, n: int):
        """
        This downloads n jobs from the self.field_listing_urls query and saves them.
        """
        if len(self.field_listing_urls) == 0:
            print("Query empty. If not intentional, run self.form_listing_urls() before.")
        job_list = []
        for url in self.field_listing_urls[:n]:
            this_url, status_code, web_content = self._single_download(url)
            if status_code != 200:
                print("Statuscode",status_code, this_url)
                continue
            else:
                print("Downloaded",this_url)
            job = JobListing(url=this_url)
            job.company = self._job_listing_company_extraction(web_content)
            language, job_description = self._job_listing_description_extraction(web_content)
            job.language = language
            job.description = job_description
            job.publish_date = self._job_listing_publish_date_extraction(web_content)
            job.expiry_date = self._job_listing_expiry_date_extraction(web_content)
            job.save()
            self.field_listing_urls.remove(this_url)
            job_list.append(job)
        return job_list
    
    def form_listing_urls(self):
        """
        This checks what listings have not been downloaded yet and adds them as urls to 
        self.field_listing_urls
        """

        # Get the main page to Ala.
        main_url, status_code, main_page = self._single_download(self.base_url)
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
        # Tried async fetch, resulted in 403 forbidden
        listed_jobs_in_pages = []
        for url in page_urls:
            this_url, status_code, page_content = self._single_download(url)
            if status_code == 200:
                listed_jobs_in_pages.append((this_url, page_content))
            else:
                print("Not all jobs were fetched.",status_code, url)     

        # Extract the listing url displayed on each page.
        res = []
        temp = self._get_job_listings(main_page)
        [res.append(i) for i in temp]
        for content in listed_jobs_in_pages:
            page_url, page_content = content
            temp = self._get_job_listings(page_content)
            [res.append(i) for i in temp]
        

        # If url not already handled, put it to query
        for url in res:
            if self.already_downloaded_listing_urls == None:
                self.field_listing_urls.append(url)
            elif url not in self.already_downloaded_listing_urls:
                self.field_listing_urls.append(url)

    def _load_all_downloaded_data(self):
        jobs = data.load_saved_listing_information()
        urls = []
        if jobs == None:
            return None
        for job in jobs:
            urls.append(job.url)
        return urls
    
    def _single_download(self, url) -> tuple[str, list[str]] | None:
        # Returns the website as tuple(url, status_code, web content)
        req = requests.get(url)
        if req.status_code == 200:
            return (url, req.status_code, req.text.splitlines())
        else:
            return (url, req.status_code, [])

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
            if 'pagination' in line:
                try:
                    start_index = line.find('pagination') + len('pagination')
                    limiter_start = line.find(">", start_index) + len(">")
                    limiter_end = line.find("<", limiter_start)
                    page = int(line[limiter_start:limiter_end])
                    if page > res:
                        res = page
                except:
                    pass
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
    