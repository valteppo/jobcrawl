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
        self.application = None
        self.contact = None 
        self.ala_id = None
        self._db_path = os.path.join(os.getcwd(), "db", "db")
    
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
            cur.execute("""
            INSERT INTO jobs (
                url, url_id, company, publish_date, expiry_date, 
                language, evaluated, ranking, description, application,
                ala_id, contact
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url_id) DO UPDATE SET
                ala_id = excluded.ala_id,
                contact = excluded.contact,
                description = excluded.description,
                company = excluded.company,
                publish_date = excluded.publish_date,
                expiry_date = excluded.expiry_date
            """, (self.url, self.url_id, self.company, self.publish_date, 
                  self.expiry_date, self.language, self.evaluated, 
                  self.ranking, self.description, self.application,
                  self.ala_id, self.contact))
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
            
        with sqlite3.connect(db_path) as con:
            cur = con.cursor()
            cur.execute("SELECT url_id FROM jobs")
            ids = cur.fetchall()
            
        return [JobListing.load(row[0]) for row in ids]
