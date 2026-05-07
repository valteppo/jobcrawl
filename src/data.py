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
        self._db_path = os.path.join(os.getcwd(), "db", "db")
        self.ala_id = None
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "url_id": self.url_id,
            "company": self.company,
            "language": self.language,
            "description": self.description,
            "publish_date": self.publish_date,
            "expiry_date": self.expiry_date,
            "evaluated": self.evaluated,
            "ranking": self.ranking,
            "application": self.application
        }
    def save(self):
        db_path = os.path.join(os.getcwd(), "db", "db")
        with sqlite3.connect(db_path) as con:
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
                description = excluded.description
            """, (self.url, self.url_id, self.company, self.publish_date, 
                  self.expiry_date, self.language, self.evaluated, 
                  self.ranking, self.description, self.application,
                  self.ala_id, self.contact))
            con.commit()

    @classmethod
    def load(cls, url_id: int):
        """Fetches a single job by url_id and returns a JobListing instance."""
        db_path = os.path.join(os.getcwd(), "db", "db")
        
        if not os.path.exists(db_path):
            return None

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
            job.company = row['company']
            job.publish_date = row['publish_date']
            job.expiry_date = row['expiry_date']
            job.language = row['language']
            job.evaluated = bool(row['evaluated']) # Convert 0/1 back to True/False
            job.ranking = row['ranking']
            job.description = row['description']
            job.application = row['application']
            
            return job

    @staticmethod
    def load_all():
        """Returns a list of all JobListing objects in the database."""
        db_path = os.path.join(os.getcwd(), "db", "db")
        with sqlite3.connect(db_path) as con:
            con.row_factory = sqlite3.Row
            cur = con.cursor()
            cur.execute("SELECT url_id FROM jobs")
            ids = cur.fetchall()
            
        return [JobListing.load(row['url_id']) for row in ids]
