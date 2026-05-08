import os
import sqlite3

class JobListing:
    def __init__(self):
        self.url = None
        self.url_id = 0
        self.company = None
        self.publish_date = None
        self.expiry_date = None
        self.language = None
        self.evaluated = False
        self.ranking = -1
        self.description = None
        self.application = ""
        self.contact = None 
        self.ala_id = None
        self._db_path = os.path.join(os.getcwd(), "db", "db")

    def __str__(self):
        status = "✅ Evaluated" if self.evaluated else "⏳ Pending"
        score = f"[{self.ranking}/10]" if self.evaluated else "[No Score]"
        
        return (
            f"--- Job Listing {self.url_id} ---\n"
            f"Company: {self.company}\n"
            f"Score:   {score}\n"
            f"Status:  {status}\n"
            f"Contact: {self.contact}\n"
            f"URL:     {self.url}\n"
            f"---------------------------"
        )

    def __repr__(self):
        return f"<JobListing(id={self.url_id}, company='{self.company}', ranking={self.ranking})>"

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "url_id": self.url_id,
            "ala_id": self.ala_id, 
            "company": self.company,
            "language": self.language,
            "description": self.description,
            "publish_date": self.publish_date,
            "expiry_date": self.expiry_date,
            "evaluated": self.evaluated,
            "ranking": self.ranking,
            "application": self.application,
            "contact": self.contact 
        }

    def save(self):
        with sqlite3.connect(self._db_path) as con:
            cur = con.cursor()
            params = (
                self.url,            # 1
                self.url_id,         # 2
                self.company,        # 3
                self.publish_date,   # 4
                self.expiry_date,    # 5
                self.language,       # 6
                int(self.evaluated), # 7 (Stored as 0 or 1)
                self.ranking,        # 8
                self.description,    # 9
                self.application,    # 10
                self.ala_id,         # 11
                self.contact         # 12
            )
            
            cur.execute("""
            INSERT INTO jobs (
                url, url_id, company, publish_date, expiry_date, 
                language, evaluated, ranking, description, application,
                ala_id, contact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url_id) DO UPDATE SET
                application = excluded.application,
                evaluated = excluded.evaluated,
                ranking = excluded.ranking,
                contact = excluded.contact,
                ala_id = excluded.ala_id
            """, params)
            con.commit()

    @classmethod
    def load(cls, url_id: int):
        db_path = os.path.join(os.getcwd(), "db", "db")

        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row 
            cur = con.cursor()
            cur.execute("SELECT * FROM jobs WHERE url_id = ?", (url_id,))
            row = cur.fetchone()
            
            if row is None:
                return None
            
            job = cls()
            job.url = row['url']
            job.url_id = row['url_id']
            job.ala_id = row['ala_id'] 
            job.company = row['company']
            job.publish_date = row['publish_date']
            job.expiry_date = row['expiry_date']
            job.language = row['language']
            job.evaluated = bool(row['evaluated'])
            job.ranking = row['ranking']
            job.description = row['description']
            job.application = row['application']
            job.contact = row['contact'] 
            
            return job

    @staticmethod
    def load_all():
        db_path = os.path.join(os.getcwd(), "db", "db")
        if not os.path.exists(db_path):
            return []
            
        jobs = []
        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT * FROM jobs")
            for row in cur.fetchall():
                job = JobListing()
                job.url = row['url']
                job.url_id = row['url_id']
                job.ala_id = row['ala_id']
                job.company = row['company']
                job.publish_date = row['publish_date']
                job.expiry_date = row['expiry_date']
                job.language = row['language']
                job.evaluated = bool(row['evaluated'])
                job.ranking = row['ranking']
                job.description = row['description']
                job.application = row['application']
                job.contact = row['contact']
                jobs.append(job)
        return jobs

