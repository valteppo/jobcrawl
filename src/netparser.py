import os
import re
import sqlite3
import requests
import time
from data import JobListing

class Netparser:
    def __init__(self, ala_name: str = "ohjelmisto_ala"):
        self._db_path = os.path.join(os.getcwd(), "db", "db")
        self.ala_name = ala_name
        self.base_url = self._get_base_url_from_db()
        self.chunk_size = 5 
        self.request_delay = 1.0 # seconds

    def _get_ala_config_from_db(self):
        with sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT id, base_url FROM ala WHERE name = ?", (self.ala_name,))
            res = cur.fetchone()
            if not res:
                raise ValueError(f"Category '{self.ala_name}' not found.")
            return res[0], res[1]

    def _get_base_url_from_db(self) -> str:
        with sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT base_url FROM ala WHERE name = ?", (self.ala_name,))
            res = cur.fetchone()
            if not res:
                raise ValueError(f"Category '{self.ala_name}' not found.")
            return res[0]

    def _get_existing_url_ids(self) -> set:
        with sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT url_id FROM jobs")
            return {row[0] for row in cur.fetchall()}

    def update_database(self):
        """Main method: Now processes in smaller batches to avoid timeouts."""
        print(f"--- Starting Update for: {self.ala_name} ---")
        
        existing_ids = self._get_existing_url_ids()
        all_online_urls = self._fetch_all_listing_urls()
        
        new_urls = []
        for url in all_online_urls:
            try:
                uid = int(url.split('-')[-1])
                if uid not in existing_ids:
                    new_urls.append((url, uid))
            except: continue

        print(f"Found {len(new_urls)} new jobs. Processing in chunks of {self.chunk_size}...")

        count = 0
        for i in range(0, len(new_urls), self.chunk_size):
            batch = new_urls[i : i + self.chunk_size]
            print(f"Processing batch {i//self.chunk_size + 1}...")
            
            for url, uid in batch:
                if self._download_and_save(url, uid):
                    count += 1
                time.sleep(self.request_delay) # Politeness delay
            
        print(f"--- Finished. {count} jobs processed. ---")

    def _fetch_all_listing_urls(self) -> list:
        """Crawls pagination with small delays to get job links."""
        first_page = self._get_raw_html(self.base_url)
        if not first_page: return []

        max_page = self._find_max_pagination(first_page)
        urls = self._extract_links_from_content(first_page)

        for p in range(2, max_page + 1):
            print(f"Scanning listing page {p}/{max_page}...")
            page_content = self._get_raw_html(f"{self.base_url}?sivu={p}")
            if page_content:
                urls.extend(self._extract_links_from_content(page_content))
            time.sleep(0.5) # Slight delay between pagination pages
            
        return list(set(urls))

def _download_and_save(self, url: str, url_id: int) -> bool:
        content = self._get_raw_html(url)
        if not content: return False

        job = JobListing()
        job.url = url
        job.url_id = url_id
        job.ala_id = self.ala_id
        job.company = self._extract_company(content)
        job.publish_date, job.expiry_date = self._extract_dates(content)
        job.language, job.description = self._extract_description(content)
        job.contact = self._extract_contact(content)
        
        job.save()
        return True

    def _get_raw_html(self, url: str):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=headers, timeout=15)
            return r.text.splitlines() if r.status_code == 200 else None
        except requests.exceptions.RequestException as e:
            print(f"Timeout or error on {url}. Skipping...")
            return None

    def _extract_links_from_content(self, lines: list) -> list:
        marker = 'href="/tyopaikat/tyo/'
        links = []
        for line in lines:
            if marker in line and "lisaa_suosikkeihin" not in line:
                match = re.search(r'href="([^"]+)"', line)
                if match:
                    links.append("https://duunitori.fi" + match.group(1))
        return links

    def _find_max_pagination(self, lines: list) -> int:
        pages = [1]
        for line in lines:
            if 'pagination' in line:
                nums = re.findall(r'>(\d+)<', line)
                pages.extend([int(n) for n in nums])
        return max(pages)

    def _extract_company(self, lines: list) -> str:
        for line in lines:
            if 'article:author" content="' in line:
                return re.sub(r'[<>:"/\\|?*]', '', line.split('content="')[1].split('"')[0])
        return "Unknown"

    def _extract_dates(self, lines: list) -> tuple:
        pub, exp = "Unknown", "Unknown"
        for line in lines:
            if 'published_time' in line: pub = line.split('content="')[1].split('"')[0]
            if 'expiration_time' in line: exp = line.split('content="')[1].split('"')[0]
        return pub, exp

    def _extract_description(self, lines: list) -> tuple:
        markers = {'om jobbet</h2>': 'sv', 'työpaikkakuvaus</h2>': 'fi', 'job description</h2>': 'en'}
        capture, lang, desc_lines, depth = False, "unknown", [], 0
        for line in lines:
            lower = line.lower()
            for m, l in markers.items():
                if m in lower:
                    lang, capture, depth = l, True, 1
                    continue
            if capture:
                desc_lines.append(line)
                depth += line.count('<div'); depth -= line.count('</div>')
                if depth <= 0: break
        raw = "\n".join(desc_lines).replace("</p>", "\n").replace("<br>", "\n")
        return lang, re.sub('<[^<]+?>', '', raw).strip()

    def _extract_contact(self, lines: list) -> str:
        """Attempts to find an email address or an application URL in the text."""
        content_text = "\n".join(lines)
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, content_text)
        if emails:
            return emails[0]            

        link_pattern = r'href="(https?://[^"]+(?:apply|rekry|careers|job)[^"]+)"'
        links = re.findall(link_pattern, content_text)
        if links:
            return links[0]
            
        return "Not found"
