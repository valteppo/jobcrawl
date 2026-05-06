--schema

CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY,
  url_id INTEGER UNIQUE,
  url TEXT,
  company TEXT,
  publish_date TIMESTAMP,
  expiry_date TIMESTAMP,
  language TEXT,
  evaluated INTEGER,
  ranking INTEGER,
  description TEXT,
  application TEXT
);

